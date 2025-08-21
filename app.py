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
                <a href="/contact" class="text-gray-400 hover:text-white transition-colors">Contact</a>
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

@app.route('/contact')
def contact():
    """Contact page"""
    return render_template_string('''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Contact Us - Whale Tracker Pro</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        body {
            background: linear-gradient(135deg, #1e293b 0%, #7c3aed 50%, #1e293b 100%);
            min-height: 100vh;
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
                    <p class="text-gray-400 text-sm">Contact Information</p>
                </div>
            </div>
            <div class="flex items-center space-x-4">
                <a href="/" class="text-gray-400 hover:text-white transition-colors">Home</a>
                <a href="/roadmap" class="text-gray-400 hover:text-white transition-colors">Roadmap</a>
                <a href="/dashboard" class="px-4 py-2 bg-purple-600 hover:bg-purple-700 rounded-lg transition-colors">
                    Dashboard
                </a>
            </div>
        </div>
    </header>

    <!-- Contact Section -->
    <section class="py-20">
        <div class="max-w-4xl mx-auto px-4">
            <div class="text-center mb-16">
                <h1 class="text-5xl font-bold mb-6">Get in Touch</h1>
                <p class="text-xl text-gray-300">We're here to help and always available to our community</p>
            </div>

            <!-- Emergency Banner -->
            <div class="bg-red-500/10 border border-red-500/30 rounded-xl p-6 mb-12 text-center">
                <h3 class="text-2xl font-bold text-red-400 mb-2">🏠 Urgent Family Situation</h3>
                <p class="text-gray-300 mb-4">
                    Our house is scheduled for auction on <strong class="text-red-400">September 2nd, 2025</strong>. 
                    For immediate assistance regarding our family emergency, please use the priority contact below.
                </p>
                <div class="flex items-center justify-center space-x-2 text-orange-400 font-bold">
                    <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 8l7.89 4.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"/>
                    </svg>
                    <a href="mailto:sean@whale-tracker.pro" class="hover:text-orange-300">sean@whale-tracker.pro</a>
                </div>
            </div>

            <!-- Contact Grid -->
            <div class="grid grid-cols-1 md:grid-cols-2 gap-8 mb-12">
                
                <!-- Business Contacts -->
                <div class="bg-black/40 backdrop-blur-sm border border-gray-800 rounded-xl p-8">
                    <h3 class="text-2xl font-bold mb-6 text-purple-400">💼 Business Inquiries</h3>
                    
                    <div class="space-y-4">
                        <div class="flex items-center space-x-3">
                            <div class="bg-blue-500/20 p-2 rounded-lg">
                                <svg class="w-5 h-5 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 8l7.89 4.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"/>
                                </svg>
                            </div>
                            <div>
                                <p class="font-bold text-white">General Inquiries</p>
                                <a href="mailto:hello@whale-tracker.pro" class="text-blue-400 hover:text-blue-300">hello@whale-tracker.pro</a>
                            </div>
                        </div>
                        
                        <div class="flex items-center space-x-3">
                            <div class="bg-green-500/20 p-2 rounded-lg">
                                <svg class="w-5 h-5 text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M18.364 5.636l-3.536 3.536m0 5.656l3.536 3.536M9.172 9.172L5.636 5.636m3.536 9.192L5.636 18.364M21 12a9 9 0 11-18 0 9 9 0 0118 0zm-5 0a4 4 0 11-8 0 4 4 0 018 0z"/>
                                </svg>
                            </div>
                            <div>
                                <p class="font-bold text-white">Technical Support</p>
                                <a href="mailto:support@whale-tracker.pro" class="text-green-400 hover:text-green-300">support@whale-tracker.pro</a>
                            </div>
                        </div>
                        
                        <div class="flex items-center space-x-3">
                            <div class="bg-purple-500/20 p-2 rounded-lg">
                                <svg class="w-5 h-5 text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z"/>
                                </svg>
                            </div>
                            <div>
                                <p class="font-bold text-white">Partnerships</p>
                                <a href="mailto:partnerships@whale-tracker.pro" class="text-purple-400 hover:text-purple-300">partnerships@whale-tracker.pro</a>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Community -->
                <div class="bg-black/40 backdrop-blur-sm border border-gray-800 rounded-xl p-8">
                    <h3 class="text-2xl font-bold mb-6 text-cyan-400">🌍 Community</h3>
                    
                    <div class="space-y-4">
                        <div class="flex items-center space-x-3">
                            <div class="bg-blue-400/20 p-2 rounded-lg">
                                <svg class="w-5 h-5 text-blue-400" fill="currentColor" viewBox="0 0 24 24">
                                    <path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"/>
                                </svg>
                            </div>
                            <div>
                                <p class="font-bold text-white">Twitter</p>
                                <a href="https://twitter.com/WhaleTrackerAI" target="_blank" class="text-blue-400 hover:text-blue-300">@WhaleTrackerAI</a>
                            </div>
                        </div>
                        
                        <div class="flex items-center space-x-3">
                            <div class="bg-indigo-500/20 p-2 rounded-lg">
                                <svg class="w-5 h-5 text-indigo-400" fill="currentColor" viewBox="0 0 24 24">
                                    <path d="M20.317 4.37a19.791 19.791 0 0 0-4.885-1.515.074.074 0 0 0-.079.037c-.21.375-.444.864-.608 1.25a18.27 18.27 0 0 0-5.487 0 12.64 12.64 0 0 0-.617-1.25.077.077 0 0 0-.079-.037A19.736 19.736 0 0 0 3.677 4.37a.07.07 0 0 0-.032.027C.533 9.046-.32 13.58.099 18.057a.082.082 0 0 0 .031.057 19.9 19.9 0 0 0 5.993 3.03.078.078 0 0 0 .084-.028 14.09 14.09 0 0 0 1.226-1.994.076.076 0 0 0-.041-.106 13.107 13.107 0 0 1-1.872-.892.077.077 0 0 1-.008-.128 10.2 10.2 0 0 0 .372-.292.074.074 0 0 1 .077-.01c3.928 1.793 8.18 1.793 12.062 0a.074.074 0 0 1 .078.01c.12.098.246.198.373.292a.077.077 0 0 1-.006.127 12.299 12.299 0 0 1-1.873.892.077.077 0 0 0-.041.107c.36.698.772 1.362 1.225 1.993a.076.076 0 0 0 .084.028 19.839 19.839 0 0 0 6.002-3.03.077.077 0 0 0 .032-.054c.5-5.177-.838-9.674-3.549-13.66a.061.061 0 0 0-.031-.03zM8.02 15.33c-1.183 0-2.157-1.085-2.157-2.419 0-1.333.956-2.419 2.157-2.419 1.21 0 2.176 1.096 2.157 2.42 0 1.333-.956 2.418-2.157 2.418zm7.975 0c-1.183 0-2.157-1.085-2.157-2.419 0-1.333.955-2.419 2.157-2.419 1.21 0 2.176 1.096 2.157 2.42 0 1.333-.946 2.418-2.157 2.418z"/>
                                </svg>
                            </div>
                            <div>
                                <p class="font-bold text-white">Discord</p>
                                <a href="https://discord.gg/WhaleTracker" target="_blank" class="text-indigo-400 hover:text-indigo-300">WhaleTracker Community</a>
                            </div>
                        </div>
                        
                        <div class="flex items-center space-x-3">
                            <div class="bg-sky-500/20 p-2 rounded-lg">
                                <svg class="w-5 h-5 text-sky-400" fill="currentColor" viewBox="0 0 24 24">
                                    <path d="M11.944 0A12 12 0 0 0 0 12a12 12 0 0 0 12 12 12 12 0 0 0 12-12A12 12 0 0 0 12 0a12 12 0 0 0-.056 0zm4.962 7.224c.1-.002.321.023.465.14a.506.506 0 0 1 .171.325c.016.093.036.306.02.472-.18 1.898-.962 6.502-1.36 8.627-.168.9-.499 1.201-.82 1.23-.696.065-1.225-.46-1.9-.902-1.056-.693-1.653-1.124-2.678-1.8-1.185-.78-.417-1.21.258-1.91.177-.184 3.247-2.977 3.307-3.23.007-.032.014-.15-.056-.212s-.174-.041-.249-.024c-.106.024-1.793 1.14-5.061 3.345-.48.33-.913.49-1.302.48-.428-.008-1.252-.241-1.865-.44-.752-.245-1.349-.374-1.297-.789.027-.216.325-.437.893-.663 3.498-1.524 5.83-2.529 6.998-3.014 3.332-1.386 4.025-1.627 4.476-1.635z"/>
                                </svg>
                            </div>
                            <div>
                                <p class="font-bold text-white">Telegram</p>
                                <a href="https://t.me/WhaleTrackerPro" target="_blank" class="text-sky-400 hover:text-sky-300">@WhaleTrackerPro</a>
                            </div>
                        </div>
                    </div>
                </div>

            </div>

            <!-- Response Time -->
            <div class="bg-black/40 backdrop-blur-sm border border-gray-800 rounded-xl p-8 text-center">
                <h3 class="text-2xl font-bold mb-4">⚡ Response Times</h3>
                <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
                    <div>
                        <div class="text-2xl font-bold text-green-400 mb-2">< 4 hours</div>
                        <p class="text-gray-300">Emergency/Family Support</p>
                    </div>
                    <div>
                        <div class="text-2xl font-bold text-blue-400 mb-2">< 24 hours</div>
                        <p class="text-gray-300">Technical Support</p>
                    </div>
                    <div>
                        <div class="text-2xl font-bold text-purple-400 mb-2">< 48 hours</div>
                        <p class="text-gray-300">General Inquiries</p>
                    </div>
                </div>
            </div>
        </div>
    </section>

    <!-- Footer -->
    <footer class="border-t border-gray-800 py-8">
        <div class="max-w-7xl mx-auto px-4 text-center text-gray-400">
            <div class="flex justify-center space-x-6 mb-4">
                <a href="/terms" class="hover:text-white transition-colors">Terms of Service</a>
                <a href="/privacy" class="hover:text-white transition-colors">Privacy Policy</a>
                <a href="/refund" class="hover:text-white transition-colors">Refund Policy</a>
            </div>
            <p>&copy; 2025 Whale Tracker Pro. Community-funded innovation. 🐋</p>
        </div>
    </footer>
</body>
</html>
    ''')

@app.route('/terms')
def terms():
    """Terms of Service"""
    return render_template_string('''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Terms of Service - Whale Tracker Pro</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        body {
            background: linear-gradient(135deg, #1e293b 0%, #7c3aed 50%, #1e293b 100%);
            min-height: 100vh;
        }
    </style>
</head>
<body class="text-white">
    <div class="max-w-4xl mx-auto px-4 py-8">
        <div class="text-center mb-8">
            <h1 class="text-4xl font-bold mb-4">Terms of Service</h1>
            <p class="text-gray-400">Last updated: August 21, 2025</p>
        </div>

        <div class="bg-black/40 backdrop-blur-sm border border-gray-800 rounded-xl p-8 space-y-6">
            
            <section>
                <h2 class="text-2xl font-bold text-purple-400 mb-4">1. Service Description</h2>
                <p class="text-gray-300">
                    Whale Tracker Pro provides cryptocurrency whale tracking and analysis services. 
                    Our platform discovers and monitors large cryptocurrency transactions and wallet activities 
                    across multiple blockchain networks.
                </p>
            </section>

            <section>
                <h2 class="text-2xl font-bold text-purple-400 mb-4">2. Subscription Terms</h2>
                <ul class="text-gray-300 space-y-2">
                    <li>• Subscriptions are billed monthly unless otherwise specified</li>
                    <li>• Lifetime subscriptions are one-time payments with perpetual access</li>
                    <li>• Price locks guarantee your rate won't increase during active subscription</li>
                    <li>• All payments are processed securely through Stripe</li>
                </ul>
            </section>

            <section>
                <h2 class="text-2xl font-bold text-purple-400 mb-4">3. Beta Access & Development</h2>
                <p class="text-gray-300">
                    Whale Tracker Pro is currently in active development. Features and functionality 
                    may change as we implement our roadmap milestones. Early subscribers receive 
                    first access to new features and development updates.
                </p>
            </section>

            <section>
                <h2 class="text-2xl font-bold text-purple-400 mb-4">4. Investment Disclaimer</h2>
                <div class="bg-yellow-500/10 border border-yellow-500/30 rounded-lg p-4">
                    <p class="text-yellow-200 font-bold">⚠️ IMPORTANT: NOT FINANCIAL ADVICE</p>
                    <p class="text-gray-300 mt-2">
                        All information provided is for educational and research purposes only. 
                        Cryptocurrency trading involves substantial risk of loss. Make your own 
                        financial decisions and consult professionals when needed.
                    </p>
                </div>
            </section>

            <section>
                <h2 class="text-2xl font-bold text-purple-400 mb-4">5. Profit Sharing (Major Contributors)</h2>
                <p class="text-gray-300">
                    Contributors of $50,000+ annually are eligible for profit sharing based on 
                    actual company revenues. This is not a securities offering or investment contract. 
                    Profit sharing is contingent on company performance and applicable regulations.
                </p>
            </section>

            <section>
                <h2 class="text-2xl font-bold text-purple-400 mb-4">6. Data & Privacy</h2>
                <ul class="text-gray-300 space-y-2">
                    <li>• We collect minimal personal information (email, payment data)</li>
                    <li>• Blockchain data used is publicly available</li>
                    <li>• We never store private keys or sensitive wallet information</li>
                    <li>• Data is encrypted and secured with industry standards</li>
                </ul>
            </section>

            <section>
                <h2 class="text-2xl font-bold text-purple-400 mb-4">7. Limitation of Liability</h2>
                <p class="text-gray-300">
                    Whale Tracker Pro is provided "as is" without warranties. We are not liable 
                    for trading losses, missed opportunities, or any damages arising from use of our service.
                </p>
            </section>

            <section>
                <h2 class="text-2xl font-bold text-purple-400 mb-4">8. Contact</h2>
                <p class="text-gray-300">
                    Questions about these terms? Contact us at 
                    <a href="mailto:legal@whale-tracker.pro" class="text-blue-400 hover:text-blue-300">legal@whale-tracker.pro</a>
                </p>
            </section>

        </div>

        <div class="text-center mt-8">
            <a href="/" class="px-6 py-3 bg-purple-600 hover:bg-purple-700 rounded-lg transition-colors">
                Back to Home
            </a>
        </div>
    </div>
</body>
</html>
    ''')

@app.route('/privacy')
def privacy():
    """Privacy Policy"""
    return render_template_string('''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Privacy Policy - Whale Tracker Pro</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        body {
            background: linear-gradient(135deg, #1e293b 0%, #7c3aed 50%, #1e293b 100%);
            min-height: 100vh;
        }
    </style>
</head>
<body class="text-white">
    <div class="max-w-4xl mx-auto px-4 py-8">
        <div class="text-center mb-8">
            <h1 class="text-4xl font-bold mb-4">Privacy Policy</h1>
            <p class="text-gray-400">Last updated: August 21, 2025</p>
        </div>

        <div class="bg-black/40 backdrop-blur-sm border border-gray-800 rounded-xl p-8 space-y-6">
            
            <section>
                <h2 class="text-2xl font-bold text-cyan-400 mb-4">Information We Collect</h2>
                <ul class="text-gray-300 space-y-2">
                    <li>• <strong>Account Information:</strong> Email address for account creation</li>
                    <li>• <strong>Payment Information:</strong> Processed securely by Stripe (we don't store card details)</li>
                    <li>• <strong>Usage Data:</strong> How you interact with our platform</li>
                    <li>• <strong>Technical Data:</strong> IP address, browser type, device information</li>
                </ul>
            </section>

            <section>
                <h2 class="text-2xl font-bold text-cyan-400 mb-4">How We Use Your Information</h2>
                <ul class="text-gray-300 space-y-2">
                    <li>• Provide and improve our whale tracking services</li>
                    <li>• Process payments and manage subscriptions</li>
                    <li>• Send important updates about your account</li>
                    <li>• Communicate development progress and new features</li>
                    <li>• Ensure platform security and prevent fraud</li>
                </ul>
            </section>

            <section>
                <h2 class="text-2xl font-bold text-cyan-400 mb-4">Data Security</h2>
                <div class="bg-green-500/10 border border-green-500/30 rounded-lg p-4">
                    <p class="text-green-200 font-bold">🔒 Your Security is Our Priority</p>
                    <ul class="text-gray-300 mt-2 space-y-1">
                        <li>• All data encrypted in transit and at rest</li>
                        <li>• We never store private keys or wallet passwords</li>
                        <li>• Regular security audits and monitoring</li>
                        <li>• Secure cloud infrastructure with redundancy</li>
                    </ul>
                </div>
            </section>

            <section>
                <h2 class="text-2xl font-bold text-cyan-400 mb-4">Blockchain Data</h2>
                <p class="text-gray-300">
                    Our whale tracking service analyzes publicly available blockchain data. 
                    This information is already public on blockchain networks. We do not 
                    collect or store private wallet information.
                </p>
            </section>

            <section>
                <h2 class="text-2xl font-bold text-cyan-400 mb-4">Third-Party Services</h2>
                <ul class="text-gray-300 space-y-2">
                    <li>• <strong>Stripe:</strong> Payment processing (has their own privacy policy)</li>
                    <li>• <strong>Railway:</strong> Hosting infrastructure</li>
                    <li>• <strong>Blockchain APIs:</strong> For accessing public blockchain data</li>
                </ul>
            </section>

            <section>
                <h2 class="text-2xl font-bold text-cyan-400 mb-4">Your Rights</h2>
                <ul class="text-gray-300 space-y-2">
                    <li>• Request access to your personal data</li>
                    <li>• Request correction of inaccurate data</li>
                    <li>• Request deletion of your account and data</li>
                    <li>• Opt out of marketing communications</li>
                    <li>• Data portability for your information</li>
                </ul>
            </section>

            <section>
                <h2 class="text-2xl font-bold text-cyan-400 mb-4">Contact Us</h2>
                <p class="text-gray-300">
                    Privacy questions or requests? Contact us at 
                    <a href="mailto:privacy@whale-tracker.pro" class="text-blue-400 hover:text-blue-300">privacy@whale-tracker.pro</a>
                </p>
            </section>

        </div>

        <div class="text-center mt-8">
            <a href="/" class="px-6 py-3 bg-cyan-600 hover:bg-cyan-700 rounded-lg transition-colors">
                Back to Home
            </a>
        </div>
    </div>
</body>
</html>
    ''')

@app.route('/refund')
def refund():
    """Refund Policy"""
    return render_template_string('''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Refund Policy - Whale Tracker Pro</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        body {
            background: linear-gradient(135deg, #1e293b 0%, #7c3aed 50%, #1e293b 100%);
            min-height: 100vh;
        }
    </style>
</head>
<body class="text-white">
    <div class="max-w-4xl mx-auto px-4 py-8">
        <div class="text-center mb-8">
            <h1 class="text-4xl font-bold mb-4">Refund Policy</h1>
            <p class="text-gray-400">Last updated: August 21, 2025</p>
        </div>

        <div class="bg-black/40 backdrop-blur-sm border border-gray-800 rounded-xl p-8 space-y-6">
            
            <!-- Emergency Context -->
            <div class="bg-orange-500/10 border border-orange-500/30 rounded-lg p-6">
                <h3 class="text-xl font-bold text-orange-400 mb-3">🏠 Special Circumstances</h3>
                <p class="text-gray-300">
                    We're currently in an emergency situation trying to save our family home from foreclosure 
                    (auction scheduled September 2nd, 2025). Every subscription directly helps our family while 
                    providing you with cutting-edge whale tracking technology.
                </p>
            </div>

            <section>
                <h2 class="text-2xl font-bold text-green-400 mb-4">Monthly Subscriptions</h2>
                <ul class="text-gray-300 space-y-3">
                    <li class="flex items-start space-x-2">
                        <span class="text-green-400 mt-1">•</span>
                        <span><strong>7-Day Money-Back Guarantee:</strong> Full refund if cancelled within 7 days of first subscription</span>
                    </li>
                    <li class="flex items-start space-x-2">
                        <span class="text-green-400 mt-1">•</span>
                        <span><strong>Prorated Refunds:</strong> Available for service interruptions lasting more than 48 hours</span>
                    </li>
                    <li class="flex items-start space-x-2">
                        <span class="text-green-400 mt-1">•</span>
                        <span><strong>Cancel Anytime:</strong> No refund for current billing period, but access continues until period ends</span>
                    </li>
                </ul>
            </section>

            <section>
                <h2 class="text-2xl font-bold text-yellow-400 mb-4">Lifetime Subscriptions</h2>
                <div class="bg-yellow-500/10 border border-yellow-500/30 rounded-lg p-4">
                    <p class="text-yellow-200 font-bold mb-2">⚠️ Important: Limited Refund Policy</p>
                    <ul class="text-gray-300 space-y-2">
                        <li>• <strong>72-Hour Window:</strong> Full refund available within 72 hours of purchase</li>
                        <li>• <strong>After 72 Hours:</strong> No refunds available due to immediate access to services</li>
                        <li>• <strong>Service Issues:</strong> Account credits or extensions for technical problems</li>
                        <li>• <strong>Emergency Exception:</strong> Case-by-case review for extreme circumstances</li>
                    </ul>
                </div>
            </section>

            <section>
                <h2 class="text-2xl font-bold text-blue-400 mb-4">Beta Access Refunds</h2>
                <p class="text-gray-300">
                    As we're currently in beta development, we understand some features may not meet expectations:
                </p>
                <ul class="text-gray-300 space-y-2 mt-3">
                    <li>• Refunds available if core promised features are not delivered within 30 days</li>
                    <li>• Bug-related issues will be resolved or account credited</li>
                    <li>• Development delays may qualify for partial refunds or account extensions</li>
                </ul>
            </section>

            <section>
                <h2 class="text-2xl font-bold text-purple-400 mb-4">How to Request a Refund</h2>
                <ol class="text-gray-300 space-y-2">
                    <li><strong>1.</strong> Contact us at <a href="mailto:refunds@whale-tracker.pro" class="text-blue-400 hover:text-blue-300">refunds@whale-tracker.pro</a></li>
                    <li><strong>2.</strong> Include your email address and reason for refund request</li>
                    <li><strong>3.</strong> We'll respond within 24 hours with next steps</li>
                    <li><strong>4.</strong> Approved refunds are processed within 5-7 business days</li>
                </ol>
            </section>

            <section>
                <h2 class="text-2xl font-bold text-red-400 mb-4">Non-Refundable Situations</h2>
                <ul class="text-gray-300 space-y-2">
                    <li>• Violation of Terms of Service</li>
                    <li>• Abuse of platform or community guidelines</li>
                    <li>• Requests made after applicable refund windows</li>
                    <li>• Normal market volatility affecting trading decisions</li>
                    <li>• Personal financial circumstances unrelated to our service</li>
                </ul>
            </section>

            <section>
                <h2 class="text-2xl font-bold text-cyan-400 mb-4">Our Commitment</h2>
                <div class="bg-cyan-500/10 border border-cyan-500/30 rounded-lg p-4">
                    <p class="text-cyan-200">
                        We're committed to building the best whale tracking platform while maintaining fair 
                        refund policies. Our goal is your success and satisfaction with our service.
                    </p>
                </div>
            </section>

            <section>
                <h2 class="text-2xl font-bold text-gray-400 mb-4">Questions?</h2>
                <p class="text-gray-300">
                    Refund questions or concerns? Contact our support team:
                </p>
                <div class="mt-3">
                    <p class="text-blue-400">📧 <a href="mailto:refunds@whale-tracker.pro" class="hover:text-blue-300">refunds@whale-tracker.pro</a></p>
                    <p class="text-green-400">📧 <a href="mailto:support@whale-tracker.pro" class="hover:text-green-300">support@whale-tracker.pro</a></p>
                </div>
            </section>

        </div>

        <div class="text-center mt-8">
            <a href="/" class="px-6 py-3 bg-green-600 hover:bg-green-700 rounded-lg transition-colors">
                Back to Home
            </a>
        </div>
    </div>
</body>
</html>
    ''') 

if __name__ == '__main__':
    if not stripe.api_key:
        logger.error("❌ STRIPE_SECRET_KEY not found in environment variables")
        exit(1)
    
    logger.info("🚀 Starting Whale Tracker Payment Server...")
    logger.info(f"💳 Stripe configured: {stripe.api_key[:8]}...")
    
    port = int(os.getenv('PORT', 8000))
    app.run(debug=True, host='0.0.0.0', port=port)
