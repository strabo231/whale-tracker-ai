import os
from datetime import timedelta

class Config:
    """Base configuration class"""
    
    # Flask settings
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    
    # Stripe configuration
    STRIPE_SECRET_KEY = os.getenv('STRIPE_SECRET_KEY')
    STRIPE_PUBLISHABLE_KEY = os.getenv('STRIPE_PUBLISHABLE_KEY')
    STRIPE_WEBHOOK_SECRET = os.getenv('STRIPE_WEBHOOK_SECRET')
    
    # Coinbase Commerce configuration
    COINBASE_API_KEY = os.getenv('COINBASE_API_KEY')
    COINBASE_WEBHOOK_SECRET = os.getenv('COINBASE_WEBHOOK_SECRET')
    
    # Database configuration
    DATABASE_URL = os.getenv('DATABASE_URL')
    DATABASE_POOL_SIZE = int(os.getenv('DATABASE_POOL_SIZE', '5'))
    DATABASE_TIMEOUT = int(os.getenv('DATABASE_TIMEOUT', '30'))
    
    # Application settings
    DOMAIN = os.getenv('DOMAIN', 'https://whale-tracker-ai.up.railway.app')
    
    # Rate limiting
    RATE_LIMIT_STORAGE_URL = os.getenv('REDIS_URL', 'memory://')
    
    # Logging
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = os.getenv('LOG_FILE', '/mnt/bridge/logs/transactions.log')
    
    # Security
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', SECRET_KEY)
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=24)
    
    # Trading AI settings
    TRADING_AI_TIMEOUT = int(os.getenv('TRADING_AI_TIMEOUT', '30'))
    TRADING_AI_MAX_RETRIES = int(os.getenv('TRADING_AI_MAX_RETRIES', '3'))

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    TESTING = False
    LOG_LEVEL = 'DEBUG'

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    TESTING = False
    
    @classmethod
    def validate(cls):
        """Validate required production settings"""
        required = [
            'STRIPE_SECRET_KEY',
            'STRIPE_WEBHOOK_SECRET', 
            'DATABASE_URL',
            'JWT_SECRET_KEY'
        ]
        missing = []
        for key in required:
            if not getattr(cls, key) or getattr(cls, key) == 'dev-secret-key-change-in-production':
                missing.append(key)
        
        if missing:
            raise RuntimeError(f"Missing required production config: {missing}")

class TestingConfig(Config):
    """Testing configuration"""
    DEBUG = True
    TESTING = True
    DATABASE_URL = 'sqlite:///:memory:'

def get_config():
    """Get configuration based on environment"""
    env = os.getenv('FLASK_ENV', 'development').lower()
    
    if env == 'production':
        config = ProductionConfig()
        config.validate()
        return config
    elif env == 'testing':
        return TestingConfig()
    else:
        return DevelopmentConfig()
