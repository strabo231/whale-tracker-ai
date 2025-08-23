# 🐋 Whale Tracker Pro - Production Ready

A comprehensive cryptocurrency whale tracking and AI-powered trading recommendation platform.

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- PostgreSQL 12+
- Redis (optional, for rate limiting)
- Stripe account (for payments)
- Coinbase Commerce account (optional, for crypto payments)

### 1. Environment Setup

```bash
# Clone the repository
git clone <your-repo>
cd whale-tracker-pro

# Copy environment template
cp .env.template .env

# Edit .env with your configuration
nano .env
```

### 2. Required Environment Variables

**Critical for launch:**
```bash
# Database
DATABASE_URL=postgresql://user:pass@host:port/dbname

# Stripe (Required for payments)
STRIPE_SECRET_KEY=sk_live_your_key
STRIPE_PUBLISHABLE_KEY=pk_live_your_key  
STRIPE_WEBHOOK_SECRET=whsec_your_secret

# Security
SECRET_KEY=your-super-secret-production-key
JWT_SECRET_KEY=your-jwt-secret-key

# Domain
DOMAIN=https://your-domain.com
```

### 3. Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Initialize database
python -c "from app import init_database; init_database()"
```

### 4. Launch Options

#### Option A: Direct Python (Development/Testing)
```bash
python app.py
```

#### Option B: Production with Gunicorn
```bash
gunicorn --bind 0.0.0.0:5000 --workers 4 app:app
```

#### Option C: Docker (Recommended for Production)
```bash
# Build image
docker build -t whale-tracker-pro .

# Run container
docker run -d \
  --name whale-tracker \
  --env-file .env \
  -p 5000:5000 \
  whale-tracker-pro
```

## 🏗️ Architecture

### Main Components

1. **app.py** - Main Flask application with payment processing
2. **ai_server.py** - AI trading recommendations server (runs on port 8001)
3. **trading_ai.py** - Enhanced AI analysis engine
4. **config.py** - Centralized configuration management
5. **utils.py** - Utility functions and helpers

### Key Features

✅ **Payment Processing**
- Stripe integration for subscriptions
- Coinbase Commerce for crypto payments
- Comprehensive webhook handling
- Multiple subscription tiers

✅ **AI Trading Recommendations**
- Real-time market analysis
- Whale pattern recognition
- Risk assessment algorithms
- Personalized recommendations

✅ **Security & Authentication**
- JWT-based authentication
- Rate limiting with Redis
- Input validation with Pydantic
- SQL injection protection

✅ **Production Ready**
- Structured logging with structlog
- Comprehensive error handling
- Health checks and monitoring
- Docker containerization

## 🔧 Configuration Guide

### Database Setup

```sql
-- Create database
CREATE DATABASE whale_tracker;

-- Create user (optional)
CREATE USER whale_user WITH PASSWORD 'secure_password';
GRANT ALL PRIVILEGES ON DATABASE whale_tracker TO whale_user;
```

### Stripe Configuration

1. Get your API keys from [Stripe Dashboard](https://dashboard.stripe.com/apikeys)
2. Set up webhooks pointing to: `https://your-domain.com/webhook`
3. Add these webhook events:
   - `checkout.session.completed`
   - `invoice.payment_succeeded`

### Coinbase Commerce (Optional)

1. Create account at [Coinbase Commerce](https://commerce.coinbase.com/)
2. Get API key and webhook secret
3. Set webhook URL: `https://your-domain.com/webhook`

## 🚀 Deployment

### Railway (Recommended)
```bash
# Install Railway CLI
npm install -g @railway/cli

# Login and deploy
railway login
railway deploy
```

### Heroku
```bash
# Create app
heroku create whale-tracker-pro

# Set environment variables
heroku config:set FLASK_ENV=production
heroku config:set DATABASE_URL=postgresql://...
# ... add all other env vars

# Deploy
git push heroku main
```

### DigitalOcean/AWS/GCP
1. Create a server/instance
2. Install Docker
3. Clone repository
4. Configure environment variables
5. Run with Docker Compose

## 📊 Monitoring & Health Checks

### Health Endpoints
- `GET /health` - Basic health check
- `GET /health/deep` - Comprehensive system check
- `GET /api/ai/health` - AI service health

### Logging
Logs are structured JSON format for easy parsing:
```json
{
  "timestamp": "2025-08-22T20:30:00Z",
  "level": "info",
  "message": "Payment completed",
  "user_id": "user_123",
  "amount": 99.00
}
```

## 🔒 Security Checklist

- [ ] Change all default secret keys
- [ ] Use HTTPS in production
- [ ] Configure proper CORS settings
- [ ] Set up rate limiting
- [ ] Enable SQL injection protection
- [ ] Configure secure cookie settings
- [ ] Set up monitoring/alerting

## 🧪 Testing

```bash
# Run tests
pytest

# Test specific module
pytest tests/test_app.py

# Test with coverage
pytest --cov=app tests/
```

## 📈 Performance Optimization

### Database
- Enable connection pooling
- Add database indexes
- Configure query optimization

### Caching
- Redis for session storage
- Cache frequently accessed data
- Use CDN for static assets

### Scaling
- Horizontal scaling with load balancer
- Separate AI server scaling
- Database read replicas

## 🔧 Troubleshooting

### Common Issues

**Database Connection Errors**
```bash
# Check connection
psql $DATABASE_URL -c "SELECT 1;"
```

**Stripe Webhook Issues**
- Verify webhook secret matches
- Check endpoint URL accessibility
- Review webhook logs in Stripe dashboard

**AI Service Not Responding**
- Check ai_server.py is running on port 8001
- Verify Trading AI initialization
- Check logs for initialization errors

## 📝 API Documentation

### Authentication
```bash
# Register user
curl -X POST https://your-domain.com/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "secure123"}'

# Login
curl -X POST https://your-domain.com/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "secure123"}'
```

### Trading AI
```bash
# Get trading advice
curl -X POST https://your-domain.com/api/ai/trading-advice \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"user_id": "user123", "query": "Should I buy Bitcoin?"}'
```

## 🤝 Support

For technical support:
1. Check logs: `/app/logs/transactions.log`
2. Review health checks: `/health/deep`
3. Check environment variables
4. Verify external service connectivity

## 📄 License

This project is proprietary. All rights reserved.

---

**Ready for launch! 🚀**

The application is production-ready with comprehensive error handling, security features, and monitoring capabilities. Just configure your environment variables and deploy!
