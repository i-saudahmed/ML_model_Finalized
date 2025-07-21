import os
from typing import List

class Config:
    """Base configuration class"""
    
    # Flask settings
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    
    # Firebase settings
    FIREBASE_KEY_PATH = os.getenv('FIREBASE_KEY_PATH', 'firebase_key.json')
    
    # CORS settings
    ALLOWED_ORIGINS = os.getenv('ALLOWED_ORIGINS', 'http://localhost:4000').split(',')
    
    # Logging settings
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    
    # Request settings
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    REQUEST_TIMEOUT = 30  # seconds
    
    # ML Model settings
    SPACY_MODEL = 'en_core_web_lg'
    SENTENCE_TRANSFORMER_MODEL = 'all-mpnet-base-v2'

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    FLASK_ENV = 'development'

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    FLASK_ENV = 'production'
    
    # Override with more secure settings for production
    SECRET_KEY = os.getenv('SECRET_KEY')
    if not SECRET_KEY:
        raise ValueError("SECRET_KEY environment variable must be set in production")

class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    DEBUG = True

# Configuration mapping
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
