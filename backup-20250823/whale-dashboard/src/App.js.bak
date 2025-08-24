import React, { useState, useEffect, useCallback} from 'react';
import { TrendingUp, Wallet, Eye, RefreshCw, Crown, Zap, Target, Star, Rocket, Users, AlertCircle } from 'lucide-react';

const WhaleTrackerBetaDashboard = () => {
  const [whales, setWhales] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [lastUpdate, setLastUpdate] = useState(null);
  const [user, setUser] = useState(null);
  const [showAuth, setShowAuth] = useState(false);
  const [authMode, setAuthMode] = useState('login');
  const [authForm, setAuthForm] = useState({ email: '', password: '' });

 // API base URL  
const API_BASE = 'https://whale-tracker-ai.up.railway.app';  // Remove trailing slash

// Check if user is authenticated
useEffect(() => {
  const token = localStorage.getItem('whale_token');
  if (token) {
    fetchUserProfile(token);
  } else {
    setShowAuth(true);
    setLoading(false);
  }
}, []);

const fetchUserProfile = async (token) => {
  try {
    const response = await fetch(`${API_BASE}/api/user/profile`, {
      headers: { 'Authorization': `Bearer ${token}` }
    });
    
    if (response.ok) {
      const userData = await response.json();
      setUser(userData);
      
      // Check subscription before showing dashboard
      if (userData.subscription_tier === 'free') {
        setShowAuth(true); // Keep them on auth screen with paywall
        setLoading(false);
        return;
      }
      
      setShowAuth(false);
      fetchWhales(token);
    } else {
      localStorage.removeItem('whale_token');
      setShowAuth(true);
      setLoading(false);
    }
  } catch (err) {
    setShowAuth(true);
    setLoading(false);
  }
};

const fetchWhales = async (token) => {
  try {
    const response = await fetch(`${API_BASE}/api/whales/top`, {
      headers: { 'Authorization': `Bearer ${token}` }
    });

    if (response.status === 402) {
      setShowAuth(true);
      setUser(null);
      setWhales([]);   
      setError(null); 
      setLoading(false);
      handleStripeCheckout();
      return;
    }
    
    if (response.ok) {
      const data = await response.json();
      setWhales(data.whales || []);
      setLastUpdate(new Date());
      setError(null);
    } else {
      throw new Error('Failed to fetch whales');
    }
  } catch (err) {
    setError(`API Error: ${err.message}`);
    setWhales([
      {
        address: '8K7x9mP2qR5vN3wL6tF4sC1dE9yH2jM5pQ7rT8xZ3aB6',
        balance: 125000,
        source: 'r/solana',
        quality_score: 85,
        first_seen: '2025-01-15T10:30:00Z'
      },
      {
        address: '3F9k2L7mR8qN4vP1tX6sC9yE5bH8jW2nQ4rT7zA5mL3K',
        balance: 89000,
        source: 'r/cryptocurrency', 
        quality_score: 78,
        first_seen: '2025-01-15T09:15:00Z'
      }
    ]);
  } finally {
    setLoading(false);
  }
};

const handleAuth = async (e) => {
  e.preventDefault();
  try {
    const endpoint = authMode === 'login' ? '/api/auth/login' : '/api/auth/register';
    const response = await fetch(`${API_BASE}${endpoint}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(authForm)
    });

    const data = await response.json();
    
    if (response.ok) {
      const token = data.token || data.api_key;
      localStorage.setItem('whale_token', token);
      fetchUserProfile(token);
      setAuthForm({ email: '', password: '' });
    } else {
      setError(data.error || 'Authentication failed');
    }
  } catch (err) {
    setError('Connection failed');
  }
};

const handleStripeCheckout = async () => {
  try {
    const response = await fetch(`${API_BASE}/api/create-checkout-session`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email: authForm.email })
    });
    
    const data = await response.json();
    
    if (response.ok && data.checkout_url) {
      window.location.href = data.checkout_url;
    } else {
      setError('Failed to create checkout session');
    }
  } catch (err) {
    setError('Payment system error');
  }
};

const logout = () => {
  localStorage.removeItem('whale_token');
  setUser(null);
  setShowAuth(true);
  setWhales([]);
};

const formatBalance = (balance) => {
  if (balance >= 1000000) return `$${(balance / 1000000).toFixed(1)}M`;
  if (balance >= 1000) return `$${(balance / 1000).toFixed(0)}K`;
  return `$${balance}`;
};

const formatAddress = (address) => {
  return `${address.slice(0, 6)}...${address.slice(-4)}`;
};

const getQualityColor = (score) => {
  if (score >= 80) return 'text-green-400 bg-green-400/10';
  if (score >= 60) return 'text-yellow-400 bg-yellow-400/10';
  return 'text-red-400 bg-red-400/10';
};

// Authentication UI
if (showAuth) {
  return (
 
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 flex items-center justify-center">
        <div className="max-w-md w-full mx-4">
          {/* Beta Banner */}
          <div className="text-center mb-8">
            <div className="inline-flex items-center px-4 py-2 bg-gradient-to-r from-orange-500 to-red-500 rounded-full text-white text-sm font-bold mb-4">
              <Rocket className="w-4 h-4 mr-2" />
              BETA ACCESS - LIMITED TIME
            </div>
            <h1 className="text-4xl font-bold bg-gradient-to-r from-purple-400 to-cyan-400 bg-clip-text text-transparent">
              Whale Tracker
            </h1>
            <p className="text-gray-400 mt-2">Early Access Beta - $19/month</p>
          </div>

          {/* Value Proposition */}
          <div className="bg-black/40 backdrop-blur-sm border border-gray-800 rounded-xl p-6 mb-6">
            <div className="text-center mb-4">
              <Star className="w-8 h-8 text-yellow-400 mx-auto mb-2" />
              <h2 className="text-xl font-bold text-white">🔥 Early Access Special</h2>
            </div>
            
            <div className="space-y-3 text-sm">
              <div className="flex items-center text-green-400">
                <Target className="w-4 h-4 mr-2" />
                Reddit whale discovery (r/solana, r/crypto, etc.)
              </div>
              <div className="flex items-center text-green-400">
                <Users className="w-4 h-4 mr-2" />
                Up to 50 tracked whales
              </div>
              <div className="flex items-center text-green-400">
                <Zap className="w-4 h-4 mr-2" />
                Quality scoring & verification
              </div>
              <div className="flex items-center text-green-400">
                <Eye className="w-4 h-4 mr-2" />
                Live dashboard & updates
              </div>
            </div>

            <div className="bg-gradient-to-r from-purple-500/20 to-cyan-500/20 rounded-lg p-4 mt-4">
              <div className="flex items-center text-yellow-400 mb-2">
                <Crown className="w-4 h-4 mr-2" />
                <span className="font-bold">BETA BONUS</span>
              </div>
              <p className="text-gray-300 text-xs">
                When we launch PRO (1-2 weeks), all beta users get automatically upgraded 
                to PRO for the remainder of their subscription - FREE!
              </p>
            </div>

            <div className="text-center mt-4">
              <div className="text-2xl font-bold text-white">$19<span className="text-gray-400 text-lg">/month</span></div>
              <div className="text-xs text-gray-400">Cancel anytime</div>
            </div>
          </div>

          {/* Auth Form */}
          <div className="bg-black/40 backdrop-blur-sm border border-gray-800 rounded-xl p-6">
            <div className="flex space-x-1 mb-6">
              <button
                onClick={() => setAuthMode('login')}
                className={`flex-1 py-2 px-4 rounded-lg text-sm font-medium transition-colors ${
                  authMode === 'login' 
                    ? 'bg-purple-600 text-white' 
                    : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                }`}
              >
                Login
              </button>
              <button
                onClick={() => setAuthMode('register')}
                className={`flex-1 py-2 px-4 rounded-lg text-sm font-medium transition-colors ${
                  authMode === 'register' 
                    ? 'bg-purple-600 text-white' 
                    : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                }`}
              >
                Start Beta
              </button>
            </div>

            <div className="space-y-4">
              <div>
                <input
                  type="email"
                  placeholder="Email address"
                  value={authForm.email}
                  onChange={(e) => setAuthForm({...authForm, email: e.target.value})}
                  className="w-full px-4 py-3 bg-gray-800 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:border-purple-500 focus:outline-none"
                />
              </div>
              <div>
                <input
                  type="password"
                  placeholder="Password (min 8 chars)"
                  value={authForm.password}
                  onChange={(e) => setAuthForm({...authForm, password: e.target.value})}
                  className="w-full px-4 py-3 bg-gray-800 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:border-purple-500 focus:outline-none"
                />
              </div>
              
              {error && (
                <div className="flex items-center text-red-400 text-sm">
                  <AlertCircle className="w-4 h-4 mr-2" />
                  {error}
                </div>
              )}

              <button
                onClick={handleAuth}
                className="w-full py-3 bg-gradient-to-r from-purple-500 to-cyan-500 rounded-lg font-semibold text-white hover:opacity-90 transition-opacity"
              >
                {authMode === 'login' ? 'Access Dashboard' : 'Start Beta Access - $19/month'}
              </button>
            </div>

            <div className="text-center mt-4">
              <p className="text-xs text-gray-400">
                Source transparency: Whale data from Reddit community mentions
              </p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Main Dashboard
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900">
      {/* Header */}
      <div className="border-b border-gray-800 bg-black/20 backdrop-blur-sm">
        <div className="max-w-7xl mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="bg-gradient-to-r from-purple-500 to-cyan-500 p-2 rounded-lg">
                <Target className="w-6 h-6 text-white" />
              </div>
              <div>
                <div className="flex items-center space-x-2">
                  <h1 className="text-2xl font-bold bg-gradient-to-r from-purple-400 to-cyan-400 bg-clip-text text-transparent">
                    Whale Tracker
                  </h1>
                  <span className="px-2 py-1 bg-orange-500 text-white text-xs font-bold rounded">BETA</span>
                </div>
                <p className="text-gray-400 text-sm">Live Crypto Whale Discovery</p>
              </div>
            </div>
            
            <div className="flex items-center space-x-4">
              <button 
                onClick={fetchWhales}
                disabled={loading}
                className="flex items-center space-x-2 px-4 py-2 bg-purple-600 hover:bg-purple-700 disabled:bg-gray-600 rounded-lg transition-colors"
              >
                <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
                <span>Refresh</span>
              </button>
              
              <div className="px-4 py-2 bg-gradient-to-r from-orange-500 to-red-500 rounded-lg">
                <Rocket className="w-4 h-4 inline mr-2" />
                <span className="font-semibold">BETA USER</span>
              </div>
              
              <button 
                onClick={logout}
                className="text-gray-400 hover:text-white transition-colors"
              >
                Logout
              </button>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 py-8">
        {/* Beta Upgrade Banner */}
        <div className="mb-8 bg-gradient-to-r from-purple-500/10 to-cyan-500/10 border border-purple-500/20 rounded-xl p-6">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-lg font-semibold text-white mb-2 flex items-center">
                <Crown className="w-5 h-5 mr-2 text-yellow-400" />
                🎉 You're a Beta Pioneer!
              </h3>
              <p className="text-gray-400 text-sm">
                When PRO launches (1-2 weeks), you'll automatically get upgraded for FREE! 
                PRO includes DEX integration, advanced analytics, unlimited whales, and real-time alerts.
              </p>
            </div>
            <div className="text-right">
              <div className="text-2xl font-bold text-green-400">FREE</div>
              <div className="text-xs text-gray-400">PRO Upgrade</div>
            </div>
          </div>
        </div>

        {/* Stats Overview */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <div className="bg-black/40 backdrop-blur-sm border border-gray-800 rounded-xl p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-400 text-sm">Beta Whales</p>
                <p className="text-2xl font-bold text-white">{whales.length}/50</p>
              </div>
              <Wallet className="w-8 h-8 text-purple-400" />
            </div>
          </div>
          
          <div className="bg-black/40 backdrop-blur-sm border border-gray-800 rounded-xl p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-400 text-sm">Total Value</p>
                <p className="text-2xl font-bold text-white">
                  {formatBalance(whales.reduce((sum, w) => sum + (w.balance || 0), 0))}
                </p>
              </div>
              <TrendingUp className="w-8 h-8 text-green-400" />
            </div>
          </div>
          
          <div className="bg-black/40 backdrop-blur-sm border border-gray-800 rounded-xl p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-400 text-sm">Avg Quality</p>
                <p className="text-2xl font-bold text-white">
                  {whales.length ? Math.round(whales.reduce((sum, w) => sum + (w.quality_score || 0), 0) / whales.length) : 0}%
                </p>
              </div>
              <Zap className="w-8 h-8 text-yellow-400" />
            </div>
          </div>
          
          <div className="bg-black/40 backdrop-blur-sm border border-gray-800 rounded-xl p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-400 text-sm">Last Update</p>
                <p className="text-sm font-semibold text-white">
                  {lastUpdate ? lastUpdate.toLocaleTimeString() : 'Never'}
                </p>
              </div>
              <Eye className="w-8 h-8 text-cyan-400" />
            </div>
          </div>
        </div>

        {/* Source Disclosure */}
        {error && (
          <div className="mb-6 p-4 bg-blue-500/10 border border-blue-500/20 rounded-xl">
            <div className="flex items-center">
              <AlertCircle className="w-4 h-4 text-blue-400 mr-2" />
              <p className="text-blue-400 text-sm">
                <strong>Data Source:</strong> Reddit community mentions (r/solana, r/cryptocurrency, r/CryptoMoonShots, r/defi)
              </p>
            </div>
          </div>
        )}

        {/* Whales Table */}
        <div className="bg-black/40 backdrop-blur-sm border border-gray-800 rounded-xl overflow-hidden">
          <div className="px-6 py-4 border-b border-gray-800">
            <h2 className="text-xl font-bold text-white flex items-center">
              <Target className="w-5 h-5 mr-2 text-purple-400" />
              Discovered Whales (Beta)
            </h2>
          </div>
          
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-900/50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">Wallet</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">Balance</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">Source</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">Quality</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">Discovered</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-800">
                {loading ? (
                  <tr>
                    <td colSpan="5" className="px-6 py-8 text-center">
                      <RefreshCw className="w-6 h-6 animate-spin mx-auto mb-2 text-purple-400" />
                      <p className="text-gray-400">Loading whales...</p>
                    </td>
                  </tr>
                ) : whales.length === 0 ? (
                  <tr>
                    <td colSpan="5" className="px-6 py-8 text-center">
                      <Target className="w-8 h-8 mx-auto mb-2 text-gray-600" />
                      <p className="text-gray-400">No whales discovered yet</p>
                      <p className="text-gray-500 text-sm">Beta scanning will begin soon</p>
                    </td>
                  </tr>
                ) : (
                  whales.map((whale, index) => (
                    <tr key={whale.address || index} className="hover:bg-gray-800/20">
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="font-mono text-sm text-gray-300">
                          {formatAddress(whale.address)}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm font-semibold text-green-400">
                          {formatBalance(whale.balance || 0)}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className="px-2 py-1 text-xs font-medium bg-blue-500/20 text-blue-400 rounded-full">
                          {whale.source}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`px-2 py-1 text-xs font-medium rounded-full ${getQualityColor(whale.quality_score || 0)}`}>
                          {whale.quality_score || 0}%
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-400">
                        {whale.first_seen ? new Date(whale.first_seen).toLocaleString() : 'Unknown'}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
};

export default WhaleTrackerBetaDashboard;
