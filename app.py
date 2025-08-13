import os
import jwt
import bcrypt
import stripe
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
    CORS(app, origins=['https://your-domain.com'])
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
            success_url=request.host_url + 'dashboard?session_id={CHECKOUT_SESSION_ID}',
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
    """Get top whales - free tier limited to 5"""
    try:
        conn = get_db_connection()
        
        # Check subscription tier
        cursor = conn.execute('SELECT subscription_tier FROM users WHERE id = ?', (g.current_user_id,))
        user = cursor.fetchone()
        
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
        
        return jsonify({
            'email': user['email'],
            'subscription_tier': user['subscription_tier'],
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

@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory('static', path)
    
@app.route('/static/<path:filename>')
def serve_static_files(filename):
    return send_from_directory('static/static', filename)
    
@app.route('/')
def serve_dashboard():
    return send_from_directory('static', 'index.html')

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
    port = int(os.environ.get('PORT', 8000))
    
    # Force production mode on Railway
    if os.environ.get('RAILWAY_ENVIRONMENT') or os.environ.get('PORT'):
        logger.info("🚀 Starting Whale Tracker API in PRODUCTION mode...")
        app.run(debug=False, host='0.0.0.0', port=port)
    else:
        logger.info("🔧 Starting Whale Tracker API in DEVELOPMENT mode...")
        app.run(debug=True, host='0.0.0.0', port=port)
# Force redeploy Wed Aug 13 05:04:51 PM EDT 2025
