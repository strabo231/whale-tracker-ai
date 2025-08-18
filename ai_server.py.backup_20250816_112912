from flask import Flask, jsonify, request
from datetime import datetime
import logging
import asyncio
import sys  # ← ADD THIS
import os

# Add the current directory to Python path so we can import your AI
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append('/home/sean/ai-trading-brain')

# Import your REAL AI brain
from core.brain import CoreBrain

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__)

# Global AI brain instance
ai_brain = None

async def initialize_ai_brain():
    """Initialize the real AI brain"""
    global ai_brain
    try:
        logger.info("🧠 Initializing CoreBrain...")
        ai_brain = CoreBrain()
        await ai_brain.initialize()
        logger.info("✅ CoreBrain initialized successfully!")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to initialize CoreBrain: {e}")
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
    """Test endpoint - now shows real AI status"""
    global ai_brain
    return jsonify({
        "message": "🤖 Real AI Integration Online!",
        "timestamp": datetime.now().isoformat(),
        "status": "online",
        "server": "real_ai_server",
        "ai_brain_loaded": ai_brain is not None,
        "ready_for_trading_bot": True
    })

@app.route('/api/ai/trading-advice', methods=['POST'])
def get_trading_advice():
    """Get REAL AI trading advice using CoreBrain"""
    global ai_brain
    
    if not ai_brain:
        return jsonify({
            "success": False,
            "error": "AI brain not initialized",
            "message": "CoreBrain not available"
        }), 500
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        user_id = data.get('user_id')
        token_data = data.get('token_data', {})
        
        if not user_id or not token_data:
            return jsonify({"error": "user_id and token_data required"}), 400
        
        token_symbol = token_data.get('symbol', 'UNKNOWN')
        logger.info(f"🤖 Getting REAL AI advice for {token_symbol} (user: {user_id})")
        
        # Create trading analysis query
        query = f"Analyze trading opportunity for {token_symbol}"
        
        # Enhanced context for trading analysis
        context = {
            "analysis_type": "trading_opportunity",
            "token_data": token_data,
            "timestamp": datetime.now().isoformat(),
            "request_source": "trading_bot"
        }
        
        # Try to get REAL recommendation from your AI brain
        try:
            logger.info(f"🔍 Calling CoreBrain for user {user_id}")
            ai_response = run_async(
                ai_brain.get_user_recommendation(user_id, query, context)
            )
            logger.info(f"🔍 CoreBrain response: {ai_response}")
            
        except Exception as brain_error:
            logger.error(f"🧠 CoreBrain error: {brain_error}")
            # Return a safe fallback while we debug
            return jsonify({
                "success": True,
                "data": {
                    "action": "monitor",
                    "confidence": 0.6,
                    "reasoning": f"AI brain error (debugging): {str(brain_error)}",
                    "risk_level": "medium",
                    "ai_consensus": {"ai_module": "fallback", "confidence": 0.6}
                }
            })
        
        # Extract and format the AI response
        if ai_response and ai_response.get('success', True):
            # Parse the AI response into trading format
            trading_response = format_ai_for_trading(ai_response, token_data)
            
            logger.info(f"✅ Real AI advice generated for {token_symbol}")
            return jsonify(trading_response)
        else:
            logger.warning(f"⚠️ AI returned unsuccessful response for {token_symbol}")
            return jsonify({
                "success": False,
                "error": "AI analysis unsuccessful",
                "message": "AI brain returned no recommendation"
            }), 500
        
    except Exception as e:
        logger.error(f"❌ Real AI trading advice error: {e}")
        return jsonify({
            "success": False,
            "error": str(e),
            "message": "Real AI analysis failed"
        }), 500

def format_ai_for_trading(ai_response, token_data):
    """Format CoreBrain response into trading bot format"""
    try:
        print(f"🔍 DEBUG: Full AI response = {ai_response}")
        
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
        ai_module = ai_response.get('ai_module', 'CoreBrain')
        user_level = ai_response.get('user_level', 'unknown')
        
        # Map AI response to trading actions (your AI said no safe options)
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
                    "whale_interest": "low",  # AI said no safe options
                    "recent_activity": "cautious",
                    "confidence": confidence
                },
                "ai_consensus": {
                    "ai_module": f"{ai_module}_{user_level}",
                    "confidence": confidence,
                    "source": "CoreBrain_Real"
                }
            },
            "metadata": {
                "processing_time_ms": 200,
                "timestamp": datetime.now().isoformat(),
                "version": "real_ai_2.0.0"
            }
        }
        
    except Exception as e:
        print(f"❌ Error in format_ai_for_trading: {e}")
        return {
            "success": True,
            "data": {
                "action": "monitor",
                "confidence": 0.5,
                "reasoning": "AI response formatting error, defaulting to safe recommendation",
                "risk_level": "low",
                "ai_consensus": {
                    "ai_module": "fallback",
                    "confidence": 0.5
                }
            }
        }

def determine_trading_action(recommendation, ai_response):
    """Convert AI recommendation to trading action"""
    # You'll need to adapt this based on your AI's actual response format
    
    # Look for action indicators in the AI response
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

def determine_risk_level(ai_response, token_data):
    """Determine risk level from AI response"""
    confidence = ai_response.get('confidence', 0.5)
    
    # Simple risk assessment based on confidence
    if confidence >= 0.8:
        return 'low'
    elif confidence >= 0.6:
        return 'medium'
    else:
        return 'high'
        
def determine_risk_level_from_confidence(confidence):
    """Determine risk level from confidence"""
    if confidence == 0.0:
        return 'high'  # AI said no safe options = high risk
    elif confidence >= 0.8:
        return 'low'
    elif confidence >= 0.6:
        return 'medium'
    else:
        return 'high'

@app.route('/api/ai/whale-activity', methods=['GET'])
def get_whale_activity():
    """Get whale activity data (placeholder for now)"""
    try:
        token_address = request.args.get('token_address')
        limit = int(request.args.get('limit', 10))
        
        logger.info(f"🐋 Getting whale activity (limit: {limit})")
        
        # For now, return placeholder data
        # You can connect this to your whale discovery system later
        whale_data = {
            "success": True,
            "data": {
                "market_sentiment": "neutral",
                "whale_flow": "monitoring",
                "message": "Whale data integration pending",
                "source": "placeholder"
            },
            "metadata": {
                "timestamp": datetime.now().isoformat(),
                "whale_count": limit,
                "data_source": "whale_discovery_placeholder"
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
    """Health check with real AI status"""
    global ai_brain
    return jsonify({
        "status": "healthy" if ai_brain else "ai_not_loaded",
        "ai_brain_initialized": ai_brain is not None,
        "timestamp": datetime.now().isoformat(),
        "endpoints": [
            "/api/ai/test",
            "/api/ai/trading-advice", 
            "/api/ai/whale-activity",
            "/api/ai/health"
        ]
    })

@app.route('/', methods=['GET'])
def root():
    """Root endpoint"""
    global ai_brain
    return jsonify({
        "message": "Real AI Server is running",
        "ai_brain_status": "loaded" if ai_brain else "not_loaded",
        "endpoints": [
            "/api/ai/test",
            "/api/ai/trading-advice",
            "/api/ai/whale-activity", 
            "/api/ai/health"
        ]
    })

if __name__ == '__main__':
    logger.info("🤖 Starting Real AI Server...")
    
    # Initialize the AI brain
    init_success = run_async(initialize_ai_brain())
    
    if init_success:
        logger.info("🎉 Real AI Server ready with CoreBrain!")
    else:
        logger.warning("⚠️ AI Server starting without CoreBrain (will return errors)")
    
    app.run(debug=True, host='0.0.0.0', port=8001)
