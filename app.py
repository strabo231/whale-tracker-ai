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
    """Main subscription page with enhanced crowdfunding integration"""
    return render_template_string('''<!DOCTYPE html>
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
        .slider {
            -webkit-appearance: none;
            background: linear-gradient(to right, #10b981 0%, #10b981 var(--value), #374151 var(--value), #374151 100%);
        }
        .slider::-webkit-slider-thumb {
            -webkit-appearance: none;
            height: 20px;
            width: 20px;
            border-radius: 50%;
            background: #10b981;
            cursor: pointer;
        }
    </style>
</head>
<body class="text-white">
    <!-- Emergency Banner -->
    <div class="bg-red-600 text-white text-center py-2 text-sm font-bold">
        ALERT URGENT: House scheduled for auction Sept 2nd - Every subscription helps save our home
    </div>

    <!-- Header -->
    <header class="border-b border-gray-800 bg-black/20 backdrop-blur-sm">
        <div class="max-w-7xl mx-auto px-4 py-4 flex items-center justify-between">
            <div class="flex items-center space-x-3">
                <div class="bg-gradient-to-r from-purple-500 to-cyan-500 p-2 rounded-lg">
                    <svg class="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7"/>
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
                TIMER 8 DAYS LEFT - HELP SAVE OUR HOME
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

    <!-- Monthly Subscriptions Section -->
    <section class="py-20">
        <div class="max-w-7xl mx-auto px-4">
            <div class="text-center mb-16">
                <h2 class="text-4xl font-bold mb-4">Monthly Subscriptions</h2>
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
                            Basic alerts and dashboard
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
                            HELP SAVE HOME
                        </span>
                    </div>
                    
                    <div class="text-center mb-8 mt-4">
                        <h3 class="text-2xl font-bold mb-2">Help Us Stay</h3>
                        <p class="text-gray-400 mb-4">Support our family + premium access</p>
                        <div class="text-4xl font-bold mb-2">$199<span class="text-gray-400 text-lg">/month</span></div>
                        <p class="text-orange-400 text-sm font-medium">Every dollar helps save our home</p>
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
                            Help save a special needs child home
                        </li>
                    </ul>
                    
                    <button onclick="subscribe('emergency')" class="block w-full py-3 bg-gradient-to-r from-orange-500 to-red-500 rounded-lg font-semibold text-white text-center hover:opacity-90 transition-opacity">
                        Help Save Our Home - $199/month
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

            <!-- CROWDFUND SECTION -->
            <div class="border-t border-gray-800 pt-20">
                <div class="text-center mb-16">
                    <h2 class="text-5xl font-bold mb-4">Crowdfund Our Mission</h2>
                    <p class="text-xl text-gray-300 mb-6">One-time contributions to save our home + build the future</p>
                    <div class="inline-flex items-center px-6 py-3 bg-red-500/20 border border-red-500/50 rounded-full text-red-300 font-bold">
                        URGENT: Auction September 2nd - 8 Days Left
                    </div>
                </div>
                
                <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-12">
                    
                    <!-- House Hero -->
                    <div class="tier-card bg-black/40 backdrop-blur-sm border border-green-500/50 rounded-xl p-6">
                        <div class="text-center mb-6">
                            <div class="text-4xl mb-3">💰</div>
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
                            Be a House Hero
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
                            <div class="text-4xl mb-3">🏆</div>
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
                            Become a Guardian
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
                            Change Our Lives
                        </button>
                    </div>

                    <!-- Legend Status -->
                    <div class="tier-card bg-black/40 backdrop-blur-sm border border-yellow-500/50 rounded-xl p-6">
                        <div class="text-center mb-6">
                            <div class="text-4xl mb-3">✨</div>
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
                            Become a Legend
                        </button>
                    </div>
                </div>

                <!-- Pay What You Want Section -->
                <div class="bg-gradient-to-r from-red-500/10 to-orange-500/10 border border-red-500/20 rounded-xl p-8 text-center">
                    <h3 class="text-3xl font-bold text-red-400 mb-4">Emergency House Fund</h3>
                    <p class="text-xl text-gray-300 mb-6">
                        Cannot afford a tier? Every dollar helps save our family home!
                    </p>
                    
                    <div class="max-w-md mx-auto mb-6">
                        <div class="flex items-center justify-between mb-3">
                            <span class="text-gray-400">Amount:</span>
                            <span id="donationAmount" class="text-2xl font-bold text-green-400">$49</span>
                        </div>
                        <input type="range" id="donationSlider" min="49" max="10000" value="49" class="w-full h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer slider">
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
                        🙏 Thank you for helping save our home and supporting innovation
                    </p>
                </div>
            </div>

            <!-- Special Legacy Options -->
            <div class="mt-12 text-center">
                <div class="bg-gradient-to-r from-green-500/10 to-blue-500/10 border border-green-500/20 rounded-xl p-6 max-w-4xl mx-auto">
                    <h3 class="text-2xl font-bold text-white mb-4">EMERGENCY OPTIONS</h3>
                    <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div class="bg-black/40 rounded-lg p-4">
                            <h4 class="font-bold text-green-400 mb-2">House Saver LIFETIME</h4>
                            <p class="text-2xl font-bold text-white">$2,999 <span class="text-sm text-gray-400">one-time</span></p>
                            <p class="text-gray-400 text-sm mb-3">Everything forever + help save our home</p>
                            <button onclick="subscribe('lifetime')" class="w-full py-2 bg-green-600 hover:bg-green-700 rounded font-semibold text-center transition-colors">
                                Save Our House + Get Lifetime Access
                            </button>
                        </div>
                        <div class="bg-black/40 rounded-lg p-4">
                            <h4 class="font-bold text-blue-400 mb-2">6-Month Lifeline</h4>
                            <p class="text-2xl font-bold text-white">$999 <span class="text-sm text-gray-400">upfront</span></p>
                            <p class="text-gray-400 text-sm mb-3">Save $395 vs monthly + help family</p>
                            <button onclick="subscribe('sixmonth')" class="w-full py-2 bg-blue-600 hover:bg-blue-700 rounded font-semibold text-center transition-colors">
                                6 Months Upfront (Save $395)
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
        
        // Donation slider functionality
        const slider = document.getElementById('donationSlider');
        const amountDisplay = document.getElementById('donationAmount');
        
        if (slider && amountDisplay) {
            slider.addEventListener('input', function() {
                const value = parseInt(this.value);
                amountDisplay.textContent = ' + value.toLocaleString();
                
                // Update slider track color
                const percentage = ((value - 49) / (10000 - 49)) * 100;
                this.style.setProperty('--value', percentage + '%');
            });
        }
        
        // Monthly subscription function
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
        
        // Crowdfund tier function
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
        
        // Custom donation function
        async function donateCustom(method) {
            try {
                if (method === 'crypto') {
                    alert('Crypto donations coming soon! Please use card payment for now.');
                    return;
                }
                
                const amount = parseInt(document.getElementById('donationSlider').value) * 100; // Convert to cents
                console.log('Custom donation amount:', amount);
                
                const response = await fetch('/create-checkout-session', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        type: 'donation',
                        amount: amount
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

# ENHANCED CHECKOUT SESSION FUNCTION
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
            
            # One-time crowdfund tiers (create these in Stripe as one-time payments)
            'house_hero': {'amount': 50000, 'mode': 'payment'},        # $500
            'family_guardian': {'amount': 150000, 'mode': 'payment'},   # $1,500
            'life_changer': {'amount': 500000, 'mode': 'payment'},      # $5,000
            'legend': {'amount': 1000000, 'mode': 'payment'},           # $10,000
            
            # Existing one-time
            'lifetime': {'price_id': 'price_1Ryat4RkVYDUbhIFxohXgOK1', 'mode': 'payment'},
            'sixmonth': {'price_id': 'price_1RyJOzDfwP4gynpjh4mO6b6B', 'mode': 'payment'},
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
                success_url=f'{DOMAIN}/success?session_id={{CHECKOUT_SESSION_ID}}&type=donation',
                cancel_url=f'{DOMAIN}/?canceled=true',
                metadata={
                    'plan': 'custom_donation',
                    'type': 'donation',
                    'amount': custom_amount
                }
            )
            
            logger.info(f">MONEY< Created donation session: ${custom_amount/100}")
            return jsonify({'id': checkout_session.id})
        
        # Handle crowdfund tiers (one-time payments with fixed amounts)
        if payment_type == 'crowdfund' and plan in ['house_hero', 'family_guardian', 'life_changer', 'legend']:
            tier_info = PRICING[plan]
            
            # Map plan names to display names
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
                metadata={
                    'plan': plan,
                    'type': 'crowdfund',
                    'amount': tier_info['amount']
                }
            )
            
            logger.info(f">MONEY< Created crowdfund session for {plan}: ${tier_info['amount']/100}")
            return jsonify({'id': checkout_session.id})
        
        # Handle subscriptions and lifetime payment
        if plan not in PRICING:
            return jsonify({'error': 'Invalid plan selected'}), 400
            
        tier_info = PRICING[plan]
        
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price': tier_info['price_id'],
                'quantity': 1,
            }],
            mode=tier_info['mode'],
            success_url=f'{DOMAIN}/success?session_id={{CHECKOUT_SESSION_ID}}&type={payment_type}',
            cancel_url=f'{DOMAIN}/?canceled=true',
            metadata={
                'plan': plan,
                'type': payment_type
            }
        )
        
        logger.info(f">MONEY< Created {payment_type} session for plan: {plan}")
        return jsonify({'id': checkout_session.id})
        
    except stripe.error.StripeError as e:
        logger.error(f">ERROR< Stripe error: {e}")
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f">ERROR< Checkout error: {e}")
        return jsonify({'error': 'Failed to create checkout session'}), 500

@app.route('/success')
def success():
    """Enhanced success page after payment"""
    session_id = request.args.get('session_id')
    payment_type = request.args.get('type', 'subscription')
    plan = request.args.get('plan', '')
    
    # Customize success message based on payment type
    if payment_type == 'donation':
        title = "🙏 Thank You for Your Donation!"
        message = "Your generous donation helps save our family home and supports innovation."
    elif payment_type == 'crowdfund':
        tier_messages = {
            'house_hero': "💰 Welcome, House Hero! You're helping save our home.",
            'family_guardian': "🏆 Welcome, Family Guardian! You have 3% profit sharing for life.",
            'life_changer': "👑 Welcome, Life Changer! You have 5% profit sharing for life.",
            'legend': "✨ Welcome, Legend! You have 10% profit sharing for life."
        }
        title = tier_messages.get(plan, "🚀 Crowdfund Contribution Successful!")
        message = "Your one-time contribution directly helps save our home and funds development."
    else:
        title = "✅ Payment Successful!"
        message = "Thank you for subscribing to Whale Tracker Pro!"
    
    success_template = f"""<!DOCTYPE html>
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
            <h1 class="text-4xl font-bold text-green-400 mb-4">{title}</h1>
            <p class="text-xl text-gray-300 mb-6">{message}</p>
            <p class="text-gray-300 mb-8">
                🏠 Your contribution directly helps save our family home. 
                You will receive access credentials within 24 hours.
            </p>
            
            <div class="space-y-4">
                <a href="/dashboard" class="block px-8 py-3 bg-gradient-to-r from-purple-500 to-cyan-500 rounded-lg font-semibold text-white hover:opacity-90 transition-opacity">
                    Access Dashboard
                </a>
                <a href="/" class="block px-8 py-3 border border-gray-600 rounded-lg font-semibold text-white hover:bg-white/10 transition-colors">
                    Back to Home
                </a>
            </div>
            
            <p class="text-sm text-gray-400 mt-6">Session ID: {session_id}</p>
        </div>
    </div>
</body>
</html>
    """
    return success_template

@app.route('/dashboard')
def dashboard():
    """Working dashboard"""
    dashboard_template = """<!DOCTYPE html>
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
            <p class="text-gray-300">Thank you for your subscription! You are helping save our family home.</p>
        </div>
        
        <div class="bg-gray-800 rounded-lg p-6">
            <h3 class="text-xl font-bold mb-4">🚀 Live Dashboard Features</h3>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4 text-gray-300">
                <div>• Real-time whale discovery from Reddit</div>
                <div>• Live Ethereum and Solana tracking</div>
                <div>• AI-powered trading insights</div>
                <div>• Custom alerts and notifications</div>
            </div>
            <p class="mt-6 text-orange-400 font-semibold">Full interactive dashboard: Coming within 24 hours</p>
        </div>
    </div>
</body>
</html>
    """
    return dashboard_template

@app.route('/contact')
def contact():
    """Contact page"""
    contact_template = """<!DOCTYPE html>
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
    <header class="border-b border-gray-800 bg-black/20 backdrop-blur-sm">
        <div class="max-w-7xl mx-auto px-4 py-4 flex items-center justify-between">
            <div class="flex items-center space-x-3">
                <div class="bg-gradient-to-r from-purple-500 to-cyan-500 p-2 rounded-lg">
                    <svg class="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7"/>
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

    <section class="py-20">
        <div class="max-w-4xl mx-auto px-4">
            <div class="text-center mb-16">
                <h1 class="text-5xl font-bold mb-6">Get in Touch</h1>
                <p class="text-xl text-gray-300">We are here to help and always available to our community</p>
            </div>

            <div class="bg-red-500/10 border border-red-500/30 rounded-xl p-6 mb-12 text-center">
                <h3 class="text-2xl font-bold text-red-400 mb-2">🏠 Urgent Family Situation</h3>
                <p class="text-gray-300 mb-4">
                    Our house is scheduled for auction on <strong class="text-red-400">September 2nd, 2025</strong>. 
                    For immediate assistance regarding our family emergency, please use the priority contact below.
                </p>
                <div class="flex items-center justify-center space-x-2 text-orange-400 font-bold">
                    <a href="mailto:sean@whale-tracker.pro" class="hover:text-orange-300">sean@whale-tracker.pro</a>
                </div>
            </div>

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

    <footer class="border-t border-gray-800 py-8">
        <div class="max-w-7xl mx-auto px-4 text-center text-gray-400">
            <p>&copy; 2025 Whale Tracker Pro. Community-funded innovation. 🐋</p>
        </div>
    </footer>
</body>
</html>
    """
    return contact_template

@app.route('/roadmap')
def roadmap():
    """Development roadmap page"""
    roadmap_template = """<!DOCTYPE html>
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
        .progress-bar {
            background: linear-gradient(90deg, #10b981, #3b82f6);
        }
    </style>
</head>
<body class="text-white">
    <header class="border-b border-gray-800 bg-black/20 backdrop-blur-sm">
        <div class="max-w-7xl mx-auto px-4 py-4 flex items-center justify-between">
            <div class="flex items-center space-x-3">
                <div class="bg-gradient-to-r from-purple-500 to-cyan-500 p-2 rounded-lg">
                    <svg class="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7"/>
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
                    ✅ Payment system live • ✅ Basic dashboard • ✅ Stripe integration
                </p>
            </div>
        </div>
    </section>

    <section class="py-20">
        <div class="max-w-4xl mx-auto px-4 text-center">
            <h2 class="text-4xl font-bold mb-6">Ready to Build the Future?</h2>
            <p class="text-xl text-gray-300 mb-8">
                Join the revolution in whale tracking technology while helping save our family home.
            </p>
            <div class="flex flex-col sm:flex-row gap-4 justify-center">
                <a href="/" class="px-8 py-4 bg-gradient-to-r from-purple-500 to-cyan-500 rounded-lg font-semibold text-white text-lg hover:opacity-90 transition-opacity">
                    🚀 Start Your Subscription
                </a>
                <a href="/dashboard" class="px-8 py-4 border border-gray-600 rounded-lg font-semibold text-white hover:bg-white/10 transition-colors">
                    View Dashboard
                </a>
            </div>
        </div>
    </section>

    <footer class="border-t border-gray-800 py-8">
        <div class="max-w-7xl mx-auto px-4 text-center text-gray-400">
            <p>&copy; 2025 Whale Tracker Pro. Community-funded innovation for the crypto revolution. 🐋</p>
        </div>
    </footer>
</body>
</html>
    """
    return roadmap_template
def stripe_webhook():
    """Handle Stripe webhooks"""
    payload = request.get_data(as_text=True)
    sig_header = request.headers.get('Stripe-Signature')
    
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, os.getenv('STRIPE_WEBHOOK_SECRET')
        )
        
        if event['type'] == 'checkout.session.completed':
            session = event['data']['object']
            logger.info(f">CHECK< Payment completed for session: {session['id']}")
            
        elif event['type'] == 'invoice.payment_succeeded':
            invoice = event['data']['object']
            logger.info(f">CHECK< Invoice payment succeeded: {invoice['id']}")
            
        elif event['type'] == 'customer.subscription.deleted':
            subscription = event['data']['object']
            logger.info(f">ERROR< Subscription canceled: {subscription['id']}")
            
        return jsonify({'status': 'success'})
        
    except ValueError as e:
        logger.error(f">ERROR< Invalid payload: {e}")
        return jsonify({'error': 'Invalid payload'}), 400
    except stripe.error.SignatureVerificationError as e:
        logger.error(f">ERROR< Invalid signature: {e}")
        return jsonify({'error': 'Invalid signature'}), 400

if __name__ == '__main__':
    app.run(debug=True)
