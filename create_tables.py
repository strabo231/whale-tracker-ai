#!/usr/bin/env python3
"""
Create Whale Tracker Database Tables
Ubuntu 24 - Working Version
"""

import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import os
from datetime import datetime

def create_whale_tracker_tables():
    print("🗄️ Creating whale tracker database tables...")
    
    try:
        conn = psycopg2.connect(
            host="127.0.0.1",
            port=5432,
            database="whale_tracker",
            user="sean",
            password="whale123"
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        print("✅ Connected to whale_tracker database!")
        
        create_tables(cursor)
        insert_sample_data(cursor)
        create_indexes(cursor)
        test_database(cursor)
        
        conn.close()
        print("🎉 Database tables setup complete!")
        
        return True
        
    except Exception as e:
        print(f"❌ Database setup failed: {e}")
        return False

def create_tables(cursor):
    print("📊 Creating database tables...")
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS whales (
            id SERIAL PRIMARY KEY,
            address VARCHAR(44) UNIQUE NOT NULL,
            nickname VARCHAR(100),
            success_score INTEGER DEFAULT 0 CHECK (success_score >= 0 AND success_score <= 100),
            win_rate DECIMAL(5,2) DEFAULT 0.00 CHECK (win_rate >= 0 AND win_rate <= 100),
            roi_7d DECIMAL(10,2) DEFAULT 0.00,
            roi_30d DECIMAL(10,2) DEFAULT 0.00,
            roi_90d DECIMAL(10,2) DEFAULT 0.00,
            total_value BIGINT DEFAULT 0,
            trading_style VARCHAR(20) DEFAULT 'Unknown' CHECK (trading_style IN ('Scalper', 'Swing', 'Position', 'Unknown')),
            confidence_level VARCHAR(10) DEFAULT 'Medium' CHECK (confidence_level IN ('High', 'Medium', 'Low')),
            last_active TIMESTAMP,
            total_trades INTEGER DEFAULT 0,
            successful_trades INTEGER DEFAULT 0,
            avg_hold_time INTEGER DEFAULT 0,
            preferred_tokens TEXT[],
            risk_score INTEGER DEFAULT 50 CHECK (risk_score >= 0 AND risk_score <= 100),
            is_active BOOLEAN DEFAULT true,
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW()
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS whale_transactions (
            id SERIAL PRIMARY KEY,
            whale_address VARCHAR(44) NOT NULL,
            token_symbol VARCHAR(20) NOT NULL,
            token_address VARCHAR(44),
            action VARCHAR(20) NOT NULL CHECK (action IN ('buy', 'sell', 'add_lp', 'remove_lp', 'stake', 'unstake', 'swap')),
            amount BIGINT NOT NULL,
            usd_value BIGINT NOT NULL,
            price_per_token DECIMAL(20,8),
            gas_used INTEGER,
            gas_price BIGINT,
            confidence_level VARCHAR(10) DEFAULT 'Medium' CHECK (confidence_level IN ('High', 'Medium', 'Low')),
            transaction_hash VARCHAR(100) UNIQUE,
            block_number BIGINT,
            timestamp TIMESTAMP NOT NULL,
            is_successful BOOLEAN DEFAULT true,
            notes TEXT,
            created_at TIMESTAMP DEFAULT NOW()
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS smart_alerts (
            id SERIAL PRIMARY KEY,
            alert_type VARCHAR(20) NOT NULL CHECK (alert_type IN ('pattern', 'rotation', 'whale', 'timing', 'volume', 'price')),
            title VARCHAR(200) NOT NULL,
            description TEXT NOT NULL,
            confidence_level VARCHAR(10) DEFAULT 'Medium' CHECK (confidence_level IN ('High', 'Medium', 'Low')),
            whale_addresses TEXT[] NOT NULL,
            token_symbol VARCHAR(20),
            token_address VARCHAR(44),
            trigger_value BIGINT,
            priority INTEGER DEFAULT 3 CHECK (priority >= 1 AND priority <= 5),
            is_active BOOLEAN DEFAULT true,
            is_read BOOLEAN DEFAULT false,
            expires_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT NOW()
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tokens (
            id SERIAL PRIMARY KEY,
            symbol VARCHAR(20) UNIQUE NOT NULL,
            address VARCHAR(44) UNIQUE NOT NULL,
            name VARCHAR(100),
            decimals INTEGER DEFAULT 9,
            total_supply BIGINT,
            market_cap BIGINT,
            price_usd DECIMAL(20,8),
            volume_24h BIGINT,
            whale_interest_score INTEGER DEFAULT 0 CHECK (whale_interest_score >= 0 AND whale_interest_score <= 100),
            is_trending BOOLEAN DEFAULT false,
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW()
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            email VARCHAR(255) UNIQUE NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            subscription_tier VARCHAR(20) DEFAULT 'free' CHECK (subscription_tier IN ('free', 'basic', 'pro', 'elite')),
            subscription_expires TIMESTAMP,
            max_tracked_whales INTEGER DEFAULT 5,
            api_key VARCHAR(64) UNIQUE,
            is_active BOOLEAN DEFAULT true,
            last_login TIMESTAMP,
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW()
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS donations (
            charge_id VARCHAR(255) PRIMARY KEY,
            amount DECIMAL(10,2) NOT NULL,
            type VARCHAR(20) NOT NULL CHECK (type IN ('crypto', 'fiat')),
            timestamp TIMESTAMP DEFAULT NOW()
        )
    ''')
    
    cursor.execute('''
        DO $$ 
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.table_constraints 
                WHERE constraint_name = 'whale_transactions_whale_address_fkey'
            ) THEN
                ALTER TABLE whale_transactions 
                ADD CONSTRAINT whale_transactions_whale_address_fkey 
                FOREIGN KEY (whale_address) REFERENCES whales(address) ON DELETE CASCADE;
            END IF;
        END $$;
    ''')
    
    print("✅ Tables created successfully!")

def insert_sample_data(cursor):
    print("📊 Inserting sample whale data...")
    
    whales_data = [
        ('8K7x9mP2nQ5rL3vW1cF6sM8dY4tR7uE9', 'Alpha Hunter', 92, 78.5, 145.2, 15600000, 'Scalper', 'High', '2024-08-12 12:00:00', 156, 122),
        ('3M9s7kL4pN2qV8xZ5bG1wC9fT6rY3uA7', 'Solana Sage', 89, 82.1, 98.7, 8900000, 'Swing', 'High', '2024-08-12 11:32:00', 89, 73),
        ('7R2n5wX8mK1dF4sL9pQ3vB6tY8rU2cA5', 'DeFi Whale', 87, 74.3, 203.4, 23400000, 'Position', 'Medium', '2024-08-12 11:00:00', 203, 151),
        ('9K8m3pT6nL2rF5xW7cV1sM4dY9tQ8uE3', 'Meme Master', 85, 69.8, 67.2, 5200000, 'Scalper', 'High', '2024-08-12 10:00:00', 245, 171),
        ('4L7x2nM9pK5rF8wV3cB6tY1sQ9dU7eA2', 'Yield Farmer', 83, 76.9, 45.8, 12100000, 'Position', 'Medium', '2024-08-12 09:00:00', 92, 71)
    ]
    
    cursor.executemany('''
        INSERT INTO whales (address, nickname, success_score, win_rate, roi_30d, total_value, 
                           trading_style, confidence_level, last_active, total_trades, successful_trades)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (address) DO NOTHING
    ''', whales_data)
    
    tokens_data = [
        ('SOL', 'So11111111111111111111111111111111111111112', 'Solana', 9, 95, True),
        ('BONK', 'DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263', 'Bonk', 5, 87, True),
        ('JUP', 'JUPyiwrYJFskUPiHa7hkeR8VUtAeFoSYbKedZNsDvCN', 'Jupiter', 6, 82, False),
        ('RAY', '4k3Dyjzvzp8eMZWUXbBCjEvwSkkk59S5iCNLY3QrkX6R', 'Raydium', 6, 79, False),
        ('WIF', 'EKpQGSJtjMFqKZ9KQanSqYXRcF8fBopzLHYxdM65zcjm', 'dogwifhat', 6, 73, True)
    ]
    
    cursor.executemany('''
        INSERT INTO tokens (symbol, address, name, decimals, whale_interest_score, is_trending)
        VALUES (%s, %s, %s, %s, %s, %s)
        ON CONFLICT (symbol) DO NOTHING
    ''', tokens_data)
    
    transactions_data = [
        ('8K7x9mP2nQ5rL3vW1cF6sM8dY4tR7uE9', 'BONK', 'buy', 2400000000, 890000, 'High', 'tx_bonk_buy_001', '2024-08-12 11:48:00'),
        ('3M9s7kL4pN2qV8xZ5bG1wC9fT6rY3uA7', 'JUP', 'sell', 50000000, 450000, 'High', 'tx_jup_sell_001', '2024-08-12 11:32:00'),
        ('7R2n5wX8mK1dF4sL9pQ3vB6tY8rU2cA5', 'RAY', 'add_lp', 100000000, 320000, 'Medium', 'tx_ray_lp_001', '2024-08-12 11:00:00'),
        ('9K8m3pT6nL2rF5xW7cV1sM4dY9tQ8uE3', 'WIF', 'buy', 75000000, 180000, 'High', 'tx_wif_buy_001', '2024-08-12 10:00:00'),
        ('4L7x2nM9pK5rF8wV3cB6tY1sQ9dU7eA2', 'SOL', 'buy', 1200000, 67000, 'Medium', 'tx_sol_buy_001', '2024-08-12 09:00:00')
    ]
    
    cursor.executemany('''
        INSERT INTO whale_transactions (whale_address, token_symbol, action, amount, usd_value, 
                                      confidence_level, transaction_hash, timestamp)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (transaction_hash) DO NOTHING
    ''', transactions_data)
    
    alerts_data = [
        ('pattern', '3 Top Whales Accumulating BONK', 'Alpha Hunter, Solana Sage, and 1 other high-success whale bought BONK in last 2h', 'High', ['8K7x9mP2nQ5rL3vW1cF6sM8dY4tR7uE9', '3M9s7kL4pN2qV8xZ5bG1wC9fT6rY3uA7'], 'BONK', 1),
        ('rotation', 'Smart Money Rotating: JUP → RAY', 'Top 5 whales moving positions from JUP to RAY tokens', 'Medium', ['3M9s7kL4pN2qV8xZ5bG1wC9fT6rY3uA7', '7R2n5wX8mK1dF4sL9pQ3vB6tY8rU2cA5'], 'RAY', 2),
        ('timing', 'High Activity Window Starting', 'Successful whales most active 2-4pm EST (historical pattern)', 'High', ['8K7x9mP2nQ5rL3vW1cF6sM8dY4tR7uE9'], None, 2),
        ('whale', 'Alpha Hunter Major Move', '$890K position opened in new token (success score: 92)', 'High', ['8K7x9mP2nQ5rL3vW1cF6sM8dY4tR7uE9'], 'BONK', 1)
    ]
    
    cursor.executemany('''
        INSERT INTO smart_alerts (alert_type, title, description, confidence_level, whale_addresses, token_symbol, priority)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    ''', alerts_data)
    
    print("✅ Sample data inserted!")

def create_indexes(cursor):
    print("🔍 Creating database indexes...")
    
    indexes = [
        'CREATE INDEX IF NOT EXISTS idx_whales_success_score ON whales(success_score DESC)',
        'CREATE INDEX IF NOT EXISTS idx_whales_total_value ON whales(total_value DESC)',
        'CREATE INDEX IF NOT EXISTS idx_whales_last_active ON whales(last_active DESC)',
        'CREATE INDEX IF NOT EXISTS idx_transactions_whale_address ON whale_transactions(whale_address)',
        'CREATE INDEX IF NOT EXISTS idx_transactions_timestamp ON whale_transactions(timestamp DESC)',
        'CREATE INDEX IF NOT EXISTS idx_transactions_token ON whale_transactions(token_symbol)',
        'CREATE INDEX IF NOT EXISTS idx_alerts_created_at ON smart_alerts(created_at DESC)',
        'CREATE INDEX IF NOT EXISTS idx_alerts_active ON smart_alerts(is_active) WHERE is_active = true',
        'CREATE INDEX IF NOT EXISTS idx_tokens_symbol ON tokens(symbol)',
        'CREATE INDEX IF NOT EXISTS idx_donations_timestamp ON donations(timestamp DESC)'
    ]
    
    for index in indexes:
        cursor.execute(index)
    
    print("✅ Indexes created!")

def test_database(cursor):
    print("\n🧪 Testing database...")
    
    cursor.execute('SELECT nickname, success_score, win_rate, total_value FROM whales ORDER BY success_score DESC LIMIT 3')
    whales = cursor.fetchall()
    
    print("📊 Top 3 Whales by Success Score:")
    for whale in whales:
        print(f"  • {whale[0]}: Score {whale[1]}, Win Rate {whale[2]}%, Value ${whale[3]:,}")
    
    cursor.execute('''
        SELECT w.nickname, wt.action, wt.token_symbol, wt.usd_value, wt.timestamp
        FROM whale_transactions wt 
        JOIN whales w ON w.address = wt.whale_address 
        ORDER BY wt.timestamp DESC LIMIT 3
    ''')
    transactions = cursor.fetchall()
    
    print("\n💰 Recent Transactions:")
    for tx in transactions:
        print(f"  • {tx[0]}: {tx[1].upper()} {tx[2]} for ${tx[3]:,}")
    
    cursor.execute('SELECT title, confidence_level FROM smart_alerts WHERE is_active = true ORDER BY created_at DESC LIMIT 2')
    alerts = cursor.fetchall()
    
    print("\n🚨 Active Alerts:")
    for alert in alerts:
        print(f"  • {alert[0]} ({alert[1]} confidence)")
    
    cursor.execute('SELECT charge_id, amount, type, timestamp FROM donations ORDER BY timestamp DESC LIMIT 2')
    donations = cursor.fetchall()
    
    print("\n💸 Recent Donations:")
    for donation in donations:
        print(f"  • {donation[0]}: ${donation[1]} ({donation[2]}) at {donation[3]}")
    
    print("\n✅ Database test successful!")

def create_final_env():
    print("📝 Creating final .env file...")
    
    env_content = """# Whale Tracker Database Configuration - Ubuntu 24 (Working)
DATABASE_URL=postgresql://sean:whale123@127.0.0.1:5432/whale_tracker
DB_HOST=127.0.0.1
DB_PORT=5432
DB_NAME=whale_tracker
DB_USER=sean
DB_PASSWORD=whale123
STRIPE_SECRET_KEY=sk_test_...
STRIPE_PUBLISHABLE_KEY=pk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
COINBASE_API_KEY=api_...
COINBASE_WEBHOOK_SECRET=whsec_...
DOMAIN=https://whale-tracker-ai.up.railway.app
OPENAI_API_KEY=your_openai_api_key_here
REDDIT_CLIENT_ID=your_reddit_client_id_here
REDDIT_CLIENT_SECRET=your_reddit_client_secret_here
REDDIT_USERNAME=your_reddit_username_here
REDDIT_PASSWORD=your_reddit_password_here
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=INFO
"""
    
    with open('.env', 'w') as f:
        f.write(env_content)
    
    print("✅ .env file created!")

if __name__ == "__main__":
    print("🚀 Setting up Whale Tracker Database Tables...")
    
    if create_whale_tracker_tables():
        create_final_env()
        
        print(f"""
🎉 Whale Tracker Database Setup Complete!

📊 Database: whale_tracker
🔌 Connection: postgresql://sean:whale123@127.0.0.1:5432/whale_tracker
📁 Environment: .env file ready

📈 Sample Data Loaded:
  • 5 whale wallets with success scores (92, 89, 87, 85, 83)
  • 5 tokens (SOL, BONK, JUP, RAY, WIF)
  • 5 recent transactions
  • 4 smart alerts

🚀 Next Steps:
1. Test Python connection: python3 -c "import psycopg2; print('✅ Ready!')"
2. Add your API keys to .env file
3. Start building whale discovery system!

🧪 Manual test:
psql -U sean -d whale_tracker -c "SELECT nickname, success_score FROM whales;"
        """)
    else:
        print("\n❌ Setup failed. Check the error messages above.")
