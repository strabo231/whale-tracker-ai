import os
import jwt
import bcrypt
import stripe
import re
from datetime import datetime, timedelta
from functools import wraps
from flask import Flask, jsonify, request, g
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask import send_from_directory
import sqlite3
import logging
from werkzeug.security import generate_password_hash, check_password_hash
# Configure logging for production
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s: %(message)s',
    handlers=[
        logging.FileHandler('whale_tracker.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Production configuration
app.config.update(
    SECRET_KEY=os.environ.get('SECRET_KEY', 'your-super-secret-key-change-this'),
    JWT_SECRET_KEY=os.environ.get('JWT_SECRET_KEY', 'jwt-secret-change-this'),
    DATABASE_URL=os.environ.get('DATABASE_URL', 'whales.db'),
    ENVIRONMENT=os.environ.get('ENVIRONMENT', 'development')
)

# Stripe configuration
stripe.api_key = os.environ.get('STRIPE_SECRET_KEY', 'sk_test_your_test_key_here')
STRIPE_WEBHOOK_SECRET = os.environ.get('STRIPE_WEBHOOK_SECRET', 'whsec_your_webhook_secret')

# Enable CORS with specific origins for production
if app.config['ENVIRONMENT'] == 'production':
    CORS(app, origins=['https://whale-tracker-ai.up.railway.app'])
else:
    CORS(app)  # Allow all origins in development

# Rate limiting
limiter = Limiter(
    key_func=get_remote_address,
    app=app,
    default_limits=["1000 per day", "100 per hour"],
    storage_uri="memory://"
)

# Database setup with error handling
def get_db_connection():
    try:
        conn = sqlite3.connect(app.config['DATABASE_URL'])
        conn.row_factory = sqlite3.Row
        return conn
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        raise

def init_db():
    """Initialize database with proper schema"""
    try:
        conn = get_db_connection()
        
        # Users table for authentication
        conn.execute('''CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            subscription_tier TEXT DEFAULT 'free',
            stripe_customer_id TEXT,
            stripe_subscription_id TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_active BOOLEAN DEFAULT 1
        )''')
        
        # Whales table with enhanced fields
        conn.execute('''CREATE TABLE IF NOT EXISTS whales (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            address TEXT UNIQUE NOT NULL,
            balance REAL,
            source TEXT,
            quality_score INTEGER,
            blockchain TEXT DEFAULT 'solana',
            first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_activity TIMESTAMP,
            is_verified BOOLEAN DEFAULT 0,
            created_by INTEGER,
            FOREIGN KEY (created_by) REFERENCES users (id)
        )''')
        
        # Minimal API usage tracking (privacy-focused)
        conn.execute('''CREATE TABLE IF NOT EXISTS api_usage (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            request_count INTEGER DEFAULT 1,
            date DATE DEFAULT (DATE('now')),
            FOREIGN KEY (user_id) REFERENCES users (id),
            UNIQUE(user_id, date)
        )''')
        
        conn.commit()
        logger.info("Database initialized successfully")
        
        # Add demo data if empty (for development)
        if app.config['ENVIRONMENT'] == 'development':
            cursor = conn.execute('SELECT COUNT(*) FROM whales')
            if cursor.fetchone()[0] == 0:
                demo_whales = [
                    ('8K7x9mP2qR5vN3wL6tF4sC1dE9yH2jM5pQ7rT8xZ3aB6', 125000, 'r/solana', 85, 'solana', datetime.now(), datetime.now(), 1),
                    ('3F9k2L7mR8qN4vP1tX6sC9yE5bH8jW2nQ4rT7zA5mL3K', 89000, 'r/cryptocurrency', 78, 'ethereum', datetime.now(), datetime.now(), 1)
                ]
                conn.executemany('''INSERT INTO whales 
                    (address, balance, source, quality_score, blockchain, first_seen, last_activity, is_verified) 
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)''', demo_whales)
                conn.commit()
                logger.info("Demo data added")
        
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise
    finally:
        conn.close()

# Authentication decorators
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        
        if not token:
            return jsonify({'error': 'Token missing'}), 401
        
        try:
            if token.startswith('Bearer '):
                token = token[7:]
            
            data = jwt.decode(token, app.config['JWT_SECRET_KEY'], algorithms=['HS256'])
            current_user_id = data['user_id']
            
            # Minimal usage tracking (privacy-focused)
            try:
                conn = get_db_connection()
                conn.execute('''INSERT INTO api_usage (user_id, date, request_count) 
                               VALUES (?, DATE('now'), 1)
                               ON CONFLICT(user_id, date) 
                               DO UPDATE SET request_count = request_count + 1''',
                           (current_user_id,))
                conn.commit()
                conn.close()
            except Exception as e:
                logger.warning(f"Failed to log API usage: {e}")
            
            g.current_user_id = current_user_id
            
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Token expired'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Invalid token'}), 401
        except Exception as e:
            logger.error(f"Token validation error: {e}")
            return jsonify({'error': 'Token validation failed'}), 401
        
        return f(*args, **kwargs)
    return decorated

def subscription_required(required_tier='pro'):
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            try:
                conn = get_db_connection()
                cursor = conn.execute('SELECT subscription_tier FROM users WHERE id = ?', (g.current_user_id,))
                user = cursor.fetchone()
                conn.close()
                
                if not user or user['subscription_tier'] != required_tier:
                    return jsonify({'error': f'{required_tier.title()} subscription required'}), 403
                    
            except Exception as e:
                logger.error(f"Subscription check failed: {e}")
                return jsonify({'error': 'Subscription validation failed'}), 500
            
            return f(*args, **kwargs)
        return decorated
    return decorator

# Public endpoints
@app.route('/api/health', methods=['GET'])
@limiter.limit("10 per minute")
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'message': 'Whale Tracker API is running securely!',
        'version': '1.0.0',
        'environment': app.config['ENVIRONMENT']
    })

@app.route('/api/auth/register', methods=['POST'])
@limiter.limit("5 per minute")
def register():
    """User registration"""
    try:
        data = request.get_json()
     
        if not data or not data.get('email') or not data.get('password'):
            return jsonify({'error': 'Email and password required'}), 400
            
        if not is_valid_email(email):
            return jsonify({'error': 'Please enter a valid email address'}), 400
        
        email = data['email'].lower().strip()
        password = data['password']
        
        # Basic password validation
        if len(password) < 8:
            return jsonify({'error': 'Password must be at least 8 characters'}), 400
        
        # Generate password hash
        password_hash = generate_password_hash(password)
        
        conn = get_db_connection()
        try:
            conn.execute('''INSERT INTO users (email, password_hash) 
                           VALUES (?, ?)''', (email, password_hash))
            conn.commit()
            
            # Get user ID for token
            cursor = conn.execute('SELECT id FROM users WHERE email = ?', (email,))
            user = cursor.fetchone()
            
            # Generate JWT token
            token = jwt.encode({
                'user_id': user['id'],
                'email': email,
                'subscription_tier': 'free',
                'exp': datetime.utcnow() + timedelta(hours=24)
            }, app.config['JWT_SECRET_KEY'], algorithm='HS256')
            
            logger.info(f"New user registered: {email}")
            return jsonify({
                'message': 'Registration successful',
                'token': token
            }), 201
            
        except sqlite3.IntegrityError:
            return jsonify({'error': 'Email already registered'}), 409
        finally:
            conn.close()
            
    except Exception as e:
        logger.error(f"Registration error: {e}")
        return jsonify({'error': 'Registration failed'}), 500

@app.route('/api/auth/login', methods=['POST'])
@limiter.limit("10 per minute")
def login():
    """User login"""
    try:
        data = request.get_json()
        
        if not data or not data.get('email') or not data.get('password'):
            return jsonify({'error': 'Email and password required'}), 400
        
        email = data['email'].lower().strip()
        password = data['password']
        
        conn = get_db_connection()
        cursor = conn.execute('SELECT id, password_hash, subscription_tier FROM users WHERE email = ? AND is_active = 1', (email,))
        user = cursor.fetchone()
        
        if user and check_password_hash(user['password_hash'], password):
            # Generate JWT token
            token = jwt.encode({
                'user_id': user['id'],
                'email': email,
                'subscription_tier': user['subscription_tier'],
                'exp': datetime.utcnow() + timedelta(hours=24)
            }, app.config['JWT_SECRET_KEY'], algorithm='HS256')
            
            logger.info(f"User logged in: {email}")
            return jsonify({
                'token': token,
                'subscription_tier': user['subscription_tier']
            })
        else:
            logger.warning(f"Failed login attempt: {email}")
            return jsonify({'error': 'Invalid credentials'}), 401
            
        conn.close()
        
    except Exception as e:
        logger.error(f"Login error: {e}")
        return jsonify({'error': 'Login failed'}), 500
@app.route('/api/fix-users', methods=['GET'])
def fix_users():
    """Fix users with NULL subscription_tier"""
    try:
        conn = get_db_connection()
        cursor = conn.execute("SELECT COUNT(*) FROM users WHERE subscription_tier IS NULL")
        count_before = cursor.fetchone()[0]
        
        conn.execute("UPDATE users SET subscription_tier = 'free' WHERE subscription_tier IS NULL")
        conn.commit()
        conn.close()
        
        return jsonify({
            'message': 'Users fixed successfully',
            'users_fixed': count_before
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500  
        
@app.route('/api/test-endpoint', methods=['GET'])
def test_endpoint():
    return jsonify({'message': 'Test endpoint works!'})

# Stripe endpoints
@app.route('/api/create-checkout-session', methods=['POST'])
@limiter.limit("10 per minute")
def create_checkout_session():
    """Create Stripe checkout session for beta subscription"""
    try:
        data = request.get_json()
        email = data.get('email', '').lower().strip()
        
        if not email:
            return jsonify({'error': 'Email required'}), 400
        
        # Create Stripe checkout session
        checkout_session = stripe.checkout.Session.create(
            customer_email=email,
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'usd',
                    'product_data': {
                        'name': 'Whale Tracker Beta Access',
                        'description': 'Early access beta - Automatic PRO upgrade included!',
                    },
                    'unit_amount': 1900,  # $19.00 in cents
                    'recurring': {
                        'interval': 'month',
                    },
                },
                'quantity': 1,
            }],
            mode='subscription',
            success_url=request.host_url + 'success?session_id={CHECKOUT_SESSION_ID}',
            cancel_url=request.host_url + 'signup?cancelled=true',
            metadata={
                'product': 'whale_tracker_beta',
                'user_email': email
            },
            subscription_data={
                'metadata': {
                    'product': 'whale_tracker_beta',
                    'tier': 'beta_early_access'
                }
            }
        )
        
        logger.info(f"Checkout session created for: {email}")
        return jsonify({'checkout_url': checkout_session.url})
        
    except stripe.error.StripeError as e:
        logger.error(f"Stripe error: {e}")
        return jsonify({'error': 'Payment system error'}), 500
    except Exception as e:
        logger.error(f"Checkout creation error: {e}")
        return jsonify({'error': 'Failed to create checkout'}), 500

@app.route('/api/stripe-webhook', methods=['POST'])
def stripe_webhook():
    """Handle Stripe webhooks for subscription events"""
    payload = request.get_data(as_text=True)
    sig_header = request.headers.get('Stripe-Signature')
    
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, STRIPE_WEBHOOK_SECRET
        )
    except ValueError:
        logger.error("Invalid payload in webhook")
        return jsonify({'error': 'Invalid payload'}), 400
    except stripe.error.SignatureVerificationError:
        logger.error("Invalid signature in webhook")
        return jsonify({'error': 'Invalid signature'}), 400
    
    # Handle successful subscription creation
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        
        if session['mode'] == 'subscription':
            customer_email = session['customer_details']['email']
            subscription_id = session['subscription']
            
            try:
                # Create user account with beta access
                conn = get_db_connection()
                
                # Generate secure password for auto-created account
                temp_password = os.urandom(16).hex()
                password_hash = generate_password_hash(temp_password)
                
                conn.execute('''INSERT OR REPLACE INTO users 
                               (email, password_hash, subscription_tier, stripe_customer_id, stripe_subscription_id) 
                               VALUES (?, ?, ?, ?, ?)''',
                            (customer_email, password_hash, 'beta_early_access', 
                             session['customer'], subscription_id))
                conn.commit()
                conn.close()
                
                logger.info(f"Beta user created: {customer_email}")
                
            except Exception as e:
                logger.error(f"Failed to create user after payment: {e}")
    
    return jsonify({'status': 'success'})

# Protected endpoints
@app.route('/api/whales/top', methods=['GET'])
@limiter.limit("100 per hour")
@token_required
def get_top_whales():
    """Get top whales - requires paid subscription"""
    try:
        conn = get_db_connection()
        
        # Check subscription tier
        cursor = conn.execute('SELECT subscription_tier FROM users WHERE id = ?', (g.current_user_id,))
        user = cursor.fetchone()
        
        # BLOCK FREE USERS - PAYWALL HERE!
        if user['subscription_tier'] == 'free' or user['subscription_tier'] is None:
            conn.close()
            return jsonify({
                'error': 'Payment required',
                'message': 'Beta access requires $19/month subscription',
                'redirect': 'payment'
            }), 402  # Payment Required
        
        # Only paid users get past this point
        limit = 5 if user['subscription_tier'] == 'free' else 100
        
        cursor = conn.execute('''SELECT * FROM whales 
                               ORDER BY balance DESC 
                               LIMIT ?''', (limit,))

        whales = []
        for row in cursor.fetchall():
            whales.append({
                'id': row['id'],
                'address': row['address'],
                'balance': row['balance'],
                'source': row['source'],
                'quality_score': row['quality_score'],
                'blockchain': row['blockchain'],
                'first_seen': row['first_seen'],
                'last_activity': row['last_activity'],
                'is_verified': bool(row['is_verified'])
            })
        
        conn.close()
        
        return jsonify({
            'whales': whales,
            'count': len(whales),
            'subscription_tier': user['subscription_tier'],
            'limit_reached': len(whales) == limit and user['subscription_tier'] == 'free'
        })
        
    except Exception as e:
        logger.error(f"Get whales error: {e}")
        return jsonify({'error': 'Failed to fetch whales'}), 500

@app.route('/api/user/profile', methods=['GET'])
@token_required
def get_user_profile():
    """Get user profile and usage stats"""
    try:
        conn = get_db_connection()
        
        # Get user info
        cursor = conn.execute('''SELECT email, subscription_tier, created_at 
                               FROM users WHERE id = ?''', (g.current_user_id,))
        user = cursor.fetchone()
        
        # Get usage stats (privacy-focused)
        cursor = conn.execute('''SELECT SUM(request_count) as total_requests
                               FROM api_usage WHERE user_id = ?''', (g.current_user_id,))

        usage = cursor.fetchone()
        
        conn.close()
        
        subscription_tier = user['subscription_tier'] or 'free'
        
        return jsonify({
            'email': user['email'],
            'subscription_tier': subscription_tier,
            'created_at': user['created_at'],
            'total_requests': usage['total_requests'] or 0
        })
        
    except Exception as e:
        logger.error(f"Profile error: {e}")
        return jsonify({'error': 'Failed to fetch profile'}), 500

@app.route('/signup')
def signup_page():
    return '''
    <html><head><title>Sign Up</title><style>
    body{background:#1a1a2e;color:white;font-family:Arial;text-align:center;padding:50px}
    input{padding:10px;margin:10px;width:200px}
    .btn{background:#ff6b6b;color:white;padding:15px 30px;border:none;border-radius:5px}
    </style></head><body>
    <h1>🐋 Whale Tracker Beta Signup</h1>
    <form action="/api/auth/register" method="post">
    <input type="email" name="email" placeholder="Email" required><br>
    <input type="password" name="password" placeholder="Password" required><br>
    <button class="btn">Start Beta - $19/month</button>
    </form>
    </body></html>
    '''
    
def is_valid_email(email):
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None
    
@app.route('/success')
def payment_success():
    return '''
    <html><head><title>Payment Success</title>
    <style>
    body{background:#1a1a2e;color:white;font-family:Arial;text-align:center;padding:50px}
    .success-box{background:#2d2d4a;border:2px solid #4CAF50;border-radius:15px;padding:30px;max-width:500px;margin:0 auto}
    .btn{background:#ff6b6b;color:white;padding:15px 30px;border:none;border-radius:5px;text-decoration:none;display:inline-block;margin-top:20px}
    .btn:hover{background:#ff5555}
    .check{font-size:60px;color:#4CAF50;margin-bottom:20px}
    </style></head><body>
    <div class="success-box">
    <div class="check">✅</div>
    <h1>🎉 Welcome to Whale Tracker Beta!</h1>
    <p>Payment successful! Your account has been upgraded to Beta access.</p>
    <p>You now have access to:</p>
    <ul style="text-align:left;display:inline-block">
    <li>🐋 Up to 50 tracked whales</li>
    <li>📊 Quality scoring & verification</li>
    <li>🔥 Reddit whale discovery</li>
    <li>👑 FREE upgrade to PRO when it launches!</li>
    </ul>
    <a href="/" class="btn">Go to Dashboard</a>
    </div>
    </body></html>
    '''

@app.route('/landing')
def landing_page():
    return '''[<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Whale Tracker - Discover Crypto Whales Before Everyone Else</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        body {
            background: linear-gradient(135deg, #1e293b 0%, #7c3aed 50%, #1e293b 100%);
            min-height: 100vh;
        }
        .hero-gradient {
            background: linear-gradient(135deg, rgba(139, 92, 246, 0.1), rgba(59, 130, 246, 0.1));
        }
        .tier-card {
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }
        .tier-card:hover {
            transform: translateY(-8px);
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.3);
        }
        .popular-badge {
            background: linear-gradient(90deg, #f59e0b, #ef4444);
        }
        .cta-button {
            background: linear-gradient(90deg, #8b5cf6, #06b6d4);
            transition: all 0.3s ease;
        }
        .cta-button:hover {
            background: linear-gradient(90deg, #7c3aed, #0891b2);
            transform: translateY(-2px);
            box-shadow: 0 10px 20px rgba(139, 92, 246, 0.4);
        }
    </style>
</head>
<body class="text-white">
    <!-- Header -->
    <header class="border-b border-gray-800 bg-black/20 backdrop-blur-sm">
        <div class="max-w-7xl mx-auto px-4 py-4 flex items-center justify-between">
            <div class="flex items-center space-x-3">
                <div class="bg-gradient-to-r from-purple-500 to-cyan-500 p-2 rounded-lg">
                    <svg class="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"/>
                    </svg>
                </div>
                <div>
                    <h1 class="text-2xl font-bold bg-gradient-to-r from-purple-400 to-cyan-400 bg-clip-text text-transparent">
                        Whale Tracker
                    </h1>
                    <p class="text-gray-400 text-sm">AI-Powered Whale Discovery</p>
                </div>
            </div>
            <div class="flex items-center space-x-4">
                <a href="/login" class="text-gray-300 hover:text-white transition-colors">Login</a>
                <a href="#pricing" class="px-4 py-2 bg-purple-600 hover:bg-purple-700 rounded-lg transition-colors">
                    Get Started
                </a>
            </div>
        </div>
    </header>

    <!-- Hero Section -->
    <section class="hero-gradient py-20">
        <div class="max-w-7xl mx-auto px-4 text-center">
            <div class="inline-flex items-center px-4 py-2 bg-gradient-to-r from-orange-500 to-red-500 rounded-full text-white text-sm font-bold mb-8">
                <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"/>
                </svg>
                BETA ACCESS - LIMITED TIME
            </div>
            
            <h1 class="text-5xl md:text-7xl font-bold mb-6">
                Discover Crypto <br>
                <span class="bg-gradient-to-r from-purple-400 to-cyan-400 bg-clip-text text-transparent">
                    Whales
                </span> First
            </h1>
            
            <p class="text-xl text-gray-300 mb-8 max-w-3xl mx-auto">
                Track the biggest crypto holders before they make their moves. Our AI scans Reddit communities 
                to discover whale wallets with massive holdings in real-time.
            </p>
            
            <div class="flex flex-col sm:flex-row gap-4 justify-center mb-12">
                <a href="#pricing" class="cta-button px-8 py-4 rounded-lg font-semibold text-white text-lg">
                    Start Tracking Whales - $19/month
                </a>
                <a href="#how-it-works" class="px-8 py-4 border border-gray-600 rounded-lg font-semibold text-white hover:bg-white/10 transition-colors">
                    See How It Works
                </a>
            </div>
            
            <!-- Social Proof -->
            <div class="flex items-center justify-center space-x-8 text-gray-400 text-sm">
                <div class="flex items-center">
                    <svg class="w-5 h-5 mr-2 text-green-400" fill="currentColor" viewBox="0 0 20 20">
                        <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"/>
                    </svg>
                    Reddit Integration
                </div>
                <div class="flex items-center">
                    <svg class="w-5 h-5 mr-2 text-green-400" fill="currentColor" viewBox="0 0 20 20">
                        <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"/>
                    </svg>
                    AI-Powered Discovery
                </div>
                <div class="flex items-center">
                    <svg class="w-5 h-5 mr-2 text-green-400" fill="currentColor" viewBox="0 0 20 20">
                        <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"/>
                    </svg>
                    Real-time Updates
                </div>
            </div>
        </div>
    </section>

    <!-- How It Works -->
    <section id="how-it-works" class="py-20 bg-black/20">
        <div class="max-w-7xl mx-auto px-4">
            <div class="text-center mb-16">
                <h2 class="text-4xl font-bold mb-4">How Whale Tracker Works</h2>
                <p class="text-gray-400 text-lg">Advanced AI scans crypto communities to find whale wallets</p>
            </div>
            
            <div class="grid md:grid-cols-3 gap-8">
                <div class="text-center">
                    <div class="bg-gradient-to-r from-purple-500 to-pink-500 w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-6">
                        <svg class="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/>
                        </svg>
                    </div>
                    <h3 class="text-xl font-bold mb-4">AI Scans Reddit</h3>
                    <p class="text-gray-400">Our AI monitors r/solana, r/cryptocurrency, and other communities for whale mentions and wallet addresses.</p>
                </div>
                
                <div class="text-center">
                    <div class="bg-gradient-to-r from-cyan-500 to-blue-500 w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-6">
                        <svg class="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"/>
                        </svg>
                    </div>
                    <h3 class="text-xl font-bold mb-4">Verifies & Scores</h3>
                    <p class="text-gray-400">Each wallet is verified for balance and activity, then scored based on holding size and community credibility.</p>
                </div>
                
                <div class="text-center">
                    <div class="bg-gradient-to-r from-green-500 to-yellow-500 w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-6">
                        <svg class="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"/>
                        </svg>
                    </div>
                    <h3 class="text-xl font-bold mb-4">Real-time Dashboard</h3>
                    <p class="text-gray-400">Access your personalized whale tracker dashboard with live updates and detailed analytics.</p>
                </div>
            </div>
        </div>
    </section>

    <!-- Pricing -->
    <section id="pricing" class="py-20">
        <div class="max-w-7xl mx-auto px-4">
            <div class="text-center mb-16">
                <h2 class="text-4xl font-bold mb-4">Simple, Transparent Pricing</h2>
                <p class="text-gray-400 text-lg">Choose the plan that fits your trading strategy</p>
            </div>
            
            <div class="grid md:grid-cols-3 gap-8 max-w-5xl mx-auto">
                <!-- Free Tier -->
                <div class="tier-card bg-gray-900/50 border border-gray-700 rounded-xl p-8">
                    <h3 class="text-2xl font-bold mb-4">Free</h3>
                    <div class="text-4xl font-bold mb-6">$0<span class="text-gray-400 text-lg">/month</span></div>
                    <ul class="space-y-4 mb-8">
                        <li class="flex items-center">
                            <svg class="w-5 h-5 mr-3 text-gray-400" fill="currentColor" viewBox="0 0 20 20">
                                <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"/>
                            </svg>
                            View whale discovery info
                        </li>
                        <li class="flex items-center text-gray-400">
                            <svg class="w-5 h-5 mr-3" fill="currentColor" viewBox="0 0 20 20">
                                <path fill-rule="evenodd" d="M13.477 14.89A6 6 0 015.11 6.524l8.367 8.368zm1.414-1.414L6.524 5.11a6 6 0 018.367 8.367zM18 10a8 8 0 11-16 0 8 8 0 0116 0z"/>
                            </svg>
                            No whale data access
                        </li>
                        <li class="flex items-center text-gray-400">
                            <svg class="w-5 h-5 mr-3" fill="currentColor" viewBox="0 0 20 20">
                                <path fill-rule="evenodd" d="M13.477 14.89A6 6 0 015.11 6.524l8.367 8.368zm1.414-1.414L6.524 5.11a6 6 0 018.367 8.367zM18 10a8 8 0 11-16 0 8 8 0 0116 0z"/>
                            </svg>
                            No premium features
                        </li>
                    </ul>
                    <a href="/register" class="block w-full py-3 text-center border border-gray-600 rounded-lg hover:bg-gray-800 transition-colors">
                        Get Started Free
                    </a>
                </div>

                <!-- Beta Tier (Popular) -->
                <div class="tier-card bg-gradient-to-b from-purple-900/50 to-cyan-900/50 border-2 border-purple-500 rounded-xl p-8 relative">
                    <div class="popular-badge absolute -top-4 left-1/2 transform -translate-x-1/2 px-4 py-2 rounded-full text-white text-sm font-bold">
                        🔥 MOST POPULAR
                    </div>
                    <h3 class="text-2xl font-bold mb-4">Beta Access</h3>
                    <div class="text-4xl font-bold mb-6">$19<span class="text-gray-400 text-lg">/month</span></div>
                    <ul class="space-y-4 mb-8">
                        <li class="flex items-center">
                            <svg class="w-5 h-5 mr-3 text-green-400" fill="currentColor" viewBox="0 0 20 20">
                                <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"/>
                            </svg>
                            Up to 50 tracked whales
                        </li>
                        <li class="flex items-center">
                            <svg class="w-5 h-5 mr-3 text-green-400" fill="currentColor" viewBox="0 0 20 20">
                                <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"/>
                            </svg>
                            Reddit whale discovery
                        </li>
                        <li class="flex items-center">
                            <svg class="w-5 h-5 mr-3 text-green-400" fill="currentColor" viewBox="0 0 20 20">
                                <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"/>
                            </svg>
                            Quality scoring & verification
                        </li>
                        <li class="flex items-center">
                            <svg class="w-5 h-5 mr-3 text-yellow-400" fill="currentColor" viewBox="0 0 20 20">
                                <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"/>
                            </svg>
                            <span class="font-bold text-yellow-400">FREE upgrade to PRO!</span>
                        </li>
                    </ul>
                    <a href="/api/auth/register" class="cta-button block w-full py-3 text-center rounded-lg font-semibold text-white">
                        Start Beta Access
                    </a>
                </div>

                <!-- Pro Tier -->
                <div class="tier-card bg-gray-900/50 border border-gray-700 rounded-xl p-8">
                    <h3 class="text-2xl font-bold mb-4">PRO</h3>
                    <div class="text-4xl font-bold mb-6">$49<span class="text-gray-400 text-lg">/month</span></div>
                    <div class="bg-gradient-to-r from-purple-500/20 to-cyan-500/20 rounded-lg p-3 mb-6">
                        <p class="text-sm text-center">🚀 Coming in 1-2 weeks</p>
                    </div>
                    <ul class="space-y-4 mb-8">
                        <li class="flex items-center">
                            <svg class="w-5 h-5 mr-3 text-green-400" fill="currentColor" viewBox="0 0 20 20">
                                <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"/>
                            </svg>
                            Unlimited tracked whales
                        </li>
                        <li class="flex items-center">
                            <svg class="w-5 h-5 mr-3 text-green-400" fill="currentColor" viewBox="0 0 20 20">
                                <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"/>
                            </svg>
                            DEX integration & analytics
                        </li>
                        <li class="flex items-center">
                            <svg class="w-5 h-5 mr-3 text-green-400" fill="currentColor" viewBox="0 0 20 20">
                                <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"/>
                            </svg>
                            Real-time alerts & notifications
                        </li>
                        <li class="flex items-center">
                            <svg class="w-5 h-5 mr-3 text-green-400" fill="currentColor" viewBox="0 0 20 20">
                                <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"/>
                            </svg>
                            Multi-chain support
                        </li>
                    </ul>
                    <button disabled class="block w-full py-3 text-center border border-gray-600 rounded-lg bg-gray-800 text-gray-500 cursor-not-allowed">
                        Coming Soon
                    </button>
                </div>
            </div>
            
            <!-- Beta Bonus -->
            <div class="mt-12 bg-gradient-to-r from-purple-500/10 to-cyan-500/10 border border-purple-500/20 rounded-xl p-8 text-center">
                <h3 class="text-2xl font-bold mb-4 flex items-center justify-center">
                    <svg class="w-6 h-6 mr-2 text-yellow-400" fill="currentColor" viewBox="0 0 20 20">
                        <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z"/>
                    </svg>
                    🎉 Beta Pioneer Bonus
                </h3>
                <p class="text-gray-300 text-lg mb-4">
                    Join during Beta and get automatically upgraded to PRO when it launches - completely FREE! 
                    That's a $30/month value at no extra cost.
                </p>
                <p class="text-sm text-gray-400">
                    Lock in your Beta price and never pay PRO pricing. Limited time offer for early adopters.
                </p>
            </div>
        </div>
    </section>

    <!-- CTA Section -->
    <section class="py-20 bg-gradient-to-r from-purple-900/50 to-cyan-900/50">
        <div class="max-w-4xl mx-auto px-4 text-center">
            <h2 class="text-4xl font-bold mb-6">Ready to Track Crypto Whales?</h2>
            <p class="text-xl text-gray-300 mb-8">
                Join the Beta today and start discovering whale wallets before the competition.
            </p>
            <a href="/api/auth/register" class="cta-button inline-block px-10 py-4 rounded-lg font-semibold text-white text-lg mr-4">
                Start Beta Access - $19/month
            </a>
            <a href="/login" class="inline-block px-8 py-4 border border-gray-600 rounded-lg font-semibold text-white hover:bg-white/10 transition-colors">
                Already have an account?
            </a>
        </div>
    </section>

    <!-- Footer -->
    <footer class="bg-black/40 border-t border-gray-800 py-12">
        <div class="max-w-7xl mx-auto px-4">
            <div class="grid md:grid-cols-4 gap-8">
                <div>
                    <div class="flex items-center space-x-2 mb-4">
                        <div class="bg-gradient-to-r from-purple-500 to-cyan-500 p-2 rounded-lg">
                            <svg class="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"/>
                            </svg>
                        </div>
                        <h3 class="font-bold">Whale Tracker</h3>
                    </div>
                    <p class="text-gray-400 text-sm">
                        AI-powered whale discovery for crypto traders and investors.
                    </p>
                </div>
                
                <div>
                    <h4 class="font-semibold mb-4">Product</h4>
                    <ul class="space-y-2 text-gray-400 text-sm">
                        <li><a href="#pricing" class="hover:text-white transition-colors">Pricing</a></li>
                        <li><a href="#how-it-works" class="hover:text-white transition-colors">How it Works</a></li>
                        <li><a href="/api/health" class="hover:text-white transition-colors">API Status</a></li>
                    </ul>
                </div>
                
                <div>
                    <h4 class="font-semibold mb-4">Support</h4>
                    <ul class="space-y-2 text-gray-400 text-sm">
                        <li><a href="mailto:support@whaletracker.com" class="hover:text-white transition-colors">Contact</a></li>
                        <li><a href="/login" class="hover:text-white transition-colors">Login Help</a></li>
                    </ul>
                </div>
                
                <div>
                    <h4 class="font-semibold mb-4">Data Sources</h4>
                    <ul class="space-y-2 text-gray-400 text-sm">
                        <li>✓ Reddit Communities</li>
                        <li>✓ Blockchain Verification</li>
                        <li>✓ AI Quality Scoring</li>
                    </ul>
                </div>
            </div>
            
            <div class="border-t border-gray-800 mt-8 pt-8 text-center text-gray-400 text-sm">
                <p>&copy; 2025 Whale Tracker. Track responsibly.</p>
            </div>
        </div>
    </footer>

    <script>
        // Smooth scrolling for anchor links
        document.querySelectorAll('a[href^="#"]').forEach(anchor => {
            anchor.addEventListener('click', function (e) {
                e.preventDefault();
                const target = document.querySelector(this.getAttribute('href'));
                if (target) {
                    target.scrollIntoView({
                        behavior: 'smooth',
                        block: 'start'
                    });
                }
            });
        });
    </script>
</body>
</html>]'''

@app.route('/login')
def login_page():
    return '''
    <html><head><title>Login - Whale Tracker</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>body {background: linear-gradient(135deg, #1e293b 0%, #7c3aed 50%, #1e293b 100%);}</style>
    </head><body class="min-h-screen flex items-center justify-center text-white">
    <div class="max-w-md w-full mx-4 bg-black/40 backdrop-blur-sm border border-gray-800 rounded-xl p-8">
        <h1 class="text-3xl font-bold text-center mb-8">Login to Whale Tracker</h1>
        <form id="loginForm" class="space-y-4">
            <input type="email" id="email" placeholder="Email" required 
                   class="w-full px-4 py-3 bg-gray-800 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:border-purple-500 focus:outline-none">
            <input type="password" id="password" placeholder="Password" required 
                   class="w-full px-4 py-3 bg-gray-800 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:border-purple-500 focus:outline-none">
            <button type="submit" class="w-full py-3 bg-gradient-to-r from-purple-500 to-cyan-500 rounded-lg font-semibold text-white hover:opacity-90 transition-opacity">
                Login to Dashboard
            </button>
        </form>
        <p class="text-center mt-4 text-gray-400">
            Don't have an account? <a href="/landing#pricing" class="text-purple-400 hover:text-purple-300">Sign up here</a>
        </p>
    </div>
    <script>
        document.getElementById('loginForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            const email = document.getElementById('email').value;
            const password = document.getElementById('password').value;
            
            try {
                const response = await fetch('/api/auth/login', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({email, password})
                });
                
                const data = await response.json();
                if (response.ok) {
                    localStorage.setItem('whale_token', data.token);
                    window.location.href = '/dashboard';
                } else {
                    alert(data.error || 'Login failed');
                }
            } catch (err) {
                alert('Connection failed');
            }
        });
    </script>
    </body></html>
    '''

@app.route('/')
def home():
    return '''[<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Whale Tracker - Discover Crypto Whales Before Everyone Else</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        body {
            background: linear-gradient(135deg, #1e293b 0%, #7c3aed 50%, #1e293b 100%);
            min-height: 100vh;
        }
        .hero-gradient {
            background: linear-gradient(135deg, rgba(139, 92, 246, 0.1), rgba(59, 130, 246, 0.1));
        }
        .tier-card {
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }
        .tier-card:hover {
            transform: translateY(-8px);
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.3);
        }
        .popular-badge {
            background: linear-gradient(90deg, #f59e0b, #ef4444);
        }
        .cta-button {
            background: linear-gradient(90deg, #8b5cf6, #06b6d4);
            transition: all 0.3s ease;
        }
        .cta-button:hover {
            background: linear-gradient(90deg, #7c3aed, #0891b2);
            transform: translateY(-2px);
            box-shadow: 0 10px 20px rgba(139, 92, 246, 0.4);
        }
    </style>
</head>
<body class="text-white">
    <!-- Header -->
    <header class="border-b border-gray-800 bg-black/20 backdrop-blur-sm">
        <div class="max-w-7xl mx-auto px-4 py-4 flex items-center justify-between">
            <div class="flex items-center space-x-3">
                <div class="bg-gradient-to-r from-purple-500 to-cyan-500 p-2 rounded-lg">
                    <svg class="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"/>
                    </svg>
                </div>
                <div>
                    <h1 class="text-2xl font-bold bg-gradient-to-r from-purple-400 to-cyan-400 bg-clip-text text-transparent">
                        Whale Tracker
                    </h1>
                    <p class="text-gray-400 text-sm">AI-Powered Whale Discovery</p>
                </div>
            </div>
            <div class="flex items-center space-x-4">
                <a href="/login" class="text-gray-300 hover:text-white transition-colors">Login</a>
                <a href="#pricing" class="px-4 py-2 bg-purple-600 hover:bg-purple-700 rounded-lg transition-colors">
                    Get Started
                </a>
            </div>
        </div>
    </header>

    <!-- Hero Section -->
    <section class="hero-gradient py-20">
        <div class="max-w-7xl mx-auto px-4 text-center">
            <div class="inline-flex items-center px-4 py-2 bg-gradient-to-r from-orange-500 to-red-500 rounded-full text-white text-sm font-bold mb-8">
                <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"/>
                </svg>
                BETA ACCESS - LIMITED TIME
            </div>
            
            <h1 class="text-5xl md:text-7xl font-bold mb-6">
                Discover Crypto <br>
                <span class="bg-gradient-to-r from-purple-400 to-cyan-400 bg-clip-text text-transparent">
                    Whales
                </span> First
            </h1>
            
            <p class="text-xl text-gray-300 mb-8 max-w-3xl mx-auto">
                Track the biggest crypto holders before they make their moves. Our AI scans Reddit communities 
                to discover whale wallets with massive holdings in real-time.
            </p>
            
            <div class="flex flex-col sm:flex-row gap-4 justify-center mb-12">
                <a href="#pricing" class="cta-button px-8 py-4 rounded-lg font-semibold text-white text-lg">
                    Start Tracking Whales - $19/month
                </a>
                <a href="#how-it-works" class="px-8 py-4 border border-gray-600 rounded-lg font-semibold text-white hover:bg-white/10 transition-colors">
                    See How It Works
                </a>
            </div>
            
            <!-- Social Proof -->
            <div class="flex items-center justify-center space-x-8 text-gray-400 text-sm">
                <div class="flex items-center">
                    <svg class="w-5 h-5 mr-2 text-green-400" fill="currentColor" viewBox="0 0 20 20">
                        <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"/>
                    </svg>
                    Reddit Integration
                </div>
                <div class="flex items-center">
                    <svg class="w-5 h-5 mr-2 text-green-400" fill="currentColor" viewBox="0 0 20 20">
                        <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"/>
                    </svg>
                    AI-Powered Discovery
                </div>
                <div class="flex items-center">
                    <svg class="w-5 h-5 mr-2 text-green-400" fill="currentColor" viewBox="0 0 20 20">
                        <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"/>
                    </svg>
                    Real-time Updates
                </div>
            </div>
        </div>
    </section>

    <!-- How It Works -->
    <section id="how-it-works" class="py-20 bg-black/20">
        <div class="max-w-7xl mx-auto px-4">
            <div class="text-center mb-16">
                <h2 class="text-4xl font-bold mb-4">How Whale Tracker Works</h2>
                <p class="text-gray-400 text-lg">Advanced AI scans crypto communities to find whale wallets</p>
            </div>
            
            <div class="grid md:grid-cols-3 gap-8">
                <div class="text-center">
                    <div class="bg-gradient-to-r from-purple-500 to-pink-500 w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-6">
                        <svg class="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/>
                        </svg>
                    </div>
                    <h3 class="text-xl font-bold mb-4">AI Scans Reddit</h3>
                    <p class="text-gray-400">Our AI monitors r/solana, r/cryptocurrency, and other communities for whale mentions and wallet addresses.</p>
                </div>
                
                <div class="text-center">
                    <div class="bg-gradient-to-r from-cyan-500 to-blue-500 w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-6">
                        <svg class="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"/>
                        </svg>
                    </div>
                    <h3 class="text-xl font-bold mb-4">Verifies & Scores</h3>
                    <p class="text-gray-400">Each wallet is verified for balance and activity, then scored based on holding size and community credibility.</p>
                </div>
                
                <div class="text-center">
                    <div class="bg-gradient-to-r from-green-500 to-yellow-500 w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-6">
                        <svg class="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"/>
                        </svg>
                    </div>
                    <h3 class="text-xl font-bold mb-4">Real-time Dashboard</h3>
                    <p class="text-gray-400">Access your personalized whale tracker dashboard with live updates and detailed analytics.</p>
                </div>
            </div>
        </div>
    </section>

    <!-- Pricing -->
    <section id="pricing" class="py-20">
        <div class="max-w-7xl mx-auto px-4">
            <div class="text-center mb-16">
                <h2 class="text-4xl font-bold mb-4">Simple, Transparent Pricing</h2>
                <p class="text-gray-400 text-lg">Choose the plan that fits your trading strategy</p>
            </div>
            
            <div class="grid md:grid-cols-3 gap-8 max-w-5xl mx-auto">
                <!-- Free Tier -->
                <div class="tier-card bg-gray-900/50 border border-gray-700 rounded-xl p-8">
                    <h3 class="text-2xl font-bold mb-4">Free</h3>
                    <div class="text-4xl font-bold mb-6">$0<span class="text-gray-400 text-lg">/month</span></div>
                    <ul class="space-y-4 mb-8">
                        <li class="flex items-center">
                            <svg class="w-5 h-5 mr-3 text-gray-400" fill="currentColor" viewBox="0 0 20 20">
                                <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"/>
                            </svg>
                            View whale discovery info
                        </li>
                        <li class="flex items-center text-gray-400">
                            <svg class="w-5 h-5 mr-3" fill="currentColor" viewBox="0 0 20 20">
                                <path fill-rule="evenodd" d="M13.477 14.89A6 6 0 015.11 6.524l8.367 8.368zm1.414-1.414L6.524 5.11a6 6 0 018.367 8.367zM18 10a8 8 0 11-16 0 8 8 0 0116 0z"/>
                            </svg>
                            No whale data access
                        </li>
                        <li class="flex items-center text-gray-400">
                            <svg class="w-5 h-5 mr-3" fill="currentColor" viewBox="0 0 20 20">
                                <path fill-rule="evenodd" d="M13.477 14.89A6 6 0 015.11 6.524l8.367 8.368zm1.414-1.414L6.524 5.11a6 6 0 018.367 8.367zM18 10a8 8 0 11-16 0 8 8 0 0116 0z"/>
                            </svg>
                            No premium features
                        </li>
                    </ul>
                    <a href="/register" class="block w-full py-3 text-center border border-gray-600 rounded-lg hover:bg-gray-800 transition-colors">
                        Get Started Free
                    </a>
                </div>

                <!-- Beta Tier (Popular) -->
                <div class="tier-card bg-gradient-to-b from-purple-900/50 to-cyan-900/50 border-2 border-purple-500 rounded-xl p-8 relative">
                    <div class="popular-badge absolute -top-4 left-1/2 transform -translate-x-1/2 px-4 py-2 rounded-full text-white text-sm font-bold">
                        🔥 MOST POPULAR
                    </div>
                    <h3 class="text-2xl font-bold mb-4">Beta Access</h3>
                    <div class="text-4xl font-bold mb-6">$19<span class="text-gray-400 text-lg">/month</span></div>
                    <ul class="space-y-4 mb-8">
                        <li class="flex items-center">
                            <svg class="w-5 h-5 mr-3 text-green-400" fill="currentColor" viewBox="0 0 20 20">
                                <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"/>
                            </svg>
                            Up to 50 tracked whales
                        </li>
                        <li class="flex items-center">
                            <svg class="w-5 h-5 mr-3 text-green-400" fill="currentColor" viewBox="0 0 20 20">
                                <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"/>
                            </svg>
                            Reddit whale discovery
                        </li>
                        <li class="flex items-center">
                            <svg class="w-5 h-5 mr-3 text-green-400" fill="currentColor" viewBox="0 0 20 20">
                                <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"/>
                            </svg>
                            Quality scoring & verification
                        </li>
                        <li class="flex items-center">
                            <svg class="w-5 h-5 mr-3 text-yellow-400" fill="currentColor" viewBox="0 0 20 20">
                                <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"/>
                            </svg>
                            <span class="font-bold text-yellow-400">FREE upgrade to PRO!</span>
                        </li>
                    </ul>
                    <a href="/api/auth/register" class="cta-button block w-full py-3 text-center rounded-lg font-semibold text-white">
                        Start Beta Access
                    </a>
                </div>

                <!-- Pro Tier -->
                <div class="tier-card bg-gray-900/50 border border-gray-700 rounded-xl p-8">
                    <h3 class="text-2xl font-bold mb-4">PRO</h3>
                    <div class="text-4xl font-bold mb-6">$49<span class="text-gray-400 text-lg">/month</span></div>
                    <div class="bg-gradient-to-r from-purple-500/20 to-cyan-500/20 rounded-lg p-3 mb-6">
                        <p class="text-sm text-center">🚀 Coming in 1-2 weeks</p>
                    </div>
                    <ul class="space-y-4 mb-8">
                        <li class="flex items-center">
                            <svg class="w-5 h-5 mr-3 text-green-400" fill="currentColor" viewBox="0 0 20 20">
                                <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"/>
                            </svg>
                            Unlimited tracked whales
                        </li>
                        <li class="flex items-center">
                            <svg class="w-5 h-5 mr-3 text-green-400" fill="currentColor" viewBox="0 0 20 20">
                                <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"/>
                            </svg>
                            DEX integration & analytics
                        </li>
                        <li class="flex items-center">
                            <svg class="w-5 h-5 mr-3 text-green-400" fill="currentColor" viewBox="0 0 20 20">
                                <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"/>
                            </svg>
                            Real-time alerts & notifications
                        </li>
                        <li class="flex items-center">
                            <svg class="w-5 h-5 mr-3 text-green-400" fill="currentColor" viewBox="0 0 20 20">
                                <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"/>
                            </svg>
                            Multi-chain support
                        </li>
                    </ul>
                    <button disabled class="block w-full py-3 text-center border border-gray-600 rounded-lg bg-gray-800 text-gray-500 cursor-not-allowed">
                        Coming Soon
                    </button>
                </div>
            </div>
            
            <!-- Beta Bonus -->
            <div class="mt-12 bg-gradient-to-r from-purple-500/10 to-cyan-500/10 border border-purple-500/20 rounded-xl p-8 text-center">
                <h3 class="text-2xl font-bold mb-4 flex items-center justify-center">
                    <svg class="w-6 h-6 mr-2 text-yellow-400" fill="currentColor" viewBox="0 0 20 20">
                        <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z"/>
                    </svg>
                    🎉 Beta Pioneer Bonus
                </h3>
                <p class="text-gray-300 text-lg mb-4">
                    Join during Beta and get automatically upgraded to PRO when it launches - completely FREE! 
                    That's a $30/month value at no extra cost.
                </p>
                <p class="text-sm text-gray-400">
                    Lock in your Beta price and never pay PRO pricing. Limited time offer for early adopters.
                </p>
            </div>
        </div>
    </section>

    <!-- CTA Section -->
    <section class="py-20 bg-gradient-to-r from-purple-900/50 to-cyan-900/50">
        <div class="max-w-4xl mx-auto px-4 text-center">
            <h2 class="text-4xl font-bold mb-6">Ready to Track Crypto Whales?</h2>
            <p class="text-xl text-gray-300 mb-8">
                Join the Beta today and start discovering whale wallets before the competition.
            </p>
            <a href="/api/auth/register" class="cta-button inline-block px-10 py-4 rounded-lg font-semibold text-white text-lg mr-4">
                Start Beta Access - $19/month
            </a>
            <a href="/login" class="inline-block px-8 py-4 border border-gray-600 rounded-lg font-semibold text-white hover:bg-white/10 transition-colors">
                Already have an account?
            </a>
        </div>
    </section>

    <!-- Footer -->
    <footer class="bg-black/40 border-t border-gray-800 py-12">
        <div class="max-w-7xl mx-auto px-4">
            <div class="grid md:grid-cols-4 gap-8">
                <div>
                    <div class="flex items-center space-x-2 mb-4">
                        <div class="bg-gradient-to-r from-purple-500 to-cyan-500 p-2 rounded-lg">
                            <svg class="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"/>
                            </svg>
                        </div>
                        <h3 class="font-bold">Whale Tracker</h3>
                    </div>
                    <p class="text-gray-400 text-sm">
                        AI-powered whale discovery for crypto traders and investors.
                    </p>
                </div>
                
                <div>
                    <h4 class="font-semibold mb-4">Product</h4>
                    <ul class="space-y-2 text-gray-400 text-sm">
                        <li><a href="#pricing" class="hover:text-white transition-colors">Pricing</a></li>
                        <li><a href="#how-it-works" class="hover:text-white transition-colors">How it Works</a></li>
                        <li><a href="/api/health" class="hover:text-white transition-colors">API Status</a></li>
                    </ul>
                </div>
                
                <div>
                    <h4 class="font-semibold mb-4">Support</h4>
                    <ul class="space-y-2 text-gray-400 text-sm">
                        <li><a href="mailto:support@whaletracker.com" class="hover:text-white transition-colors">Contact</a></li>
                        <li><a href="/login" class="hover:text-white transition-colors">Login Help</a></li>
                    </ul>
                </div>
                
                <div>
                    <h4 class="font-semibold mb-4">Data Sources</h4>
                    <ul class="space-y-2 text-gray-400 text-sm">
                        <li>✓ Reddit Communities</li>
                        <li>✓ Blockchain Verification</li>
                        <li>✓ AI Quality Scoring</li>
                    </ul>
                </div>
            </div>
            
            <div class="border-t border-gray-800 mt-8 pt-8 text-center text-gray-400 text-sm">
                <p>&copy; 2025 Whale Tracker. Track responsibly.</p>
            </div>
        </div>
    </footer>

    <script>
        // Smooth scrolling for anchor links
        document.querySelectorAll('a[href^="#"]').forEach(anchor => {
            anchor.addEventListener('click', function (e) {
                e.preventDefault();
                const target = document.querySelector(this.getAttribute('href'));
                if (target) {
                    target.scrollIntoView({
                        behavior: 'smooth',
                        block: 'start'
                    });
                }
            });
        });
    </script>
</body>
</html>]'''
    
@app.route('/dashboard')
def dashboard():
    return send_from_directory('static', 'index.html')
   
@app.route('/static/<path:filename>')
def serve_static_files(filename):
    return send_from_directory('static/static', filename)
    
@app.route('/init-db')
def initialize_database():
    try:
        init_db()
        return jsonify({'status': 'Database initialized successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
# @app.route('/<path:path>')
# def serve_static(path):
#   return send_from_directory('static', path)

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal server error: {error}")
    return jsonify({'error': 'Internal server error'}), 500

@app.errorhandler(429)
def rate_limit_handler(e):
    return jsonify({'error': 'Rate limit exceeded', 'message': str(e.description)}), 429

if __name__ == '__main__':
    init_db()
    port = int(os.environ.get('PORT', 8000))
    
    # Force production mode on Railway
    if os.environ.get('RAILWAY_ENVIRONMENT') or os.environ.get('PORT'):
        logger.info("🚀 Starting Whale Tracker API in PRODUCTION mode...")
        app.run(debug=False, host='0.0.0.0', port=port)
    else:
        logger.info("🔧 Starting Whale Tracker API in DEVELOPMENT mode...")
        app.run(debug=True, host='0.0.0.0', port=port)
# Force redeploy Wed Aug 13 05:04:51 PM EDT 2025
