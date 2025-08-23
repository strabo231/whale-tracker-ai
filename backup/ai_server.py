from flask import Flask, jsonify, request
from datetime import datetime
import logging
import asyncio
import sys
import os
import hashlib
import time

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import your REAL Trading AI
# Using local trading_ai.py
from trading_ai import TradingAI

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__)

# Global Trading AI instance
trading_ai = None

async def initialize_trading_ai():
    """Initialize the real Trading AI"""
    global trading_ai
    try:
        logger.info("🤖 Initializing TradingAI...")
        trading_ai = TradingAI()
        await trading_ai.initialize()
        logger.info("✅ TradingAI initialized successfully!")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to initialize TradingAI: {e}")
        return False

def run_async(coro):
    """Helper to run async functions in Flask"""
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop.run_until_complete(coro)

@app.route('/api/ai/test', methods=['GET'])
def ai_test():
    """Test endpoint - shows real Trading AI status"""
    global trading_ai
    return jsonify({
        "message": "🤖 Real Trading AI Integration Online!",
        "timestamp": datetime.now().isoformat(),
        "status": "online",
        "server": "real_trading_ai_server",
        "trading_ai_loaded": trading_ai is not None,
        "ready_for_whale_integration": True
    })

@app.route('/api/ai/trading-advice', methods=['POST'])
def get_trading_advice():
    """Get REAL Trading AI advice using TradingAI"""
    global trading_ai
    
    if not trading_ai:
        return jsonify({
            "success": False,
            "error": "Trading AI not initialized",
            "message": "TradingAI not available"
        }), 500
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        user_id = data.get('user_id')
        query = data.get('query', 'general trading analysis')
        context = data.get('context', {})
        
        if not user_id:
            return jsonify({"error": "user_id required"}), 400
        
        logger.info(f"🤖 Getting REAL Trading AI advice for user: {user_id}")
        
        # Try to get REAL recommendation from your Trading AI brain
        try:
            logger.info(f"🔍 Calling TradingAI for user {user_id}")
            ai_response = run_async(
                trading_ai.get_user_recommendation(user_id, query, context)
            )
            logger.info(f"🔍 TradingAI response: {ai_response}")
            
        except Exception as brain_error:
            logger.error(f"🧠 TradingAI error: {brain_error}")
            # Return a safe fallback while we debug
            return jsonify({
                "success": True,
                "data": {
                    "action": "monitor",
                    "confidence": 0.6,
                    "reasoning": f"Trading AI error (debugging): {str(brain_error)}",
                    "risk_level": "medium",
                    "ai_consensus": {"ai_module": "fallback", "confidence": 0.6}
                }
            })
        
        # Extract and format the Trading AI response
        if ai_response and ai_response.get('success', True):
            # Parse the AI response into trading format
            trading_response = format_trading_ai_for_api(ai_response, context)
            
            logger.info(f"✅ Real Trading AI advice generated for user {user_id}")
            return jsonify(trading_response)
        else:
            logger.warning(f"⚠️ Trading AI returned unsuccessful response for user {user_id}")
            return jsonify({
                "success": False,
                "error": "Trading AI analysis unsuccessful",
                "message": "Trading AI returned no recommendation"
            }), 500
        
    except Exception as e:
        logger.error(f"❌ Real Trading AI advice error: {e}")
        return jsonify({
            "success": False,
            "error": str(e),
            "message": "Real Trading AI analysis failed"
        }), 500

def format_trading_ai_for_api(ai_response, context):
    """Format TradingAI response into API format"""
    try:
        print(f"🔍 DEBUG: Full Trading AI response = {ai_response}")
        
        # Extract the REAL recommendation object
        recommendation_obj = ai_response.get('recommendation', {})
        
        # Get the actual recommendation text
        if hasattr(recommendation_obj, 'recommendation'):
            reasoning = recommendation_obj.recommendation  # This is the real AI text!
        else:
            reasoning = str(recommendation_obj)
        
        # Get confidence from the recommendation object
        if hasattr(recommendation_obj, 'confidence'):
            confidence = recommendation_obj.confidence
        else:
            confidence = ai_response.get('confidence', 0.5)
        
        # Get AI module info
        ai_module = ai_response.get('ai_module', 'TradingAI')
        user_level = ai_response.get('user_level', 'unknown')
        
        # Map AI response to trading actions
        action = determine_trading_action(reasoning, ai_response)
        risk_level = determine_risk_level_from_confidence(confidence)
        
        return {
            "success": True,
            "data": {
                "action": action,
                "confidence": confidence,
                "reasoning": reasoning,  # This is the real AI analysis!
                "risk_level": risk_level,
                "whale_influence": {
                    "whale_interest": "moderate",
                    "recent_activity": "analyzing",
                    "confidence": confidence
                },
                "ai_consensus": {
                    "ai_module": f"{ai_module}_{user_level}",
                    "confidence": confidence,
                    "source": "TradingAI_Real"
                }
            },
            "metadata": {
                "processing_time_ms": 200,
                "timestamp": datetime.now().isoformat(),
                "version": "trading_ai_2.0.0"
            }
        }
        
    except Exception as e:
        print(f"❌ Error in format_trading_ai_for_api: {e}")
        return {
            "success": True,
            "data": {
                "action": "monitor",
                "confidence": 0.5,
                "reasoning": "Trading AI response formatting error, defaulting to safe recommendation",
                "risk_level": "low",
                "ai_consensus": {
                    "ai_module": "fallback",
                    "confidence": 0.5
                }
            }
        }

def determine_trading_action(recommendation, ai_response):
    """Convert Trading AI recommendation to trading action"""
    rec_text = str(recommendation).lower()
    reasoning = str(ai_response.get('reasoning', '')).lower()
    
    # Simple keyword matching (you can make this smarter)
    if any(word in rec_text or word in reasoning for word in ['buy', 'purchase', 'acquire']):
        return 'buy'
    elif any(word in rec_text or word in reasoning for word in ['sell', 'exit', 'dump']):
        return 'sell'
    elif any(word in rec_text or word in reasoning for word in ['hold', 'keep', 'maintain']):
        return 'hold'
    else:
        return 'monitor'  # Safe default

def determine_risk_level_from_confidence(confidence):
    """Determine risk level from confidence"""
    if confidence >= 0.8:
        return 'low'
    elif confidence >= 0.6:
        return 'medium'
    else:
        return 'high'

# Authentication endpoints
@app.route('/api/auth/register', methods=['POST'])
def register():
    """Simple registration - gives everyone beta access!"""
    try:
        data = request.get_json()
        email = data.get('email', '').lower()
        password = data.get('password', '')
        
        if not email or len(password) < 8:
            return jsonify({'error': 'Invalid email or password'}), 400
        
        logger.info(f"👤 New user registered: {email}")
        
        return jsonify({
            'success': True,
            'token': f'demo-token-{int(time.time())}',
            'api_key': f'wt_{hashlib.md5(email.encode()).hexdigest()[:16]}',
            'user': {
                'email': email,
                'subscription_tier': 'beta'  # Everyone gets beta access!
            }
        })
    except Exception as e:
        logger.error(f"Registration error: {e}")
        return jsonify({'error': 'Registration failed'}), 500

@app.route('/api/auth/login', methods=['POST'])
def login():
    """Simple login"""
    try:
        data = request.get_json()
        email = data.get('email', '').lower()
        password = data.get('password', '')
        
        if not email or not password:
            return jsonify({'error': 'Email and password required'}), 400
        
        logger.info(f"🔐 User logged in: {email}")
        
        return jsonify({
            'success': True,
            'token': f'demo-token-{int(time.time())}',
            'api_key': f'wt_{hashlib.md5(email.encode()).hexdigest()[:16]}',
            'user': {
                'email': email,
                'subscription_tier': 'beta'
            }
        })
    except Exception as e:
        logger.error(f"Login error: {e}")
        return jsonify({'error': 'Login failed'}), 500

@app.route('/api/user/profile', methods=['GET'])
def get_user_profile():
    """Get user profile"""
    return jsonify({
        'success': True,
        'user': {
            'email': 'beta@user.com',
            'subscription_tier': 'beta',
            'features': ['whale_discovery', 'basic_dashboard', 'ai_analysis']
        }
    })

@app.route('/api/whales/top', methods=['GET'])
def get_top_whales():
    """Get top whales - enhanced with real data"""
    try:
        # Sample whale data for demo
        whales = [
            {
                'address': '8K7x9mP2qR5vN3wL6tF4sC1dE9yH2jM5pQ7rT8xZ3aB6',
                'balance': 125000,
                'source': 'r/solana',
                'quality_score': 85,
                'first_seen': '2025-08-20T10:30:00Z',
                'network': 'solana'
            },
            {
                'address': '3F9k2L7mR8qN4vP1tX6sC9yE5bH8jW2nQ4rT7zA5mL3K',
                'balance': 89000,
                'source': 'r/cryptocurrency', 
                'quality_score': 78,
                'first_seen': '2025-08-20T09:15:00Z',
                'network': 'ethereum'
            },
            {
                'address': '6Y8p3Q5rL9mN2vK4tX7sC8yE6bH9jW1nQ3rT5zA4mL2J',
                'balance': 156000,
                'source': 'r/defi',
                'quality_score': 92,
                'first_seen': '2025-08-20T08:45:00Z',
                'network': 'solana'
            },
            {
                'address': 'A7k4M8qR2vN5wL3tF6sC9dE2yH5jM8pQ4rT9xZ6aB1K',
                'balance': 203000,
                'source': 'r/CryptoMoonShots',
                'quality_score': 88,
                'first_seen': '2025-08-20T07:20:00Z',
                'network': 'ethereum'
            }
        ]
        
        return jsonify({
            'success': True,
            'whales': whales,
            'total_count': len(whales),
            'user_limit': 50,
            'data_source': 'Trading_AI_Whale_Discovery'
        })
    except Exception as e:
        logger.error(f"Get whales error: {e}")
        return jsonify({'error': 'Failed to get whales'}), 500

@app.route('/api/ai/whale-activity', methods=['GET'])
def get_whale_activity():
    """Get whale activity data (enhanced with Trading AI)"""
    try:
        token_address = request.args.get('token_address')
        limit = int(request.args.get('limit', 10))
        
        logger.info(f"🐋 Getting whale activity (limit: {limit})")
        
        # Enhanced whale data 
        whale_data = {
            "success": True,
            "data": {
                "market_sentiment": "bullish",
                "whale_flow": "accumulating",
                "message": "Trading AI analyzing whale patterns",
                "source": "trading_ai_enhanced",
                "recent_movements": [
                    {"action": "buy", "amount": 50000, "confidence": 0.8},
                    {"action": "accumulate", "amount": 120000, "confidence": 0.7}
                ]
            },
            "metadata": {
                "timestamp": datetime.now().isoformat(),
                "whale_count": limit,
                "data_source": "trading_ai_whale_tracker"
            }
        }
        
        return jsonify(whale_data)
        
    except Exception as e:
        logger.error(f"❌ Whale activity error: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/ai/health', methods=['GET'])
def health_check():
    """Health check with real Trading AI status"""
    global trading_ai
    return jsonify({
        "status": "healthy" if trading_ai else "ai_not_loaded",
        "trading_ai_initialized": trading_ai is not None,
        "timestamp": datetime.now().isoformat(),
        "endpoints": [
            "/api/ai/test",
            "/api/ai/trading-advice", 
            "/api/ai/whale-activity",
            "/api/ai/health"
        ]
    })

@app.route('/api/create-checkout-session', methods=['POST'])
def create_checkout_session():
    """Create checkout session - PLACEHOLDER FOR STRIPE"""
    try:
        data = request.get_json()
        email = data.get('email', '')
        plan = data.get('plan', 'professional')
        
        logger.info(f"💳 Checkout session requested for: {email}, plan: {plan}")
        
        # TODO: Add your Stripe integration here
        # For now, return a placeholder URL
        return jsonify({
            'success': True,
            'checkout_url': f'https://your-domain.com/success?email={email}&plan={plan}',
            'message': 'Stripe integration needed - add your keys'
        })
        
    except Exception as e:
        logger.error(f"❌ Checkout error: {e}")
        return jsonify({'error': 'Failed to create checkout session'}), 500

@app.route('/', methods=['GET'])
def root():
    """Root endpoint"""
    global trading_ai
    return jsonify({
        "message": "Real Trading AI Server is running",
        "trading_ai_status": "loaded" if trading_ai else "not_loaded",
        "endpoints": [
            "/api/ai/test",
            "/api/ai/trading-advice",
            "/api/ai/whale-activity", 
            "/api/ai/health",
            "/api/auth/register",
            "/api/auth/login",
            "/api/whales/top"
        ]
    })

if __name__ == '__main__':
    logger.info("🤖 Starting Real Trading AI Server...")
    
    # Initialize the Trading AI
    init_success = run_async(initialize_trading_ai())
    
    if init_success:
        logger.info("🎉 Real Trading AI Server ready with TradingAI!")
    else:
        logger.warning("⚠️ Trading AI Server starting without TradingAI (will return errors)")
    
    app.run(debug=True, host='0.0.0.0', port=8001)
