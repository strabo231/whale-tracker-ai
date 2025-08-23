import asyncio
import threading
import time
import hashlib
import logging
import psycopg2
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
from functools import wraps
from flask import jsonify, request
from pydantic import BaseModel, validator
from typing import Optional, Dict, Any, List
import jwt
from config import get_config

config = get_config()
logger = logging.getLogger(__name__)

# Pydantic Models for Request Validation
class TradingAdviceRequest(BaseModel):
    user_id: str
    query: str = "general trading analysis"
    context: Dict[str, Any] = {}
    
    @validator('user_id')
    def user_id_must_not_be_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('user_id cannot be empty')
        return v.strip()

class DonationRequest(BaseModel):
    amount: float
    method: str = "card"
    
    @validator('amount')
    def validate_amount(cls, v):
        if not isinstance(v, (int, float)):
            raise ValueError('Amount must be a number')
        if not (49 <= v <= 10000):
            raise ValueError('Amount must be between $49 and $10,000')
        return float(v)
    
    @validator('method')
    def validate_method(cls, v):
        if v not in ['card', 'crypto']:
            raise ValueError('Method must be either "card" or "crypto"')
        return v

class CheckoutRequest(BaseModel):
    plan: str
    type: str = "subscription"
    
    @validator('plan')
    def validate_plan(cls, v):
        valid_plans = ['professional', 'emergency', 'enterprise', 'sixmonth', 
                      'house_hero', 'family_guardian', 'life_changer', 'legend']
        if v not in valid_plans:
            raise ValueError(f'Invalid plan. Must be one of: {valid_plans}')
        return v

# Standardized API Response Functions
def api_success(data=None, message="Success", metadata=None):
    """Standardized success response"""
    response = {
        "success": True,
        "message": message,
        "timestamp": datetime.now().isoformat()
    }
    if data is not None:
        response["data"] = data
    if metadata:
        response["metadata"] = metadata
    return jsonify(response)

def api_error(message, code=400, details=None, error_type="ValidationError"):
    """Standardized error response"""
    response = {
        "success": False,
        "error": {
            "type": error_type,
            "message": message,
            "code": code
        },
        "timestamp": datetime.now().isoformat()
    }
    if details:
        response["error"]["details"] = details
    
    logger.warning(f"API Error {code}: {message}", extra={"details": details})
    return jsonify(response), code

# Database Connection Management
class DatabaseManager:
    """Thread-safe database connection manager"""
    
    def __init__(self):
        self.pool = None
        self._lock = threading.Lock()
    
    def get_connection(self):
        """Get database connection with proper error handling"""
        try:
            conn = psycopg2.connect(
                config.DATABASE_URL,
                connect_timeout=config.DATABASE_TIMEOUT
            )
            conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
            return conn
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            raise
    
    def safe_execute(self, query, params=None, fetch=False):
        """Execute database query with proper error handling"""
        conn = None
        cursor = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute(query, params or ())
            
            if fetch:
                return cursor.fetchall()
            return cursor.rowcount
            
        except Exception as e:
            logger.error(f"Database query failed: {e}", extra={
                "query": query,
                "params": params
            })
            if conn:
                conn.rollback()
            raise
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

# Global database manager instance
db_manager = DatabaseManager()

# Whitelist Management
class WhitelistManager:
    """Manage beta access whitelist"""
    
    def __init__(self):
        # For launch, you can add emails manually here
        # Later, move to database
        self.whitelist_emails = {
            # Add your beta testers here - REPLACE THESE WITH REAL EMAILS
            "your-email@gmail.com",        # Replace with your actual email
            "beta@whaletracker.com",       # Replace with real beta tester
            "investor@example.com",        # Replace with real investor email
            "friend@gmail.com",            # Replace with real friend's email
            # Add more real emails as needed
        }
        
        # VIP list gets instant access + perks  
        self.vip_emails = {
            "your-admin-email@gmail.com",  # Replace with your real admin email
            # Add investors, key supporters with their real emails
        }
    
    def is_whitelisted(self, email):
        """Check if email is whitelisted"""
        email = email.lower().strip()
        return email in self.whitelist_emails or email in self.vip_emails
    
    def get_user_tier(self, email):
        """Get user tier based on whitelist status"""
        email = email.lower().strip()
        if email in self.vip_emails:
            return "vip"
        elif email in self.whitelist_emails:
            return "beta"
        else:
            return "waitlist"
    
    def add_to_whitelist(self, email, tier="beta"):
        """Add email to whitelist (for admin use)"""
        email = email.lower().strip()
        if tier == "vip":
            self.vip_emails.add(email)
        else:
            self.whitelist_emails.add(email)
        
        # In production, save to database
        self._save_to_database(email, tier)
    
    def _save_to_database(self, email, tier):
        """Save whitelist status to database"""
        try:
            db_manager.safe_execute(
                """INSERT INTO whitelist (email, tier, added_at) 
                   VALUES (%s, %s, NOW()) 
                   ON CONFLICT (email) DO UPDATE SET tier = EXCLUDED.tier""",
                (email, tier)
            )
        except Exception as e:
            logger.error("Failed to save whitelist", extra={"email": email, "error": str(e)})

# Global whitelist manager
whitelist_manager = WhitelistManager()

# Helper functions for whitelist (to be used in app.py)
def handle_waitlist_signup(email):
    """Handle users not on whitelist"""
    try:
        # Add to waitlist database
        db_manager.safe_execute(
            """INSERT INTO waitlist (email, signup_date) 
               VALUES (%s, NOW()) 
               ON CONFLICT (email) DO NOTHING""",
            (email,)
        )
        
        logger.info("User added to waitlist", extra={"email": email})
        
        return api_success({
            'waitlisted': True,
            'message': 'Thanks for your interest! You\'ve been added to our beta waitlist. We\'ll notify you when access becomes available.',
            'position': get_waitlist_position(email)
        })
        
    except Exception as e:
        logger.error("Waitlist signup error", extra={"error": str(e)})
        return api_error("Failed to join waitlist", 500, error_type="WaitlistError")

def get_waitlist_position(email):
    """Get user's position in waitlist"""
    try:
        result = db_manager.safe_execute(
            """SELECT COUNT(*) FROM waitlist 
               WHERE signup_date <= (SELECT signup_date FROM waitlist WHERE email = %s)""",
            (email,), fetch=True
        )
        return result[0][0] if result else 1
    except:
        return 1

# Async Helper for Trading AI
class AsyncHelper:
    """Helper to run async functions in Flask synchronous context"""
    
    def __init__(self):
        self.executor = ThreadPoolExecutor(max_workers=4)
        self.loop = None
        self._start_loop()
    
    def _start_loop(self):
        """Start background event loop"""
        def run_loop():
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)
            self.loop.run_forever()
        
        thread = threading.Thread(target=run_loop, daemon=True)
        thread.start()
        
        # Wait for loop to be ready
        while self.loop is None:
            time.sleep(0.01)
    
    def run_async(self, coro, timeout=None):
        """Run async coroutine and return result"""
        if timeout is None:
            timeout = config.TRADING_AI_TIMEOUT
            
        try:
            future = asyncio.run_coroutine_threadsafe(coro, self.loop)
            return future.result(timeout=timeout)
        except asyncio.TimeoutError:
            logger.error(f"Async operation timed out after {timeout}s")
            raise
        except Exception as e:
            logger.error(f"Async operation failed: {e}")
            raise

# Global async helper instance
async_helper = AsyncHelper()

# Authentication Functions
def create_jwt_token(user_data):
    """Create JWT token for user"""
    payload = {
        'user_id': user_data.get('user_id'),
        'email': user_data.get('email'),
        'tier': user_data.get('subscription_tier', 'basic'),
        'exp': datetime.utcnow() + config.JWT_ACCESS_TOKEN_EXPIRES,
        'iat': datetime.utcnow()
    }
    return jwt.encode(payload, config.JWT_SECRET_KEY, algorithm='HS256')

def verify_jwt_token(token):
    """Verify and decode JWT token"""
    try:
        if token.startswith('Bearer '):
            token = token[7:]
        payload = jwt.decode(token, config.JWT_SECRET_KEY, algorithms=['HS256'])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

# Authentication Decorators
def require_auth(f):
    """Decorator to require authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return api_error("Authentication required", 401, error_type="AuthenticationError")
        
        payload = verify_jwt_token(token)
        if not payload:
            return api_error("Invalid or expired token", 401, error_type="AuthenticationError")
        
        request.current_user = payload
        return f(*args, **kwargs)
    return decorated_function

def require_tier(min_tier):
    """Decorator to require minimum subscription tier"""
    tier_levels = {'basic': 0, 'beta': 1, 'professional': 2, 'enterprise': 3, 'vip': 4}
    
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not hasattr(request, 'current_user'):
                return api_error("Authentication required", 401, error_type="AuthenticationError")
            
            user_tier = request.current_user.get('tier', 'basic')
            user_level = tier_levels.get(user_tier, 0)
            required_level = tier_levels.get(min_tier, 0)
            
            if user_level < required_level:
                return api_error(
                    f"Subscription tier '{min_tier}' or higher required",
                    403,
                    error_type="SubscriptionError"
                )
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# Validation Helper
def validate_request_json(model_class):
    """Decorator to validate request JSON against Pydantic model"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                data = request.get_json()
                if not data:
                    return api_error("Request body required", 400)
                
                validated_data = model_class(**data)
                request.validated_data = validated_data
                return f(*args, **kwargs)
                
            except Exception as e:
                return api_error(f"Validation error: {str(e)}", 400)
        return decorated_function
    return decorator

# Health Check Functions
def check_database_connection():
    """Check if database is accessible"""
    try:
        db_manager.safe_execute("SELECT 1")
        return True
    except Exception:
        return False

def check_stripe_connection():
    """Check if Stripe is configured"""
    return bool(config.STRIPE_SECRET_KEY and config.STRIPE_WEBHOOK_SECRET)

def check_coinbase_connection():
    """Check if Coinbase is configured"""
    return bool(config.COINBASE_API_KEY and config.COINBASE_WEBHOOK_SECRET)

# Utility Functions
def generate_api_key(email):
    """Generate API key for user"""
    return f'wt_{hashlib.md5(email.encode()).hexdigest()[:16]}'

def log_user_action(user_id, action, details=None):
    """Log user action for analytics"""
    logger.info(f"User action: {action}", extra={
        "user_id": user_id,
        "action": action,
        "details": details,
        "timestamp": datetime.now().isoformat()
    })

def safe_float(value, default=0.0):
    """Safely convert value to float"""
    try:
        return float(value)
    except (ValueError, TypeError):
        return default

def safe_int(value, default=0):
    """Safely convert value to int"""
    try:
        return int(value)
    except (ValueError, TypeError):
        return default

# Contact Configuration
class ContactConfig:
    """Real contact information for the platform"""
    
    # UPDATE THESE WITH YOUR REAL INFORMATION
    COMPANY_NAME = "Whale Tracker Pro"
    SUPPORT_EMAIL = "support@your-domain.com"  # Replace with real email
    BUSINESS_EMAIL = "business@your-domain.com"  # Replace with real email
    PHONE_NUMBER = "+1 (555) 123-4567"  # Replace with real phone
    
    # Business Address (if you have one, or use a business mailbox service)
    BUSINESS_ADDRESS = {
        "street": "123 Business St",
        "city": "Charlotte", 
        "state": "NC",
        "zip": "28202",
        "country": "USA"
    }
    
    # Social Media (optional)
    SOCIAL_LINKS = {
        "twitter": "https://twitter.com/whaletrackerpro",
        "linkedin": "https://linkedin.com/company/whaletrackerpro",
        "discord": "https://discord.gg/whaletracker"
    }
    
    # Legal/Privacy
    PRIVACY_POLICY_URL = "/privacy"
    TERMS_OF_SERVICE_URL = "/terms"
    
    @classmethod
    def get_contact_info(cls):
        return {
            "support_email": cls.SUPPORT_EMAIL,
            "business_email": cls.BUSINESS_EMAIL,
            "phone": cls.PHONE_NUMBER,
            "address": cls.BUSINESS_ADDRESS,
            "social": cls.SOCIAL_LINKS
        }
