# REPLACE your create_checkout_session function in app.py with this enhanced version

@app.route('/create-checkout-session', methods=['POST'])
def create_checkout_session():
    """Enhanced checkout session for subscriptions, crowdfund, and donations"""
    try:
        data = request.get_json()
        plan = data.get('plan', 'professional')
        payment_type = data.get('type', 'subscription')  # subscription, crowdfund, donation
        custom_amount = data.get('amount')  # For custom donations (in cents)
        
        # Define all pricing
        PRICING = {
            # Monthly subscriptions
            'professional': {'price_id': 'price_1RyKygRkVYDUbhIFgs8JUTTR', 'mode': 'subscription'},
            'emergency': {'price_id': 'price_1RyJOzDfwP4gynpjh4mO6b6B', 'mode': 'subscription'},
            'enterprise': {'price_id': 'price_1RyJR4DfwP4gynpj3sURTxuU', 'mode': 'subscription'},
            
            # One-time crowdfund tiers (create these in Stripe as one-time payments)
            'house_hero': {'amount': 50000, 'mode': 'payment'},        # $500
            'family_guardian': {'amount': 150000, 'mode': 'payment'},   # $1,500
            'life_changer': {'amount': 500000, 'mode': 'payment'},      # $5,000
            'legend': {'amount': 1000000, 'mode': 'payment'},           # $10,000
            
            # Existing one-time
            'lifetime': {'price_id': 'price_1RyJS8DfwP4gynpjb23JQGGn', 'mode': 'payment'},
        }
        
        # Handle custom donations
        if payment_type == 'donation' and custom_amount:
            checkout_session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[{
                    'price_data': {
                        'currency': 'usd',
                        'product_data': {
                            'name': '🏠 Emergency House Fund Donation',
                            'description': 'Help save our family home from foreclosure'
                        },
                        'unit_amount': custom_amount,
                    },
                    'quantity': 1,
                }],
                mode='payment',
                success_url='https://whale-tracker-ai.up.railway.app/success?session_id={CHECKOUT_SESSION_ID}&type=donation',
                cancel_url='https://whale-tracker-ai.up.railway.app/?canceled=true',
                metadata={
                    'plan': 'custom_donation',
                    'type': 'donation',
                    'amount': custom_amount
                }
            )
            
            logger.info(f"💰 Created donation session: ${custom_amount/100}")
            return jsonify({'id': checkout_session.id})
        
        # Handle crowdfund tiers (one-time payments with fixed amounts)
        if payment_type == 'crowdfund' and plan in ['house_hero', 'family_guardian', 'life_changer', 'legend']:
            tier_info = PRICING[plan]
            
            # Map plan names to display names
            display_names = {
                'house_hero': '💰 House Hero - 1 Year Access',
                'family_guardian': '🏆 Family Guardian - 2 Years + 3% Profit Share',
                'life_changer': '👑 Life Changer - Lifetime + 5% Profit Share',
                'legend': '🌟 Legend Status - Everything + 10% Profit Share'
            }
