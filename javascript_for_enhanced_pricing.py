<script>
    const stripe = Stripe('{{ stripe_publishable_key }}');
    
    // Update donation amount display
    const donationSlider = document.getElementById('donationSlider');
    const donationAmount = document.getElementById('donationAmount');
    
    if (donationSlider && donationAmount) {
        donationSlider.addEventListener('input', function() {
            const amount = this.value;
            donationAmount.textContent = '$' + parseInt(amount).toLocaleString();
        });
    }
    
    // Monthly subscription function (existing)
    async function subscribe(planType) {
        try {
            console.log('Subscribing to:', planType);
            
            const response = await fetch('/create-checkout-session', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    plan: planType,
                    type: 'subscription'
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
    
    // Crowdfund one-time payments
    async function crowdfund(tierType) {
        try {
            console.log('Crowdfunding tier:', tierType);
            
            const response = await fetch('/create-checkout-session', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    plan: tierType,
                    type: 'crowdfund'
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
    
    // Custom donation amount
    async function donateCustom(paymentMethod) {
        const amount = document.getElementById('donationSlider').value;
        
        if (paymentMethod === 'crypto') {
            // TODO: Implement crypto payment
            alert('Crypto payments coming in the next update! Use card for now.');
            return;
        }
        
        try {
            console.log('Custom donation:', amount);
            
            const response = await fetch('/create-checkout-session', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    plan: 'custom_donation',
                    type: 'donation',
                    amount: parseInt(amount) * 100 // Convert to cents
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
