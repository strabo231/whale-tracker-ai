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
    try:
        return render_template_string('''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Whale Tracker Pro - Get Access</title>
    <script src="https://js.stripe.com/v3/"></script>
    <script src="https://cdn.tailwindcss.com"></script>
    <script>
        tailwind.config = {
            theme: {
                extend: {
                    colors: {
                        'green-400': '#4ade80',
                        'blue-400': '#60a5fa', 
                        'purple-400': '#a78bfa',
                        'orange-400': '#fb923c',
                        'red-400': '#f87171'
                    }
                }
            }
        }
    </script>
    <style>
        body {
            background: linear-gradient(135deg, #1e293b 0%, #7c3aed 50%, #1e293b 100%);
            min-height: 100vh;
            color: white;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        }
        .tier-card {
            transition: transform 0.3s ease, box-shadow 0.3s ease;
            background: rgba(0, 0, 0, 0.4);
            backdrop-filter: blur(8px);
            border-radius: 12px;
            padding: 2rem;
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
        .text-green-400 { color: #4ade80; }
        .text-blue-400 { color: #60a5fa; }
        .text-purple-400 { color: #a78bfa; }
        .text-orange-400 { color: #fb923c; }
        .text-red-400 { color: #f87171; }
        .text-yellow-400 { color: #facc15; }
        .text-cyan-400 { color: #22d3ee; }
        .bg-green-500 { background-color: #22c55e; }
        .bg-blue-500 { background-color: #3b82f6; }
        .bg-purple-500 { background-color: #8b5cf6; }
        .bg-red-500 { background-color: #ef4444; }
        .border-green-500 { border-color: #22c55e; }
        .border-blue-500 { border-color: #3b82f6; }
        .border-purple-500 { border-color: #8b5cf6; }
        .border-orange-500 { border-color: #f97316; }
        .border-red-500 { border-color: #ef4444; }
        .border-yellow-500 { border-color: #eab308; }
    </style>
</head>
<body class="text-white">
    <!-- Emergency Banner -->
    <div class="bg-red-600 text-white text-center py-2 text-sm font-bold">
        URGENT: House scheduled for auction Sept 2nd - Every subscription helps save our home
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
                ⚠️ 8 DAYS LEFT - HELP SAVE OUR HOME
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
            <h2 class="text-4xl font-bold mb-4">💳 Monthly Subscriptions</h2>
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
                    <li class="flex items-center" style="color: #4ade80;">
                        <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/>
                        </svg>
                        ETH + SOL whale discovery
                    </li>
                    <li class="flex items-center" style="color: #4ade80;">
                        <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/>
                        </svg>
                        Reddit community scanning
                    </li>
                    <li class="flex items-center" style="color: #4ade80;">
                        <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/>
                        </svg>
                        Up to 100 tracked whales
                    </li>
                    <li class="flex items-center" style="color: #4ade80;">
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
                        🏠 HELP SAVE HOME
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
                <h2 class="text-5xl font-bold mb-4">🚀 Crowdfund Our Mission</h2>
                <p class="text-xl text-gray-300 mb-6">One-time contributions to save our home + build the future</p>
                <div class="inline-flex items-center px-6 py-3 bg-red-500/20 border border-red-500/50 rounded-full text-red-300 font-bold">
                    ⚠️ URGENT: Auction September 2nd - 8 Days Left
                </div>
            </div>
            
            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-12">
                
                <!-- House Hero -->
                <div class="tier-card bg-black/40 backdrop-blur-sm border border-green-500/50 rounded-xl p-6">
                    <div class="text-center mb-6">
                        <div class="text-4xl mb-3">🏠</div>
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
                        🏠 Be a House Hero
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
                        <div class="text-4xl mb-3">🛡️</div>
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
                        🛡️ Become a Guardian
                    </button>
                </div>

                <!-- Life Changer -->
                <div class="tier-card bg-black/40 backdrop-blur-sm border border-purple-500/50 rounded-xl p-6">
                    <div class="text-center mb-6">
                        <div class="text-4xl mb-3">👑</div>
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
                        👑 Change Our Lives
                    </button>
                </div>

                <!-- Legend Status -->
                <div class="tier-card bg-black/40 backdrop-blur-sm border border-yellow-500/50 rounded-xl p-6">
                    <div class="text-center mb-6">
                        <div class="text-4xl mb-3">🌟</div>
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
                        🌟 Become a Legend
                    </button>
                </div>
            </div>

            <!-- Pay What You Want Section -->
            <div class="bg-gradient-to-r from-red-500/10 to-orange-500/10 border border-red-500/20 rounded-xl p-8 text-center">
                <h3 class="text-3xl font-bold text-red-400 mb-4">🏠 Emergency House Fund</h3>
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
                        💳 Donate with Card
                    </button>
                    <button onclick="donateCustom('crypto')" class="px-8 py-3 bg-gradient-to-r from-orange-500 to-yellow-500 rounded-lg font-semibold text-white hover:opacity-90 transition-opacity">
                        🚀 Donate with Crypto
                    </button>
                </div>
                
                <p class="text-gray-400 text-sm mt-4">
                    ❤️ Thank you for helping save our home and supporting innovation
                </p>
            </div>
        </div>
    </div>
</section>

    <!-- Footer -->
    <footer class="border-t border-gray-800 py-8">
        <div class="max-w-7xl mx-auto px-4 text-center text-gray-400">
            <p>&copy; 2025 Whale Tracker Pro. Built with love by Sean for his family. Every subscription helps. ❤️</p>
        </div>
    </footer>

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
    
    // Monthly subscription function
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
    except Exception as e:
        logger.error(f"❌ Error rendering home page: {e}")
        return f"Error loading page: {e}", 500

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
            # Monthly subscriptions - Updated price IDs from your enhanced file
            'professional': {'price_id': 'price_1RyKygRkVYDUbhIFgs8JUTTR', 'mode': 'subscription'},
            'emergency': {'price_id': 'price_1RyJOzDfwP4gynpjh4mO6b6B', 'mode': 'subscription'},  # Updated
            'enterprise': {'price_id': 'price_1RyJR4DfwP4gynpj3sURTxuU', 'mode': 'subscription'},  # Updated
            
            # One-time crowdfund tiers
            'house_hero': {'amount': 50000, 'mode': 'payment'},        # $500
            'family_guardian': {'amount': 150000, 'mode': 'payment'},   # $1,500
            'life_changer': {'amount': 500000, 'mode': 'payment'},      # $5,000
            'legend': {'amount': 1000000, 'mode': 'payment'},           # $10,000
            
            # Existing one-time - Updated price ID
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
                    'name': '🏠 House Hero - Save Our Home',
                    'description': '1 year premium access + Hero badge + Help save our family home from foreclosure',
                    'benefits': ['1 Year Premium Access', 'Hero Badge in Dashboard', 'Monthly Progress Updates', 'Help Save Our Home']
                },
                'family_guardian': {
                    'name': '🛡️ Family Guardian - Protector Status', 
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
                    'description': 'Everything + Legend badge + Advisory board + 10% profit sharing for life',
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
        
        # Handle regular subscriptions
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
            'icon': '🏠',
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
            'icon': '🛡️',
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
                    <div class="text-3xl mb-3">🔒</div>
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
    
    <script>
        setTimeout(() => {
            console.log('🎉 Welcome to Whale Tracker Pro! 🎉');
        }, 1000);
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
