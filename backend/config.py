import os


class Config:
    SECRET_KEY = os.urandom(16)
    SQLALCHEMY_DATABASE_URI = os.environ['DATABASE_URL']
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Database connection pool settings to handle multiple scheduled monitoring jobs
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 20,            # Increase from default 5 to 20 connections
        'pool_timeout': 60,         # Increase timeout from 30 to 60 seconds
        'pool_recycle': 3600,       # Recycle connections after 1 hour
        'max_overflow': 30,         # Allow up to 30 overflow connections
        'pool_pre_ping': True,      # Validate connections before use
    }
    
    # 'users' is a key that we need to write into the class
    SQLALCHEMY_BINDS = {
        'probe_list_db': os.environ['DATABASE_URL'],
        'b11_huck_ge_database': os.environ['DATABASE_URL'],
    }       


class ProdConfig(Config):
    DEBUG = False


class DevConfig(Config):
    DEBUG = True
