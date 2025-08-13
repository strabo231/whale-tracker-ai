#!/bin/bash
# ===============================================
# POSTGRESQL RESET & FIX FOR UBUNTU 24
# Fixes authentication issues
# ===============================================

echo "🔧 Fixing PostgreSQL authentication issues..."

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

USERNAME=$(whoami)
DB_PASSWORD="whale123"

echo -e "${BLUE}👤 User: $USERNAME${NC}"
echo -e "${BLUE}🔐 Password: $DB_PASSWORD${NC}"

# Step 1: Reset user and database completely
echo -e "${YELLOW}🗄️ Resetting PostgreSQL user and database...${NC}"

sudo -u postgres psql << EOF
-- Drop existing user and database if they exist
DROP DATABASE IF EXISTS whale_tracker;
DROP USER IF EXISTS sean;

-- Create user with all privileges
CREATE USER sean WITH PASSWORD '$DB_PASSWORD' CREATEDB SUPERUSER LOGIN;

-- Create database
CREATE DATABASE whale_tracker OWNER sean;

-- Grant all privileges
GRANT ALL PRIVILEGES ON DATABASE whale_tracker TO sean;
GRANT ALL PRIVILEGES ON SCHEMA public TO sean;

-- Show created user
\du sean

-- Test connection as user
\c whale_tracker sean

-- Create a test table to verify permissions
CREATE TABLE test_connection (id INTEGER, message TEXT);
INSERT INTO test_connection VALUES (1, 'Connection successful!');
SELECT * FROM test_connection;
DROP TABLE test_connection;

-- Exit
\q
EOF

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ User and database reset successfully${NC}"
else
    echo -e "${RED}❌ Failed to reset user/database${NC}"
    exit 1
fi

# Step 2: Fix PostgreSQL authentication configuration
echo -e "${YELLOW}🔧 Configuring PostgreSQL authentication...${NC}"

# Find PostgreSQL version
PG_VERSION=$(sudo -u postgres psql -t -c "SELECT version();" | grep -oP '\d+' | head -1)
echo -e "${BLUE}📊 PostgreSQL version: $PG_VERSION${NC}"

PG_CONFIG_DIR="/etc/postgresql/$PG_VERSION/main"

if [ -f "$PG_CONFIG_DIR/pg_hba.conf" ]; then
    # Backup original config
    sudo cp "$PG_CONFIG_DIR/pg_hba.conf" "$PG_CONFIG_DIR/pg_hba.conf.backup.$(date +%Y%m%d)"
    
    # Update authentication method
    echo -e "${BLUE}🔧 Updating pg_hba.conf...${NC}"
    
    # Add specific rule for our user at the top
    sudo sed -i '/#.*TYPE.*DATABASE.*USER.*ADDRESS.*METHOD/a local   whale_tracker   sean                                    md5' "$PG_CONFIG_DIR/pg_hba.conf"
    
    # Change default local authentication to md5
    sudo sed -i 's/local   all             all                                     peer/local   all             all                                     md5/' "$PG_CONFIG_DIR/pg_hba.conf"
    
    # Ensure localhost connections work
    sudo sed -i 's/host    all             all             127.0.0.1\/32            ident/host    all             all             127.0.0.1\/32            md5/' "$PG_CONFIG_DIR/pg_hba.conf"
    
    echo -e "${GREEN}✅ pg_hba.conf updated${NC}"
    
    # Restart PostgreSQL
    echo -e "${BLUE}🔄 Restarting PostgreSQL...${NC}"
    sudo systemctl restart postgresql
    
    # Wait for restart
    sleep 3
    
    if sudo systemctl is-active --quiet postgresql; then
        echo -e "${GREEN}✅ PostgreSQL restarted successfully${NC}"
    else
        echo -e "${RED}❌ PostgreSQL restart failed${NC}"
        sudo systemctl status postgresql
        exit 1
    fi
else
    echo -e "${RED}❌ PostgreSQL config file not found${NC}"
    exit 1
fi

# Step 3: Test different connection methods
echo -e "${YELLOW}🧪 Testing database connections...${NC}"

# Test 1: Local connection with password
echo -e "${BLUE}Test 1: Local connection${NC}"
if PGPASSWORD=$DB_PASSWORD psql -U sean -d whale_tracker -c "SELECT 'Local connection works!' as status;" 2>/dev/null; then
    echo -e "${GREEN}✅ Local connection successful${NC}"
    LOCAL_WORKS=true
else
    echo -e "${RED}❌ Local connection failed${NC}"
    LOCAL_WORKS=false
fi

# Test 2: TCP connection with password
echo -e "${BLUE}Test 2: TCP connection (127.0.0.1)${NC}"
if PGPASSWORD=$DB_PASSWORD psql -h 127.0.0.1 -U sean -d whale_tracker -c "SELECT 'TCP connection works!' as status;" 2>/dev/null; then
    echo -e "${GREEN}✅ TCP connection successful${NC}"
    TCP_WORKS=true
else
    echo -e "${RED}❌ TCP connection failed${NC}"
    TCP_WORKS=false
fi

# Test 3: TCP connection with localhost
echo -e "${BLUE}Test 3: TCP connection (localhost)${NC}"
if PGPASSWORD=$DB_PASSWORD psql -h localhost -U sean -d whale_tracker -c "SELECT 'Localhost connection works!' as status;" 2>/dev/null; then
    echo -e "${GREEN}✅ Localhost connection successful${NC}"
    LOCALHOST_WORKS=true
else
    echo -e "${RED}❌ Localhost connection failed${NC}"
    LOCALHOST_WORKS=false
fi

# Step 4: Create appropriate .env file based on what works
echo -e "${YELLOW}📝 Creating .env file with working connection...${NC}"

if [ "$TCP_WORKS" = true ]; then
    CONNECTION_STRING="postgresql://sean:$DB_PASSWORD@127.0.0.1:5432/whale_tracker"
    echo -e "${GREEN}✅ Using TCP connection (127.0.0.1)${NC}"
elif [ "$LOCALHOST_WORKS" = true ]; then
    CONNECTION_STRING="postgresql://sean:$DB_PASSWORD@localhost:5432/whale_tracker"
    echo -e "${GREEN}✅ Using localhost connection${NC}"
elif [ "$LOCAL_WORKS" = true ]; then
    CONNECTION_STRING="postgresql://sean:$DB_PASSWORD@/whale_tracker"
    echo -e "${GREEN}✅ Using local socket connection${NC}"
else
    echo -e "${RED}❌ No connection method worked${NC}"
    CONNECTION_STRING="postgresql://sean:$DB_PASSWORD@localhost:5432/whale_tracker"
    echo -e "${YELLOW}⚠️ Using localhost anyway - may need manual fix${NC}"
fi

# Create .env file
cat > .env << EOF
# Whale Tracker Database Configuration - Ubuntu 24 (Fixed)
DATABASE_URL=$CONNECTION_STRING
DB_HOST=127.0.0.1
DB_PORT=5432
DB_NAME=whale_tracker
DB_USER=sean
DB_PASSWORD=$DB_PASSWORD

# API Keys
OPENAI_API_KEY=your_openai_api_key_here
REDDIT_CLIENT_ID=your_reddit_client_id_here
REDDIT_CLIENT_SECRET=your_reddit_client_secret_here
REDDIT_USERNAME=your_reddit_username_here
REDDIT_PASSWORD=your_reddit_password_here

# Application Settings
ENVIRONMENT=development
DEBUG=true
EOF

echo -e "${GREEN}✅ .env file created${NC}"

# Step 5: Final Python test
echo -e "${YELLOW}🐍 Testing Python connection...${NC}"

python3 << EOF
import sys
try:
    import psycopg2
    conn = psycopg2.connect('$CONNECTION_STRING')
    cursor = conn.cursor()
    cursor.execute("SELECT 'Python connection successful!' as status, current_user, current_database();")
    result = cursor.fetchone()
    print(f"✅ {result[0]}")
    print(f"📊 User: {result[1]}, Database: {result[2]}")
    conn.close()
except Exception as e:
    print(f"❌ Python connection failed: {e}")
    sys.exit(1)
EOF

if [ $? -eq 0 ]; then
    echo -e "${GREEN}🎉 PostgreSQL authentication fixed successfully!${NC}"
    echo ""
    echo -e "${BLUE}📊 Connection Details:${NC}"
    echo -e "${BLUE}🔌 URL:${NC} $CONNECTION_STRING"
    echo -e "${BLUE}👤 User:${NC} sean"
    echo -e "${BLUE}🔐 Password:${NC} $DB_PASSWORD"
    echo ""
    echo -e "${GREEN}🚀 Ready to proceed with whale tracker setup!${NC}"
else
    echo -e "${RED}❌ Python connection still failing${NC}"
    echo "Try manual connection: psql -h 127.0.0.1 -U sean -d whale_tracker"
fi
