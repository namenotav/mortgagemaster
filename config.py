import os
from datetime import timedelta

class Config:
    # ==============================
    # 🔐 Flask Core Settings
    # ==============================
    SECRET_KEY = os.environ.get('SECRET_KEY')
    if not SECRET_KEY:
        # Only allow fallback in development
        if os.environ.get('FLASK_ENV') == 'development':
            SECRET_KEY = 'dev-secret-key-ONLY-FOR-LOCAL-TESTING'
        else:
            raise ValueError("SECRET_KEY environment variable must be set in production!")

    PERMANENT_SESSION_LIFETIME = timedelta(days=7)

    # ==============================
    # 🔒 Security Settings
    # ==============================
    # CSRF Protection
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = None  # No time limit on CSRF tokens

    # Secure Session Cookies
    SESSION_COOKIE_SECURE = os.environ.get('FLASK_ENV') != 'development'  # HTTPS only in production
    SESSION_COOKIE_HTTPONLY = True  # Prevent JavaScript access
    SESSION_COOKIE_SAMESITE = 'Lax'  # CSRF protection

    # Remember Me Cookie Security
    REMEMBER_COOKIE_SECURE = os.environ.get('FLASK_ENV') != 'development'
    REMEMBER_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_DURATION = timedelta(days=7)

    # ==============================
    # 🗄️ Database Configuration
    # ==============================
    raw_url = os.environ.get('DATABASE_URL')
    if raw_url:
        # ✅ Railway sometimes sets postgres:// instead of postgresql:// — this fixes it
        SQLALCHEMY_DATABASE_URI = raw_url.replace('postgres://', 'postgresql://')
    else:
        # ✅ Local fallback (persistent file-based SQLite in instance folder)
        SQLALCHEMY_DATABASE_URI = 'sqlite:///instance/database.db'

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,  # Verify connections before using them
        'pool_recycle': 300,    # Recycle connections after 5 minutes
    }

    # ==============================
    # 📧 Email Configuration (Flask-Mail)
    # ==============================
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.environ.get('EMAIL_USERNAME') or 'your-email@gmail.com'
    MAIL_PASSWORD = os.environ.get('EMAIL_PASSWORD') or 'your-app-password'
    MAIL_DEFAULT_SENDER = MAIL_USERNAME

    # ==============================
    # 💳 Stripe Integration
    # ==============================
    STRIPE_PUBLIC_KEY = os.environ.get('STRIPE_PUBLIC_KEY') or 'pk_test_your_key'
    STRIPE_SECRET_KEY = os.environ.get('STRIPE_SECRET_KEY') or 'sk_test_your_key'
    STRIPE_WEBHOOK_SECRET = os.environ.get('STRIPE_WEBHOOK_SECRET') or 'whsec_your_secret'

    # Stripe Price IDs (set these in environment variables for production)
    STRIPE_YEARLY_PRICE_ID = os.environ.get('STRIPE_YEARLY_PRICE_ID') or 'price_1STXcVD2EDcoPFLNECjwrN1p'
    STRIPE_MONTHLY_PRICE_ID = os.environ.get('STRIPE_MONTHLY_PRICE_ID') or 'price_1STXbDD2EDcoPFLN6hEU2gS9'

    # NEW: Premium Subscription Price IDs (£19.99 and £49.99)
    STRIPE_PREMIUM_PRICE_ID = os.environ.get('STRIPE_PREMIUM_PRICE_ID') or 'price_PREMIUM_1999_PLACEHOLDER'
    STRIPE_PREMIUM_PLUS_PRICE_ID = os.environ.get('STRIPE_PREMIUM_PLUS_PRICE_ID') or 'price_PREMIUM_PLUS_4999_PLACEHOLDER'

    # Pricing (in pence)
    PRO_ONETIME_PRICE = 4900  # £49.00
    PRO_MONTHLY_PRICE = 1499  # £14.99
    PREMIUM_PRICE = 1999  # £19.99/month
    PREMIUM_PLUS_PRICE = 4999  # £49.99/month

    # ==============================
    # 🌍 Site Info
    # ==============================
    SITE_URL = os.environ.get('SITE_URL') or 'https://mortgagedealshub.co.uk'
