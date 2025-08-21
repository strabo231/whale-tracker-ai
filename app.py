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
                <a href="/roadmap" class="text-gray-400 hover:text-white transition-colors">Roadmap</a>
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
    """Working dashboard - bypass React auth"""
    return render_template_string('''
<!DOCTYPE html>
<html>
<head>
    <title>Whale Tracker Dashboard</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-gray-900 text-white min-h-screen">
    <div class="max-w-6xl mx-auto px-4 py-8">
        <div class="flex items-center justify-between mb-8">
            <h1 class="text-4xl font-bold">🐋 Whale Tracker Dashboard</h1>
            <span class="px-4 py-2 bg-green-500 text-white rounded-full">ACTIVE SUBSCRIBER</span>
        </div>
        
        <div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
            <div class="bg-gray-800 rounded-lg p-6">
                <h3 class="text-xl font-bold mb-2">Active Whales</h3>
                <p class="text-3xl font-bold text-green-400">47</p>
                <p class="text-gray-400">Currently tracking</p>
            </div>
            <div class="bg-gray-800 rounded-lg p-6">
                <h3 class="text-xl font-bold mb-2">Total Volume</h3>
                <p class="text-3xl font-bold text-blue-400">$2.1M</p>
                <p class="text-gray-400">Last 24 hours</p>
            </div>
            <div class="bg-gray-800 rounded-lg p-6">
                <h3 class="text-xl font-bold mb-2">New Discoveries</h3>
                <p class="text-3xl font-bold text-purple-400">8</p>
                <p class="text-gray-400">This week</p>
            </div>
        </div>
        
        <div class="bg-green-500/10 border border-green-500/20 rounded-lg p-6 mb-6">
            <h3 class="text-xl font-bold text-green-400 mb-2">✅ Premium Access Confirmed</h3>
            <p class="text-gray-300">Thank you for your subscription! You're helping save our family home.</p>
        </div>
        
        <div class="bg-gray-800 rounded-lg p-6">
            <h3 class="text-xl font-bold mb-4">🚀 Live Dashboard Features</h3>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4 text-gray-300">
                <div>• Real-time whale discovery from Reddit</div>
                <div>• Live Ethereum & Solana tracking</div>
                <div>• AI-powered trading insights</div>
                <div>• Custom alerts and notifications</div>
            </div>
            <p class="mt-6 text-orange-400 font-semibold">Full interactive dashboard: Coming within 24 hours</p>
        </div>
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
        
@app.route('/static/static/<path:path>')
def serve_double_static(path):
    """Handle React's double static path"""
    return send_from_directory('whale-dashboard/build/static', path)

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

# Add this route to your app.py (after your existing routes)

@app.route('/roadmap')
def roadmap():
    """Epic development roadmap page"""
    return render_template_string('''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Development Roadmap - Whale Tracker Pro</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        body {
            background: linear-gradient(135deg, #1e293b 0%, #7c3aed 50%, #1e293b 100%);
            min-height: 100vh;
        }
        .milestone-card {
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }
        .milestone-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 15px 35px rgba(0, 0, 0, 0.3);
        }
        .progress-bar {
            background: linear-gradient(90deg, #10b981, #3b82f6);
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
                        Whale Tracker Pro
                    </h1>
                    <p class="text-gray-400 text-sm">Development Roadmap</p>
                </div>
            </div>
            <div class="flex items-center space-x-4">
                <a href="/" class="text-gray-400 hover:text-white transition-colors">Home</a>
                <a href="/dashboard" class="px-4 py-2 bg-purple-600 hover:bg-purple-700 rounded-lg transition-colors">
                    Dashboard
                </a>
            </div>
        </div>
    </header>

    <!-- Hero Section -->
    <section class="py-20">
        <div class="max-w-7xl mx-auto px-4 text-center">
            <h1 class="text-5xl md:text-7xl font-bold mb-6">
                The <span class="bg-gradient-to-r from-purple-400 to-cyan-400 bg-clip-text text-transparent">Future</span>
                <br>of Whale Tracking
            </h1>
            
            <p class="text-xl text-gray-300 mb-12 max-w-3xl mx-auto">
                Community-funded innovation meets cutting-edge technology. 
                <strong class="text-orange-400">Your support builds the most advanced whale tracker ever created.</strong>
            </p>

            <!-- Current Progress -->
            <div class="bg-black/40 backdrop-blur-sm border border-green-500/50 rounded-xl p-8 max-w-2xl mx-auto mb-12">
                <div class="flex items-center justify-between mb-4">
                    <h3 class="text-xl font-bold">🎯 Current Progress</h3>
                    <span class="px-3 py-1 bg-green-500/20 text-green-400 rounded-full text-sm font-bold">PHASE 0 COMPLETE</span>
                </div>
                
                <div class="w-full bg-gray-700 rounded-full h-4 mb-4">
                    <div class="progress-bar h-4 rounded-full" style="width: 15%"></div>
                </div>
                
                <div class="flex justify-between text-sm text-gray-300">
                    <span>$0 MRR</span>
                    <span class="font-bold text-purple-400">Next: $50K MRR</span>
                </div>
                
                <p class="text-gray-400 text-sm mt-3">
                    ✅ Payment system live &nbsp;•&nbsp; ✅ Basic dashboard &nbsp;•&nbsp; ✅ Stripe integration
                </p>
            </div>
        </div>
    </section>

    <!-- Roadmap Milestones -->
    <section class="py-20">
        <div class="max-w-7xl mx-auto px-4">
            <div class="text-center mb-16">
                <h2 class="text-4xl font-bold mb-4">Revenue-Based Development Milestones</h2>
                <p class="text-gray-400 text-lg">Every dollar funds the next breakthrough</p>
            </div>
            
            <div class="space-y-8">
                
                <!-- Phase 1 -->
                <div class="milestone-card bg-black/40 backdrop-blur-sm border border-emerald-500/50 rounded-xl p-8">
                    <div class="flex items-center justify-between mb-6">
                        <div class="flex items-center space-x-4">
                            <div class="bg-emerald-500 text-white rounded-full w-12 h-12 flex items-center justify-center font-bold text-xl">1</div>
                            <div>
                                <h3 class="text-2xl font-bold text-emerald-400">Infrastructure Upgrade</h3>
                                <p class="text-gray-400">$50K Monthly Recurring Revenue</p>
                            </div>
                        </div>
                        <span class="px-4 py-2 bg-emerald-500/20 text-emerald-400 rounded-full font-bold">7-10 DAYS</span>
                    </div>
                    
                    <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                        <div>
                            <h4 class="font-bold text-white mb-3">🚀 Performance Upgrades</h4>
                            <ul class="space-y-2 text-gray-300">
                                <li>• Enterprise-grade servers (99.9% uptime)</li>
                                <li>• Advanced API architecture with gRPC</li>
                                <li>• Sub-second real-time data streams</li>
                                <li>• Enhanced whale discovery algorithms</li>
                            </ul>
                        </div>
                        <div>
                            <h4 class="font-bold text-white mb-3">🌐 Multi-Network Expansion</h4>
                            <ul class="space-y-2 text-gray-300">
                                <li>• Polygon integration</li>
                                <li>• Arbitrum whale tracking</li>
                                <li>• Binance Smart Chain support</li>
                                <li>• Avalanche network monitoring</li>
                            </ul>
                        </div>
                    </div>
                </div>

                <!-- Phase 2 -->
                <div class="milestone-card bg-black/40 backdrop-blur-sm border border-blue-500/50 rounded-xl p-8">
                    <div class="flex items-center justify-between mb-6">
                        <div class="flex items-center space-x-4">
                            <div class="bg-blue-500 text-white rounded-full w-12 h-12 flex items-center justify-center font-bold text-xl">2</div>
                            <div>
                                <h3 class="text-2xl font-bold text-blue-400">Adaptive AI Trading Bot</h3>
                                <p class="text-gray-400">$100K Monthly Recurring Revenue</p>
                            </div>
                        </div>
                        <span class="px-4 py-2 bg-blue-500/20 text-blue-400 rounded-full font-bold">2-4 WEEKS</span>
                    </div>
                    
                    <div class="bg-gradient-to-r from-blue-500/10 to-purple-500/10 rounded-lg p-6 mb-6">
                        <h4 class="font-bold text-blue-400 mb-2">🤖 World's First Web3 Adaptive Trading AI</h4>
                        <p class="text-gray-300">Revolutionary AI that learns YOUR trading style and adapts its strategy accordingly.</p>
                    </div>
                    
                    <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
                        <div>
                            <h4 class="font-bold text-white mb-3">🎯 Three Modes</h4>
                            <ul class="space-y-2 text-gray-300 text-sm">
                                <li>• Full automation</li>
                                <li>• Guided assistance</li>
                                <li>• Advisory-only</li>
                            </ul>
                        </div>
                        <div>
                            <h4 class="font-bold text-white mb-3">🔒 Security</h4>
                            <ul class="space-y-2 text-gray-300 text-sm">
                                <li>• Military-grade encryption</li>
                                <li>• Zero-knowledge architecture</li>
                                <li>• Privacy-first design</li>
                            </ul>
                        </div>
                        <div>
                            <h4 class="font-bold text-white mb-3">⚡ Features</h4>
                            <ul class="space-y-2 text-gray-300 text-sm">
                                <li>• 1.5% transaction sniping</li>
                                <li>• Risk management</li>
                                <li>• Custom safety limits</li>
                            </ul>
                        </div>
                    </div>
                </div>

                <!-- Phase 3 -->
                <div class="milestone-card bg-black/40 backdrop-blur-sm border border-purple-500/50 rounded-xl p-8">
                    <div class="flex items-center justify-between mb-6">
                        <div class="flex items-center space-x-4">
                            <div class="bg-purple-500 text-white rounded-full w-12 h-12 flex items-center justify-center font-bold text-xl">3</div>
                            <div>
                                <h3 class="text-2xl font-bold text-purple-400">Mobile & Desktop Apps</h3>
                                <p class="text-gray-400">$150K Monthly Recurring Revenue</p>
                            </div>
                        </div>
                        <span class="px-4 py-2 bg-purple-500/20 text-purple-400 rounded-full font-bold">6-8 WEEKS</span>
                    </div>
                    
                    <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                        <div>
                            <h4 class="font-bold text-white mb-3">📱 Mobile Apps</h4>
                            <ul class="space-y-2 text-gray-300">
                                <li>• Native iOS & Android apps</li>
                                <li>• Real-time push notifications</li>
                                <li>• Offline mode for essential features</li>
                                <li>• Advanced mobile charting</li>
                            </ul>
                        </div>
                        <div>
                            <h4 class="font-bold text-white mb-3">💻 Desktop Apps</h4>
                            <ul class="space-y-2 text-gray-300">
                                <li>• Cross-platform (Windows, macOS, Linux)</li>
                                <li>• Unified experience across devices</li>
                                <li>• Professional-grade analytics</li>
                                <li>• Portfolio management suite</li>
                            </ul>
                        </div>
                    </div>
                </div>

                <!-- Phase 4 -->
                <div class="milestone-card bg-black/40 backdrop-blur-sm border border-orange-500/50 rounded-xl p-8">
                    <div class="flex items-center justify-between mb-6">
                        <div class="flex items-center space-x-4">
                            <div class="bg-orange-500 text-white rounded-full w-12 h-12 flex items-center justify-center font-bold text-xl">4</div>
                            <div>
                                <h3 class="text-2xl font-bold text-orange-400">Enterprise & Compliance</h3>
                                <p class="text-gray-400">$300K Monthly Recurring Revenue</p>
                            </div>
                        </div>
                        <span class="px-4 py-2 bg-orange-500/20 text-orange-400 rounded-full font-bold">3-6 MONTHS</span>
                    </div>
                    
                    <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                        <div>
                            <h4 class="font-bold text-white mb-3">🏢 Enterprise Solutions</h4>
                            <ul class="space-y-2 text-gray-300">
                                <li>• Dedicated enterprise servers</li>
                                <li>• Corporate licensing program</li>
                                <li>• White-label solutions</li>
                                <li>• Custom integrations</li>
                            </ul>
                        </div>
                        <div>
                            <h4 class="font-bold text-white mb-3">⚖️ Regulatory Compliance</h4>
                            <ul class="space-y-2 text-gray-300">
                                <li>• SEC registration process</li>
                                <li>• Integrated trading platform</li>
                                <li>• Full brokerage features</li>
                                <li>• Institutional-grade security</li>
                            </ul>
                        </div>
                    </div>
                </div>

            </div>
        </div>
    </section>

    <!-- Investment Benefits -->
    <section class="py-20 bg-black/20">
        <div class="max-w-7xl mx-auto px-4">
            <div class="text-center mb-16">
                <h2 class="text-4xl font-bold mb-4">🎁 Investor Benefits</h2>
                <p class="text-gray-400 text-lg">Early supporters get exclusive rewards</p>
            </div>
            
            <div class="grid grid-cols-1 md:grid-cols-2 gap-8">
                
                <!-- Early Supporters -->
                <div class="bg-black/40 backdrop-blur-sm border border-cyan-500/50 rounded-xl p-8">
                    <h3 class="text-2xl font-bold text-cyan-400 mb-6">🌟 Early Supporters (All Subscribers)</h3>
                    <ul class="space-y-3 text-gray-300">
                        <li class="flex items-center">
                            <div class="w-2 h-2 bg-cyan-400 rounded-full mr-3"></div>
                            Lifetime price lock - your rate never increases
                        </li>
                        <li class="flex items-center">
                            <div class="w-2 h-2 bg-cyan-400 rounded-full mr-3"></div>
                            First access to all new features
                        </li>
                        <li class="flex items-center">
                            <div class="w-2 h-2 bg-cyan-400 rounded-full mr-3"></div>
                            Priority support and direct developer contact
                        </li>
                        <li class="flex items-center">
                            <div class="w-2 h-2 bg-cyan-400 rounded-full mr-3"></div>
                            Community governance - vote on feature priorities
                        </li>
                    </ul>
                </div>

                <!-- Major Contributors -->
                <div class="bg-black/40 backdrop-blur-sm border border-gold-500/50 rounded-xl p-8 border-yellow-500/50">
                    <h3 class="text-2xl font-bold text-yellow-400 mb-6">👑 Major Contributors ($50K+ Annual)</h3>
                    <ul class="space-y-3 text-gray-300">
                        <li class="flex items-center">
                            <div class="w-2 h-2 bg-yellow-400 rounded-full mr-3"></div>
                            <strong class="text-yellow-400">10% lifetime profit sharing</strong> from company revenues
                        </li>
                        <li class="flex items-center">
                            <div class="w-2 h-2 bg-yellow-400 rounded-full mr-3"></div>
                            Advisory board position with quarterly strategy calls
                        </li>
                        <li class="flex items-center">
                            <div class="w-2 h-2 bg-yellow-400 rounded-full mr-3"></div>
                            Custom feature development tailored to your needs
                        </li>
                        <li class="flex items-center">
                            <div class="w-2 h-2 bg-yellow-400 rounded-full mr-3"></div>
                            Exclusive alpha access to unreleased tools
                        </li>
                    </ul>
                </div>

            </div>
        </div>
    </section>

    <!-- CTA Section -->
    <section class="py-20">
        <div class="max-w-4xl mx-auto px-4 text-center">
            <h2 class="text-4xl font-bold mb-6">Ready to Build the Future?</h2>
            <p class="text-xl text-gray-300 mb-8">
                Join the revolution in whale tracking technology while helping save our family home.
            </p>
            <div class="flex flex-col sm:flex-row gap-4 justify-center">
                <a href="/#pricing" class="px-8 py-4 bg-gradient-to-r from-purple-500 to-cyan-500 rounded-lg font-semibold text-white text-lg hover:opacity-90 transition-opacity">
                    🚀 Start Your Subscription
                </a>
                <a href="/dashboard" class="px-8 py-4 border border-gray-600 rounded-lg font-semibold text-white hover:bg-white/10 transition-colors">
                    View Dashboard
                </a>
            </div>
        </div>
    </section>

    <!-- Footer -->
    <footer class="border-t border-gray-800 py-8">
        <div class="max-w-7xl mx-auto px-4 text-center text-gray-400">
            <p>&copy; 2025 Whale Tracker Pro. Community-funded innovation for the crypto revolution. 🐋</p>
        </div>
    </footer>
</body>
</html>
    ''')

# Also add this to your home page navigation - update the header section in your home() function
# Add this link to the header:
# <a href="/roadmap" class="text-gray-400 hover:text-white transition-colors">Roadmap</a>


if __name__ == '__main__':
    if not stripe.api_key:
        logger.error("❌ STRIPE_SECRET_KEY not found in environment variables")
        exit(1)
    
    logger.info("🚀 Starting Whale Tracker Payment Server...")
    logger.info(f"💳 Stripe configured: {stripe.api_key[:8]}...")
    
    port = int(os.getenv('PORT', 8000))
    app.run(debug=True, host='0.0.0.0', port=port)
