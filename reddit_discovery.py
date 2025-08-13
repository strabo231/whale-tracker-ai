#!/usr/bin/env python3
"""
Basic Reddit Whale Discovery
Finds wallet addresses mentioned in crypto subreddits
No AI required - uses pattern matching and basic scoring
"""

import praw
import re
import psycopg2
from psycopg2.extras import RealDictCursor
import os
from datetime import datetime, timedelta
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class BasicRedditWhaleDiscovery:
    def __init__(self):
        # Initialize Reddit connection
        self.reddit = praw.Reddit(
            client_id=os.getenv('REDDIT_CLIENT_ID'),
            client_secret=os.getenv('REDDIT_CLIENT_SECRET'),
            username=os.getenv('REDDIT_USERNAME'),
            password=os.getenv('REDDIT_PASSWORD'),
            user_agent='whale-tracker-discovery/1.0'
        )
        
        # Wallet address patterns
        self.solana_pattern = re.compile(r'\b[1-9A-HJ-NP-Za-km-z]{32,44}\b')
        self.ethereum_pattern = re.compile(r'\b0x[a-fA-F0-9]{40}\b')
        
        # Quality indicators
        self.quality_keywords = [
            'analysis', 'research', 'dd', 'due diligence', 'wallet',
            'address', 'successful', 'profitable', 'alpha', 'tracking'
        ]
        
        self.spam_keywords = [
            'moon', 'pump', 'dump', 'scam', 'free money', 'guaranteed',
            'easy money', 'get rich', 'lambo', 'diamond hands'
        ]
        
    def extract_wallet_addresses(self, text):
        """Extract potential wallet addresses from text"""
        # Clean text
        text = text.lower().replace('\n', ' ').replace('\t', ' ')
        
        # Find Solana addresses
        solana_addresses = self.solana_pattern.findall(text)
        
        # Find Ethereum addresses  
        ethereum_addresses = self.ethereum_pattern.findall(text)
        
        # Combine and filter
        all_addresses = solana_addresses + ethereum_addresses
        
        # Filter out obvious false positives
        filtered_addresses = []
        for addr in all_addresses:
            if self.is_valid_address(addr):
                filtered_addresses.append(addr)
        
        return list(set(filtered_addresses))  # Remove duplicates
    
    def is_valid_address(self, address):
        """Basic validation for wallet addresses"""
        # Filter out common false positives
        false_positives = [
            'example', 'test', 'demo', 'placeholder', 'your_address',
            'wallet_address', 'contract_address', 'token_address'
        ]
        
        address_lower = address.lower()
        
        # Check for false positives
        for fp in false_positives:
            if fp in address_lower:
                return False
        
        # Basic length checks
        if len(address) < 32 or len(address) > 44:
            return False
            
        # Ethereum addresses must start with 0x
        if address.startswith('0x') and len(address) != 42:
            return False
            
        return True
    
    def calculate_post_quality_score(self, post):
        """Calculate quality score for a Reddit post"""
        score = 0
        
        # Upvote ratio
        if hasattr(post, 'upvote_ratio'):
            score += post.upvote_ratio * 20
        
        # Post score (upvotes)
        if post.score > 0:
            score += min(post.score / 10, 20)  # Cap at 20 points
        
        # Comment engagement
        if post.num_comments > 0:
            score += min(post.num_comments / 5, 15)  # Cap at 15 points
        
        # Text quality analysis
        full_text = f"{post.title} {post.selftext}".lower()
        
        # Bonus for quality keywords
        for keyword in self.quality_keywords:
            if keyword in full_text:
                score += 5
        
        # Penalty for spam keywords
        for keyword in self.spam_keywords:
            if keyword in full_text:
                score -= 10
        
        # Minimum text length
        if len(full_text) > 100:
            score += 5
        
        return max(0, min(100, score))  # Clamp between 0-100
    
    def scan_subreddit(self, subreddit_name, limit=50):
        """Scan a subreddit for whale mentions"""
        print(f"🔍 Scanning r/{subreddit_name}...")
        
        try:
            subreddit = self.reddit.subreddit(subreddit_name)
            
            # Get hot and new posts
            hot_posts = list(subreddit.hot(limit=limit//2))
            new_posts = list(subreddit.new(limit=limit//2))
            
            all_posts = hot_posts + new_posts
            
            discoveries = []
            
            for post in all_posts:
                try:
                    # Skip if post is too old (> 7 days)
                    post_age = datetime.now() - datetime.fromtimestamp(post.created_utc)
                    if post_age > timedelta(days=7):
                        continue
                    
                    # Extract wallet addresses
                    full_text = f"{post.title} {post.selftext}"
                    addresses = self.extract_wallet_addresses(full_text)
                    
                    if addresses:
                        # Calculate post quality
                        quality_score = self.calculate_post_quality_score(post)
                        
                        # Only process high-quality posts
                        if quality_score >= 30:
                            for address in addresses:
                                discovery = {
                                    'address': address,
                                    'source': 'reddit',
                                    'subreddit': subreddit_name,
                                    'post_id': post.id,
                                    'post_title': post.title[:200],  # Truncate
                                    'post_score': post.score,
                                    'post_comments': post.num_comments,
                                    'quality_score': quality_score,
                                    'post_url': f"https://reddit.com{post.permalink}",
                                    'discovered_at': datetime.now(),
                                    'context': self.extract_context(full_text, address)
                                }
                                discoveries.append(discovery)
                                print(f"  📍 Found wallet: {address[:8]}... (Quality: {quality_score})")
                
                except Exception as e:
                    print(f"  ⚠️ Error processing post {post.id}: {e}")
                    continue
                
                # Rate limiting
                time.sleep(0.1)
            
            print(f"  ✅ Found {len(discoveries)} wallet mentions in r/{subreddit_name}")
            return discoveries
        
        except Exception as e:
            print(f"  ❌ Error scanning r/{subreddit_name}: {e}")
            return []
    
    def extract_context(self, text, address):
        """Extract context around wallet address mention"""
        # Find the sentence containing the address
        sentences = text.split('.')
        for sentence in sentences:
            if address in sentence:
                return sentence.strip()[:500]  # Return up to 500 chars
        
        return "Wallet address mentioned in post"
    
    def scan_multiple_subreddits(self):
        """Scan multiple crypto subreddits"""
        subreddits = [
            'solana',
            'CryptoCurrency', 
            'defi',
            'SolanaNFTs',
            'JupiterExchange',
            'raydium',
            'ethtrader',
            'pancakeswap'
        ]
        
        all_discoveries = []
        
        for subreddit in subreddits:
            try:
                discoveries = self.scan_subreddit(subreddit, limit=25)
                all_discoveries.extend(discoveries)
                
                # Rate limiting between subreddits
                time.sleep(2)
                
            except Exception as e:
                print(f"❌ Failed to scan r/{subreddit}: {e}")
                continue
        
        return all_discoveries
    
    def save_discoveries_to_database(self, discoveries):
        """Save discovered wallets to database"""
        if not discoveries:
            print("📊 No discoveries to save")
            return
        
        try:
            conn = psycopg2.connect(
                host=os.getenv("DB_HOST", "127.0.0.1"),
                port=os.getenv("DB_PORT", 5432),
                database=os.getenv("DB_NAME", "whale_tracker"),
                user=os.getenv("DB_USER", "sean"),
                password=os.getenv("DB_PASSWORD", "whale123"),
                cursor_factory=RealDictCursor
            )
            cursor = conn.cursor()
            
            # Group discoveries by address (combine multiple mentions)
            address_groups = {}
            for discovery in discoveries:
                addr = discovery['address']
                if addr not in address_groups:
                    address_groups[addr] = {
                        'mentions': [],
                        'total_score': 0,
                        'best_quality': 0
                    }
                
                address_groups[addr]['mentions'].append(discovery)
                address_groups[addr]['total_score'] += discovery['quality_score']
                address_groups[addr]['best_quality'] = max(
                    address_groups[addr]['best_quality'], 
                    discovery['quality_score']
                )
            
            # Insert new whales
            saved_count = 0
            for address, data in address_groups.items():
                # Calculate combined score
                mention_count = len(data['mentions'])
                avg_quality = data['total_score'] / mention_count
                combined_score = min(100, avg_quality + (mention_count * 5))
                
                # Only save high-quality discoveries
                if combined_score >= 40:
                    nickname = self.generate_nickname(data['mentions'])
                    
                    # Insert whale
                    cursor.execute("""
                        INSERT INTO whales (
                            address, nickname, success_score, confidence_level,
                            total_trades, is_active, created_at
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (address) DO UPDATE SET
                            success_score = GREATEST(whales.success_score, %s),
                            updated_at = NOW()
                    """, (
                        address, nickname, int(combined_score), 'Medium',
                        mention_count, True, datetime.now(),
                        int(combined_score)
                    ))
                    
                    saved_count += 1
                    print(f"  💾 Saved: {nickname} ({address[:8]}...) Score: {int(combined_score)}")
            
            conn.commit()
            conn.close()
            
            print(f"✅ Saved {saved_count} new whales to database")
            
        except Exception as e:
            print(f"❌ Database save failed: {e}")
    
    def generate_nickname(self, mentions):
        """Generate a nickname based on mentions"""
        # Use most common subreddit
        subreddits = [m['subreddit'] for m in mentions]
        most_common = max(set(subreddits), key=subreddits.count)
        
        prefixes = {
            'solana': 'Solana',
            'defi': 'DeFi',
            'ethtrader': 'Ethereum',
            'CryptoCurrency': 'Crypto',
            'SolanaNFTs': 'NFT'
        }
        
        prefix = prefixes.get(most_common, 'Reddit')
        return f"{prefix} Discoverer"
    
    def run_discovery(self):
        """Run the complete discovery process"""
        print("🚀 Starting Reddit whale discovery...")
        print("📊 Scanning crypto subreddits for wallet mentions...")
        
        # Scan subreddits
        discoveries = self.scan_multiple_subreddits()
        
        print(f"\n📈 Discovery Summary:")
        print(f"  • Total mentions found: {len(discoveries)}")
        
        if discoveries:
            # Save to database
            self.save_discoveries_to_database(discoveries)
            
            # Show best discoveries
            best_discoveries = sorted(discoveries, key=lambda x: x['quality_score'], reverse=True)[:5]
            print(f"\n🏆 Top 5 Quality Discoveries:")
            for i, discovery in enumerate(best_discoveries[:5], 1):
                print(f"  {i}. {discovery['address'][:8]}... from r/{discovery['subreddit']} (Score: {discovery['quality_score']})")
        
        print("\n✅ Reddit discovery complete!")

if __name__ == "__main__":
    print("🔍 Reddit Whale Discovery - Basic Version")
    print("=" * 50)
    
    # Create discovery instance
    discovery = BasicRedditWhaleDiscovery()
    
    # Run discovery
    discovery.run_discovery()
    
    print("\n🎯 Next Steps:")
    print("1. Check database: psql -U sean -d whale_tracker -c \"SELECT nickname, address, success_score FROM whales ORDER BY success_score DESC;\"")
    print("2. Add OpenAI API key for advanced analysis")
    print("3. Set up automated discovery (cron job)")
