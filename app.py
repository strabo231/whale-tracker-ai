from flask import Flask, jsonify, request, render_template_string
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
    <title>Whale Tracker - Professional Crypto Whale Intelligence</title>
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
        .emergency-badge {
            background: linear-gradient(90deg, #ef4444, #dc2626);
            animation: pulse 2s infinite;
        }
        .professional-badge {
            background: linear-gradient(90deg, #06b6d4, #0891b2);
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
                    <p class="text-gray-400 text-sm">ETH + SOL Whale Intelligence</p>
                </div>
            </div>
            <div class="flex items-center space-x-4">
                <a href="#story" class="text-orange-400 hover:text-orange-300 font-medium">Our Story</a>
                <a href="#pricing" class="px-4 py-2 bg-purple-600 hover:bg-purple-700 rounded-lg transition-colors">
                    Help + Get Access
                </a>
            </div>
        </div>
    </header>

    <!-- Hero Section -->
    <section class="hero-gradient py-20">
        <div class="max-w-7xl mx-auto px-4 text-center">
            <div class="inline-flex items-center px-4 py-2 emergency-badge rounded-full text-white text-sm font-bold mb-8">
                ⏰ 8 DAYS LEFT - HELP SAVE OUR HOME
            </div>
            
            <h1 class="text-5xl md:text-7xl font-bold mb-6">
                Professional <br>
                <span class="bg-gradient-to-r from-purple-400 to-cyan-400 bg-clip-text text-transparent">
                    Whale Intelligence
                </span>
            </h1>
            
            <p class="text-xl text-gray-300 mb-8 max-w-3xl mx-auto">
                Track Ethereum & Solana whales through Reddit discovery + on-chain analysis. 
                <strong class="text-orange-400">Built by a developer fighting foreclosure to keep his special needs son's home.</strong>
            </p>
            
            <div class="flex flex-col sm:flex-row gap-4 justify-center mb-12">
                <a href="#pricing" class="cta-button px-8 py-4 rounded-lg font-semibold text-white text-lg">
                    🏠 Help Save Our Home + Get Access
                </a>
                <a href="#features" class="px-8 py-4 border border-gray-600 rounded-lg font-semibold text-white hover:bg-white/10 transition-colors">
                    See Features
                </a>
            </div>
        </div>
    </section>

    <!-- Story Section -->
    <section id="story" class="py-20 bg-red-900/10 border-y border-red-800/30">
        <div class="max-w-4xl mx-auto px-4 text-center">
            <h2 class="text-4xl font-bold mb-8 text-red-400">🏠 Help Save Our Home</h2>
            
            <div class="bg-black/40 backdrop-blur-sm border border-red-800/50 rounded-xl p-8">
                <div class="text-lg text-gray-300 space-y-4 text-left max-w-3xl mx-auto">
                    <p><strong class="text-white">My name is Sean.</strong> I'm a developer, father, and I'm fighting to save my family's home.</p>
                    
                    <p><strong class="text-orange-400">The situation:</strong> Our house is scheduled for foreclosure auction on <strong class="text-red-400">September 2nd, 2025</strong>. I need to raise <strong class="text-green-400">$10,000 in the next 8 days</strong> to stop it.</p>
                    
                    <p><strong class="text-purple-400">Why this matters:</strong> My son has <strong>Angelman syndrome</strong>, a rare neurological disorder. He needs stability, routine, and the safety of his home environment. Losing our house would be devastating for his development and wellbeing.</p>
                    
                    <p><strong class="text-cyan-400">What I built:</strong> Instead of just asking for help, I've spent months building a professional-grade whale tracking system. It discovers crypto whales through Reddit communities and tracks them across Ethereum and Solana networks.</p>
                    
                    <p class="text-center font-bold text-white text-xl border-t border-gray-700 pt-4">
                        Every subscription directly helps save our home. You get professional whale intelligence, we keep our house. Win-win. 🙏
                    </p>
                </div>
                
                <div class="mt-8 text-center">
                    <div class="inline-flex items-center px-6 py-3 bg-red-600 rounded-lg text-white font-bold">
                        ⏰ DEADLINE: September 2nd, 2025 - 8 days left
                    </div>
                </div>
            </div>
        </div>
    </section>

    <!-- Features Section -->
    <section id="features" class="py-20 bg-black/20">
        <div class="max-w-7xl mx-auto px-4">
            <div class="text-center mb-16">
                <h2 class="text-4xl font-bold mb-4">Professional Whale Intelligence</h2>
                <p class="text-gray-400 text-lg">Multi-chain discovery + on-chain verification</p>
            </div>
            
            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
                <div class="text-center">
                    <div class="bg-gradient-to-r from-purple-500 to-cyan-500 w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-4">
                        <svg class="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/>
                        </svg>
                    </div>
                    <h3 class="text-xl font-bold mb-2">Reddit Discovery</h3>
                    <p class="text-gray-400">AI scans r/ethereum, r/solana, r/cryptocurrency for whale mentions</p>
                </div>
                
                <div class="text-center">
                    <div class="bg-gradient-to-r from-purple-500 to-cyan-500 w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-4">
                        <svg class="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/>
                        </svg>
                    </div>
                    <h3 class="text-xl font-bold mb-2">On-Chain Verification</h3>
                    <p class="text-gray-400">Real wallet balances, transaction history, DeFi activity</p>
                </div>
                
                <div class="text-center">
                    <div class="bg-gradient-to-r from-purple-500 to-cyan-500 w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-4">
                        <svg class="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"/>
                        </svg>
                    </div>
                    <h3 class="text-xl font-bold mb-2">Multi-Chain Support</h3>
                    <p class="text-gray-400">Ethereum + Solana whale tracking in one platform</p>
                </div>
                
                <div class="text-center">
                    <div class="bg-gradient-to-r from-purple-500 to-cyan-500 w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-4">
                        <svg class="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 17h5l-5 5-5-5h5v-5a7.5 7.5 0 01-7.5-7.5h5a2.5 2.5 0 012.5 2.5z"/>
                        </svg>
                    </div>
                    <h3 class="text-xl font-bold mb-2">Real-Time Updates</h3>
                    <p class="text-gray-400">Live dashboard, API access, instant notifications</p>
                </div>
            </div>
        </div>
    </section>

    <!-- Roadmap Section -->
    <section class="py-20 bg-black/30">
        <div class="max-w-7xl mx-auto px-4">
            <div class="text-center mb-16">
                <h2 class="text-4xl font-bold mb-4">🚀 Product Roadmap</h2>
                <p class="text-gray-400 text-lg">This isn't charity - it's investing in the future of whale intelligence</p>
            </div>
            
            <div class="grid grid-cols-1 md:grid-cols-3 gap-8">
                
                <!-- Phase 1 - Current -->
                <div class="bg-green-500/10 border border-green-500/30 rounded-xl p-6">
                    <div class="flex items-center mb-4">
                        <div class="bg-green-500 w-3 h-3 rounded-full mr-3"></div>
                        <h3 class="text-xl font-bold text-green-400">Phase 1 - LIVE NOW</h3>
                    </div>
                    <ul class="space-y-2 text-gray-300">
                        <li>✅ Ethereum whale discovery</li>
                        <li>✅ Solana whale tracking</li>
                        <li>✅ Reddit community scanning</li>
                        <li>✅ Real-time dashboard</li>
                        <li>✅ Quality scoring system</li>
                        <li>✅ Basic API access</li>
                    </ul>
                </div>

                <!-- Phase 2 - Next 30 Days -->
                <div class="bg-yellow-500/10 border border-yellow-500/30 rounded-xl p-6">
                    <div class="flex items-center mb-4">
                        <div class="bg-yellow-500 w-3 h-3 rounded-full mr-3"></div>
                        <h3 class="text-xl font-bold text-yellow-400">Phase 2 - Next 30 Days</h3>
                    </div>
                    <ul class="space-y-2 text-gray-300">
                        <li>🔄 Polygon + Arbitrum support</li>
                        <li>🔄 DeFi protocol integration</li>
                        <li>🔄 Advanced whale alerts</li>
                        <li>🔄 Portfolio replication tools</li>
                        <li>🔄 Twitter/Discord monitoring</li>
                        <li>🔄 Mobile app (iOS/Android)</li>
                    </ul>
                </div>

                <!-- Phase 3 - Q1 2025 -->
                <div class="bg-purple-500/10 border border-purple-500/30 rounded-xl p-6">
                    <div class="flex items-center mb-4">
                        <div class="bg-purple-500 w-3 h-3 rounded-full mr-3"></div>
                        <h3 class="text-xl font-bold text-purple-400">Phase 3 - Q1 2025</h3>
                    </div>
                    <ul class="space-y-2 text-gray-300">
                        <li>🚀 BSC + Avalanche networks</li>
                        <li>🚀 AI-powered trade prediction</li>
                        <li>🚀 Copy trading automation</li>
                        <li>🚀 Institutional dashboard</li>
                        <li>🚀 Custom whale lists</li>
                        <li>🚀 White-label solutions</li>
                    </ul>
                </div>

            </div>

            <!-- Revenue Model -->
            <div class="mt-16 bg-black/40 border border-gray-800 rounded-xl p-8">
                <h3 class="text-2xl font-bold text-center mb-6">💰 Sustainable Business Model</h3>
                <div class="grid grid-cols-1 md:grid-cols-2 gap-8 text-gray-300">
                    <div>
                        <h4 class="font-bold text-cyan-400 mb-3">Revenue Streams:</h4>
                        <ul class="space-y-2">
                            <li>📊 SaaS subscriptions (primary)</li>
                            <li>🔌 API licensing to institutions</li>
                            <li>🏷️ White-label solutions</li>
                            <li>📱 Premium mobile features</li>
                            <li>🤖 AI trading signal licensing</li>
                        </ul>
                    </div>
                    <div>
                        <h4 class="font-bold text-green-400 mb-3">Growth Strategy:</h4>
                        <ul class="space-y-2">
                            <li>🎯 Target hedge funds & institutions</li>
                            <li>📈 Scale to all major blockchains</li>
                            <li>🤝 Partner with DeFi protocols</li>
                            <li>🔍 Advanced analytics platform</li>
                            <li>💼 Enterprise consulting services</li>
                        </ul>
                    </div>
                </div>
                
                <div class="text-center mt-6 p-4 bg-purple-500/10 rounded-lg">
                    <p class="text-purple-400 font-bold">
                        🎯 TARGET: $50K MRR by Q2 2025 through enterprise clients
                    </p>
                    <p class="text-gray-400 text-sm mt-2">
                        Your early support helps us reach profitability and scale globally
                    </p>
                </div>
            </div>

            <!-- Competitive Advantage -->
            <div class="mt-12 text-center">
                <h3 class="text-2xl font-bold mb-6">🥇 Why We'll Win</h3>
                <div class="grid grid-cols-1 md:grid-cols-4 gap-6 text-sm">
                    <div class="bg-black/40 rounded-lg p-4">
                        <div class="text-2xl mb-2">🎯</div>
                        <h4 class="font-bold text-white mb-2">First Mover</h4>
                        <p class="text-gray-400">Reddit + multi-chain discovery nobody else has</p>
                    </div>
                    <div class="bg-black/40 rounded-lg p-4">
                        <div class="text-2xl mb-2">🤖</div>
                        <h4 class="font-bold text-white mb-2">AI Integration</h4>
                        <p class="text-gray-400">Machine learning whale behavior prediction</p>
                    </div>
                    <div class="bg-black/40 rounded-lg p-4">
                        <div class="text-2xl mb-2">⚡</div>
                        <h4 class="font-bold text-white mb-2">Speed</h4>
                        <p class="text-gray-400">Real-time discovery before competitors</p>
                    </div>
                    <div class="bg-black/40 rounded-lg p-4">
                        <div class="text-2xl mb-2">💼</div>
                        <h4 class="font-bold text-white mb-2">Enterprise</h4>
                        <p class="text-gray-400">Built for institutional scale from day 1</p>
                    </div>
                </div>
            </div>
        </div>
    </section>
    <section id="pricing" class="py-20">
        <div class="max-w-7xl mx-auto px-4">
            <div class="text-center mb-16">
                <h2 class="text-4xl font-bold mb-4">Choose Your Plan</h2>
                <p class="text-gray-400 text-lg">Professional whale intelligence + help save our home</p>
            </div>
            
            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8 max-w-6xl mx-auto">
                
                <!-- Professional Tier -->
                <div class="tier-card bg-black/40 backdrop-blur-sm border border-cyan-500/50 rounded-xl p-8">
                    <div class="absolute -top-3 left-1/2 transform -translate-x-1/2">
                        <span class="professional-badge px-4 py-1 text-white text-sm font-bold rounded-full">
                            💼 PROFESSIONAL
                        </span>
                    </div>
                    
                    <div class="text-center mb-8 mt-4">
                        <h3 class="text-2xl font-bold mb-2">Professional</h3>
                        <p class="text-gray-400 mb-4">Standard whale tracking</p>
                        <div class="text-4xl font-bold mb-2">$49<span class="text-gray-400 text-lg">/month</span></div>
                        <p class="text-gray-500 text-sm">Market competitive rate</p>
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
                    
                    <a href="/checkout?plan=professional" class="block w-full py-3 bg-gradient-to-r from-cyan-500 to-blue-500 rounded-lg font-semibold text-white text-center hover:opacity-90 transition-opacity">
                        Subscribe - $49/month
                    </a>
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
                        <li class="flex items-center text-green-400">
                            <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/>
                            </svg>
                            Real-time notifications
                        </li>
                        <li class="flex items-center text-green-400">
                            <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/>
                            </svg>
                            Direct email updates from Sean
                        </li>
                        <li class="flex items-center text-orange-400">
                            <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z"/>
                            </svg>
                            Help save a special needs child's home
                        </li>
                    </ul>
                    
                    <a href="/checkout?plan=emergency" class="block w-full py-3 bg-gradient-to-r from-orange-500 to-red-500 rounded-lg font-semibold text-white text-center hover:opacity-90 transition-opacity">
                        🏠 Help Save Our Home - $199/month
                    </a>
                </div>

                <!-- Enterprise Tier -->
                <div class="tier-card bg-black/40 backdrop-blur-sm border border-purple-500/50 rounded-xl p-8">
                    <div class="absolute -top-3 left-1/2 transform -translate-x-1/2">
                        <span class="bg-gradient-to-r from-purple-500 to-indigo-500 px-4 py-1 text-white text-sm font-bold rounded-full">
                            🚀 ENTERPRISE
                        </span>
                    </div>
                    
                    <div class="text-center mb-8 mt-4">
                        <h3 class="text-2xl font-bold mb-2">Enterprise</h3>
                        <p class="text-gray-400 mb-4">Full API + custom solutions</p>
                        <div class="text-4xl font-bold mb-2">$899<span class="text-gray-400 text-lg">/month</span></div>
                        <p class="text-gray-500 text-sm">White-label available</p>
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
                            Custom integrations
                        </li>
                        <li class="flex items-center text-green-400">
                            <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/>
                            </svg>
                            Priority support & consultation
                        </li>
                        <li class="flex items-center text-green-400">
                            <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/>
                            </svg>
                            White-label options
                        </li>
                    </ul>
                    
                    <a href="/checkout?plan=enterprise" class="block w-full py-3 bg-gradient-to-r from-purple-500 to-indigo-500 rounded-lg font-semibold text-white text-center hover:opacity-90 transition-opacity">
                        Contact Sales - $899/month
                    </a>
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
                            <p class="text-gray-400 text-sm">Everything forever + help save our home</p>
                            <a href="/checkout?plan=lifetime" class="mt-3 block py-2 bg-green-600 hover:bg-green-700 rounded font-semibold text-center transition-colors">
                                🏠 Save Our House + Get Lifetime Access
                            </a>
                        </div>
                        <div class="bg-black/40 rounded-lg p-4">
                            <h4 class="font-bold text-blue-400 mb-2">6-Month Lifeline</h4>
                            <p class="text-2xl font-bold text-white">$999 <span class="text-sm text-gray-400">upfront</span></p>
                            <p class="text-gray-400 text-sm">Save $395 vs monthly + help family</p>
                            <a href="/checkout?plan=sixmonth" class="mt-3 block py-2 bg-blue-600 hover:bg-blue-700 rounded font-semibold text-center transition-colors">
                                💪 6 Months Upfront (Save $395)
                            </a>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </section>

    <!-- Final CTA -->
    <section class="py-20 bg-gradient-to-r from-red-900/20 to-orange-900/20">
        <div class="max-w-4xl mx-auto px-4 text-center">
            <h2 class="text-4xl font-bold mb-6">⏰ Time is Running Out</h2>
            <p class="text-xl text-gray-300 mb-8">
                House auction: <strong class="text-red-400">September 2nd, 2025</strong><br>
                Help save a home for a special needs child while getting professional whale intelligence.
            </p>
            <a href="#pricing" class="cta-button px-12 py-4 rounded-lg font-bold text-white text-xl">
                🏠 Help Save Our Home Now
            </a>
        </div>
    </section>

    <!-- Footer -->
    <footer class="border-t border-gray-800 py-8">
        <div class="max-w-7xl mx-auto px-4 text-center text-gray-400">
            <p>&copy; 2025 Whale Tracker Pro. Built with love by Sean for his family. Every subscription helps. 🙏</p>
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

@app.route('/checkout')
def checkout():
    plan = request.args.get('plan', 'professional')
    
    plan_info = {
        'professional': {'name': 'Professional', 'price': '$49/month'},
        'emergency': {'name': 'Help Us Stay', 'price': '$199/month'},
        'enterprise': {'name': 'Enterprise', 'price': '$899/month'},
        'lifetime': {'name': 'House Saver LIFETIME', 'price': '$2,999 one-time'},
        'sixmonth': {'name': '6-Month Lifeline', 'price': '$999 upfront'}
    }
    
    selected_plan = plan_info.get(plan, plan_info['professional'])
    
    return f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Checkout - {selected_plan["name"]} - Whale Tracker Pro</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 min-h-screen text-white">
    <div class="max-w-2xl mx-auto px-4 py-16">
        <div class="text-center mb-8">
            <h1 class="text-4xl font-bold bg-gradient-to-r from-purple-400 to-cyan-400 bg-clip-text text-transparent mb-4">
                Thank You! 🙏
            </h1>
            <p class="text-xl text-gray-300">
                You're about to subscribe to: <strong class="text-white">{selected_plan["name"]}</strong> - {selected_plan["price"]}
            </p>
        </div>
        
        <div class="bg-black/40 backdrop-blur-sm border border-gray-800 rounded-xl p-8 mb-8">
            <h2 class="text-2xl font-bold mb-6">🏠 You're Helping Save Our Home!</h2>
            <p class="text-gray-300 mb-6">
                Your subscription directly helps keep our family in our home and provides stability for my son with Angelman syndrome. 
                This means everything to us.
            </p>
            
            <div class="bg-green-500/10 border border-green-500/20 rounded-lg p-4 mb-6">
                <h3 class="font-bold text-green-400 mb-2">What happens next:</h3>
                <ul class="text-sm text-gray-300 space-y-1">
                    <li>• Payment processing through
