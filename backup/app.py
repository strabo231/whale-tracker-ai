from flask import Flask, render_template, request, jsonify, render_template_string
import stripe
import coinbase_commerce
from coinbase_commerce.client import Client
from coinbase_commerce.error import WebhookInvalidPayload, SignatureError
import logging
import os
from datetime import datetime
from dotenv import load_dotenv
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

# Initialize Flask app
app = Flask(__name__, template_folder='templates')
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    handlers=[
        logging.FileHandler('/mnt/bridge/logs/transactions.log'),
        logging.StreamHandler()  # Also log to console for Railway
    ],
    format='%(asctime)s %(levelname)s: %(message)s'
)
logger = logging.getLogger(__name__)

# Stripe setup
stripe.api_key = os.getenv('STRIPE_SECRET_KEY')
STRIPE_PUBLISHABLE_KEY = os.getenv('STRIPE_PUBLISHABLE_KEY')
DOMAIN = os.getenv('DOMAIN', 'https://whale-tracker-ai.up.railway.app')

# Coinbase Commerce setup
coinbase_client = Client(api_key=os.getenv('COINBASE_API_KEY'))
COINBASE_WEBHOOK_SECRET = os.getenv('COINBASE_WEBHOOK_SECRET')

# Price IDs for Stripe
PRICE_IDS = {
    'professional': 'price_1RyKygRkVYDUbhIFgs8JUTTR',
    'emergency': 'price_1RyapeRkVYDUbhIFwSQYNIAw',
    'enterprise': 'price_1Ryar9RkVYDUbhIFr4Oe7N9C',
    'lifetime': 'price_1Ryat4RkVYDUbhIFxohXgOK1',
    'sixmonth': 'price_1RyJOzDfwP4gynpjh4mO6b6B'
}

def get_db_connection():
    conn = psycopg2.connect(os.getenv('DATABASE_URL'))
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    return conn

@app.route('/')
def home():
    """Main subscription page with enhanced crowdfunding integration"""
    return render_template('index.html', stripe_publishable_key=STRIPE_PUBLISHABLE_KEY)

@app.route('/create-checkout-session', methods=['POST'])
def create_checkout_session():
    """Enhanced checkout session for subscriptions and crowdfund"""
    try:
        data = request.get_json()
        plan = data.get('plan', 'professional')
        payment_type = data.get('type', 'subscription')

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
        
        if payment_type == 'crowdfund' and plan in ['house_hero', 'family_guardian', 'life_changer', 'legend']:
            tier_info = PRICING[plan]
            display_names = {
                'house_hero': '💰 House Hero - 1 Year Access',
                'family_guardian': '🏆 Family Guardian - 2 Years + 3% Profit Share',
                'life_changer': '👑 Life Changer - Lifetime + 5% Profit Share',
                'legend': '✨ Legend Status - Everything + 10% Profit Share'
            }
            checkout_session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[{
                    'price_data': {
                        'currency': 'usd',
                        'product_data': {
                            'name': display_names[plan],
                            'description': 'Support Whale Tracker Pro and help save our family home'
                        },
                        'unit_amount': tier_info['amount'],
                    },
                    'quantity': 1,
                }],
                mode='payment',
                success_url=f'{DOMAIN}/success?session_id={{CHECKOUT_SESSION_ID}}&type=crowdfund&plan={plan}',
                cancel_url=f'{DOMAIN}/?canceled=true',
                metadata={'plan': plan, 'type': 'crowdfund', 'amount': tier_info['amount']}
            )
            logger.info(f"[{datetime.now()}] Created crowdfund session for {plan}: ${tier_info['amount']/100}")
            return jsonify({'id': checkout_session.id})

        if plan not in PRICING:
            logger.error(f"[{datetime.now()}] Invalid plan selected: {plan}")
            return jsonify({'error': 'Invalid plan selected'}), 400

        tier_info = PRICING[plan]
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{'price': tier_info['price_id'], 'quantity': 1}],
            mode=tier_info['mode'],
            success_url=f'{DOMAIN}/success?session_id={{CHECKOUT_SESSION_ID}}&type={payment_type}',
            cancel_url=f'{DOMAIN}/?canceled=true',
            metadata={'plan': plan, 'type': payment_type}
        )
        logger.info(f"[{datetime.now()}] Created {payment_type} session for plan: {plan}")
        return jsonify({'id': checkout_session.id})

    except stripe.error.StripeError as e:
        logger.error(f"[{datetime.now()}] Stripe error: {e}")
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"[{datetime.now()}] Checkout error: {e}")
        return jsonify({'error': 'Failed to create checkout session'}), 500

@app.route('/create-donation-session', methods=['POST'])
def create_donation_session():
    """Handle crypto and fiat donations"""
    try:
        data = request.get_json()
        amount = data.get('amount')
        method = data.get('method')
        if not amount or amount < 49 or amount > 10000:
            return jsonify({'error': 'Amount must be between $49 and $10,000'}), 400

        if method == 'crypto':
            charge = coinbase_client.charge.create(
                name='Whale Tracker Pro Donation',
                description='Help save our family home',
                local_price={'amount': str(amount), 'currency': 'USD'},
                pricing_type='fixed_price',
                metadata={'type': 'donation', 'amount': amount}
            )
            logger.info(f"[{datetime.now()}] Created Coinbase donation charge: {charge.id}, amount: ${amount}")
            return jsonify({'url': charge.hosted_url, 'id': charge.id})
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
                success_url=f'{DOMAIN}/success?session_id={{CHECKOUT_SESSION_ID}}&type=donation',
                cancel_url=f'{DOMAIN}/?canceled=true',
                metadata={'type': 'donation', 'amount': amount}
            )
            logger.info(f"[{datetime.now()}] Created Stripe donation session: ${amount}, session_id: {checkout_session.id}")
            return jsonify({'id': checkout_session.id})

    except stripe.error.StripeError as e:
        logger.error(f"[{datetime.now()}] Stripe error: {e}")
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"[{datetime.now()}] Donation error: {e}")
        return jsonify({'error': 'Failed to create donation session'}), 500

@app.route('/webhook', methods=['POST'])
def webhook():
    """Handle Stripe and Coinbase webhooks"""
    payload = request.get_data(as_text=True)
    sig_header = request.headers.get('Stripe-Signature') or request.headers.get('X-Cc-Webhook-Signature')
    logger.debug(f"[{datetime.now()}] Received webhook with signature: {sig_header}")
    logger.debug(f"[{datetime.now()}] Webhook payload: {payload}")
    
    try:
        if sig_header and 'Stripe-Signature' in request.headers:
            event = stripe.Webhook.construct_event(payload, sig_header, os.getenv('STRIPE_WEBHOOK_SECRET'))
            if event['type'] == 'checkout.session.completed':
                session = event['data']['object']
                logger.info(f"[{datetime.now()}] Stripe payment completed: {session['id']}, plan: {session['metadata']['plan']}")
                with get_db_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(
                        "INSERT INTO users (stripe_session_id, subscription_tier) VALUES (%s, %s) "
                        "ON CONFLICT (stripe_session_id) DO UPDATE SET subscription_tier = EXCLUDED.subscription_tier",
                        (session['id'], session['metadata']['plan'])
                    )
        elif sig_header and 'X-Cc-Webhook-Signature' in request.headers:
            coinbase_client.webhook.verify(payload, sig_header, COINBASE_WEBHOOK_SECRET)
            event = coinbase_client.webhook.parse(payload)
            logger.info(f"[{datetime.now()}] Coinbase event: {event.type}, charge_id: {event.data.id}")
            if event.type == 'charge:confirmed':
                charge = event.data
                logger.info(f"[{datetime.now()}] Crypto donation confirmed: {charge.id}, amount: {charge.payments[0]['value']['local']['amount']} USD")
                with get_db_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(
                        "INSERT INTO donations (charge_id, amount, type, timestamp) VALUES (%s, %s, %s, NOW()) "
                        "ON CONFLICT (charge_id) DO NOTHING",
                        (charge.id, charge.payments[0]['value']['local']['amount'], 'crypto')
                    )
        return jsonify({'status': 'success'})
    except (WebhookInvalidPayload, SignatureError, Exception) as e:
        logger.error(f"[{datetime.now()}] Webhook error: {e}")
        return jsonify({'error': str(e)}), 400

@app.route('/success')
def success():
    """Success page for payments"""
    session_id = request.args.get('session_id')
    payment_type = request.args.get('type', 'subscription')
    plan = request.args.get('plan', '')
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

@app.route('/dashboard')
def dashboard():
    """Dashboard placeholder"""
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
        </div>
    </body>
    </html>
    """)

if __name__ == '__main__':
    app.run(debug=True)
