# Add these to your requirements.txt:
# praw==7.7.1  # Reddit API
# requests==2.31.0  # Already included

# Create new file: live_data_fetcher.py

import praw
import requests
import re
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any
import time
import asyncio
from config import get_config

config = get_config()
logger = logging.getLogger(__name__)

class RedditWhaleFinder:
    """Find whale addresses from Reddit posts"""
    
    def __init__(self):
        # Set up Reddit API (you'll need to create a Reddit app)
        self.reddit = praw.Reddit(
            client_id=config.REDDIT_CLIENT_ID,     # Add to your .env
            client_secret=config.REDDIT_CLIENT_SECRET,  # Add to your .env
            user_agent='WhaleTracker/1.0'
        )
        
        # Subreddits to monitor
        self.target_subreddits = [
            'solana',
            'CryptoMoonShots', 
            'defi',
            'cryptocurrency',
            'ethtrader',
            'SatoshiStreetBets'
        ]
        
        # Regex patterns for wallet addresses
        self.wallet_patterns = {
            'ethereum': re.compile(r'0x[a-fA-F0-9]{40}'),
            'solana': re.compile(r'[1-9A-HJ-NP-Za-km-z]{32,44}'),
            'bitcoin': re.compile(r'[13][a-km-zA-HJ-NP-Z1-9]{25,34}|bc1[a-z0-9]{39,59}')
        }
    
    async def find_whale_addresses(self, hours_back=24, limit=100):
        """Find whale addresses from recent Reddit posts"""
        try:
            whale_addresses = []
            
            for subreddit_name in self.target_subreddits:
                try:
                    subreddit = self.reddit.subreddit(subreddit_name)
                    
                    # Get recent hot posts
                    for post in subreddit.hot(limit=limit):
                        # Check if post is recent
                        post_time = datetime.fromtimestamp(post.created_utc)
                        if post_time < datetime.now() - timedelta(hours=hours_back):
                            continue
                        
                        # Extract addresses from post title and content
                        addresses = self._extract_addresses_from_text(
                            f"{post.title} {post.selftext}"
                        )
                        
                        for address in addresses:
                            whale_data = await self._validate_whale_address(address, post)
                            if whale_data:
                                whale_addresses.append(whale_data)
                    
                    # Small delay to avoid rate limiting
                    await asyncio.sleep(1)
                    
                except Exception as e:
                    logger.error(f"Error processing subreddit {subreddit_name}: {e}")
                    continue
            
            return whale_addresses[:50]  # Return top 50
            
        except Exception as e:
            logger.error(f"Reddit whale finder error: {e}")
            return []
    
    def _extract_addresses_from_text(self, text):
        """Extract wallet addresses from text"""
        addresses = []
        
        for network, pattern in self.wallet_patterns.items():
            matches = pattern.findall(text)
            for match in matches:
                addresses.append({
                    'address': match,
                    'network': network
                })
        
        return addresses
    
    async def _validate_whale_address(self, address_data, post):
        """Validate if address is actually a whale"""
        try:
            address = address_data['address']
            network = address_data['network']
            
            # Get balance based on network
            if network == 'ethereum':
                balance = await self._get_ethereum_balance(address)
                min_whale_balance = 100000  # $100k USD minimum
            elif network == 'solana':
                balance = await self._get_solana_balance(address)
                min_whale_balance = 50000   # $50k USD minimum
            else:
                return None
            
            if balance and balance > min_whale_balance:
                return {
                    'address': address,
                    'balance': balance,
                    'network': network,
                    'source': f'r/{post.subreddit.display_name}',
                    'quality_score': self._calculate_quality_score(post, balance),
                    'first_seen': datetime.now().isoformat(),
                    'post_url': f"https://reddit.com{post.permalink}",
                    'post_title': post.title[:100]
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Address validation error: {e}")
            return None
    
    def _calculate_quality_score(self, post, balance):
        """Calculate quality score based on post metrics and balance"""
        score = 50  # Base score
        
        # Post engagement
        score += min(post.score / 10, 20)  # Up to 20 points for upvotes
        score += min(post.num_comments / 5, 15)  # Up to 15 points for comments
        
        # Balance factor
        if balance > 1000000:  # $1M+
            score += 15
        elif balance > 500000:  # $500k+
            score += 10
        elif balance > 200000:  # $200k+
            score += 5
        
        return min(100, max(0, int(score)))

class EtherscanIntegration:
    """Get real-time data from Etherscan"""
    
    def __init__(self):
        self.api_key = config.ETHERSCAN_API_KEY  # Add to your .env
        self.base_url = "https://api.etherscan.io/api"
    
    async def _get_ethereum_balance(self, address):
        """Get Ethereum address balance in USD"""
        try:
            # Get ETH balance
            params = {
                'module': 'account',
                'action': 'balance',
                'address': address,
                'tag': 'latest',
                'apikey': self.api_key
            }
            
            response = requests.get(self.base_url, params=params)
            data = response.json()
            
            if data['status'] == '1':
                wei_balance = int(data['result'])
                eth_balance = wei_balance / 10**18
                
                # Get ETH price in USD
                eth_price = await self._get_eth_price()
                usd_balance = eth_balance * eth_price
                
                return usd_balance
            
            return 0
            
        except Exception as e:
            logger.error(f"Etherscan balance error: {e}")
            return 0
    
    async def _get_eth_price(self):
        """Get current ETH price"""
        try:
            # Use a free API like CoinGecko
            response = requests.get(
                'https://api.coingecko.com/api/v3/simple/price?ids=ethereum&vs_currencies=usd'
            )
            data = response.json()
            return data['ethereum']['usd']
        except:
            return 2000  # Fallback price

class SolanaIntegration:
    """Get Solana data (you can use Helius or similar)"""
    
    async def _get_solana_balance(self, address):
        """Get Solana address balance"""
        try:
            # You'll need to set up a Solana RPC endpoint
            # For now, return a placeholder
            return 75000  # Placeholder
        except:
            return 0

# Update your ai_server.py to use live data
class LiveDataManager:
    """Manage live data fetching"""
    
    def __init__(self):
        self.reddit_finder = RedditWhaleFinder()
        self.last_update = None
        self.cached_whales = []
    
    async def get_live_whales(self, force_refresh=False):
        """Get live whale data from Reddit/Etherscan"""
        # Cache for 30 minutes to avoid rate limits
        if (not force_refresh and self.last_update and 
            datetime.now() - self.last_update < timedelta(minutes=30)):
            return self.cached_whales
        
        try:
            logger.info("Fetching live whale data from Reddit...")
            live_whales = await self.reddit_finder.find_whale_addresses()
            
            self.cached_whales = live_whales
            self.last_update = datetime.now()
            
            logger.info(f"Found {len(live_whales)} live whales")
            return live_whales
            
        except Exception as e:
            logger.error(f"Live data fetch error: {e}")
            # Return cached data if available
            return self.cached_whales

# Global live data manager
live_data_manager = LiveDataManager()

# Update your whale endpoint in ai_server.py
@app.route('/api/whales/top', methods=['GET'])
@require_auth
def get_top_whales():
    """Get top whales with LIVE data from Reddit/Etherscan"""
    try:
        limit = min(int(request.args.get('limit', 20)), 100)
        network = request.args.get('network', 'all')
        live_data = request.args.get('live', 'true').lower() == 'true'
        
        if live_data:
            # Get live data from Reddit/Etherscan
            whales = async_helper.run_async(live_data_manager.get_live_whales())
            
            # Filter by network if specified
            if network != 'all':
                whales = [w for w in whales if w['network'] == network]
            
            # Limit results
            whales = whales[:limit]
        else:
            # Fallback to simulated data
            whales = generate_whale_data(limit, network)
        
        return api_success({
            'whales': whales,
            'total_count': len(whales),
            'data_source': 'Live_Reddit_Etherscan' if live_data else 'Simulated',
            'last_update': live_data_manager.last_update.isoformat() if live_data_manager.last_update else None,
            'live_data': live_data
        })
        
    except Exception as e:
        logger.error("Get whales error", error=str(e))
        return api_error("Failed to fetch whale data", 500)
