from flask import Flask, jsonify, request
import os
from datetime import datetime

# Create Flask app
app = Flask(__name__)

@app.route('/')
def home():
    return '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Whale Tracker - Discover Crypto Whales Before Everyone Else</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        body {
            background: linear-gradient(135deg, #1e293b 0%, #7c3aed 50%, #1e293b 100%);
            min-height: 100vh;
        }
        .hero-gradient {
            background: linear-gradient(135deg, rgba(139, 92, 246, 0.1), rgba(59, 130, 246, 0.1));
        }
        .tier-card {
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }
        .tier-card:hover {
            transform: translateY(-8px);
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.3);
        }
        .popular-badge {
            background: linear-gradient(90deg, #f59e0b, #ef4444);
        }
        .cta-button {
            background: linear-gradient(90deg, #8b5cf6, #06b6d4);
            transition: all 0.3s ease;
        }
        .cta-button:hover {
            background: linear-gradient(90deg, #7c3aed, #0891b2);
            transform: translateY(-2px);
            box-shadow: 0 10px 20px rgba(139, 92, 246, 0.4);
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
                        Whale Tracker
                    </h1>
                    <p class="text-gray-400 text-sm">AI-Powered Whale Discovery</p>
                </div>
            </div>
            <div class="flex items-center space-x-4">
                <a href="/login" class="text-gray-300 hover:text-white transition-colors">Login</a>
                <a href="#pricing" class="px-4 py-2 bg-purple-600 hover:bg-purple-700 rounded-lg transition-colors">
                    Get Started
                </a>
            </div>
        </div>
    </header>

    <!-- Hero Section -->
    <section class="hero-gradient py-20">
        <div class="max-w-7xl mx-auto px-4 text-center">
            <div class="inline-flex items-center px-4 py-2 bg-gradient-to-r from-orange-500 to-red-500 rounded-full text-white text-sm font-bold mb-8">
                <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"/>
                </svg>
                BETA ACCESS - LIMITED TIME
            </div>
            
            <h1 class="text-5xl md:text-7xl font-bold mb-6">
                Discover Crypto <br>
                <span class="bg-gradient-to-r from-purple-400 to-cyan-400 bg-clip-text text-transparent">
                    Whales
                </span> First
            </h1>
            
            <p class="text-xl text-gray-300 mb-8 max-w-3xl mx-auto">
                Track the biggest crypto holders before they make their moves. Our AI scans Reddit communities 
                to discover whale wallets with massive holdings in real-time.
            </p>
            
            <div class="flex flex-col sm:flex-row gap-4 justify-center mb-12">
                <a href="#pricing" class="cta-button px-8 py-4 rounded-lg font-semibold text-white text-lg">
                    Start Tracking Whales
                </a>
                <a href="#how-it-works" class="px-8 py-4 border border-gray-600 rounded-lg font-semibold text-white hover:bg-white/10 transition-colors">
                    See How It Works
                </a>
            </div>
        </div>
    </section>

    <!-- How It Works Section -->
    <section id="how-it-works" class="py-20 bg-black/20">
        <div class="max-w-7xl mx-auto px-4">
            <div class="text-center mb-16">
                <h2 class="text-4xl font-bold mb-4">How It Works</h2>
                <p class="text-gray-400 text-lg">AI-powered whale discovery in three simple steps</p>
            </div>
            
            <div class="grid grid-cols-1 md:grid-cols-3 gap-8">
                <div class="text-center">
                    <div class="bg-gradient-to-r from-purple-500 to-cyan-500 w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-4">
                        <svg class="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/>
                        </svg>
                    </div>
                    <h3 class="text-xl font-bold mb-2">1. AI Scans Reddit</h3>
                    <p class="text-gray-400">Our AI monitors crypto communities like r/solana, r/cryptocurrency for whale mentions</p>
                </div>
                
                <div class="text-center">
                    <div class="bg-gradient-to-r from-purple-500 to-cyan-500 w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-4">
                        <svg class="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/>
                        </svg>
                    </div>
                    <h3 class="text-xl font-bold mb-2">2. Quality Verification</h3>
                    <p class="text-gray-400">Each whale gets a quality score based on community engagement and verification</p>
                </div>
                
                <div class="text-center">
                    <div class="bg-gradient-to-r from-purple-500 to-cyan-500 w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-4">
                        <svg class="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"/>
                        </svg>
                    </div>
                    <h3 class="text-xl font-bold mb-2">3. Real-Time Tracking</h3>
                    <p class="text-gray-400">Get instant access to whale wallets and their holdings before they move</p>
                </div>
            </div>
        </div>
    </section>

    <!-- Pricing Section -->
    <section id="pricing" class="py-20">
        <div class="max-w-7xl mx-auto px-4">
            <div class="text-center mb-16">
                <h2 class="text-4xl font-bold mb-4">Choose Your Plan</h2>
                <p class="text-gray-400 text-lg">Start tracking whales today</p>
            </div>
            
            <div class="grid grid-cols-1 md:grid-cols-3 gap-8 max-w-5xl mx-auto">
                <!-- Beta Access Tier -->
                <div class="tier-card bg-black/40 backdrop-blur-sm border border-gray-800 rounded-xl p-8 relative">
                    <div class="absolute -top-3 left-1/2 transform -translate-x-1/2">
                        <span class="popular-badge px-4 py-1 text-white text-sm font-bold rounded-full">
                            🔥 BETA ACCESS
                        </span>
                    </div>
                    
                    <div class="text-center mb-8">
                        <h3 class="text-2xl font-bold mb-2">Beta Access</h3>
                        <p class="text-gray-400 mb-4">Perfect for getting started</p>
                        <div class="text-4xl font-bold mb-2">$29<span class="text-gray-400 text-lg">/month</span></div>
                        <p class="text-gray-500 text-sm">Limited time beta pricing</p>
                    </div>
                    
                    <ul class="space-y-3 mb-8">
                        <li class="flex items-center text-green-400">
                            <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/>
                            </svg>
                            Up to 50 tracked whales
                        </li>
                        <li class="flex items-center text-green-400">
                            <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/>
                            </svg>
                            Reddit whale discovery
                        </li>
                        <li class="flex items-center text-green-400">
                            <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/>
                            </svg>
                            Quality scoring & verification
                        </li>
                        <li class="flex items-center text-green-400">
                            <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/>
                            </svg>
                            Live dashboard access
                        </li>
                        <li class="flex items-center text-yellow-400">
                            <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.915c.969 0 1.371 1.24.588 1.81l-3.976 2.888a1 1 0 00-.363 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.976-2.888a1 1 0 00-1.176 0l-3.976 2.888c-.783.57-1.838-.197-1.538-1.118l1.518-4.674a1 1 0 00-.363-1.118l-3.976-2.888c-.784-.57-.38-1.81.588-1.81h4.914a1 1 0 00.951-.69l1.519-4.674z"/>
                            </svg>
                            FREE PRO upgrade when launched!
                        </li>
                    </ul>
                    
                    <a href="/register" class="block w-full py-3 bg-gradient-to-r from-purple-500 to-cyan-500 rounded-lg font-semibold text-white text-center hover:opacity-90 transition-opacity">
                        Start Beta Access
                    </a>
                </div>

                <!-- Pro Tier (Coming Soon) -->
                <div class="tier-card bg-black/40 backdrop-blur-sm border border-purple-500/50 rounded-xl p-8">
                    <div class="text-center mb-8">
                        <h3 class="text-2xl font-bold mb-2">Pro</h3>
                        <p class="text-gray-400 mb-4">Advanced whale tracking</p>
                        <div class="text-4xl font-bold mb-2">$49<span class="text-gray-400 text-lg">/month</span></div>
                        <p class="text-orange-400 text-sm font-medium">Launching Soon</p>
                    </div>
                    
                    <ul class="space-y-3 mb-8">
                        <li class="flex items-center text-gray-300">
                            <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/>
                            </svg>
                            Everything in Beta
                        </li>
                        <li class="flex items-center text-gray-300">
                            <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/>
                            </svg>
                            Unlimited whale tracking
                        </li>
                        <li class="flex items-center text-gray-300">
                            <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/>
                            </svg>
                            DEX integration & analytics
                        </li>
                        <li class="flex items-center text-gray-300">
                            <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/>
                            </svg>
                            Real-time whale alerts
                        </li>
                        <li class="flex items-center text-gray-300">
                            <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/>
                            </svg>
                            Advanced filtering & search
                        </li>
                    </ul>
                    
                    <div class="block w-full py-3 bg-gray-600 rounded-lg font-semibold text-white text-center cursor-not-allowed">
                        Coming Soon
                    </div>
                </div>

                <!-- Enterprise Tier -->
                <div class="tier-card bg-black/40 backdrop-blur-sm border border-gray-800 rounded-xl p-8">
                    <div class="text-center mb-8">
                        <h3 class="text-2xl font-bold mb-2">Enterprise</h3>
                        <p class="text-gray-400 mb-4">API access & custom solutions</p>
                        <div class="text-4xl font-bold mb-2">Custom</div>
                        <p class="text-gray-500 text-sm">Contact for pricing</p>
                    </div>
                    
                    <ul class="space-y-3 mb-8">
                        <li class="flex items-center text-gray-300">
                            <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/>
                            </svg>
                            Everything in Pro
                        </li>
                        <li class="flex items-center text-gray-300">
                            <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/>
                            </svg>
                            Full API access
                        </li>
                        <li class="flex items-center text-gray-300">
                            <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/>
                            </svg>
                            Custom integrations
                        </li>
                        <li class="flex items-center text-gray-300">
                            <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/>
                            </svg>
                            Priority support
                        </li>
                        <li class="flex items-center text-gray-300">
                            <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/>
                            </svg>
                            White-label options
                        </li>
                    </ul>
                    
                    <a href="mailto:contact@whale-tracker.ai" class="block w-full py-3 bg-gray-700 hover:bg-gray-600 rounded-lg font-semibold text-white text-center transition-colors">
                        Contact Sales
                    </a>
                </div>
            </div>
        </div>
    </section>

    <!-- Footer -->
    <footer class="border-t border-gray-800 py-8">
        <div class="max-w-7xl mx-auto px-4 text-center text-gray-400">
            <p>&copy; 2025 Whale Tracker. All rights reserved.</p>
        </div>
    </footer>

    <script>
        // Smooth scrolling for anchor links
        document.querySelectorAll('a[href^="#"]').forEach(anchor => {
            anchor.addEventListener('click', function (e) {
                e.preventDefault();
                const target = document.querySelector(this.getAttribute('href'));
                if (target) {
                    target.scrollIntoView({
                        behavior: 'smooth',
                        block: 'start'
                    });
                }
            });
        });
    </script>
</body>
</html>'''

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8000))
    app.run(debug=True, host='0.0.0.0', port=port)
