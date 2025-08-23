from flask import Flask, render_template, request, jsonify, render_template_string
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_cors import CORS
import stripe
import coinbase_commerce
from coinbase_commerce.client import Client
try:
    from coinbase_commerce.error import WebhookInvalidPayload, SignatureError
except ImportError:
    # Create fallback exception classes
    class WebhookInvalidPayload(Exception):
        pass
    class SignatureError(Exception):
        pass
import logging
import os
import time
from datetime import datetime
from dotenv import load_dotenv
import structlog

# Import our modules
from config import get_config
from utils import (
    api_success, api_error, db_manager, 
    validate_request_json, CheckoutRequest, DonationRequest,
    create_jwt_token, log_user_action
)

# Initialize Flask app
# Load environment FIRST
load_dotenv()

# Get configuration SECOND  
config = get_config()

# Initialize Flask app THIRD
app = Flask(__name__, template_folder='templates')
app.config.from_object(config)

# Initialize extensions FOURTH
CORS(app)

# Fixed limiter setup (remove the key_func from the try block)
try:
    limiter = Limiter(
        key_func=get_remote_address,  # key_func goes here, not in app parameter
        app=app,  # app goes here
        default_limits=["200 per day", "50 per hour"],
        storage_uri=getattr(config, 'RATE_LIMIT_STORAGE_URL', 'memory://')
    )
except Exception as e:
    print(f"Rate limiter setup failed, using basic limiter: {e}")  # Use print instead of logger
    # Fallback to simple limiter
    limiter = Limiter(
        key_func=get_remote_address,
        app=app,
        default_limits=["200 per day", "50 per hour"]
    )

# Configure structured logging
# Configure logging with safe fallbacks
def setup_logging():
    """Setup logging with safe fallbacks"""
    log_level = getattr(logging, config.LOG_LEVEL, logging.INFO)
    
    # Try to use configured log file, fall back to local file
    log_handlers = []
    
    # Always add console handler
    log_handlers.append(logging.StreamHandler())
    
    # Try to add file handler with fallbacks
    try:
        # Create logs directory if it doesn't exist
        log_file = getattr(config, 'LOG_FILE', './logs/transactions.log')
        log_dir = os.path.dirname(log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)
        log_handlers.append(logging.FileHandler(log_file))
        print(f"✅ Logging to file: {log_file}")
    except Exception as e:
        # Fall back to local file
        try:
            if not os.path.exists('./logs'):
                os.makedirs('./logs', exist_ok=True)
            log_handlers.append(logging.FileHandler('./logs/app.log'))
            print("⚠️  Using fallback log file: ./logs/app.log")
        except Exception as e2:
            print(f"⚠️  File logging disabled: {e2}")
    
    # Setup logging
    logging.basicConfig(
        level=log_level,
        handlers=log_handlers,
        format='%(asctime)s %(levelname)s: %(message)s'
    )

# Call the safe logging setup
setup_logging()
logger = structlog.get_logger(__name__)

# Stripe setup
stripe.api_key = config.STRIPE_SECRET_KEY

# Coinbase Commerce setup
coinbase_client = None
if config.COINBASE_API_KEY:
    coinbase_client = Client(api_key=config.COINBASE_API_KEY)

# Price configurations
PRICING = {
    'professional': {'price_id': 'price_1RyKygRkVYDUbhIFgs8JUTTR', 'mode': 'subscription'},
    'emergency': {'price_id': 'price_1RyapeRkVYDUbhIFwSQYNIAw', 'mode': 'subscription'},
    'enterprise': {'price_id': 'price_1Ryar9RkVYDUbhIFr4Oe7N9C', 'mode': 'payment'},
    'sixmonth': {'price_id': 'price_1RyJOzDfwP4gynpjh4mO6b6B', 'mode': 'payment'},
    'house_hero': {'amount': 50000, 'mode': 'payment'},
    'family_guardian': {'amount': 150000, 'mode': 'payment'},
    'life_changer': {'amount': 500000, 'mode': 'payment'},
    'legend': {'amount': 1000000, 'mode': 'payment'}
}

DISPLAY_NAMES = {
    'house_hero': '💰 House Hero - 1 Year Access',
    'family_guardian': '🏆 Family Guardian - 2 Years + 3% Profit Share',
    'life_changer': '👑 Life Changer - Lifetime + 5% Profit Share',
    'legend': '✨ Legend Status - Everything + 10% Profit Share'
}

# Request logging middleware
@app.before_request
def log_request_info():
    request.start_time = time.time()
    logger.info(
        "Request started",
        method=request.method,
        path=request.path,
        remote_addr=request.remote_addr,
        user_agent=str(request.user_agent)
    )

@app.after_request
def log_response_info(response):
    duration = time.time() - request.start_time
    logger.info(
        "Request completed",
        method=request.method,
        path=request.path,
        status_code=response.status_code,
        duration_ms=round(duration * 1000, 2)
    )
    return response

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return api_error("Endpoint not found", 404, error_type="NotFoundError")

@app.errorhandler(500)
def internal_error(error):
    logger.error("Internal server error", exc_info=True)
    return api_error("Internal server error", 500, error_type="InternalError")

@app.errorhandler(429)
def ratelimit_handler(e):
    return api_error(
        "Rate limit exceeded", 
        429, 
        details={"retry_after": str(e.retry_after)},
        error_type="RateLimitError"
    )

# Routes
@app.route('/')
def home():
    """Main subscription page with enhanced crowdfunding integration"""
    try:
        return render_template('index.html', stripe_publishable_key=config.STRIPE_PUBLISHABLE_KEY)
    except Exception as e:
        logger.error("Error rendering home page", error=str(e))
        return api_error("Failed to load page", 500, error_type="TemplateError")

@app.route('/create-checkout-session', methods=['POST'])
@limiter.limit("10 per minute")
@validate_request_json(CheckoutRequest)
def create_checkout_session():
    """Enhanced checkout session for subscriptions and crowdfund"""
    try:
        data = request.validated_data
        plan = data.plan
        payment_type = data.type

        logger.info("Creating checkout session", plan=plan, payment_type=payment_type)
        
        if payment_type == 'crowdfund' and plan in ['house_hero', 'family_guardian', 'life_changer', 'legend']:
            return create_crowdfund_session(plan)
        
        if plan not in PRICING:
            return api_error(f"Invalid plan: {plan}", 400)

        tier_info = PRICING[plan]
        
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{'price': tier_info['price_id'], 'quantity': 1}],
            mode=tier_info['mode'],
            success_url=f'{config.DOMAIN}/success?session_id={{CHECKOUT_SESSION_ID}}&type={payment_type}',
            cancel_url=f'{config.DOMAIN}/?canceled=true',
            metadata={'plan': plan, 'type': payment_type}
        )
        
        logger.info("Checkout session created", 
                   session_id=checkout_session.id, 
                   plan=plan, 
                   type=payment_type)
        
        return api_success({"id": checkout_session.id})

    except stripe.error.StripeError as e:
        logger.error("Stripe error in checkout", error=str(e))
        return api_error(f"Payment processing error: {str(e)}", 400, error_type="StripeError")
    except Exception as e:
        logger.error("Checkout session creation failed", error=str(e), exc_info=True)
        return api_error("Failed to create checkout session", 500, error_type="CheckoutError")

def create_crowdfund_session(plan):
    """Create crowdfund checkout session"""
    try:
        tier_info = PRICING[plan]
        
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'usd',
                    'product_data': {
                        'name': DISPLAY_NAMES[plan],
                        'description': 'Support Whale Tracker Pro and help save our family home'
                    },
                    'unit_amount': tier_info['amount'],
                },
                'quantity': 1,
            }],
            mode='payment',
            success_url=f'{config.DOMAIN}/success?session_id={{CHECKOUT_SESSION_ID}}&type=crowdfund&plan={plan}',
            cancel_url=f'{config.DOMAIN}/?canceled=true',
            metadata={'plan': plan, 'type': 'crowdfund', 'amount': tier_info['amount']}
        )
        
        logger.info("Crowdfund session created", 
                   plan=plan, 
                   amount=tier_info['amount']/100,
                   session_id=checkout_session.id)
        
        return api_success({"id": checkout_session.id})
        
    except Exception as e:
        logger.error("Crowdfund session creation failed", error=str(e))
        raise

@app.route('/create-donation-session', methods=['POST'])
@limiter.limit("5 per minute")
@validate_request_json(DonationRequest)
def create_donation_session():
    """Handle crypto and fiat donations with validation"""
    try:
        data = request.validated_data
        amount = data.amount
        method = data.method

        logger.info("Creating donation session", amount=amount, method=method)

        if method == 'crypto':
            if not coinbase_client:
                return api_error("Crypto donations not available", 503, error_type="ServiceUnavailable")
                
            charge = coinbase_client.charge.create(
                name='Whale Tracker Pro Donation',
                description='Help save our family home',
                local_price={'amount': str(amount), 'currency': 'USD'},
                pricing_type='fixed_price',
                metadata={'type': 'donation', 'amount': amount}
            )
            
            logger.info("Coinbase donation charge created", 
                       charge_id=charge.id, 
                       amount=amount)
            
            return api_success({
                "url": charge.hosted_url, 
                "id": charge.id
            })
        else:
            checkout_session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[{
                    'price_data': {
                        'currency': 'usd',
                        'product_data': {'name': 'Emergency House Fund Donation'},
                        'unit_amount': int(amount * 100),
                    },
                    'quantity': 1,
                }],
                mode='payment',
                success_url=f'{config.DOMAIN}/success?session_id={{CHECKOUT_SESSION_ID}}&type=donation',
                cancel_url=f'{config.DOMAIN}/?canceled=true',
                metadata={'type': 'donation', 'amount': amount}
            )
            
            logger.info("Stripe donation session created", 
                       session_id=checkout_session.id, 
                       amount=amount)
            
            return api_success({"id": checkout_session.id})

    except stripe.error.StripeError as e:
        logger.error("Stripe error in donation", error=str(e))
        return api_error(f"Payment processing error: {str(e)}", 400, error_type="StripeError")
    except Exception as e:
        logger.error("Donation session creation failed", error=str(e), exc_info=True)
        return api_error("Failed to create donation session", 500, error_type="DonationError")

@app.route('/webhook', methods=['POST'])
@limiter.exempt
def webhook():
    """Handle Stripe and Coinbase webhooks with proper validation"""
    payload = request.get_data(as_text=True)
    sig_header = request.headers.get('Stripe-Signature') or request.headers.get('X-Cc-Webhook-Signature')
    
    logger.debug("Webhook received", 
                signature_present=bool(sig_header),
                payload_length=len(payload))
    
    try:
        if sig_header and 'Stripe-Signature' in request.headers:
            return handle_stripe_webhook(payload, sig_header)
        elif sig_header and 'X-Cc-Webhook-Signature' in request.headers:
            return handle_coinbase_webhook(payload, sig_header)
        else:
            logger.warning("Webhook received without valid signature")
            return api_error("Invalid webhook signature", 400, error_type="WebhookError")
            
    except Exception as e:
        logger.error("Webhook processing failed", error=str(e), exc_info=True)
        return api_error("Webhook processing failed", 400, error_type="WebhookError")

def handle_stripe_webhook(payload, sig_header):
    """Handle Stripe webhook events"""
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, config.STRIPE_WEBHOOK_SECRET
        )
        
        if event['type'] == 'checkout.session.completed':
            session = event['data']['object']
            plan = session['metadata'].get('plan')
            session_id = session['id']
            
            logger.info("Stripe payment completed", 
                       session_id=session_id, 
                       plan=plan)
            
            # Store user subscription in database
            try:
                db_manager.safe_execute(
                    """INSERT INTO users (stripe_session_id, subscription_tier, created_at) 
                       VALUES (%s, %s, NOW()) 
                       ON CONFLICT (stripe_session_id) 
                       DO UPDATE SET subscription_tier = EXCLUDED.subscription_tier, updated_at = NOW()""",
                    (session_id, plan)
                )
                
                log_user_action(session_id, "subscription_created", {"plan": plan})
                
            except Exception as db_error:
                logger.error("Database error in webhook", 
                           error=str(db_error), 
                           session_id=session_id)
                # Don't fail the webhook for DB errors
        
        return api_success({"event_processed": event['type']})
        
    except stripe.error.SignatureVerificationError as e:
        logger.error("Stripe signature verification failed", error=str(e))
        return api_error("Invalid signature", 400, error_type="SignatureError")

def handle_coinbase_webhook(payload, sig_header):
    """Handle Coinbase Commerce webhook events"""
    try:
        if not coinbase_client:
            return api_error("Coinbase not configured", 503)
            
        coinbase_client.webhook.verify(payload, sig_header, config.COINBASE_WEBHOOK_SECRET)
        event = coinbase_client.webhook.parse(payload)
        
        logger.info("Coinbase webhook event", 
                   event_type=event.type, 
                   charge_id=event.data.id)
        
        if event.type == 'charge:confirmed':
            charge = event.data
            amount = charge.payments[0]['value']['local']['amount']
            
            logger.info("Crypto donation confirmed", 
                       charge_id=charge.id, 
                       amount=amount)
            
            # Store donation in database
            try:
                db_manager.safe_execute(
                    """INSERT INTO donations (charge_id, amount, type, timestamp) 
                       VALUES (%s, %s, %s, NOW()) 
                       ON CONFLICT (charge_id) DO NOTHING""",
                    (charge.id, amount, 'crypto')
                )
                
                log_user_action(charge.id, "crypto_donation", {"amount": amount})
                
            except Exception as db_error:
                logger.error("Database error in Coinbase webhook", 
                           error=str(db_error), 
                           charge_id=charge.id)
        
        return api_success({"event_processed": event.type})
        
    except (WebhookInvalidPayload, SignatureError) as e:
        logger.error("Coinbase webhook validation failed", error=str(e))
        return api_error("Invalid webhook", 400, error_type="WebhookError")

@app.route('/success')
def success():
    """Success page for payments with proper error handling"""
    try:
        session_id = request.args.get('session_id')
        payment_type = request.args.get('type', 'subscription')
        plan = request.args.get('plan', '')
        
        logger.info("Success page accessed",
                   session_id=session_id,
                   payment_type=payment_type,
                   plan=plan)
        
        title = "Thank You!"
        message = "Your contribution helps save our family home."
        
        if payment_type == 'donation':
            title = "🙏 Thank You for Your Donation!"
            message = "Your generous donation supports Whale Tracker Pro and our family."
        elif payment_type == 'crowdfund':
            title = f"Thank You for Your {plan.replace('_', ' ').title()} Contribution!"
            message = "Your one-time contribution directly supports our mission."
        
        return render_template_string("""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Payment Successful</title>
            <script src="https://cdn.tailwindcss.com"></script>
        </head>
        <body class="bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 min-h-screen text-white">
            <div class="max-w-2xl mx-auto px-4 py-16 text-center">
                <div class="bg-black/40 backdrop-blur-sm border border-green-500/50 rounded-xl p-8">
                    <div class="text-6xl mb-6">🎉</div>
                    <h1 class="text-4xl font-bold text-green-400 mb-4">{{ title }}</h1>
                    <p class="text-xl text-gray-300 mb-6">{{ message }}</p>
                    <a href="/dashboard" class="block px-8 py-3 bg-gradient-to-r from-purple-500 to-cyan-500 rounded-lg font-semibold text-white hover:opacity-90 transition-opacity">
                        Access Dashboard
                    </a>
                </div>
            </div>
        </body>
        </html>
        """, title=title, message=message)
        
    except Exception as e:
        logger.error("Error rendering success page", error=str(e))
        return api_error("Failed to load success page", 500, error_type="TemplateError")

@app.route('/dashboard')
def dashboard():
    """Dashboard placeholder with error handling"""
    try:
        return render_template_string("""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Whale Tracker Dashboard</title>
            <script src="https://cdn.tailwindcss.com"></script>
        </head>
        <body class="bg-gray-900 text-white min-h-screen">
            <div class="max-w-6xl mx-auto px-4 py-8">
                <h1 class="text-4xl font-bold">🐋 Whale Tracker Dashboard</h1>
                <p class="text-gray-300">Dashboard under development. Access granted!</p>
                <div class="mt-8 p-4 bg-gray-800 rounded-lg">
                    <h2 class="text-2xl font-semibold mb-4">Coming Soon</h2>
                    <ul class="list-disc list-inside space-y-2">
                        <li>Real-time whale tracking</li>
                        <li>AI-powered trading recommendations</li>
                        <li>Portfolio analysis</li>
                        <li>Market sentiment analysis</li>
                    </ul>
                </div>
            </div>
        </body>
        </html>
        """)
    except Exception as e:
        logger.error("Error rendering dashboard", error=str(e))
        return api_error("Failed to load dashboard", 500, error_type="TemplateError")

# Health check endpoints
@app.route('/health', methods=['GET'])
def health_check():
    """Basic health check"""
    return api_success({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    })

@app.route('/health/deep', methods=['GET'])
def deep_health_check():
    """Comprehensive health check"""
    checks = {
        "database": check_database_health(),
        "stripe": check_stripe_health(),
        "coinbase": check_coinbase_health()
    }
    
    all_healthy = all(checks.values())
    status_code = 200 if all_healthy else 503
    
    return jsonify({
        "status": "healthy" if all_healthy else "unhealthy",
        "checks": checks,
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    }), status_code

def check_database_health():
    """Check database connectivity"""
    try:
        db_manager.safe_execute("SELECT 1")
        return True
    except Exception as e:
        logger.error("Database health check failed", error=str(e))
        return False

def check_stripe_health():
    """Check Stripe configuration"""
    return bool(config.STRIPE_SECRET_KEY and config.STRIPE_WEBHOOK_SECRET)

def check_coinbase_health():
    """Check Coinbase configuration"""
    return bool(config.COINBASE_API_KEY and config.COINBASE_WEBHOOK_SECRET)

# API endpoints for external integration
@app.route('/api/config', methods=['GET'])
def get_public_config():
    """Get public configuration for frontend"""
    return api_success({
        "stripe_publishable_key": config.STRIPE_PUBLISHABLE_KEY,
        "domain": config.DOMAIN,
        "features": {
            "crypto_payments": coinbase_client is not None,
            "stripe_payments": bool(config.STRIPE_SECRET_KEY)
        }
    })

@app.route('/api/plans', methods=['GET'])
def get_pricing_plans():
    """Get available pricing plans"""
    plans = []
    for plan_id, plan_info in PRICING.items():
        plan_data = {
            "id": plan_id,
            "name": DISPLAY_NAMES.get(plan_id, plan_id.replace('_', ' ').title()),
            "mode": plan_info["mode"]
        }
        if "amount" in plan_info:
            plan_data["amount"] = plan_info["amount"] / 100  # Convert to dollars
        else:
            plan_data["price_id"] = plan_info["price_id"]
        
        plans.append(plan_data)
    
    return api_success(plans)

# Development/Debug endpoints (only in dev mode)
if config.DEBUG:
    @app.route('/debug/logs', methods=['GET'])
    def get_recent_logs():
        """Get recent log entries (dev only)"""
        try:
            with open(config.LOG_FILE, 'r') as f:
                lines = f.readlines()
                recent_logs = lines[-50:]  # Last 50 lines
            return api_success({"logs": recent_logs})
        except Exception as e:
            return api_error(f"Failed to read logs: {str(e)}", 500)
    
    @app.route('/debug/config', methods=['GET'])
    def debug_config():
        """Show configuration (dev only, sensitive data masked)"""
        debug_config = {
            "DEBUG": config.DEBUG,
            "LOG_LEVEL": config.LOG_LEVEL,
            "DOMAIN": config.DOMAIN,
            "DATABASE_URL": "***configured***" if config.DATABASE_URL else "not set",
            "STRIPE_KEY": "***configured***" if config.STRIPE_SECRET_KEY else "not set",
            "COINBASE_KEY": "***configured***" if config.COINBASE_API_KEY else "not set"
        }
        return api_success(debug_config)

# Initialize database tables if needed
def init_database():
    """Initialize database tables"""
    try:
        # Create users table
        db_manager.safe_execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                stripe_session_id VARCHAR(255) UNIQUE,
                subscription_tier VARCHAR(50),
                email VARCHAR(255),
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW()
            )
        """)
        
        # Create donations table
        db_manager.safe_execute("""
            CREATE TABLE IF NOT EXISTS donations (
                id SERIAL PRIMARY KEY,
                charge_id VARCHAR(255) UNIQUE,
                amount DECIMAL(10,2),
                type VARCHAR(50),
                timestamp TIMESTAMP DEFAULT NOW()
            )
        """)
        
        logger.info("Database tables initialized successfully")
        return True
        
    except Exception as e:
        logger.error("Database initialization failed", error=str(e))
        return False

@app.route('/api/auth/register', methods=['POST'])
@limiter.limit("5 per minute")
def register():
    """Clean registration with whitelist check"""
    try:
        data = request.get_json()
        if not data:
            return api_error("Request body required", 400)
            
        email = data.get('email', '').lower().strip()
        password = data.get('password', '')
        
        logger.info(f"Registration attempt for: {email}")
        
        # Validation
        if not email or '@' not in email:
            return api_error("Valid email required", 400)
        if len(password) < 8:
            return api_error("Password must be at least 8 characters", 400)
        
        # WHITELIST CHECK - This is where the magic happens!
        if not whitelist_manager.is_whitelisted(email):
            logger.info(f"Non-whitelisted user tried to register: {email}")
            return handle_waitlist_signup(email)
        
        # User is whitelisted! Get their tier
        user_tier = whitelist_manager.get_user_tier(email)
        logger.info(f"Whitelisted user registered: {email}, tier: {user_tier}")
        
        # Create user data
        user_data = {
            'user_id': generate_api_key(email),
            'email': email,
            'subscription_tier': user_tier
        }
        
        # Generate tokens
        token = create_jwt_token(user_data)
        api_key = generate_api_key(email)
        
        # Log the action
        log_user_action(user_data['user_id'], "user_registered", {"email": email, "tier": user_tier})
        
        # Store user in database (optional - for persistence)
        try:
            db_manager.safe_execute(
                """INSERT INTO users (email, subscription_tier, user_id, created_at) 
                   VALUES (%s, %s, %s, NOW()) 
                   ON CONFLICT (email) DO UPDATE SET 
                   subscription_tier = EXCLUDED.subscription_tier,
                   updated_at = NOW()""",
                (email, user_tier, user_data['user_id'])
            )
        except Exception as db_error:
            logger.error(f"Database error during registration: {db_error}")
            # Continue anyway - user still gets access
        
        return api_success({
            'token': token,
            'api_key': api_key,
            'user': user_data,
            'message': f'🎉 Welcome to Whale Tracker Pro! You have {user_tier} access.',
            'whitelisted': True
        })
        
    except Exception as e:
        logger.error(f"Registration error: {e}")
        return api_error("Registration failed", 500, error_type="RegistrationError")

@app.route('/api/auth/login', methods=['POST'])
@limiter.limit("10 per minute")
def login():
    """Clean login system"""
    try:
        data = request.get_json()
        if not data:
            return api_error("Request body required", 400)
            
        email = data.get('email', '').lower().strip()
        password = data.get('password', '')
        
        if not email or not password:
            return api_error("Email and password required", 400)
        
        logger.info(f"Login attempt for: {email}")
        
        # Check if user is whitelisted
        if not whitelist_manager.is_whitelisted(email):
            return api_error("Account not found or not approved for beta access", 401)
        
        # Get user tier
        user_tier = whitelist_manager.get_user_tier(email)
        
        # Create user data (in production, you'd validate password against database)
        user_data = {
            'user_id': generate_api_key(email),
            'email': email,
            'subscription_tier': user_tier
        }
        
        # Generate tokens
        token = create_jwt_token(user_data)
        api_key = generate_api_key(email)
        
        # Log successful login
        log_user_action(user_data['user_id'], "user_logged_in", {"email": email})
        
        logger.info(f"Successful login: {email}")
        
        return api_success({
            'token': token,
            'api_key': api_key,
            'user': user_data,
            'message': f'Welcome back! You have {user_tier} access.'
        })
        
    except Exception as e:
        logger.error(f"Login error: {e}")
        return api_error("Login failed", 500, error_type="LoginError")

@app.route('/api/auth/verify', methods=['GET'])
def verify_token():
    """Verify if user's token is still valid"""
    try:
        token = request.headers.get('Authorization')
        if not token:
            return api_error("No token provided", 401)
        
        from utils import verify_jwt_token
        payload = verify_jwt_token(token)
        
        if not payload:
            return api_error("Invalid or expired token", 401)
        
        return api_success({
            'valid': True,
            'user': {
                'email': payload.get('email'),
                'tier': payload.get('tier'),
                'user_id': payload.get('user_id')
            }
        })
        
    except Exception as e:
        logger.error(f"Token verification error: {e}")
        return api_error("Token verification failed", 500)

@app.route('/api/waitlist', methods=['POST'])
@limiter.limit("3 per minute")
def join_waitlist():
    """Join waitlist endpoint (for the roadmap modal)"""
    try:
        data = request.get_json()
        if not data:
            return api_error("Request body required", 400)
            
        email = data.get('email', '').lower().strip()
        
        if not email or '@' not in email:
            return api_error("Valid email required", 400)
        
        return handle_waitlist_signup(email)
        
    except Exception as e:
        logger.error(f"Waitlist signup error: {e}")
        return api_error("Failed to join waitlist", 500)

# =====================================
# ADMIN ROUTES (for managing whitelist)
# =====================================

@app.route('/admin/whitelist', methods=['POST'])
def admin_add_whitelist():
    """Admin endpoint to add emails to whitelist"""
    try:
        # Simple admin check - replace with your actual admin email
        admin_key = request.headers.get('X-Admin-Key')
        if admin_key != 'your-secret-admin-key-12345':  # Change this!
            return api_error("Admin access required", 403)
        
        data = request.get_json()
        email = data.get('email', '').lower().strip()
        tier = data.get('tier', 'beta')
        
        if not email:
            return api_error("Email required", 400)
        
        whitelist_manager.add_to_whitelist(email, tier)
        logger.info(f"Admin added {email} to {tier} whitelist")
        
        return api_success({"message": f"Added {email} to {tier} whitelist"})
        
    except Exception as e:
        logger.error(f"Admin whitelist error: {e}")
        return api_error("Failed to add to whitelist", 500)

@app.route('/admin/whitelist', methods=['GET'])
def admin_view_whitelist():
    """View current whitelist (admin only)"""
    try:
        admin_key = request.headers.get('X-Admin-Key')
        if admin_key != 'your-secret-admin-key-12345':  # Change this!
            return api_error("Admin access required", 403)
        
        return api_success({
            'beta_emails': list(whitelist_manager.whitelist_emails),
            'vip_emails': list(whitelist_manager.vip_emails),
            'total_whitelisted': len(whitelist_manager.whitelist_emails) + len(whitelist_manager.vip_emails)
        })
        
    except Exception as e:
        logger.error(f"Admin view whitelist error: {e}")
        return api_error("Failed to get whitelist", 500)

# =====================================
# USER PROFILE & INFO
# =====================================

@app.route('/api/user/profile', methods=['GET'])
def get_user_profile():
    """Get user profile (no auth required for demo)"""
    try:
        # In production, you'd require authentication here
        # For demo purposes, return a sample profile
        return api_success({
            'user': {
                'email': 'demo@user.com',
                'subscription_tier': 'beta',
                'features': ['whale_discovery', 'basic_dashboard', 'ai_analysis'],
                'api_usage': {
                    'requests_today': 15,
                    'limit': 100
                }
            }
        })
        
    except Exception as e:
        logger.error(f"Profile fetch error: {e}")
        return api_error("Failed to fetch profile", 500)

@app.route('/api/contact-info', methods=['GET'])
def get_contact_info():
    """Get current contact information"""
    from utils import ContactConfig
    return api_success(ContactConfig.get_contact_info())

if __name__ == '__main__':
    logger.info("Starting Whale Tracker Flask application",
               environment=os.getenv('FLASK_ENV', 'development'),
               debug=config.DEBUG)
    
    # Initialize database
    if not init_database():
        logger.warning("Database initialization failed - continuing anyway")
    
    # Validate configuration
    if not config.DEBUG:
        try:
            config.validate()
            logger.info("Production configuration validated successfully")
        except RuntimeError as e:
            logger.error("Configuration validation failed", error=str(e))
            exit(1)
    
    # Start the application
    app.run(
        debug=config.DEBUG,
        host='0.0.0.0',
        port=int(os.getenv('PORT', 5000))
    )
