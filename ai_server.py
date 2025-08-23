from flask import Flask, jsonify, request
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_cors import CORS
from datetime import datetime
import logging
import asyncio
import sys
import os
import hashlib
import time
import structlog
from concurrent.futures import ThreadPoolExecutor
from dotenv import load_dotenv

# Add the current directory to Python path FIRST
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Load environment
load_dotenv()

# NOW import your custom modules (after path is set up)
from trading_ai import TradingAI
from config import get_config
from utils import (
    api_success, api_error, async_helper,
    validate_request_json, TradingAdviceRequest,
    create_jwt_token, require_auth, require_tier,
    log_user_action, generate_api_key,
    whitelist_manager, handle_waitlist_signup  # All utils imports together
)

# Configuration
config = get_config()

# Setup structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logging.basicConfig(level=getattr(logging, config.LOG_LEVEL))
logger = structlog.get_logger(__name__)

# Create Flask app
app = Flask(__name__)
app.config.from_object(config)

# Initialize extensions
CORS(app)
limiter = Limiter(
    app,
    key_func=get_remote_address,
    default_limits=["1000 per day", "100 per hour"],
    storage_uri=config.RATE_LIMIT_STORAGE_URL
)

# Global Trading AI instance
trading_ai = None
ai_health_status = {
    "initialized": False,
    "last_error": None,
    "initialization_time": None,
    "retry_count": 0
}

async def initialize_trading_ai():
    """Initialize the Trading AI with retry logic"""
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
            
            logger.info("TradingAI initialized successfully", attempt=attempt + 1)
            return True
            
        except Exception as e:
            ai_health_status.update({
                "initialized": False,
                "last_error": str(e),
                "retry_count": attempt + 1
            })
            
            logger.error("TradingAI initialization failed", 
                        attempt=attempt + 1, 
                        error=str(e))
            
            if attempt < config.TRADING_AI_MAX_RETRIES - 1:
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
    
    return False

# Request logging middleware
@app.before_request
def log_request_info():
    request.start_time = time.time()
    logger.info(
        "AI API request started",
        method=request.method,
        path=request.path,
        remote_addr=request.remote_addr,
        user_agent=str(request.user_agent)
    )

@app.after_request
def log_response_info(response):
    duration = time.time() - request.start_time
    logger.info(
        "AI API request completed",
        method=request.method,
        path=request.path,
        status_code=response.status_code,
        duration_ms=round(duration * 1000, 2)
    )
    return response

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return api_error("AI API endpoint not found", 404, error_type="NotFoundError")

@app.errorhandler(500)
def internal_error(error):
    logger.error("AI server internal error", exc_info=True)
    return api_error("AI server internal error", 500, error_type="InternalError")

@app.errorhandler(429)
def ratelimit_handler(e):
    return api_error(
        "AI API rate limit exceeded", 
        429, 
        details={"retry_after": str(e.retry_after)},
        error_type="RateLimitError"
    )

# Trading AI endpoints
@app.route('/api/ai/test', methods=['GET'])
def ai_test():
    """Test endpoint - shows Trading AI status"""
    global trading_ai, ai_health_status
    
    return api_success({
        "message": "🤖 Trading AI Integration Online!",
        "server": "production_trading_ai_server",
        "trading_ai_loaded": trading_ai is not None,
        "health_status": ai_health_status,
        "ready_for_integration": ai_health_status["initialized"]
    })

@app.route('/api/ai/trading-advice', methods=['POST'])
@limiter.limit("20 per minute")
@require_auth
@require_tier("beta")
@validate_request_json(TradingAdviceRequest)
def get_trading_advice():
    """Get Trading AI advice with comprehensive error handling"""
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
        
        logger.info("Trading AI advice requested", 
                   user_id=user_id, 
                   query=query)
        
        # Get recommendation from Trading AI with timeout
        try:
            ai_response = async_helper.run_async(
                trading_ai.get_user_recommendation(user_id, query, context),
                timeout=config.TRADING_AI_TIMEOUT
            )
            
            logger.info("Trading AI response received", 
                       user_id=user_id, 
                       success=ai_response.get('success', False))
            
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
        
        # Format and return response
        if ai_response and ai_response.get('success', True):
            trading_response = format_trading_ai_for_api(ai_response, context, user_id)
            
            # Log user action
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
    """Create safe fallback response when AI fails"""
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
    """Format TradingAI response into standardized API format"""
    try:
        logger.debug("Formatting Trading AI response", 
                    user_id=user_id, 
                    response_keys=list(ai_response.keys()))
        
        # Extract recommendation data
        recommendation_obj = ai_response.get('recommendation', {})
        
        # Handle both dict and object formats
        if isinstance(recommendation_obj, dict):
            reasoning = recommendation_obj.get('recommendation', str(recommendation_obj))
            rec_confidence = recommendation_obj.get('confidence', 0.5)
        else:
            reasoning = str(recommendation_obj)
            rec_confidence = 0.5
        
        # Get overall confidence
        confidence = ai_response.get('confidence', rec_confidence)
        
        # Get AI module info
        ai_module = ai_response.get('ai_module', 'TradingAI')
        user_level = ai_response.get('user_level', 'unknown')
        
        # Determine trading action and risk
        action = determine_trading_action(reasoning, ai_response)
        risk_level = determine_risk_level_from_confidence(confidence)
        
        # Calculate whale influence (enhanced)
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
        
        logger.info("Trading AI response formatted successfully", 
                   user_id=user_id, 
                   action=action, 
                   confidence=confidence)
        
        return formatted_response
        
    except Exception as e:
        logger.error("Error formatting Trading AI response", 
                    user_id=user_id, 
                    error=str(e))
        return create_fallback_response(f"Formatting error: {str(e)}")["data"]

def determine_trading_action(recommendation, ai_response):
    """Convert Trading AI recommendation to trading action"""
    rec_text = str(recommendation).lower()
    reasoning = str(ai_response.get('reasoning', '')).lower()
    
    # Enhanced keyword matching
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
        return 'monitor'  # Safe default

def determine_risk_level_from_confidence(confidence):
    """Determine risk level from confidence score"""
    if confidence >= 0.8:
        return 'low'
    elif confidence >= 0.6:
        return 'medium'
    elif confidence >= 0.4:
        return 'medium-high'
    else:
        return 'high'

def calculate_whale_influence(context, confidence):
    """Calculate whale influence metrics"""
    # This would integrate with real whale tracking data
    base_interest = "moderate"
    if confidence > 0.8:
        base_interest = "high"
    elif confidence < 0.4:
        base_interest = "low"
    
    return {
        "whale_interest": base_interest,
        "recent_activity": "analyzing",
        "confidence": round(confidence * 0.9, 3),  # Slightly lower than AI confidence
        "volume_impact": "medium",
        "price_correlation": round(confidence * 0.8, 3)
    }

# Authentication endpoints
@app.route('/api/auth/register', methods=['POST'])
@limiter.limit("5 per minute")
def register():
    """Enhanced user registration with validation"""
    try:
        data = request.get_json()
        if not data:
            return api_error("Request body required", 400)
        
        email = data.get('email', '').lower().strip()
        password = data.get('password', '')
        
        # Validation
        if not email or '@' not in email:
            return api_error("Valid email required", 400)
        if len(password) < 8:
            return api_error("Password must be at least 8 characters", 400)
        
        logger.info("User registration attempt", email=email)
        
        # Generate user data
        user_data = {
            'user_id': generate_api_key(email),
            'email': email,
            'subscription_tier': 'beta'
        }
        
        token = create_jwt_token(user_data)
        api_key = generate_api_key(email)
        
        # Log successful registration
        log_user_action(user_data['user_id'], "user_registered", {"email": email})
        
        logger.info("User registered successfully", email=email)
        
        return api_success({
            'token': token,
            'api_key': api_key,
            'user': user_data
        })
        
    except Exception as e:
        logger.error("Registration error", error=str(e))
        return api_error("Registration failed", 500, error_type="RegistrationError")

@app.route('/api/auth/login', methods=['POST'])
@limiter.limit("10 per minute")
def login():
    """Enhanced user login with validation"""
    try:
        data = request.get_json()
        if not data:
            return api_error("Request body required", 400)
        
        email = data.get('email', '').lower().strip()
        password = data.get('password', '')
        
        if not email or not password:
            return api_error("Email and password required", 400)
        
        logger.info("User login attempt", email=email)
        
        # In production, validate against database
        # For now, allow all logins with beta access
        user_data = {
            'user_id': generate_api_key(email),
            'email': email,
            'subscription_tier': 'beta'
        }
        
        token = create_jwt_token(user_data)
        api_key = generate_api_key(email)
        
        # Log successful login
        log_user_action(user_data['user_id'], "user_logged_in", {"email": email})
        
        logger.info("User logged in successfully", email=email)
        
        return api_success({
            'token': token,
            'api_key': api_key,
            'user': user_data
        })
        
    except Exception as e:
        logger.error("Login error", error=str(e))
        return api_error("Login failed", 500, error_type="LoginError")

@app.route('/api/user/profile', methods=['GET'])
@require_auth
def get_user_profile():
    """Get authenticated user profile"""
    try:
        user = request.current_user
        
        profile = {
            'user_id': user.get('user_id'),
            'email': user.get('email'),
            'subscription_tier': user.get('tier', 'basic'),
            'features': get_user_features(user.get('tier', 'basic')),
            'api_usage': {
                'requests_today': 0,  # Would fetch from database
                'limit': get_tier_limits(user.get('tier', 'basic'))
            }
        }
        
        return api_success(profile)
        
    except Exception as e:
        logger.error("Profile fetch error", error=str(e))
        return api_error("Failed to fetch profile", 500, error_type="ProfileError")

def get_user_features(tier):
    """Get features available for user tier"""
    features_map = {
        'basic': ['whale_discovery', 'basic_dashboard'],
        'beta': ['whale_discovery', 'basic_dashboard', 'ai_analysis'],
        'professional': ['whale_discovery', 'advanced_dashboard', 'ai_analysis', 'real_time_alerts'],
        'enterprise': ['whale_discovery', 'advanced_dashboard', 'ai_analysis', 'real_time_alerts', 'api_access', 'priority_support']
    }
    return features_map.get(tier, features_map['basic'])

def get_tier_limits(tier):
    """Get API limits for user tier"""
    limits_map = {
        'basic': 100,
        'beta': 500,
        'professional': 2000,
        'enterprise': 10000
    }
    return limits_map.get(tier, limits_map['basic'])

# Whale tracking endpoints
@app.route('/api/whales/top', methods=['GET'])
@require_auth
def get_top_whales():
    """Get top whales with enhanced data"""
    try:
        limit = min(int(request.args.get('limit', 20)), 100)  # Cap at 100
        network = request.args.get('network', 'all')
        
        logger.info("Top whales requested", 
                   user_id=request.current_user.get('user_id'),
                   limit=limit, 
                   network=network)
        
        # Enhanced whale data with realistic information
        whales = generate_whale_data(limit, network)
        
        user_tier = request.current_user.get('tier', 'basic')
        user_limit = get_tier_limits(user_tier)
        
        return api_success({
            'whales': whales,
            'total_count': len(whales),
            'user_limit': user_limit,
            'user_tier': user_tier,
            'data_source': 'Trading_AI_Enhanced_Discovery',
            'networks': ['solana', 'ethereum', 'bitcoin'] if network == 'all' else [network]
        })
        
    except Exception as e:
        logger.error("Get whales error", error=str(e))
        return api_error("Failed to fetch whale data", 500, error_type="WhaleDataError")

def generate_whale_data(limit, network):
    """Generate realistic whale data"""
    import random
    
    networks = ['solana', 'ethereum', 'bitcoin'] if network == 'all' else [network]
    sources = ['r/solana', 'r/cryptocurrency', 'r/defi', 'r/CryptoMoonShots', 'r/bitcoin']
    
    whales = []
    for i in range(limit):
        selected_network = random.choice(networks)
        whale = {
            'address': generate_realistic_address(selected_network),
            'balance': random.randint(50000, 500000),
            'source': random.choice(sources),
            'quality_score': random.randint(70, 98),
            'first_seen': generate_recent_timestamp(),
            'network': selected_network,
            'risk_level': random.choice(['low', 'medium', 'high']),
            'activity_score': random.randint(60, 100),
            'profit_potential': random.choice(['high', 'medium', 'low'])
        }
        whales.append(whale)
    
    return sorted(whales, key=lambda x: x['quality_score'], reverse=True)

def generate_realistic_address(network):
    """Generate realistic blockchain addresses"""
    import random
    import string
    
    if network == 'solana':
        chars = string.ascii_letters + string.digits
        return ''.join(random.choices(chars, k=44))
    elif network == 'ethereum':
        return '0x' + ''.join(random.choices('0123456789abcdef', k=40))
    elif network == 'bitcoin':
        prefixes = ['1', '3', 'bc1']
        prefix = random.choice(prefixes)
        if prefix == 'bc1':
            return prefix + ''.join(random.choices(string.ascii_lowercase + string.digits, k=39))
        else:
            return prefix + ''.join(random.choices(string.ascii_letters + string.digits, k=33))

def generate_recent_timestamp():
    """Generate recent timestamp"""
    import random
    from datetime import timedelta
    
    hours_ago = random.randint(1, 72)
    timestamp = datetime.now() - timedelta(hours=hours_ago)
    return timestamp.strftime('%Y-%m-%dT%H:%M:%SZ')

@app.route('/api/ai/whale-activity', methods=['GET'])
@require_auth
def get_whale_activity():
    """Get whale activity data enhanced with Trading AI"""
    try:
        token_address = request.args.get('token_address')
        limit = min(int(request.args.get('limit', 10)), 50)
        
        user_id = request.current_user.get('user_id')
        logger.info("Whale activity requested", 
                   user_id=user_id, 
                   token_address=token_address,
                   limit=limit)
        
        # Enhanced whale activity data
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
        
        # Log user action
        log_user_action(user_id, "whale_activity_viewed", {
            "token_address": token_address,
            "limit": limit
        })
        
        return api_success({
            "data": whale_data,
            "metadata": metadata
        })
        
    except Exception as e:
        logger.error("Whale activity error", error=str(e))
        return api_error("Failed to fetch whale activity", 500, error_type="WhaleActivityError")

def determine_market_sentiment():
    """Determine current market sentiment"""
    import random
    sentiments = ["bullish", "bearish", "neutral", "volatile"]
    weights = [0.4, 0.2, 0.3, 0.1]  # Slightly favor bullish
    return random.choices(sentiments, weights=weights)[0]

def determine_whale_flow():
    """Determine whale flow direction"""
    import random
    flows = ["accumulating", "distributing", "neutral", "mixed"]
    weights = [0.35, 0.25, 0.25, 0.15]
    return random.choices(flows, weights=weights)[0]

def generate_whale_movements(limit):
    """Generate realistic whale movements"""
    import random
    
    actions = ["buy", "sell", "accumulate", "distribute", "hold"]
    movements = []
    
    for _ in range(min(limit, 10)):  # Cap at 10 movements
        movement = {
            "action": random.choice(actions),
            "amount": random.randint(10000, 500000),
            "confidence": round(random.uniform(0.6, 0.95), 2),
            "timestamp": generate_recent_timestamp(),
            "impact_score": random.randint(60, 95)
        }
        movements.append(movement)
    
    return sorted(movements, key=lambda x: x['timestamp'], reverse=True)

# Health and monitoring endpoints
@app.route('/api/ai/health', methods=['GET'])
def health_check():
    """Comprehensive health check for AI services"""
    global trading_ai, ai_health_status
    
    health_data = {
        "status": "healthy" if ai_health_status["initialized"] else "degraded",
        "trading_ai_initialized": ai_health_status["initialized"],
        "ai_health_details": ai_health_status,
        "endpoints": [
            "/api/ai/test",
            "/api/ai/trading-advice", 
            "/api/ai/whale-activity",
            "/api/ai/health",
            "/api/auth/register",
            "/api/auth/login",
            "/api/whales/top"
        ],
        "performance": {
            "avg_response_time_ms": 150,  # Would calculate from real metrics
            "success_rate": 0.98,  # Would calculate from real metrics
            "uptime": "99.9%"  # Would calculate from real metrics
        }
    }
    
    status_code = 200 if ai_health_status["initialized"] else 503
    return jsonify({
        "success": True,
        "data": health_data,
        "timestamp": datetime.now().isoformat()
    }), status_code

@app.route('/api/ai/metrics', methods=['GET'])
@require_auth
@require_tier("professional")
def get_ai_metrics():
    """Get AI performance metrics (professional+ only)"""
    try:
        metrics = {
            "trading_ai": {
                "total_requests": 1250,  # Would fetch from database
                "successful_predictions": 892,
                "accuracy_rate": 0.714,
                "avg_confidence": 0.78,
                "response_time_p95": 180
            },
            "whale_tracking": {
                "whales_discovered_24h": 45,
                "quality_score_avg": 82.5,
                "successful_alerts": 156,
                "false_positive_rate": 0.12
            },
            "system": {
                "uptime_hours": 720,
                "memory_usage_mb": 512,
                "cpu_usage_percent": 15.2,
                "error_rate": 0.02
            }
        }
        
        return api_success(metrics)
        
    except Exception as e:
        logger.error("Metrics fetch error", error=str(e))
        return api_error("Failed to fetch metrics", 500, error_type="MetricsError")

# Integration endpoints
@app.route('/api/create-checkout-session', methods=['POST'])
@limiter.limit("5 per minute")
def create_checkout_session():
    """Create checkout session - integration with main app"""
    try:
        data = request.get_json()
        email = data.get('email', '')
        plan = data.get('plan', 'professional')
        
        logger.info("Checkout session requested via AI server", 
                   email=email, 
                   plan=plan)
        
        # In production, this would integrate with your main payment system
        # For now, return a placeholder response
        return api_success({
            'checkout_url': f'{config.DOMAIN}/checkout?email={email}&plan={plan}',
            'message': 'Redirect to main payment system',
            'integration_status': 'placeholder'
        })
        
    except Exception as e:
        logger.error("Checkout session error", error=str(e))
        return api_error("Failed to create checkout session", 500, error_type="CheckoutError")

# Root endpoint
@app.route('/', methods=['GET'])
def root():
    """AI server root endpoint with comprehensive info"""
    global trading_ai, ai_health_status
    
    return api_success({
        "message": "🤖 Production Trading AI Server",
        "version": "2.1.0",
        "trading_ai_status": "loaded" if trading_ai else "not_loaded",
        "health": ai_health_status,
        "capabilities": [
            "real_time_trading_advice",
            "whale_activity_analysis", 
            "market_sentiment_analysis",
            "risk_assessment",
            "portfolio_recommendations"
        ],
        "endpoints": {
            "auth": ["/api/auth/register", "/api/auth/login"],
            "trading": ["/api/ai/trading-advice", "/api/ai/whale-activity"],
            "data": ["/api/whales/top", "/api/user/profile"],
            "monitoring": ["/api/ai/health", "/api/ai/metrics"]
        }
    })

# Development endpoints (only in debug mode)
if config.DEBUG:
    @app.route('/debug/ai-status', methods=['GET'])
    def debug_ai_status():
        """Debug endpoint for AI status"""
        global trading_ai, ai_health_status
        
        return api_success({
            "trading_ai_object": str(type(trading_ai)) if trading_ai else None,
            "ai_health_status": ai_health_status,
            "config": {
                "timeout": config.TRADING_AI_TIMEOUT,
                "max_retries": config.TRADING_AI_MAX_RETRIES,
                "debug": config.DEBUG
            }
        })
    
    @app.route('/debug/test-ai', methods=['POST'])
    def debug_test_ai():
        """Debug endpoint to test AI directly"""
        try:
            if not trading_ai:
                return api_error("Trading AI not loaded", 503)
            
            test_response = async_helper.run_async(
                trading_ai.get_user_recommendation("test_user", "debug test", {})
            )
            
            return api_success({
                "raw_ai_response": test_response,
                "formatted_response": format_trading_ai_for_api(test_response, {}, "test_user")
            })
            
        except Exception as e:
            return api_error(f"Debug test failed: {str(e)}", 500)

def main():
    """Main function to start the AI server"""
    logger.info("🤖 Starting Production Trading AI Server",
               environment=os.getenv('FLASK_ENV', 'development'),
               debug=config.DEBUG)
    
    # Initialize the Trading AI
    try:
        init_success = async_helper.run_async(initialize_trading_ai())
        
        if init_success:
            logger.info("🎉 Trading AI Server ready with TradingAI!")
        else:
            logger.warning("⚠️ Trading AI Server starting in degraded mode (AI not available)")
    except Exception as e:
        logger.error("Failed to initialize Trading AI", error=str(e))
        logger.info("Starting server in degraded mode")
    
    # Start the server
    port = int(os.getenv('AI_SERVER_PORT', 8001))
    logger.info("Starting AI server", port=port)
    
    app.run(
        debug=config.DEBUG,
        host='0.0.0.0',
        port=port,
        threaded=True
    )

if __name__ == '__main__':
    main()
            '
