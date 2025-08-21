from flask import Flask, jsonify, request, render_template_string, redirect, send_from_directory
import stripe
import os
import logging
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Stripe configuration
stripe.api_key = os.getenv('STRIPE_SECRET_KEY')
STRIPE_PUBLISHABLE_KEY = os.getenv('STRIPE_PUBLISHABLE_KEY')
DOMAIN = os.getenv('DOMAIN', 'https://whale-tracker-ai.up.railway.app')

# Price IDs - YOUR ACTUAL STRIPE PRICE IDS
PRICE_IDS = {
    'professional': 'price_1RyKygRkVYDUbhIFgs8JUTTR',  # Professional $49/month
    'emergency': 'price_1RyapeRkVYDUbhIFwSQYNIAw',     # Help Save Home $199/month  
    'enterprise': 'price_1Ryar9RkVYDUbhIFr4Oe7N9C',    # Enterprise $899/month
    'lifetime': 'price_1Ryat4RkVYDUbhIFxohXgOK1',      # Lifetime $2,999 one-time
    'sixmonth': 'price_1RyJOzDfwP4gynpjh4mO6b6B'       # Use Help Save Home for now
}

@app.route('/')
def home():
    """Main subscription page with real Stripe integration"""
    return render_template_string('''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Whale Tracker Pro - Get Access</title>
    <script src="https://js.stripe.com/v3/"></script>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        body {
            background: linear-gradient(135deg, #1e293b 0%, #7c3aed 50%, #1e293b 100%);
            min-height: 100vh;
        }
        .tier-card {
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }
        .tier-card:hover {
            transform: translateY(-8px);
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.3);
        }
        .emergency-badge {
            background: linear-gradient(90deg, #ef4444, #dc2626);
            animation: pulse 2s infinite;
        }
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.8; }
        }
    </style>
</head>
<body class="text-white">
    <!-- Emergency Banner -->
    <div class="bg-red-600 text-white text-center py-2 text-sm font-bold">
        🚨 URGENT: House scheduled for auction Sept 2nd - Every subscription helps save our home 🏠
    </div>

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
                        Whale Tracker Pro
                    </h1>
                    <p class="text-gray-400 text-sm">Professional Whale Intelligence</p>
                </div>
            </div>
            <div class="flex items-center space-x-4">
                <a href="/dashboard" class="px-4 py-2 bg-purple-600 hover:bg-purple-700 rounded-lg transition-colors">
                    Access Dashboard
                </a>
            </div>
        </div>
    </header>

    <!-- Hero Section -->
    <section class="py-20">
        <div class="max-w-7xl mx-auto px-4 text-center">
            <div class="inline-flex items-center px-4 py-2 emergency-badge rounded-full text-white text-sm font-bold mb-8">
                ⏰ 8 DAYS LEFT - HELP SAVE OUR HOME
            </div>
            
            <h1 class="text-5xl md:text-7xl font-bold mb-6">
                Get <span class="bg-gradient-to-r from-purple-400 to-cyan-400 bg-clip-text text-transparent">Access Now</span>
            </h1>
            
            <p class="text-xl text-gray-300 mb-12 max-w-3xl mx-auto">
                Track Ethereum & Solana whales through Reddit discovery + on-chain analysis. 
                <strong class="text-orange-400">Built by a developer fighting foreclosure to keep his special needs son's home.</strong>
            </p>
        </div>
    </section>

    <!-- Pricing Section -->
    <section class="py-20">
        <div class="max-w-7xl mx-auto px-4">
            <div class="text-center mb-16">
                <h2 class="text-4xl font-bold mb-4">Choose Your Plan</h2>
                <p class="text-gray-400 text-lg">Professional whale intelligence + help save our home</p>
            </div>
            
            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8 max-w-6xl mx-auto">
                
                <!-- Professional Tier -->
                <div class="tier-card bg-black/40 backdrop-blur-sm border border-cyan-500/50 rounded-xl p-8">
                    <div class="text-center mb-8">
                        <h3 class="text-2xl font-bold mb-2">Professional</h3>
                        <p class="text-gray-400 mb-4">Standard whale tracking</p>
                        <div class="text-4xl font-bold mb-2">$49<span class="text-gray-400 text-lg">/month</span></div>
                    </div>
                    
                    <ul class="space-y-3 mb-8">
                        <li class="flex items-center text-green-400">
                            <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/>
                            </svg>
                            ETH + SOL whale discovery
                        </li>
                        <li class="flex items-center text-green-400">
                            <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/>
                            </svg>
                            Reddit community scanning
                        </li>
                        <li class="flex items-center text-green-400">
                            <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/>
                            </svg>
                            Up to 100 tracked whales
                        </li>
                        <li class="flex items-center text-green-400">
                            <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/>
                            </svg>
                            Basic alerts & dashboard
                        </li>
                    </ul>
                    
                    <button onclick="subscribe('professional')" class="block w-full py-3 bg-gradient-to-r from-cyan-500 to-blue-500 rounded-lg font-semibold text-white text-center hover:opacity-90 transition-opacity">
                        Subscribe - $49/month
                    </button>
                </div>

                <!-- Help Us Stay Tier -->
                <div class="tier-card bg-black/40 backdrop-blur-sm border border-orange-500/50 rounded-xl p-8 relative">
                    <div class="absolute -top-3 left-1/2 transform -translate-x-1/2">
                        <span class="emergency-badge px-4 py-1 text-white text-sm font-bold rounded-full">
                            🏠 HELP SAVE HOME
                        </span>
                    </div>
                    
                    <div class="text-center mb-8 mt-4">
                        <h3 class="text-2xl font-bold mb-2">Help Us Stay</h3>
                        <p class="text-gray-400 mb-4">Support our family + get premium access</p>
                        <div class="text-4xl font-bold mb-2">$199<span class="text-gray-400 text-lg">/month</span></div>
                        <p class="text-orange-400 text-sm font-medium">Every $ helps save our home</p>
                    </div>
                    
                    <ul class="space-y-3 mb-8">
                        <li class="flex items-center text-green-400">
                            <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/>
                            </svg>
                            Everything in Professional
                        </li>
                        <li class="flex items-center text-green-400">
                            <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/>
                            </svg>
                            Unlimited whale tracking
                        </li>
                        <li class="flex items-center text-orange-400">
                            <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z"/>
                            </svg>
                            Help save a special needs child's home
                        </li>
                    </ul>
                    
                    <button onclick="subscribe('emergency')" class="block w-full py-3 bg-gradient-to-r from-orange-500 to-red-500 rounded-lg font-semibold text-white text-center hover:opacity-90 transition-opacity">
                        🏠 Help Save Our Home - $199/month
                    </button>
                </div>

                <!-- Enterprise Tier -->
                <div class="tier-card bg-black/40 backdrop-blur-sm border border-purple-500/50 rounded-xl p-8">
                    <div class="text-center mb-8">
                        <h3 class="text-2xl font-bold mb-2">Enterprise</h3>
                        <p class="text-gray-400 mb-4">Full API + custom solutions</p>
                        <div class="text-4xl font-bold mb-2">$899<span class="text-gray-400 text-lg">/month</span></div>
                    </div>
                    
                    <ul class="space-y-3 mb-8">
                        <li class="flex items-center text-green-400">
                            <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/>
                            </svg>
                            Everything in Help Us Stay
                        </li>
                        <li class="flex items-center text-green-400">
                            <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/>
                            </svg>
                            Full API access
                        </li>
                        <li class="flex items-center text-green-400">
                            <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/>
                            </svg>
                            White-label options
                        </li>
                    </ul>
                    
                    <button onclick="subscribe('enterprise')" class="block w-full py-3 bg-gradient-to-r from-purple-500 to-indigo-500 rounded-lg font-semibold text-white text-center hover:opacity-90 transition-opacity">
                        Contact Sales - $899/month
                    </button>
                </div>

            </div>

            <!-- Special Options -->
            <div class="mt-12 text-center">
                <div class="bg-gradient-to-r from-green-500/10 to-blue-500/10 border border-green-500/20 rounded-xl p-6 max-w-4xl mx-auto">
                    <h3 class="text-2xl font-bold text-white mb-4">🚨 EMERGENCY OPTIONS</h3>
                    <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div class="bg-black/40 rounded-lg p-4">
                            <h4 class="font-bold text-green-400 mb-2">House Saver LIFETIME</h4>
                            <p class="text-2xl font-bold text-white">$2,999 <span class="text-sm text-gray-400">one-time</span></p>
                            <p class="text-gray-400 text-sm mb-3">Everything forever + help save our home</p>
                            <button onclick="subscribe('lifetime')" class="w-full py-2 bg-green-600 hover:bg-green-700 rounded font-semibold text-center transition-colors">
                                🏠 Save Our House + Get Lifetime Access
                            </button>
                        </div>
                        <div class="bg-black/40 rounded-lg p-4">
                            <h4 class="font-bold text-blue-400 mb-2">6-Month Lifeline</h4>
                            <p class="text-2xl font-bold text-white">$999 <span class="text-sm text-gray-400">upfront</span></p>
                            <p class="text-gray-400 text-sm mb-3">Save $395 vs monthly + help family</p>
                            <button onclick="subscribe('sixmonth')" class="w-full py-2 bg-blue-600 hover:bg-blue-700 rounded font-semibold text-center transition-colors">
                                💪 6 Months Upfront (Save $395)
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </section>

    <!-- Footer -->
    <footer class="border-t border-gray-800 py-8">
        <div class="max-w-7xl mx-auto px-4 text-center text-gray-400">
            <p>&copy; 2025 Whale Tracker Pro. Built with love by Sean for his family. Every subscription helps. 🙏</p>
        </div>
    </footer>

    <script>
        const stripe = Stripe('{{ stripe_publishable_key }}');
        
        async function subscribe(planType) {
            try {
                console.log('Subscribing to:', planType);
                
                const response = await fetch('/create-checkout-session', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        plan: planType
                    }),
                });
                
                const session = await response.json();
                
                if (session.error) {
                    alert('Error: ' + session.error);
                    return;
                }
                
                // Redirect to Stripe Checkout
                const result = await stripe.redirectToCheckout({
                    sessionId: session.id
                });
                
                if (result.error) {
                    alert('Payment error: ' + result.error.message);
                }
                
            } catch (error) {
                console.error('Error:', error);
                alert('Payment system error. Please try again.');
            }
        }
    </script>
</body>
</html>
    ''', stripe_publishable_key=STRIPE_PUBLISHABLE_KEY)

@app.route('/create-checkout-session', methods=['POST'])
def create_checkout_session():
    """Create Stripe checkout session"""
    try:
        data = request.get_json()
        plan = data.get('plan', 'professional')
        
        # Get the price ID for the selected plan
        price_id = PRICE_IDS.get(plan)
        
        if not price_id or price_id.startswith('price_UPDATE'):
            return jsonify({
                'error': 'Price ID not configured for plan: ' + plan
            }), 400
        
        # Create Stripe checkout session
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price': price_id,
                'quantity': 1,
            }],
            mode='subscription' if plan != 'lifetime' else 'payment',
            success_url='https://whale-tracker-ai.up.railway.app/success?   session_id={CHECKOUT_SESSION_ID}',
            cancel_url='https://whale-tracker-ai.up.railway.app/?canceled=true',
            metadata={
                'plan': plan,
                'user_source': 'whale_tracker_domain'
            }
        )
        
        logger.info(f"💳 Created checkout session for plan: {plan}")
        
        return jsonify({
            'id': checkout_session.id
        })
        
    except stripe.error.StripeError as e:
        logger.error(f"❌ Stripe error: {e}")
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"❌ Checkout error: {e}")
        return jsonify({'error': 'Failed to create checkout session'}), 500

@app.route('/success')
def success():
    """Success page after payment"""
    session_id = request.args.get('session_id')
    
    return render_template_string('''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Payment Successful - Whale Tracker Pro</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 min-h-screen text-white">
    <div class="max-w-2xl mx-auto px-4 py-16 text-center">
        <div class="bg-black/40 backdrop-blur-sm border border-green-500/50 rounded-xl p-8">
            <div class="text-6xl mb-6">🎉</div>
            <h1 class="text-4xl font-bold text-green-400 mb-4">Payment Successful!</h1>
            <p class="text-xl text-gray-300 mb-6">
                Thank you for subscribing to Whale Tracker Pro!
            </p>
            <p class="text-gray-300 mb-8">
                🏠 Your subscription directly helps save our family's home. 
                You'll receive access credentials within 24 hours.
            </p>
            
            <div class="space-y-4">
                <a href="/dashboard" class="block px-8 py-3 bg-gradient-to-r from-purple-500 to-cyan-500 rounded-lg font-semibold text-white hover:opacity-90 transition-opacity">
                    Access Dashboard
                </a>
                <a href="/" class="block px-8 py-3 border border-gray-600 rounded-lg font-semibold text-white hover:bg-white/10 transition-colors">
                    Back to Home
                </a>
            </div>
            
            <p class="text-sm text-gray-400 mt-6">
                Session ID: {{ session_id }}
            </p>
        </div>
    </div>
</body>
</html>
    ''', session_id=session_id)

# FIXED DASHBOARD ROUTES
@app.route('/dashboard')
def dashboard():
    """Serve React dashboard"""
    try:
        return send_from_directory('whale-dashboard/build', 'index.html')
    except FileNotFoundError:
        # Fallback if React build doesn't exist
        return render_template_string('''
<!DOCTYPE html>
<html>
<head>
    <title>Dashboard - Whale Tracker Pro</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-gray-900 text-white min-h-screen flex items-center justify-center">
    <div class="text-center">
        <h1 class="text-4xl font-bold mb-4">🎉 Welcome to Whale Tracker Pro!</h1>
        <p class="text-xl mb-6">Your dashboard is being prepared...</p>
        <p class="text-gray-400 mb-8">Full access will be granted within 24 hours.</p>
        
        <div class="bg-black/40 rounded-xl p-6 max-w-md mx-auto mb-8">
            <h3 class="text-lg font-bold mb-4">🐋 What You'll Get:</h3>
            <ul class="text-left space-y-2 text-gray-300">
                <li>• Real-time whale discovery</li>
                <li>• Reddit community scanning</li>
                <li>• Ethereum + Solana tracking</li>
                <li>• AI-powered insights</li>
                <li>• Live market alerts</li>
            </ul>
        </div>
        
        <a href="/" class="inline-block px-6 py-3 bg-purple-600 rounded-lg hover:bg-purple-700 transition-colors">
            Back to Home
        </a>
        
        <p class="text-sm text-gray-500 mt-6">
            Questions? Contact: sean@whale-tracker.pro
        </p>
    </div>
</body>
</html>
        ''')

@app.route('/static/<path:path>')
def serve_react_static(path):
    """Serve React static files (CSS, JS, etc.)"""
    try:
        if path.startswith('static/'):
            # Remove the extra 'static/' prefix
            path = path[7:]  # Remove 'static/' from beginning
        return send_from_directory('whale-dashboard/build/static', path)
    except FileNotFoundError:
        return jsonify({'error': 'Static file not found'}), 404

@app.route('/dashboard/<path:path>')
def dashboard_catch_all(path):
    """Catch-all route for React Router (SPA routing)"""
    try:
        return send_from_directory('whale-dashboard/build', 'index.html')
    except FileNotFoundError:
        return redirect('/dashboard')

@app.route('/webhook', methods=['POST'])
def stripe_webhook():
    """Handle Stripe webhooks"""
    payload = request.get_data(as_text=True)
    sig_header = request.headers.get('Stripe-Signature')
    
    try:
        # Verify webhook signature
        event = stripe.Webhook.construct_event(
            payload, sig_header, os.getenv('STRIPE_WEBHOOK_SECRET')
        )
        
        # Handle the event
        if event['type'] == 'checkout.session.completed':
            session = event['data']['object']
            logger.info(f"✅ Payment completed for session: {session['id']}")
            
            # TODO: Grant user access to dashboard
            # TODO: Send welcome email
            # TODO: Update user database
            
        elif event['type'] == 'invoice.payment_succeeded':
            invoice = event['data']['object']
            logger.info(f"✅ Invoice payment succeeded: {invoice['id']}")
            
        elif event['type'] == 'customer.subscription.deleted':
            subscription = event['data']['object']
            logger.info(f"❌ Subscription canceled: {subscription['id']}")
            
            # TODO: Revoke user access
            
        return jsonify({'status': 'success'})
        
    except ValueError as e:
        logger.error(f"❌ Invalid payload: {e}")
        return jsonify({'error': 'Invalid payload'}), 400
    except stripe.error.SignatureVerificationError as e:
        logger.error(f"❌ Invalid signature: {e}")
        return jsonify({'error': 'Invalid signature'}), 400

if __name__ == '__main__':
    if not stripe.api_key:
        logger.error("❌ STRIPE_SECRET_KEY not found in environment variables")
        exit(1)
    
    logger.info("🚀 Starting Whale Tracker Payment Server...")
    logger.info(f"💳 Stripe configured: {stripe.api_key[:8]}...")
    
    port = int(os.getenv('PORT', 8000))
    app.run(debug=True, host='0.0.0.0', port=port)
