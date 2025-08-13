# Add to your secure API (app.py)

import stripe
import os

# Stripe configuration
stripe.api_key = os.environ.get('STRIPE_SECRET_KEY', 'sk_test_your_test_key_here')
STRIPE_WEBHOOK_SECRET = os.environ.get('STRIPE_WEBHOOK_SECRET', 'whsec_your_webhook_secret')

@app.route('/api/create-checkout-session', methods=['POST'])
@limiter.limit("10 per minute")
def create_checkout_session():
    """Create Stripe checkout session for beta subscription"""
    try:
        data = request.get_json()
        email = data.get('email', '').lower().strip()
        
        if not email:
            return jsonify({'error': 'Email required'}), 400
        
        # Create Stripe checkout session
        checkout_session = stripe.checkout.Session.create(
            customer_email=email,
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'usd',
                    'product_data': {
                        'name': 'Whale Tracker Beta Access',
                        'description': 'Early access beta - Automatic PRO upgrade included!',
                        'images': ['https://your-domain.com/whale-icon.png'],  # Optional
                    },
                    'unit_amount': 1900,  # $19.00 in cents
                    'recurring': {
                        'interval': 'month',
                    },
                },
                'quantity': 1,
            }],
            mode='subscription',
            success_url=request.host_url + 'dashboard?session_id={CHECKOUT_SESSION_ID}',
            cancel_url=request.host_url + 'signup?cancelled=true',
            metadata={
                'product': 'whale_tracker_beta',
                'user_email': email
            },
            subscription_data={
                'metadata': {
                    'product': 'whale_tracker_beta',
                    'tier': 'beta_early_access'
                }
            }
        )
        
        logger.info(f"Checkout session created for: {email}")
        return jsonify({'checkout_url': checkout_session.url})
        
    except stripe.error.StripeError as e:
        logger.error(f"Stripe error: {e}")
        return jsonify({'error': 'Payment system error'}), 500
    except Exception as e:
        logger.error(f"Checkout creation error: {e}")
        return jsonify({'error': 'Failed to create checkout'}), 500

@app.route('/api/stripe-webhook', methods=['POST'])
def stripe_webhook():
    """Handle Stripe webhooks for subscription events"""
    payload = request.get_data(as_text=True)
    sig_header = request.headers.get('Stripe-Signature')
    
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, STRIPE_WEBHOOK_SECRET
        )
    except ValueError:
        logger.error("Invalid payload in webhook")
        return jsonify({'error': 'Invalid payload'}), 400
    except stripe.error.SignatureVerificationError:
        logger.error("Invalid signature in webhook")
        return jsonify({'error': 'Invalid signature'}), 400
    
    # Handle successful subscription creation
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        
        if session['mode'] == 'subscription':
            customer_email = session['customer_details']['email']
            subscription_id = session['subscription']
            
            try:
                # Create user account with beta access
                conn = get_db_connection()
                
                # Generate secure password for auto-created account
                temp_password = os.urandom(16).hex()
                password_hash = generate_password_hash(temp_password)
                
                conn.execute('''INSERT OR REPLACE INTO users 
                               (email, password_hash, subscription_tier, stripe_customer_id, stripe_subscription_id) 
                               VALUES (?, ?, ?, ?, ?)''',
                            (customer_email, password_hash, 'beta_early_access', 
                             session['customer'], subscription_id))
                conn.commit()
                
                # Generate JWT token for immediate access
                token = jwt.encode({
                    'email': customer_email,
                    'subscription_tier': 'beta_early_access',
                    'exp': datetime.utcnow() + timedelta(days=30)
                }, app.config['JWT_SECRET_KEY'], algorithm='HS256')
                
                conn.close()
                
                logger.info(f"Beta user created: {customer_email}")
                
                # TODO: Send welcome email with login instructions
                # send_welcome_email(customer_email, temp_password, token)
                
            except Exception as e:
                logger.error(f"Failed to create user after payment: {e}")
    
    # Handle subscription cancellation
    elif event['type'] == 'customer.subscription.deleted':
        subscription = event['data']['object']
        
        try:
            conn = get_db_connection()
            conn.execute('UPDATE users SET subscription_tier = ?, is_active = ? WHERE stripe_subscription_id = ?',
                        ('cancelled', False, subscription['id']))
            conn.commit()
            conn.close()
            
            logger.info(f"Subscription cancelled: {subscription['id']}")
            
        except Exception as e:
            logger.error(f"Failed to handle cancellation: {e}")
    
    return jsonify({'status': 'success'})

@app.route('/api/billing/manage', methods=['POST'])
@token_required
def manage_billing():
    """Create Stripe customer portal session"""
    try:
        conn = get_db_connection()
        cursor = conn.execute('SELECT stripe_customer_id FROM users WHERE id = ?', (g.current_user_id,))
        user = cursor.fetchone()
        conn.close()
        
        if not user or not user['stripe_customer_id']:
            return jsonify({'error': 'No billing account found'}), 404
        
        # Create customer portal session
        portal_session = stripe.billing_portal.Session.create(
            customer=user['stripe_customer_id'],
            return_url=request.host_url + 'dashboard'
        )
        
        return jsonify({'portal_url': portal_session.url})
        
    except Exception as e:
        logger.error(f"Billing portal error: {e}")
        return jsonify({'error': 'Failed to access billing'}), 500

# Add these fields to your users table
def update_users_table_for_stripe():
    """Add Stripe fields to users table"""
    conn = get_db_connection()
    try:
        # Add Stripe customer ID
        conn.execute('ALTER TABLE users ADD COLUMN stripe_customer_id TEXT')
    except:
        pass  # Column might already exist
    
    try:
        # Add Stripe subscription ID  
        conn.execute('ALTER TABLE users ADD COLUMN stripe_subscription_id TEXT')
    except:
        pass  # Column might already exist
    
    conn.close()

# Call this once to update your database
# update_users_table_for_stripe()
