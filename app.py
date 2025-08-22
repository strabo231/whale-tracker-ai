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
        ðŸš¨ URGENT: House scheduled for auction Sept 2nd - Every subscription helps save our home ðŸ 
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
                â° 8 DAYS LEFT - HELP SAVE OUR HOME
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
        
        <!-- Monthly Subscriptions -->
        <div class="text-center mb-16">
            <h2 class="text-4xl font-bold mb-4">ðŸ’³ Monthly Subscriptions</h2>
            <p class="text-gray-400 text-lg">Ongoing access to professional whale intelligence</p>
        </div>
        
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8 max-w-5xl mx-auto mb-20">
            
            <!-- Professional Tier -->
            <div class="tier-card bg-black/40 backdrop-blur-sm border border-cyan-500/50 rounded-xl p-8">
                <div class="text-center mb-8">
                    <h3 class="text-2xl font-bold mb-2">Professional</h3>
                    <p class="text-gray-400 mb-4">Essential whale tracking</p>
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

            <!-- Help Save Home Tier -->
            <div class="tier-card bg-black/40 backdrop-blur-sm border border-orange-500/50 rounded-xl p-8 relative">
                <div class="absolute -top-3 left-1/2 transform -translate-x-1/2">
                    <span class="emergency-badge px-4 py-1 text-white text-sm font-bold rounded-full">
                        ðŸ  HELP SAVE HOME
                    </span>
                </div>
                
                <div class="text-center mb-8 mt-4">
                    <h3 class="text-2xl font-bold mb-2">Help Us Stay</h3>
                    <p class="text-gray-400 mb-4">Support our family + premium access</p>
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
                    <li class="flex items-center text-green-400">
                        <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/>
                        </svg>
                        Priority support
                    </li>
                    <li class="flex items-center text-orange-400">
                        <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z"/>
                        </svg>
                        Help save a special needs child's home
                    </li>
                </ul>
                
                <button onclick="subscribe('emergency')" class="block w-full py-3 bg-gradient-to-r from-orange-500 to-red-500 rounded-lg font-semibold text-white text-center hover:opacity-90 transition-opacity">
                    ðŸ  Help Save Our Home - $199/month
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
                    <li class="flex items-center text-green-400">
                        <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/>
                        </svg>
                        Priority consultation
                    </li>
                </ul>
                
                <button onclick="subscribe('enterprise')" class="block w-full py-3 bg-gradient-to-r from-purple-500 to-indigo-500 rounded-lg font-semibold text-white text-center hover:opacity-90 transition-opacity">
                    Contact Sales - $899/month
                </button>
            </div>
        </div>

        <!-- ONE-TIME CROWDFUND SECTION -->
        <div class="border-t border-gray-800 pt-20">
            <div class="text-center mb-16">
                <h2 class="text-5xl font-bold mb-4">ðŸš€ Crowdfund Our Mission</h2>
                <p class="text-xl text-gray-300 mb-6">One-time contributions to save our home + build the future</p>
                <div class="inline-flex items-center px-6 py-3 bg-red-500/20 border border-red-500/50 rounded-full text-red-300 font-bold">
                    â° URGENT: Auction September 2nd - 8 Days Left
                </div>
            </div>
            
            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-12">
                
                <!-- House Hero -->
                <div class="tier-card bg-black/40 backdrop-blur-sm border border-green-500/50 rounded-xl p-6">
                    <div class="text-center mb-6">
                        <div class="text-4xl mb-3">ðŸ’°</div>
                        <h3 class="text-xl font-bold text-green-400 mb-2">House Hero</h3>
                        <div class="text-3xl font-bold mb-2">$500</div>
                        <p class="text-gray-400 text-sm">One-time contribution</p>
                    </div>
                    
                    <ul class="space-y-2 mb-6 text-sm">
                        <li class="flex items-center text-green-400">
                            <div class="w-1.5 h-1.5 bg-green-400 rounded-full mr-2"></div>
                            1 year premium access
                        </li>
                        <li class="flex items-center text-green-400">
                            <div class="w-1.5 h-1.5 bg-green-400 rounded-full mr-2"></div>
                            Hero badge in dashboard
                        </li>
                        <li class="flex items-center text-green-400">
                            <div class="w-1.5 h-1.5 bg-green-400 rounded-full mr-2"></div>
                            Monthly progress updates
                        </li>
                        <li class="flex items-center text-orange-400">
                            <div class="w-1.5 h-1.5 bg-orange-400 rounded-full mr-2"></div>
                            Help save our home
                        </li>
                    </ul>
                    
                    <button onclick="crowdfund('house_hero')" class="block w-full py-3 bg-gradient-to-r from-green-500 to-emerald-500 rounded-lg font-semibold text-white text-center hover:opacity-90 transition-opacity text-sm">
                        ðŸ  Be a House Hero
                    </button>
                </div>

                <!-- Family Guardian -->
                <div class="tier-card bg-black/40 backdrop-blur-sm border border-blue-500/50 rounded-xl p-6 relative">
                    <div class="absolute -top-2 left-1/2 transform -translate-x-1/2">
                        <span class="px-3 py-1 bg-blue-500 text-white text-xs font-bold rounded-full">
                            POPULAR
                        </span>
                    </div>
                    
                    <div class="text-center mb-6 mt-2">
                        <div class="text-4xl mb-3">ðŸ†</div>
                        <h3 class="text-xl font-bold text-blue-400 mb-2">Family Guardian</h3>
                        <div class="text-3xl font-bold mb-2">$1,500</div>
                        <p class="text-gray-400 text-sm">One-time contribution</p>
                    </div>
                    
                    <ul class="space-y-2 mb-6 text-sm">
                        <li class="flex items-center text-green-400">
                            <div class="w-1.5 h-1.5 bg-green-400 rounded-full mr-2"></div>
                            2 years premium access
                        </li>
                        <li class="flex items-center text-green-400">
                            <div class="w-1.5 h-1.5 bg-green-400 rounded-full mr-2"></div>
                            Guardian badge + special features
                        </li>
                        <li class="flex items-center text-green-400">
                            <div class="w-1.5 h-1.5 bg-green-400 rounded-full mr-2"></div>
                            Quarterly strategy calls
                        </li>
                        <li class="flex items-center text-blue-400">
                            <div class="w-1.5 h-1.5 bg-blue-400 rounded-full mr-2"></div>
                            3% profit sharing for life
                        </li>
                    </ul>
                    
                    <button onclick="crowdfund('family_guardian')" class="block w-full py-3 bg-gradient-to-r from-blue-500 to-cyan-500 rounded-lg font-semibold text-white text-center hover:opacity-90 transition-opacity text-sm">
                        ðŸ›¡ï¸ Become a Guardian
                    </button>
                </div>

                <!-- Life Changer -->
                <div class="tier-card bg-black/40 backdrop-blur-sm border border-purple-500/50 rounded-xl p-6">
                    <div class="text-center mb-6">
                        <div class="text-4xl mb-3">ðŸ‘‘</div>
                        <h3 class="text-xl font-bold text-purple-400 mb-2">Life Changer</h3>
                        <div class="text-3xl font-bold mb-2">$5,000</div>
                        <p class="text-gray-400 text-sm">One-time contribution</p>
                    </div>
                    
                    <ul class="space-y-2 mb-6 text-sm">
                        <li class="flex items-center text-green-400">
                            <div class="w-1.5 h-1.5 bg-green-400 rounded-full mr-2"></div>
                            Lifetime premium access
                        </li>
                        <li class="flex items-center text-green-400">
                            <div class="w-1.5 h-1.5 bg-green-400 rounded-full mr-2"></div>
                            VIP badge + exclusive features
                        </li>
                        <li class="flex items-center text-green-400">
                            <div class="w-1.5 h-1.5 bg-green-400 rounded-full mr-2"></div>
                            Monthly 1-on-1 calls
                        </li>
                        <li class="flex items-center text-purple-400">
                            <div class="w-1.5 h-1.5 bg-purple-400 rounded-full mr-2"></div>
                            5% profit sharing for life
                        </li>
                    </ul>
                    
                    <button onclick="crowdfund('life_changer')" class="block w-full py-3 bg-gradient-to-r from-purple-500 to-pink-500 rounded-lg font-semibold text-white text-center hover:opacity-90 transition-opacity text-sm">
                        ðŸ‘‘ Change Our Lives
                    </button>
                </div>

                <!-- Legend Status -->
                <div class="tier-card bg-black/40 backdrop-blur-sm border border-yellow-500/50 rounded-xl p-6">
                    <div class="text-center mb-6">
                        <div class="text-4xl mb-3">ðŸŒŸ</div>
                        <h3 class="text-xl font-bold text-yellow-400 mb-2">Legend Status</h3>
                        <div class="text-3xl font-bold mb-2">$10,000</div>
                        <p class="text-gray-400 text-sm">One-time contribution</p>
                    </div>
                    
                    <ul class="space-y-2 mb-6 text-sm">
                        <li class="flex items-center text-green-400">
                            <div class="w-1.5 h-1.5 bg-green-400 rounded-full mr-2"></div>
                            Everything in Life Changer
                        </li>
                        <li class="flex items-center text-green-400">
                            <div class="w-1.5 h-1.5 bg-green-400 rounded-full mr-2"></div>
                            Legend badge + co-branding
                        </li>
                        <li class="flex items-center text-green-400">
                            <div class="w-1.5 h-1.5 bg-green-400 rounded-full mr-2"></div>
                            Advisory board position
                        </li>
                        <li class="flex items-center text-yellow-400">
                            <div class="w-1.5 h-1.5 bg-yellow-400 rounded-full mr-2"></div>
                            <strong>10% profit sharing for life</strong>
                        </li>
                    </ul>
                    
                    <button onclick="crowdfund('legend')" class="block w-full py-3 bg-gradient-to-r from-yellow-500 to-orange-500 rounded-lg font-semibold text-white text-center hover:opacity-90 transition-opacity text-sm">
                        ðŸŒŸ Become a Legend
                    </button>
                </div>
            </div>

            <!-- Pay What You Want Section -->
            <div class="bg-gradient-to-r from-red-500/10 to-orange-500/10 border border-red-500/20 rounded-xl p-8 text-center">
                <h3 class="text-3xl font-bold text-red-400 mb-4">ðŸ  Emergency House Fund</h3>
                <p class="text-xl text-gray-300 mb-6">
                    Can't afford a tier? Every dollar helps save our family home!
                </p>
                
                <div class="max-w-md mx-auto mb-6">
                    <div class="flex items-center justify-between mb-3">
                        <span class="text-gray-400">Amount:</span>
                        <span id="donationAmount" class="text-2xl font-bold text-green-400">$49</span>
                    </div>
                    <input type="range" id="donationSlider" min="49" max="10000" value="49" 
                           class="w-full h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer slider">
                    <div class="flex justify-between text-sm text-gray-400 mt-2">
                        <span>$49 min</span>
                        <span>$10,000 max</span>
                    </div>
                </div>
                
                <div class="flex flex-col sm:flex-row gap-4 justify-center">
                    <button onclick="donateCustom('stripe')" class="px-8 py-3 bg-gradient-to-r from-green-500 to-emerald-500 rounded-lg font-semibold text-white hover:opacity-90 transition-opacity">
                        ðŸ’³ Donate with Card
                    </button>
                    <button onclick="donateCustom('crypto')" class="px-8 py-3 bg-gradient-to-r from-orange-500 to-yellow-500 rounded-lg font-semibold text-white hover:opacity-90 transition-opacity">
                        ðŸš€ Donate with Crypto
                    </button>
                </div>
                
                <p class="text-gray-400 text-sm mt-4">
                    ðŸ™ Thank you for helping save our home and supporting innovation
                </p>
            </div>
        </div>
    </div>
</section>

    <!-- Footer -->
    <footer class="border-t border-gray-800 py-8">
        <div class="max-w-7xl mx-auto px-4 text-center text-gray-400">
            <p>&copy; 2025 Whale Tracker Pro. Built with love by Sean for his family. Every subscription helps. ðŸ™</p>
        </div>
    </footer>
// Complete JavaScript for your app.py template (replace existing script section)

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
            console.log('🚀 Subscribing to:', planType);
            
            // Show loading state
            const button = event.target;
            const originalText = button.innerHTML;
            button.innerHTML = '⏳ Processing...';
            button.disabled = true;
            
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
                button.innerHTML = originalText;
                button.disabled = false;
                return;
            }
            
            // Redirect to Stripe Checkout
            const result = await stripe.redirectToCheckout({
                sessionId: session.id
            });
            
            if (result.error) {
                alert('Payment error: ' + result.error.message);
                button.innerHTML = originalText;
                button.disabled = false;
            }
            
        } catch (error) {
            console.error('❌ Error:', error);
            alert('Payment system error. Please try again.');
            button.innerHTML = originalText;
            button.disabled = false;
        }
    }
    
    // Crowdfund one-time payments
    async function crowdfund(tierType) {
        try {
            console.log('💰 Crowdfunding tier:', tierType);
            
            // Show loading state
            const button = event.target;
            const originalText = button.innerHTML;
            button.innerHTML = '⏳ Processing...';
            button.disabled = true;
            
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
                button.innerHTML = originalText;
                button.disabled = false;
                return;
            }
            
            // Redirect to Stripe Checkout
            const result = await stripe.redirectToCheckout({
                sessionId: session.id
            });
            
            if (result.error) {
                alert('Payment error: ' + result.error.message);
                button.innerHTML = originalText;
                button.disabled = false;
            }
            
        } catch (error) {
            console.error('❌ Error:', error);
            alert('Payment system error. Please try again.');
            button.innerHTML = originalText;
            button.disabled = false;
        }
    }
    
    // Custom donation amount
    async function donateCustom(paymentMethod) {
        const amount = document.getElementById('donationSlider').value;
        
        if (paymentMethod === 'crypto') {
            // Show crypto coming soon modal
            showCryptoModal();
            return;
        }
        
        try {
            console.log('💝 Custom donation:', amount);
            
            // Show loading state
            const button = event.target;
            const originalText = button.innerHTML;
            button.innerHTML = '⏳ Processing...';
            button.disabled = true;
            
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
                button.innerHTML = originalText;
                button.disabled = false;
                return;
            }
            
            // Redirect to Stripe Checkout
            const result = await stripe.redirectToCheckout({
                sessionId: session.id
            });
            
            if (result.error) {
                alert('Payment error: ' + result.error.message);
                button.innerHTML = originalText;
                button.disabled = false;
            }
            
        } catch (error) {
            console.error('❌ Error:', error);
            alert('Payment system error. Please try again.');
            button.innerHTML = originalText;
            button.disabled = false;
        }
    }
    
    // Show crypto coming soon modal
    function showCryptoModal() {
        const modal = document.createElement('div');
        modal.className = 'fixed inset-0 bg-black/50 flex items-center justify-center z-50';
        modal.innerHTML = `
            <div class="bg-gray-900 border border-purple-500/50 rounded-xl p-8 max-w-md mx-4 text-center">
                <div class="text-6xl mb-4">🚀</div>
                <h3 class="text-2xl font-bold text-purple-400 mb-4">Crypto Payments Coming Soon!</h3>
                <p class="text-gray-300 mb-6">
                    We're adding Bitcoin, Ethereum, and other crypto payments in our next update! 
                    For now, please use card payments to help save our home.
                </p>
                <div class="flex gap-4">
                    <button onclick="this.closest('.fixed').remove()" 
                            class="px-6 py-3 bg-gray-600 hover:bg-gray-700 rounded-lg transition-colors flex-1">
                        Close
                    </button>
                    <button onclick="this.closest('.fixed').remove(); donateCustom('stripe')" 
                            class="px-6 py-3 bg-purple-600 hover:bg-purple-700 rounded-lg transition-colors flex-1">
                        Pay with Card
                    </button>
                </div>
            </div>
        `;
        document.body.appendChild(modal);
    }
    
    // Add some epic animations
    document.addEventListener('DOMContentLoaded', function() {
        // Animate progress bars
        const progressBars = document.querySelectorAll('.progress-bar');
        progressBars.forEach(bar => {
            const width = bar.style.width;
            bar.style.width = '0%';
            setTimeout(() => {
                bar.style.width = width;
                bar.style.transition = 'width 2s ease-out';
            }, 500);
        });
        
        // Add pulse animation to emergency elements
        const emergencyElements = document.querySelectorAll('.emergency-badge');
        emergencyElements.forEach(el => {
            setInterval(() => {
                el.style.transform = 'scale(1.05)';
                setTimeout(() => {
                    el.style.transform = 'scale(1)';
                }, 200);
            }, 2000);
        });
    });
</script>
</body>
</html>
    ''', stripe_publishable_key=STRIPE_PUBLISHABLE_KEY)

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
            'emergency': {'price_id': 'price_1RyapeRkVYDUbhIFwSQYNIAw', 'mode': 'subscription'},
            'enterprise': {'price_id': 'price_1Ryar9RkVYDUbhIFr4Oe7N9C', 'mode': 'subscription'},
            
            # One-time crowdfund tiers
            'house_hero': {'amount': 50000, 'mode': 'payment'},        # $500
            'family_guardian': {'amount': 150000, 'mode': 'payment'},   # $1,500
            'life_changer': {'amount': 500000, 'mode': 'payment'},      # $5,000
            'legend': {'amount': 1000000, 'mode': 'payment'},           # $10,000
            
            # Existing one-time
            'lifetime': {'price_id': 'price_1Ryat4RkVYDUbhIFxohXgOK1', 'mode': 'payment'},
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
                            'description': 'Help save our family home from foreclosure - every dollar counts!',
                            'images': ['https://whale-tracker-ai.up.railway.app/static/house-hero.png'],
                        },
                        'unit_amount': custom_amount,
                    },
                    'quantity': 1,
                }],
                mode='payment',
                success_url=f'{DOMAIN}/success?session_id={{CHECKOUT_SESSION_ID}}&type=donation',
                cancel_url=f'{DOMAIN}/?canceled=true',
                metadata={
                    'plan': 'custom_donation',
                    'type': 'donation',
                    'amount': custom_amount,
                    'source': 'whale_tracker_emergency_fund'
                }
            )
            
            logger.info(f"💰 Created donation session: ${custom_amount/100}")
            return jsonify({'id': checkout_session.id})
        
        # Handle crowdfund tiers (one-time payments with fixed amounts)
        if payment_type == 'crowdfund' and plan in ['house_hero', 'family_guardian', 'life_changer', 'legend']:
            tier_info = PRICING[plan]
            
            # Map plan names to display names and benefits
            tier_details = {
                'house_hero': {
                    'name': '💰 House Hero - Save Our Home',
                    'description': '1 year premium access + Hero badge + Help save our family home',
                    'benefits': ['1 Year Premium Access', 'Hero Badge in Dashboard', 'Monthly Progress Updates', 'Help Save Our Home']
                },
                'family_guardian': {
                    'name': '🏆 Family Guardian - Protector Status', 
                    'description': '2 years premium access + Guardian badge + 3% profit sharing + Help save our home',
                    'benefits': ['2 Years Premium Access', 'Guardian Badge + Special Features', 'Quarterly Strategy Calls', '3% Profit Sharing for Life']
                },
                'life_changer': {
                    'name': '👑 Life Changer - VIP Status',
                    'description': 'Lifetime premium access + VIP badge + 5% profit sharing + Monthly 1-on-1 calls',
                    'benefits': ['Lifetime Premium Access', 'VIP Badge + Exclusive Features', 'Monthly 1-on-1 Calls', '5% Profit Sharing for Life']
                },
                'legend': {
                    'name': '🌟 Legend Status - Ultimate Supporter',
                    'description': 'Everything + Legend badge + Advisory board + 10% profit sharing',
                    'benefits': ['Everything in Life Changer', 'Legend Badge + Co-branding', 'Advisory Board Position', '10% Profit Sharing for Life']
                }
            }
            
            tier = tier_details[plan]
            
            checkout_session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[{
                    'price_data': {
                        'currency': 'usd',
                        'product_data': {
                            'name': tier['name'],
                            'description': tier['description'],
                            'images': ['https://whale-tracker-ai.up.railway.app/static/whale-hero.png'],
                        },
                        'unit_amount': tier_info['amount'],
                    },
                    'quantity': 1,
                }],
                mode='payment',
                success_url=f'{DOMAIN}/success?session_id={{CHECKOUT_SESSION_ID}}&type=crowdfund&tier={plan}',
                cancel_url=f'{DOMAIN}/?canceled=true',
                metadata={
                    'plan': plan,
                    'type': 'crowdfund',
                    'tier': plan,
                    'user_source': 'whale_tracker_crowdfund'
                }
            )
            
            logger.info(f"🚀 Created crowdfund session for {plan}: ${tier_info['amount']/100}")
            return jsonify({'id': checkout_session.id})
        
        # Handle regular subscriptions (existing logic with enhancements)
        price_id = PRICING.get(plan, {}).get('price_id')
        mode = PRICING.get(plan, {}).get('mode', 'subscription')
        
        if not price_id:
            return jsonify({
                'error': f'Price ID not configured for plan: {plan}'
            }), 400
        
        # Create Stripe checkout session
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price': price_id,
                'quantity': 1,
            }],
            mode=mode,
            success_url=f'{DOMAIN}/success?session_id={{CHECKOUT_SESSION_ID}}&plan={plan}',
            cancel_url=f'{DOMAIN}/?canceled=true',
            metadata={
                'plan': plan,
                'type': 'subscription',
                'user_source': 'whale_tracker_domain'
            }
        )
        
        logger.info(f"💳 Created {mode} session for plan: {plan}")
        
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
    """Enhanced success page with tier recognition"""
    session_id = request.args.get('session_id')
    payment_type = request.args.get('type', 'subscription')
    tier = request.args.get('tier', 'professional')
    plan = request.args.get('plan', 'professional')
    
    # Define success messages and benefits by tier
    tier_benefits = {
        'house_hero': {
            'icon': '💰',
            'title': 'House Hero Status Unlocked!',
            'subtitle': 'You\'re helping save our family home!',
            'benefits': [
                '✅ 1 Year Premium Access Activated',
                '✅ Hero Badge Added to Your Profile',
                '✅ Monthly Progress Updates Enabled',
                '✅ You\'re Officially a House Hero!'
            ],
            'special_message': '🏠 Your contribution goes directly to saving our home from foreclosure. Thank you for being a hero!'
        },
        'family_guardian': {
            'icon': '🏆',
            'title': 'Family Guardian Status Achieved!',
            'subtitle': 'You\'re protecting our family\'s future!',
            'benefits': [
                '✅ 2 Years Premium Access Activated',
                '✅ Guardian Badge + Special Features',
                '✅ Quarterly Strategy Calls Scheduled',
                '✅ 3% Profit Sharing Activated for Life'
            ],
            'special_message': '🛡️ You\'re now a Family Guardian! Your support means everything to us.'
        },
        'life_changer': {
            'icon': '👑',
            'title': 'Life Changer VIP Status!',
            'subtitle': 'You\'ve literally changed our lives!',
            'benefits': [
                '✅ Lifetime Premium Access Activated',
                '✅ VIP Badge + Exclusive Features',
                '✅ Monthly 1-on-1 Calls Scheduled',
                '✅ 5% Profit Sharing Activated for Life'
            ],
            'special_message': '👑 You are a true LIFE CHANGER! We will never forget your kindness.'
        },
        'legend': {
            'icon': '🌟',
            'title': 'LEGEND STATUS UNLOCKED!',
            'subtitle': 'You\'re now part of Whale Tracker history!',
            'benefits': [
                '✅ Everything in Life Changer',
                '✅ Legend Badge + Co-branding Rights',
                '✅ Advisory Board Position Confirmed',
                '✅ 10% Profit Sharing Activated for Life'
            ],
            'special_message': '🌟 LEGENDARY! You\'ve secured your place in Whale Tracker history forever!'
        },
        'professional': {
            'icon': '🐋',
            'title': 'Welcome to Whale Tracker Pro!',
            'subtitle': 'Professional whale intelligence activated',
            'benefits': [
                '✅ ETH + SOL Whale Discovery',
                '✅ Reddit Community Scanning',
                '✅ Up to 100 Tracked Whales',
                '✅ Basic Alerts & Dashboard'
            ],
            'special_message': '🚀 Welcome to the whale tracking revolution!'
        },
        'emergency': {
            'icon': '🏠',
            'title': 'Thank You for Helping Save Our Home!',
            'subtitle': 'Premium access + family support',
            'benefits': [
                '✅ Unlimited Whale Tracking',
                '✅ Priority Support Access',
                '✅ All Premium Features',
                '✅ You\'re Helping Save Our Home!'
            ],
            'special_message': '🙏 Your subscription directly helps prevent our foreclosure. We\'re forever grateful!'
        },
        'custom_donation': {
            'icon': '💝',
            'title': 'Emergency Fund Donation Received!',
            'subtitle': 'Every dollar helps save our home',
            'benefits': [
                '✅ Donation Confirmed',
                '✅ Supporter Badge Earned',
                '✅ Progress Updates Enabled',
                '✅ Part of Our Rescue Mission!'
            ],
            'special_message': '🏠 Your donation goes directly to our emergency house fund. Thank you for caring!'
        }
    }
    
    # Determine which tier to show
    if payment_type == 'crowdfund':
        current_tier = tier_benefits.get(tier, tier_benefits['professional'])
    elif payment_type == 'donation':
        current_tier = tier_benefits['custom_donation']
    else:
        current_tier = tier_benefits.get(plan, tier_benefits['professional'])
    
    return render_template_string('''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ title }} - Whale Tracker Pro</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        body {
            background: linear-gradient(135deg, #1e293b 0%, #7c3aed 50%, #1e293b 100%);
            min-height: 100vh;
        }
        .celebration {
            animation: celebration 3s ease-out;
        }
        @keyframes celebration {
            0% { transform: scale(0.8); opacity: 0; }
            50% { transform: scale(1.1); }
            100% { transform: scale(1); opacity: 1; }
        }
        .bounce {
            animation: bounce 2s infinite;
        }
        @keyframes bounce {
            0%, 20%, 50%, 80%, 100% { transform: translateY(0); }
            40% { transform: translateY(-10px); }
            60% { transform: translateY(-5px); }
        }
    </style>
</head>
<body class="text-white">
    <div class="max-w-4xl mx-auto px-4 py-16">
        
        <!-- Main Success Card -->
        <div class="celebration bg-black/40 backdrop-blur-sm border border-green-500/50 rounded-xl p-8 text-center mb-8">
            <div class="text-8xl mb-6 bounce">{{ icon }}</div>
            <h1 class="text-4xl font-bold text-green-400 mb-4">{{ title }}</h1>
            <p class="text-xl text-gray-300 mb-8">{{ subtitle }}</p>
            
            <!-- Benefits List -->
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mb-8">
                {% for benefit in benefits %}
                <div class="bg-green-500/10 border border-green-500/20 rounded-lg p-4">
                    <p class="text-green-300">{{ benefit }}</p>
                </div>
                {% endfor %}
            </div>
            
            <!-- Special Message -->
            <div class="bg-gradient-to-r from-purple-500/10 to-cyan-500/10 border border-purple-500/30 rounded-lg p-6 mb-8">
                <p class="text-lg text-purple-200">{{ special_message }}</p>
            </div>
        </div>
        
        <!-- Next Steps -->
        <div class="bg-black/40 backdrop-blur-sm border border-gray-800 rounded-xl p-8 mb-8">
            <h3 class="text-2xl font-bold mb-6 text-center">🚀 What Happens Next?</h3>
            <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div class="text-center">
                    <div class="text-3xl mb-3">📧</div>
                    <h4 class="font-bold mb-2">Check Your Email</h4>
                    <p class="text-gray-400 text-sm">Confirmation and access details sent within 5 minutes</p>
                </div>
                <div class="text-center">
                    <div class="text-3xl mb-3">🔑</div>
                    <h4 class="font-bold mb-2">Dashboard Access</h4>
                    <p class="text-gray-400 text-sm">Full access activated within 24 hours</p>
                </div>
                <div class="text-center">
                    <div class="text-3xl mb-3">📊</div>
                    <h4 class="font-bold mb-2">Start Tracking</h4>
                    <p class="text-gray-400 text-sm">Begin discovering whales immediately</p>
                </div>
            </div>
        </div>
        
        <!-- Progress Update -->
        {% if payment_type == 'crowdfund' or payment_type == 'donation' %}
        <div class="bg-orange-500/10 border border-orange-500/30 rounded-xl p-6 mb-8 text-center">
            <h3 class="text-xl font-bold text-orange-400 mb-3">🏠 House Rescue Progress</h3>
            <div class="w-full bg-gray-700 rounded-full h-4 mb-4">
                <div class="bg-gradient-to-r from-green-500 to-blue-500 h-4 rounded-full" style="width: 23%"></div>
            </div>
            <div class="flex justify-between text-sm text-gray-300">
                <span>$12,847 raised</span>
                <span class="font-bold text-orange-400">Goal: $55,000</span>
            </div>
            <p class="text-orange-300 text-sm mt-2">💪 Your contribution brings us closer to saving our home!</p>
        </div>
        {% endif %}
        
        <!-- Action Buttons -->
        <div class="text-center space-y-4">
            <a href="/dashboard" class="block w-full md:w-auto md:inline-block px-8 py-4 bg-gradient-to-r from-purple-500 to-cyan-500 rounded-lg font-semibold text-white text-lg hover:opacity-90 transition-opacity">
                🐋 Access Dashboard
            </a>
            <div class="flex flex-col md:flex-row gap-4 justify-center mt-4">
                <a href="/roadmap" class="px-6 py-3 border border-gray-600 rounded-lg font-semibold text-white hover:bg-white/10 transition-colors">
                    View Development Roadmap
                </a>
                <a href="/contact" class="px-6 py-3 border border-gray-600 rounded-lg font-semibold text-white hover:bg-white/10 transition-colors">
                    Contact Support
                </a>
            </div>
        </div>
        
        <!-- Session ID for Reference -->
        <div class="text-center mt-8">
            <p class="text-sm text-gray-400">
                Transaction ID: {{ session_id }}<br>
                Keep this for your records
            </p>
        </div>
    </div>
    
    <!-- Auto-redirect to dashboard after 30 seconds -->
    <script>
        // Celebration confetti effect
        setTimeout(() => {
            // You can add a confetti library here for extra celebration
            console.log('🎉 Welcome to Whale Tracker Pro! 🎉');
        }, 1000);
        
        // Optional auto-redirect (uncomment if desired)
        // setTimeout(() => {
        //     window.location.href = '/dashboard';
        // }, 30000);
    </script>
</body>
</html>
    ''', 
    title=current_tier['title'],
    icon=current_tier['icon'],
    subtitle=current_tier['subtitle'],
    benefits=current_tier['benefits'],
    special_message=current_tier['special_message'],
    session_id=session_id,
    payment_type=payment_type
    )

# FIXED DASHBOARD ROUTES
import React, { useState, useEffect } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar, PieChart, Pie, Cell } from 'recharts';

const WhaleDashboard = () => {
  const [whaleData, setWhaleData] = useState([]);
  const [totalVolume, setTotalVolume] = useState(0);
  const [activeWhales, setActiveWhales] = useState(0);
  const [topTokens, setTopTokens] = useState([]);
  const [recentTransactions, setRecentTransactions] = useState([]);
  const [loading, setLoading] = useState(true);

  // Simulate real whale data
  useEffect(() => {
    const generateWhaleData = () => {
      const tokens = ['ETH', 'PEPE', 'SHIB', 'DOGE', 'BTC', 'SOL', 'MATIC', 'LINK'];
      const whaleAddresses = [
        '0x123...abc',
        '0x456...def', 
        '0x789...ghi',
        '0xabc...123',
        '0xdef...456'
      ];

      // Generate recent transactions
      const transactions = [];
      for (let i = 0; i < 15; i++) {
        const token = tokens[Math.floor(Math.random() * tokens.length)];
        const amount = (Math.random() * 5000000 + 100000);
        const address = whaleAddresses[Math.floor(Math.random() * whaleAddresses.length)];
        
        transactions.push({
          id: i,
          token,
          amount: amount,
          address,
          type: Math.random() > 0.5 ? 'BUY' : 'SELL',
          time: new Date(Date.now() - Math.random() * 3600000).toLocaleTimeString(),
          price: Math.random() > 0.7 ? 'PUMP' : Math.random() > 0.4 ? 'DUMP' : 'STABLE'
        });
      }

      // Generate volume data for chart
      const volumeData = [];
      for (let i = 0; i < 24; i++) {
        volumeData.push({
          hour: `${i}:00`,
          volume: Math.random() * 10000000 + 1000000,
          transactions: Math.floor(Math.random() * 50 + 10)
        });
      }

      // Generate top tokens data
      const tokenData = tokens.slice(0, 6).map(token => ({
        token,
        volume: Math.random() * 50000000 + 5000000,
        whales: Math.floor(Math.random() * 20 + 5),
        change: (Math.random() - 0.5) * 200
      }));

      setRecentTransactions(transactions);
      setWhaleData(volumeData);
      setTopTokens(tokenData);
      setTotalVolume(transactions.reduce((sum, tx) => sum + tx.amount, 0));
      setActiveWhales(47);
      setLoading(false);
    };

    generateWhaleData();
    
    // Update data every 10 seconds to simulate real-time
    const interval = setInterval(generateWhaleData, 10000);
    return () => clearInterval(interval);
  }, []);

  const COLORS = ['#10b981', '#3b82f6', '#8b5cf6', '#f59e0b', '#ef4444', '#06b6d4'];

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 flex items-center justify-center">
        <div className="text-center">
          <div className="text-6xl mb-4 animate-bounce">WHALE</div>
          <div className="text-2xl font-bold text-white mb-2">Hunting for Whales...</div>
          <div className="text-gray-400">Scanning blockchain for massive movements</div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 text-white p-6">
      
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div className="flex items-center space-x-4">
          <div className="text-4xl">WHALE</div>
          <div>
            <h1 className="text-3xl font-bold">Whale Tracker Pro</h1>
            <p className="text-gray-400">Live Whale Intelligence Dashboard</p>
          </div>
        </div>
        
        <div className="flex items-center space-x-4">
          <div className="bg-green-500/20 px-4 py-2 rounded-full border border-green-500/50">
            <span className="text-green-400 font-bold">LIVE</span>
          </div>
          <div className="bg-orange-500/20 px-4 py-2 rounded-full border border-orange-500/50">
            <span className="text-orange-400 font-bold">HOME< 8 Days Left</span>
          </div>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
        <div className="bg-black/40 backdrop-blur-sm border border-green-500/50 rounded-xl p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-400 text-sm">Active Whales</p>
              <p className="text-3xl font-bold text-green-400">{activeWhales}</p>
            </div>
            <div className="text-3xl">WHALE</div>
          </div>
          <p className="text-gray-400 text-xs mt-2">+8 new this hour</p>
        </div>

        <div className="bg-black/40 backdrop-blur-sm border border-blue-500/50 rounded-xl p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-400 text-sm">24h Volume</p>
              <p className="text-3xl font-bold text-blue-400">${(totalVolume/1000000).toFixed(1)}M</p>
            </div>
            <div className="text-3xl">HOME</div>
          </div>
          <p className="text-gray-400 text-xs mt-2">+23% from yesterday</p>
        </div>

        <div className="bg-black/40 backdrop-blur-sm border border-purple-500/50 rounded-xl p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-400 text-sm">Alerts Sent</p>
              <p className="text-3xl font-bold text-purple-400">1,247</p>
            </div>
            <div className="text-3xl">ALERT</div>
          </div>
          <p className="text-gray-400 text-xs mt-2">Last alert: 2 min ago</p>
        </div>

        <div className="bg-black/40 backdrop-blur-sm border border-orange-500/50 rounded-xl p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-400 text-sm">House Fund</p>
              <p className="text-3xl font-bold text-orange-400">$12,847</p>
            </div>
            <div className="text-3xl">HOME</div>
          </div>
          <div className="w-full bg-gray-700 rounded-full h-2 mt-2">
            <div className="bg-gradient-to-r from-orange-500 to-red-500 h-2 rounded-full" style={{width: '23%'}}></div>
          </div>
        </div>
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        
        {/* Volume Chart */}
        <div className="bg-black/40 backdrop-blur-sm border border-gray-800 rounded-xl p-6">
          <h3 className="text-xl font-bold mb-4">24h Whale Volume</h3>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={whaleData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
              <XAxis dataKey="hour" stroke="#9ca3af" />
              <YAxis stroke="#9ca3af" tickFormatter={(value) => `$${(value/1000000).toFixed(1)}M`} />
              <Tooltip 
                contentStyle={{ 
                  backgroundColor: '#1f2937', 
                  border: '1px solid #374151',
                  borderRadius: '8px'
                }}
                formatter={(value) => [`$${(value/1000000).toFixed(2)}M`, 'Volume']}
              />
              <Line 
                type="monotone" 
                dataKey="volume" 
                stroke="#10b981" 
                strokeWidth={3}
                dot={{ fill: '#10b981', strokeWidth: 2, r: 4 }}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* Top Tokens */}
        <div className="bg-black/40 backdrop-blur-sm border border-gray-800 rounded-xl p-6">
          <h3 className="text-xl font-bold mb-4">Top Whale Tokens</h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={topTokens}>
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
              <XAxis dataKey="token" stroke="#9ca3af" />
              <YAxis stroke="#9ca3af" tickFormatter={(value) => `$${(value/1000000).toFixed(0)}M`} />
              <Tooltip 
                contentStyle={{ 
                  backgroundColor: '#1f2937', 
                  border: '1px solid #374151',
                  borderRadius: '8px'
                }}
                formatter={(value) => [`$${(value/1000000).toFixed(2)}M`, 'Volume']}
              />
              <Bar dataKey="volume" fill="#3b82f6" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Recent Transactions */}
      <div className="bg-black/40 backdrop-blur-sm border border-gray-800 rounded-xl p-6">
        <div className="flex items-center justify-between mb-6">
          <h3 className="text-xl font-bold">🚨 Live Whale Transactions</h3>
          <div className="flex items-center space-x-2">
            <div className="w-3 h-3 bg-green-500 rounded-full animate-pulse"></div>
            <span className="text-green-400 text-sm font-bold">LIVE</span>
          </div>
        </div>
        
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-gray-700">
                <th className="text-left py-3 text-gray-400">Time</th>
                <th className="text-left py-3 text-gray-400">Token</th>
                <th className="text-left py-3 text-gray-400">Amount</th>
                <th className="text-left py-3 text-gray-400">Type</th>
                <th className="text-left py-3 text-gray-400">Whale</th>
                <th className="text-left py-3 text-gray-400">Impact</th>
                <th className="text-left py-3 text-gray-400">Action</th>
              </tr>
            </thead>
            <tbody>
              {recentTransactions.map((tx) => (
                <tr key={tx.id} className="border-b border-gray-800 hover:bg-gray-800/50">
                  <td className="py-3 text-gray-300">{tx.time}</td>
                  <td className="py-3">
                    <span className="font-bold text-white">{tx.token}</span>
                  </td>
                  <td className="py-3 font-bold text-cyan-400">
                    ${(tx.amount/1000000).toFixed(2)}M
                  </td>
                  <td className="py-3">
                    <span className={`px-2 py-1 rounded text-xs font-bold ${
                      tx.type === 'BUY' ? 'bg-green-500/20 text-green-400' : 'bg-red-500/20 text-red-400'
                    }`}>
                      {tx.type}
                    </span>
                  </td>
                  <td className="py-3 text-gray-400 font-mono text-sm">{tx.address}</td>
                  <td className="py-3">
                    <span className={`px-2 py-1 rounded text-xs font-bold ${
                      tx.price === 'PUMP' ? 'bg-green-500/20 text-green-400' : 
                      tx.price === 'DUMP' ? 'bg-red-500/20 text-red-400' : 
                      'bg-gray-500/20 text-gray-400'
                    }`}>
                      {tx.price}
                    </span>
                  </td>
                  <td className="py-3">
                    <button className="px-3 py-1 bg-purple-600 hover:bg-purple-700 rounded text-xs font-bold transition-colors">
                      📋 Copy
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Bottom Banner */}
      <div className="mt-8 bg-gradient-to-r from-red-500/10 to-orange-500/10 border border-red-500/30 rounded-xl p-6 text-center">
        <h3 className="text-2xl font-bold text-red-400 mb-2">ALERT< URGENT: Help Save Our Home!</h3>
        <p className="text-gray-300 mb-4">
          House auction in 8 days. Every subscription helps save our special needs son's home.
        </p>
        <div className="flex items-center justify-center space-x-4">
          <button className="px-6 py-3 bg-gradient-to-r from-green-500 to-emerald-500 rounded-lg font-bold hover:opacity-90 transition-opacity">
            🏠 Help Save Our Home - $199/month
          </button>
          <button className="px-6 py-3 bg-gradient-to-r from-blue-500 to-cyan-500 rounded-lg font-bold hover:opacity-90 transition-opacity">
            🐋 Professional - $49/month
          </button>
        </div>
      </div>
    </div>
  );
};

export default WhaleDashboard;

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
            logger.info(f"âœ… Payment completed for session: {session['id']}")
            
            # TODO: Grant user access to dashboard
            # TODO: Send welcome email
            # TODO: Update user database
            
        elif event['type'] == 'invoice.payment_succeeded':
            invoice = event['data']['object']
            logger.info(f"âœ… Invoice payment succeeded: {invoice['id']}")
            
        elif event['type'] == 'customer.subscription.deleted':
            subscription = event['data']['object']
            logger.info(f"âŒ Subscription canceled: {subscription['id']}")
                      
            # TODO: Revoke user access
            
        return jsonify({'status': 'success'})
        
    except ValueError as e:
        logger.error(f"âŒ Invalid payload: {e}")
        return jsonify({'error': 'Invalid payload'}), 400
    except stripe.error.SignatureVerificationError as e:
        logger.error(f"âŒ Invalid signature: {e}")
        return jsonify({'error': 'Invalid signature'}), 400

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
                <h3 class="text-2xl font-bold text-red-400 mb-2">ðŸ  Urgent Family Situation</h3>
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
                    <h3 class="text-2xl font-bold mb-6 text-purple-400">ðŸ’¼ Business Inquiries</h3>
                    
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
                    <h3 class="text-2xl font-bold mb-6 text-cyan-400">ðŸŒ Community</h3>
                    
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
                <h3 class="text-2xl font-bold mb-4">âš¡ Response Times</h3>
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
            <p>&copy; 2025 Whale Tracker Pro. Community-funded innovation. ðŸ‹</p>
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
                    <li>â€¢ Subscriptions are billed monthly unless otherwise specified</li>
                    <li>â€¢ Lifetime subscriptions are one-time payments with perpetual access</li>
                    <li>â€¢ Price locks guarantee your rate won't increase during active subscription</li>
                    <li>â€¢ All payments are processed securely through Stripe</li>
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
                    <p class="text-yellow-200 font-bold">âš ï¸ IMPORTANT: NOT FINANCIAL ADVICE</p>
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
                    <li>â€¢ We collect minimal personal information (email, payment data)</li>
                    <li>â€¢ Blockchain data used is publicly available</li>
                    <li>â€¢ We never store private keys or sensitive wallet information</li>
                    <li>â€¢ Data is encrypted and secured with industry standards</li>
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
                    <li>â€¢ <strong>Account Information:</strong> Email address for account creation</li>
                    <li>â€¢ <strong>Payment Information:</strong> Processed securely by Stripe (we don't store card details)</li>
                    <li>â€¢ <strong>Usage Data:</strong> How you interact with our platform</li>
                    <li>â€¢ <strong>Technical Data:</strong> IP address, browser type, device information</li>
                </ul>
            </section>

            <section>
                <h2 class="text-2xl font-bold text-cyan-400 mb-4">How We Use Your Information</h2>
                <ul class="text-gray-300 space-y-2">
                    <li>â€¢ Provide and improve our whale tracking services</li>
                    <li>â€¢ Process payments and manage subscriptions</li>
                    <li>â€¢ Send important updates about your account</li>
                    <li>â€¢ Communicate development progress and new features</li>
                    <li>â€¢ Ensure platform security and prevent fraud</li>
                </ul>
            </section>

            <section>
                <h2 class="text-2xl font-bold text-cyan-400 mb-4">Data Security</h2>
                <div class="bg-green-500/10 border border-green-500/30 rounded-lg p-4">
                    <p class="text-green-200 font-bold">ðŸ”’ Your Security is Our Priority</p>
                    <ul class="text-gray-300 mt-2 space-y-1">
                        <li>â€¢ All data encrypted in transit and at rest</li>
                        <li>â€¢ We never store private keys or wallet passwords</li>
                        <li>â€¢ Regular security audits and monitoring</li>
                        <li>â€¢ Secure cloud infrastructure with redundancy</li>
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
                    <li>â€¢ <strong>Stripe:</strong> Payment processing (has their own privacy policy)</li>
                    <li>â€¢ <strong>Railway:</strong> Hosting infrastructure</li>
                    <li>â€¢ <strong>Blockchain APIs:</strong> For accessing public blockchain data</li>
                </ul>
            </section>

            <section>
                <h2 class="text-2xl font-bold text-cyan-400 mb-4">Your Rights</h2>
                <ul class="text-gray-300 space-y-2">
                    <li>â€¢ Request access to your personal data</li>
                    <li>â€¢ Request correction of inaccurate data</li>
                    <li>â€¢ Request deletion of your account and data</li>
                    <li>â€¢ Opt out of marketing communications</li>
                    <li>â€¢ Data portability for your information</li>
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
                <h3 class="text-xl font-bold text-orange-400 mb-3">ðŸ  Special Circumstances</h3>
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
                        <span class="text-green-400 mt-1">â€¢</span>
                        <span><strong>7-Day Money-Back Guarantee:</strong> Full refund if cancelled within 7 days of first subscription</span>
                    </li>
                    <li class="flex items-start space-x-2">
                        <span class="text-green-400 mt-1">â€¢</span>
                        <span><strong>Prorated Refunds:</strong> Available for service interruptions lasting more than 48 hours</span>
                    </li>
                    <li class="flex items-start space-x-2">
                        <span class="text-green-400 mt-1">â€¢</span>
                        <span><strong>Cancel Anytime:</strong> No refund for current billing period, but access continues until period ends</span>
                    </li>
                </ul>
            </section>

            <section>
                <h2 class="text-2xl font-bold text-yellow-400 mb-4">Lifetime Subscriptions</h2>
                <div class="bg-yellow-500/10 border border-yellow-500/30 rounded-lg p-4">
                    <p class="text-yellow-200 font-bold mb-2">âš ï¸ Important: Limited Refund Policy</p>
                    <ul class="text-gray-300 space-y-2">
                        <li>â€¢ <strong>72-Hour Window:</strong> Full refund available within 72 hours of purchase</li>
                        <li>â€¢ <strong>After 72 Hours:</strong> No refunds available due to immediate access to services</li>
                        <li>â€¢ <strong>Service Issues:</strong> Account credits or extensions for technical problems</li>
                        <li>â€¢ <strong>Emergency Exception:</strong> Case-by-case review for extreme circumstances</li>
                    </ul>
                </div>
            </section>

            <section>
                <h2 class="text-2xl font-bold text-blue-400 mb-4">Beta Access Refunds</h2>
                <p class="text-gray-300">
                    As we're currently in beta development, we understand some features may not meet expectations:
                </p>
                <ul class="text-gray-300 space-y-2 mt-3">
                    <li>â€¢ Refunds available if core promised features are not delivered within 30 days</li>
                    <li>â€¢ Bug-related issues will be resolved or account credited</li>
                    <li>â€¢ Development delays may qualify for partial refunds or account extensions</li>
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
                    <li>â€¢ Violation of Terms of Service</li>
                    <li>â€¢ Abuse of platform or community guidelines</li>
                    <li>â€¢ Requests made after applicable refund windows</li>
                    <li>â€¢ Normal market volatility affecting trading decisions</li>
                    <li>â€¢ Personal financial circumstances unrelated to our service</li>
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
                    <p class="text-blue-400">ðŸ“§ <a href="mailto:refunds@whale-tracker.pro" class="hover:text-blue-300">refunds@whale-tracker.pro</a></p>
                    <p class="text-green-400">ðŸ“§ <a href="mailto:support@whale-tracker.pro" class="hover:text-green-300">support@whale-tracker.pro</a></p>
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
                    <h3 class="text-xl font-bold">ðŸŽ¯ Current Progress</h3>
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
                    âœ… Payment system live &nbsp;â€¢&nbsp; âœ… Basic dashboard &nbsp;â€¢&nbsp; âœ… Stripe integration
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
                            <h4 class="font-bold text-white mb-3">ðŸš€ Performance Upgrades</h4>
                            <ul class="space-y-2 text-gray-300">
                                <li>â€¢ Enterprise-grade servers (99.9% uptime)</li>
                                <li>â€¢ Advanced API architecture with gRPC</li>
                                <li>â€¢ Sub-second real-time data streams</li>
                                <li>â€¢ Enhanced whale discovery algorithms</li>
                            </ul>
                        </div>
                        <div>
                            <h4 class="font-bold text-white mb-3">ðŸŒ Multi-Network Expansion</h4>
                            <ul class="space-y-2 text-gray-300">
                                <li>â€¢ Polygon integration</li>
                                <li>â€¢ Arbitrum whale tracking</li>
                                <li>â€¢ Binance Smart Chain support</li>
                                <li>â€¢ Avalanche network monitoring</li>
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
                        <h4 class="font-bold text-blue-400 mb-2">ðŸ¤– World's First Web3 Adaptive Trading AI</h4>
                        <p class="text-gray-300">Revolutionary AI that learns YOUR trading style and adapts its strategy accordingly.</p>
                    </div>
                    
                    <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
                        <div>
                            <h4 class="font-bold text-white mb-3">ðŸŽ¯ Three Modes</h4>
                            <ul class="space-y-2 text-gray-300 text-sm">
                                <li>â€¢ Full automation</li>
                                <li>â€¢ Guided assistance</li>
                                <li>â€¢ Advisory-only</li>
                            </ul>
                        </div>
                        <div>
                            <h4 class="font-bold text-white mb-3">ðŸ”’ Security</h4>
                            <ul class="space-y-2 text-gray-300 text-sm">
                                <li>â€¢ Military-grade encryption</li>
                                <li>â€¢ Zero-knowledge architecture</li>
                                <li>â€¢ Privacy-first design</li>
                            </ul>
                        </div>
                        <div>
                            <h4 class="font-bold text-white mb-3">âš¡ Features</h4>
                            <ul class="space-y-2 text-gray-300 text-sm">
                                <li>â€¢ 1.5% transaction sniping</li>
                                <li>â€¢ Risk management</li>
                                <li>â€¢ Custom safety limits</li>
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
                            <h4 class="font-bold text-white mb-3">ðŸ“± Mobile Apps</h4>
                            <ul class="space-y-2 text-gray-300">
                                <li>â€¢ Native iOS & Android apps</li>
                                <li>â€¢ Real-time push notifications</li>
                                <li>â€¢ Offline mode for essential features</li>
                                <li>â€¢ Advanced mobile charting</li>
                            </ul>
                        </div>
                        <div>
                            <h4 class="font-bold text-white mb-3">ðŸ’» Desktop Apps</h4>
                            <ul class="space-y-2 text-gray-300">
                                <li>â€¢ Cross-platform (Windows, macOS, Linux)</li>
                                <li>â€¢ Unified experience across devices</li>
                                <li>â€¢ Professional-grade analytics</li>
                                <li>â€¢ Portfolio management suite</li>
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
                            <h4 class="font-bold text-white mb-3">ðŸ¢ Enterprise Solutions</h4>
                            <ul class="space-y-2 text-gray-300">
                                <li>â€¢ Dedicated enterprise servers</li>
                                <li>â€¢ Corporate licensing program</li>
                                <li>â€¢ White-label solutions</li>
                                <li>â€¢ Custom integrations</li>
                            </ul>
                        </div>
                        <div>
                            <h4 class="font-bold text-white mb-3">âš–ï¸ Regulatory Compliance</h4>
                            <ul class="space-y-2 text-gray-300">
                                <li>â€¢ SEC registration process</li>
                                <li>â€¢ Integrated trading platform</li>
                                <li>â€¢ Full brokerage features</li>
                                <li>â€¢ Institutional-grade security</li>
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
                <h2 class="text-4xl font-bold mb-4">ðŸŽ Investor Benefits</h2>
                <p class="text-gray-400 text-lg">Early supporters get exclusive rewards</p>
            </div>
            
            <div class="grid grid-cols-1 md:grid-cols-2 gap-8">
                
                <!-- Early Supporters -->
                <div class="bg-black/40 backdrop-blur-sm border border-cyan-500/50 rounded-xl p-8">
                    <h3 class="text-2xl font-bold text-cyan-400 mb-6">ðŸŒŸ Early Supporters (All Subscribers)</h3>
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
                    <h3 class="text-2xl font-bold text-yellow-400 mb-6">ðŸ‘‘ Major Contributors ($50K+ Annual)</h3>
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
                    ðŸš€ Start Your Subscription
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
            <p>&copy; 2025 Whale Tracker Pro. Community-funded innovation for the crypto revolution. ðŸ‹</p>
        </div>
    </footer>
</body>
</html>
    ''')


if __name__ == '__main__':
    if not stripe.api_key:
        logger.error("âŒ STRIPE_SECRET_KEY not found in environment variables")
        exit(1)
    
    logger.info("ðŸš€ Starting Whale Tracker Payment Server...")
    logger.info(f"ðŸ’³ Stripe configured: {stripe.api_key[:8]}...")
    
    port = int(os.getenv('PORT', 8000))
    app.run(debug=True, host='0.0.0.0', port=port)

