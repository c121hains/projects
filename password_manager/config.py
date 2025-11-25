import os
import secrets

basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    """Application configuration settings."""
    SECRET_KEY = os.environ.get('SECRET_KEY') or secrets.token_hex(32)
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'passwords.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # Session configuration
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    # Password encryption key - in production, use environment variable
    ENCRYPTION_KEY = os.environ.get('ENCRYPTION_KEY')
