"""
Configuration module for Evergrow360 backend

This module contains configuration classes for different environments
with security-first design and production-ready settings.
"""

import os
from datetime import timedelta


class Config:
    """Base configuration class"""
    
    # Flask settings
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # JWT settings
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or SECRET_KEY
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(
        seconds=int(os.environ.get('JWT_ACCESS_TOKEN_EXPIRES', 3600))
    )
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(
        seconds=int(os.environ.get('JWT_REFRESH_TOKEN_EXPIRES', 2592000))
    )
    JWT_ALGORITHM = 'HS256'
    
    # Firebase settings
    FIREBASE_PROJECT_ID = os.environ.get('FIREBASE_PROJECT_ID')
    FIREBASE_PRIVATE_KEY_ID = os.environ.get('FIREBASE_PRIVATE_KEY_ID')
    FIREBASE_PRIVATE_KEY = os.environ.get('FIREBASE_PRIVATE_KEY')
    FIREBASE_CLIENT_EMAIL = os.environ.get('FIREBASE_CLIENT_EMAIL')
    FIREBASE_CLIENT_ID = os.environ.get('FIREBASE_CLIENT_ID')
    FIREBASE_AUTH_URI = os.environ.get('FIREBASE_AUTH_URI', 'https://accounts.google.com/o/oauth2/auth')
    FIREBASE_TOKEN_URI = os.environ.get('FIREBASE_TOKEN_URI', 'https://oauth2.googleapis.com/token')
    
    # OpenAI settings
    OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
    OPENAI_MODEL = 'gpt-4-turbo-preview'
    OPENAI_MAX_TOKENS = 2000
    OPENAI_TEMPERATURE = 0.7
    
    # Stripe settings
    STRIPE_SECRET_KEY = os.environ.get('STRIPE_SECRET_KEY')
    STRIPE_PUBLISHABLE_KEY = os.environ.get('STRIPE_PUBLISHABLE_KEY')
    STRIPE_WEBHOOK_SECRET = os.environ.get('STRIPE_WEBHOOK_SECRET')
    
    # Email settings
    SENDGRID_API_KEY = os.environ.get('SENDGRID_API_KEY')
    FROM_EMAIL = os.environ.get('FROM_EMAIL', 'noreply@evergrow360.com')
    
    # CORS settings
    CORS_ORIGINS = os.environ.get('CORS_ORIGINS', 'http://localhost:5000,http://127.0.0.1:5000,http://localhost:3000,http://localhost:8080,http://127.0.0.1:8080').split(',')
    
    # Rate limiting
    RATE_LIMIT_STORAGE_URL = os.environ.get('RATE_LIMIT_STORAGE_URL', 'memory://')
    
    # Security settings
    DATA_ENCRYPTION_KEY = os.environ.get('DATA_ENCRYPTION_KEY')
    
    # Session settings
    PERMANENT_SESSION_LIFETIME = timedelta(hours=24)
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # Monitoring
    SENTRY_DSN = os.environ.get('SENTRY_DSN')
    
    @staticmethod
    def init_app(app):
        """Initialize app with this configuration"""
        pass


class DevelopmentConfig(Config):
    """Development configuration"""
    
    DEBUG = True
    TESTING = False
    
    # Less strict security for development
    SESSION_COOKIE_SECURE = False
    
    # Development logging
    LOG_LEVEL = 'DEBUG'
    
    @staticmethod
    def init_app(app):
        Config.init_app(app)
        
        # Development-specific initialization
        import logging
        logging.basicConfig(level=logging.DEBUG)


class ProductionConfig(Config):
    """Production configuration"""
    
    DEBUG = False
    TESTING = False
    
    # Production logging
    LOG_LEVEL = 'WARNING'
    
    # Enhanced security for production
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Strict'
    
    # Production rate limits (more restrictive)
    RATE_LIMIT_STORAGE_URL = os.environ.get('RATE_LIMIT_STORAGE_URL', 'redis://localhost:6379/1')
    
    @staticmethod
    def init_app(app):
        Config.init_app(app)
        
        # Production-specific initialization
        import logging
        from logging.handlers import RotatingFileHandler
        
        # File logging for production
        if not os.path.exists('logs'):
            os.mkdir('logs')
        
        file_handler = RotatingFileHandler(
            'logs/evergrow360.log',
            maxBytes=10240000,
            backupCount=10
        )
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(logging.WARNING)
        app.logger.addHandler(file_handler)
        app.logger.setLevel(logging.WARNING)
        app.logger.info('Evergrow360 startup')


class TestingConfig(Config):
    """Testing configuration"""
    
    DEBUG = True
    TESTING = True
    
    # Use in-memory storage for testing
    RATE_LIMIT_STORAGE_URL = 'memory://'
    
    # Disable CSRF for testing
    WTF_CSRF_ENABLED = False
    
    # Use test keys
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=5)
    
    @staticmethod
    def init_app(app):
        Config.init_app(app)
        
        # Testing-specific initialization
        import logging
        logging.basicConfig(level=logging.INFO)


# Configuration mapping
config_by_name = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}