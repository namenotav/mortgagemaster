import os
from datetime import timedelta

class Config:
    # ==============================
    # 🔐 Flask Core Settings
    # ==============================
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-later'
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)

    # ==============================
    # 🗄️ Database Configuration
    # ==============================
    raw_url = os.environ.get('DATABASE_URL')
    if raw_url:
        # ✅ Railway sometimes sets postgres:// instead of postgresql:// — this fixes it
        SQLALCHEMY_DATABASE_URI = raw_url.replace('postgres://', 'postgresql://')
    else:
        # ✅ Local fallback (persistent file-based SQLite)
        SQLALCHEMY_DATABASE_URI = 'sqlite:///database.db'

    SQLALCHEMY_TRACK_MODIFICATIONS = False

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

    # Pricing (in pence)
    PRO_ONETIME_PRICE = 4900  # £49.00
    PRO_MONTHLY_PRICE = 1499  # £14.99

    # ==============================
    # 🌍 Site Info
    # ==============================
    SITE_URL = os.environ.get('SITE_URL') or 'https://mortgagedealshub.co.uk'
