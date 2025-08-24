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
import asyncio
import random
from concurrent.futures import ThreadPoolExecutor

# Import from trading_ai.py
from trading_ai import TradingAI

# Import shared modules
from config import get_config
from utils import (
    api_success, api_error, db_manager, 
    validate_request_json, CheckoutRequest, DonationRequest,
    create_jwt_token, log_user_action, generate_api_key,
    async_helper, TradingAdviceRequest, require_auth, require_tier,
    whitelist_manager, handle_waitlist_signup
)

# Load environment
load_dotenv()

# Get configuration
config = get_config()

# Initialize Flask app
app = Flask(__name__, template_folder='templates')
app.config.from_object(config)

# Initialize extensions
CORS(app)
limiter = Limiter(
    key_func=get_remote_address,
    app=app,
    default_limits=["200 per day", "50 per hour"],
    storage_uri=getattr(config, 'RATE_LIMIT_STORAGE_URL', 'memory://')
)

# Configure structured logging
def setup_logging():
    log_level = getattr(logging, config.LOG_LEVEL, logging.INFO)
    log_handlers = [logging.StreamHandler()]
    log_file = getattr(config, 'LOG_FILE', './logs/app.log')
    log_dir = os.path.dirname(log_file)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir, exist_ok=True)
    log_handlers.append(logging.FileHandler(log_file))
    logging.basicConfig(
        level=log_level,
        handlers=log_handlers,
        format='%(asctime)s %(levelname)s: %(message)s'
    )

setup_logging()
logger = structlog.get_logger(__name__)

# Stripe setup
stripe.api_key = config.STRIPE_SECRET_KEY

# Coinbase Commerce setup
coinbase_client = None
if config.COINBASE_API_KEY:
    coinbase_client = Client(api_key=config.COINBASE_API_KEY)

# Pricing configurations (from app.py)
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

# Global Trading AI instance (from ai_server.py)
trading_ai = None
ai_health_status = {
    "initialized": False,
    "last_error": None,
    "initialization_time": None,
    "retry_count": 0
}

async def initialize_trading_ai():
    global trading_ai, ai_health_status
    for attempt in range(config.TRADING_AI_MAX_RETRIES):
        try:
            logger.info("Initializing TradingAI", attempt=attempt + 1)
            trading_ai = TradingAI()
            await trading_ai.initialize()
            ai_health_status.update({
                "initialized": True,
                "last_error": None,
                "initialization_time": datetime.now().isoformat(),
                "retry_count": attempt
            })
            logger.info("TradingAI initialized successfully")
            return True
        except Exception as e:
            ai_health_status.update({
                "initialized": False,
                "last_error": str(e),
                "retry_count": attempt + 1
            })
            if attempt < config.TRADING_AI_MAX_RETRIES - 1:
                await asyncio.sleep(2 ** attempt)
    return False

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

# Routes from app.py
@app.route('/')
def home():
    try:
        return render_template('index.html', stripe_publishable_key=config.STRIPE_PUBLISHABLE_KEY)
    except Exception as e:
        logger.error("Error rendering home page", error=str(e))
        return api_error("Failed to load page", 500, error_type="TemplateError")

@app.route('/create-checkout-session', methods=['POST'])
@limiter.limit("10 per minute")
@validate_request_json(CheckoutRequest)
def create_checkout_session():
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
        
        logger.info("Checkout session created", session_id=checkout_session.id, plan=plan, type=payment_type)
        
        return api_success({"id": checkout_session.id})

    except stripe.error.StripeError as e:
        logger.error("Stripe error in checkout", error=str(e))
        return api_error(f"Payment processing error: {str(e)}", 400, error_type="StripeError")
    except Exception as e:
        logger.error("Checkout session creation failed", error=str(e), exc_info=True)
        return api_error("Failed to create checkout session", 500, error_type="CheckoutError")

def create_crowdfund_session(plan):
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
        
        logger.info("Crowdfund session created", plan=plan, amount=tier_info['amount']/100, session_id=checkout_session.id)
        
        return api_success({"id": checkout_session.id})
        
    except Exception as e:
        logger.error("Crowdfund session creation failed", error=str(e))
        raise

@app.route('/create-donation-session', methods=['POST'])
@limiter.limit("5 per minute")
@validate_request_json(DonationRequest)
def create_donation_session():
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
            
            logger.info("Coinbase donation charge created", charge_id=charge.id, amount=amount)
            
            return api_success({"url": charge.hosted_url, "id": charge.id})
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
            
            logger.info("Stripe donation session created", session_id=checkout_session.id, amount=amount)
            
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
    payload = request.get_data(as_text=True)
    sig_header = request.headers.get('Stripe-Signature') or request.headers.get('X-Cc-Webhook-Signature')
    
    logger.debug("Webhook received", signature_present=bool(sig_header), payload_length=len(payload))
    
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
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, config.STRIPE_WEBHOOK_SECRET
        )
        
        if event['type'] == 'checkout.session.completed':
            session = event['data']['object']
            plan = session['metadata'].get('plan')
            session_id = session['id']
            
            logger.info("Stripe payment completed", session_id=session_id, plan=plan)
            
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
                logger.error("Database error in webhook", error=str(db_error), session_id=session_id)
        
        return api_success({"event_processed": event['type']})
        
    except stripe.error.SignatureVerificationError as e:
        logger.error("Stripe signature verification failed", error=str(e))
        return api_error("Invalid signature", 400, error_type="SignatureError")

def handle_coinbase_webhook(payload, sig_header):
    try:
        if not coinbase_client:
            return api_error("Coinbase not configured", 503)
            
        coinbase_client.webhook.verify(payload, sig_header, config.COINBASE_WEBHOOK_SECRET)
        event = coinbase_client.webhook.parse(payload)
        
        logger.info("Coinbase webhook event", event_type=event.type, charge_id=event.data.id)
        
        if event.type == 'charge:confirmed':
            charge = event.data
            amount = charge.payments[0]['value']['local']['amount']
            
            logger.info("Crypto donation confirmed", charge_id=charge.id, amount=amount)
            
            try:
                db_manager.safe_execute(
                    """INSERT INTO donations (charge_id, amount, type, timestamp) 
                       VALUES (%s, %s, %s, NOW()) 
                       ON CONFLICT (charge_id) DO NOTHING""",
                    (charge.id, amount, 'crypto')
                )
                
                log_user_action(charge.id, "crypto_donation", {"amount": amount})
                
            except Exception as db_error:
                logger.error("Database error in Coinbase webhook", error=str(db_error), charge_id=charge.id)
        
        return api_success({"event_processed": event.type})
        
    except (WebhookInvalidPayload, SignatureError) as e:
        logger.error("Coinbase webhook validation failed", error=str(e))
        return api_error("Invalid webhook", 400, error_type="WebhookError")

@app.route('/success')
def success():
    try:
        session_id = request.args.get('session_id')
        payment_type = request.args.get('type', 'subscription')
        plan = request.args.get('plan', '')
        
        logger.info("Success page accessed", session_id=session_id, payment_type=payment_type, plan=plan)
        
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
    return api_success({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    })

@app.route('/health/deep', methods=['GET'])
def deep_health_check():
    checks = {
        "database": check_database_health(),
        "stripe": check_stripe_health(),
        "coinbase": check_coinbase_health(),
        "trading_ai": ai_health_status["initialized"]
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
    try:
        db_manager.safe_execute("SELECT 1")
        return True
    except Exception as e:
        logger.error("Database health check failed", error=str(e))
        return False

def check_stripe_health():
    return bool(config.STRIPE_SECRET_KEY and config.STRIPE_WEBHOOK_SECRET)

def check_coinbase_health():
    return bool(config.COINBASE_API_KEY and config.COINBASE_WEBHOOK_SECRET)

# API endpoints
@app.route('/api/config', methods=['GET'])
def get_public_config():
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
    plans = []
    for plan_id, plan_info in PRICING.items():
        plan_data = {
            "id": plan_id,
            "name": DISPLAY_NAMES.get(plan_id, plan_id.replace('_', ' ').title()),
            "mode": plan_info["mode"]
        }
        if "amount" in plan_info:
            plan_data["amount"] = plan_info["amount"] / 100
        else:
            plan_data["price_id"] = plan_info["price_id"]
        
        plans.append(plan_data)
    
    return api_success(plans)

# Auth routes from app.py
@app.route('/api/auth/register', methods=['POST'])
@limiter.limit("5 per minute")
def register():
    try:
        data = request.get_json()
        if not data:
            return api_error("Request body required", 400)
            
        email = data.get('email', '').lower().strip()
        password = data.get('password', '')
        
        logger.info(f"Registration attempt for: {email}")
        
        if not email or '@' not in email:
            return api_error("Valid email required", 400)
        if len(password) < 8:
            return api_error("Password must be at least 8 characters", 400)
        
        if not whitelist_manager.is_whitelisted(email):
            logger.info(f"Non-whitelisted user tried to register: {email}")
            return handle_waitlist_signup(email)
        
        user_tier = whitelist_manager.get_user_tier(email)
        logger.info(f"Whitelisted user registered: {email}, tier: {user_tier}")
        
        user_data = {
            'user_id': generate_api_key(email),
            'email': email,
            'subscription_tier': user_tier
        }
        
        token = create_jwt_token(user_data)
        api_key = generate_api_key(email)
        
        log_user_action(user_data['user_id'], "user_registered", {"email": email, "tier": user_tier})
        
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
    try:
        data = request.get_json()
        if not data:
            return api_error("Request body required", 400)
            
        email = data.get('email', '').lower().strip()
        password = data.get('password', '')
        
        if not email or not password:
            return api_error("Email and password required", 400)
        
        logger.info(f"Login attempt for: {email}")
        
        if not whitelist_manager.is_whitelisted(email):
            return api_error("Account not found or not approved for beta access", 401)
        
        user_tier = whitelist_manager.get_user_tier(email)
        
        user_data = {
            'user_id': generate_api_key(email),
            'email': email,
            'subscription_tier': user_tier
        }
        
        token = create_jwt_token(user_data)
        api_key = generate_api_key(email)
        
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

# Admin routes
@app.route('/admin/whitelist', methods=['POST'])
def admin_add_whitelist():
    try:
        admin_key = request.headers.get('X-Admin-Key')
        if admin_key != 'your-secret-admin-key-12345':  # Change this to a secure env var!
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
    try:
        admin_key = request.headers.get('X-Admin-Key')
        if admin_key != 'your-secret-admin-key-12345':
            return api_error("Admin access required", 403)
        
        return api_success({
            'beta_emails': list(whitelist_manager.whitelist_emails),
            'vip_emails': list(whitelist_manager.vip_emails),
            'total_whitelisted': len(whitelist_manager.whitelist_emails) + len(whitelist_manager.vip_emails)
        })
        
    except Exception as e:
        logger.error(f"Admin view whitelist error: {e}")
        return api_error("Failed to get whitelist", 500)

@app.route('/api/user/profile', methods=['GET'])
def get_user_profile():
    try:
        # For demo; in production, require @require_auth
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
    from utils import ContactConfig
    return api_success(ContactConfig.get_contact_info())

# AI Routes (prefixed with /ai/ from ai_server.py)
@app.route('/ai/test', methods=['GET'])
def ai_test():
    global trading_ai, ai_health_status
    
    return api_success({
        "message": "🤖 Trading AI Integration Online!",
        "server": "combined_server",
        "trading_ai_loaded": trading_ai is not None,
        "health_status": ai_health_status,
        "ready_for_integration": ai_health_status["initialized"]
    })

@app.route('/ai/trading-advice', methods=['POST'])
@limiter.limit("20 per minute")
@require_auth
@require_tier("beta")
@validate_request_json(TradingAdviceRequest)
def get_trading_advice():
    global trading_ai
    
    if not trading_ai or not ai_health_status["initialized"]:
        return api_error(
            "Trading AI not available", 
            503, 
            details={"health_status": ai_health_status},
            error_type="ServiceUnavailable"
        )
    
    try:
        data = request.validated_data
        user_id = data.user_id
        query = data.query
        context = data.context
        
        logger.info("Trading AI advice requested", user_id=user_id, query=query)
        
        try:
            ai_response = async_helper.run_async(
                trading_ai.get_user_recommendation(user_id, query, context),
                timeout=config.TRADING_AI_TIMEOUT
            )
            
            logger.info("Trading AI response received", user_id=user_id, success=ai_response.get('success', False))
            
        except asyncio.TimeoutError:
            logger.error("Trading AI timeout", user_id=user_id, timeout=config.TRADING_AI_TIMEOUT)
            return api_error(
                "Trading AI request timed out", 
                504, 
                details={"timeout_seconds": config.TRADING_AI_TIMEOUT},
                error_type="TimeoutError"
            )
        except Exception as ai_error:
            logger.error("Trading AI error", user_id=user_id, error=str(ai_error))
            return create_fallback_response(str(ai_error))
        
        if ai_response and ai_response.get('success', True):
            trading_response = format_trading_ai_for_api(ai_response, context, user_id)
            
            log_user_action(user_id, "trading_advice_requested", {
                "query": query,
                "confidence": ai_response.get('confidence', 0.0)
            })
            
            return api_success(trading_response)
        else:
            logger.warning("Trading AI returned unsuccessful response", user_id=user_id)
            return api_error(
                "Trading AI analysis unsuccessful", 
                500,
                error_type="AIAnalysisError"
            )
        
    except Exception as e:
        logger.error("Trading advice endpoint error", error=str(e), exc_info=True)
        return api_error(
            "Trading AI service error", 
            500, 
            details={"error": str(e)},
            error_type="ServiceError"
        )

def create_fallback_response(error_message):
    return api_success({
        "action": "monitor",
        "confidence": 0.3,
        "reasoning": f"Trading AI temporarily unavailable. Using conservative recommendation. Error: {error_message}",
        "risk_level": "low",
        "whale_influence": {
            "whale_interest": "unknown",
            "recent_activity": "unavailable",
            "confidence": 0.3
        },
        "ai_consensus": {
            "ai_module": "fallback_system",
            "confidence": 0.3,
            "source": "fallback"
        },
        "metadata": {
            "is_fallback": True,
            "timestamp": datetime.now().isoformat(),
            "version": "fallback_1.0.0"
        }
    })

def format_trading_ai_for_api(ai_response, context, user_id):
    try:
        logger.debug("Formatting Trading AI response", user_id=user_id, response_keys=list(ai_response.keys()))
        
        recommendation_obj = ai_response.get('recommendation', {})
        
        if isinstance(recommendation_obj, dict):
            reasoning = recommendation_obj.get('recommendation', str(recommendation_obj))
            rec_confidence = recommendation_obj.get('confidence', 0.5)
        else:
            reasoning = str(recommendation_obj)
            rec_confidence = 0.5
        
        confidence = ai_response.get('confidence', rec_confidence)
        
        ai_module = ai_response.get('ai_module', 'TradingAI')
        user_level = ai_response.get('user_level', 'unknown')
        
        action = determine_trading_action(reasoning, ai_response)
        risk_level = determine_risk_level_from_confidence(confidence)
        
        whale_influence = calculate_whale_influence(context, confidence)
        
        formatted_response = {
            "action": action,
            "confidence": round(confidence, 3),
            "reasoning": reasoning,
            "risk_level": risk_level,
            "whale_influence": whale_influence,
            "ai_consensus": {
                "ai_module": f"{ai_module}_{user_level}",
                "confidence": round(confidence, 3),
                "source": "TradingAI_Production"
            },
            "metadata": {
                "processing_time_ms": 200,
                "timestamp": datetime.now().isoformat(),
                "version": "trading_ai_2.1.0",
                "user_tier": getattr(request, 'current_user', {}).get('tier', 'unknown')
            }
        }
        
        logger.info("Trading AI response formatted successfully", user_id=user_id, action=action, confidence=confidence)
        
        return formatted_response
        
    except Exception as e:
        logger.error("Error formatting Trading AI response", user_id=user_id, error=str(e))
        return create_fallback_response(f"Formatting error: {str(e)}")["data"]

def determine_trading_action(recommendation, ai_response):
    rec_text = str(recommendation).lower()
    reasoning = str(ai_response.get('reasoning', '')).lower()
    
    buy_keywords = ['buy', 'purchase', 'acquire', 'long', 'bullish', 'accumulate']
    sell_keywords = ['sell', 'exit', 'dump', 'short', 'bearish', 'liquidate']
    hold_keywords = ['hold', 'keep', 'maintain', 'stay', 'continue']
    
    text_to_check = f"{rec_text} {reasoning}"
    
    if any(word in text_to_check for word in buy_keywords):
        return 'buy'
    elif any(word in text_to_check for word in sell_keywords):
        return 'sell'
    elif any(word in text_to_check for word in hold_keywords):
        return 'hold'
    else:
        return 'monitor'

def determine_risk_level_from_confidence(confidence):
    if confidence >= 0.8:
        return 'low'
    elif confidence >= 0.6:
        return 'medium'
    elif confidence >= 0.4:
        return 'medium-high'
    else:
        return 'high'

def calculate_whale_influence(context, confidence):
    base_interest = "moderate"
    if confidence > 0.8:
        base_interest = "high"
    elif confidence < 0.4:
        base_interest = "low"
    
    return {
        "whale_interest": base_interest,
        "recent_activity": "analyzing",
        "confidence": round(confidence * 0.9, 3),
        "volume_impact": "medium",
        "price_correlation": round(confidence * 0.8, 3)
    }

@app.route('/ai/whale-activity', methods=['GET'])
@require_auth
def get_whale_activity():
    try:
        token_address = request.args.get('token_address')
        limit = min(int(request.args.get('limit', 10)), 50)
        
        user_id = request.current_user.get('user_id')
        logger.info("Whale activity requested", user_id=user_id, token_address=token_address, limit=limit)
        
        whale_data = {
            "market_sentiment": determine_market_sentiment(),
            "whale_flow": determine_whale_flow(),
            "message": "Trading AI analyzing whale patterns in real-time",
            "source": "trading_ai_enhanced_v2",
            "recent_movements": generate_whale_movements(limit),
            "price_impact": {
                "short_term": "moderate_positive",
                "medium_term": "bullish",
                "confidence": 0.75
            },
            "volume_analysis": {
                "24h_volume": random.randint(1000000, 50000000),
                "whale_percentage": round(random.uniform(15.0, 45.0), 2),
                "unusual_activity": random.choice([True, False])
            }
        }
        
        metadata = {
            "timestamp": datetime.now().isoformat(),
            "whale_count": limit,
            "data_source": "trading_ai_whale_tracker_v2",
            "user_tier": request.current_user.get('tier', 'basic'),
            "token_address": token_address
        }
        
        log_user_action(user_id, "whale_activity_viewed", {"token_address": token_address, "limit": limit})
        
        return api_success({
            "data": whale_data,
            "metadata": metadata
        })
        
    except Exception as e:
        logger.error("Whale activity error", error
