#!/usr/bin/env python3
"""Comprehensive test script for MortgageMaster"""
import sqlite3
import os
import sys

print("=" * 70)
print("🔍 COMPREHENSIVE MORTGAGEMASTER TESTING")
print("=" * 70)

# Test 1: Check database exists
print("\n1️⃣  DATABASE CHECK")
print("-" * 70)
db_path = 'instance/database.db'
if os.path.exists(db_path):
    print(f"✅ Database exists at: {db_path}")
    db_size = os.path.getsize(db_path)
    print(f"   Size: {db_size:,} bytes ({db_size/1024:.2f} KB)")
else:
    print(f"❌ Database not found at: {db_path}")
    sys.exit(1)

# Test 2: Check database tables
print("\n2️⃣  DATABASE TABLES")
print("-" * 70)
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()
expected_tables = ['users2', 'deal', 'subscriber', 'settings', 'saved_deal',
                   'deal_alert', 'uploaded_document', 'eligibility_result',
                   'consultation_booking']

for table in expected_tables:
    if any(table in t[0] for t in tables):
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]
        print(f"✅ {table:25} - {count:4} rows")
    else:
        print(f"❌ {table:25} - MISSING!")

# Test 3: Check deals data
print("\n3️⃣  DEAL DATA SAMPLE")
print("-" * 70)
cursor.execute("SELECT lender, rate, ltv_max, accepts_bad_credit, lender_type FROM deal LIMIT 5")
deals = cursor.fetchall()
if deals:
    print(f"✅ Found {len(deals)} sample deals:")
    for deal in deals:
        print(f"   📍 {deal[0]:20} | Rate: {deal[1]:.2f}% | LTV: {deal[2]:.0f}% | Bad Credit: {deal[3]} | Type: {deal[4]}")
else:
    print("❌ No deals found in database!")

# Test 4: Check settings
print("\n4️⃣  APPLICATION SETTINGS")
print("-" * 70)
cursor.execute("SELECT key, value FROM settings")
settings = cursor.fetchall()
if settings:
    for key, value in settings:
        print(f"✅ {key}: {value}")
else:
    print("⚠️  No settings configured")

# Test 5: Check user schema for subscription fields
print("\n5️⃣  USER SUBSCRIPTION SCHEMA")
print("-" * 70)
cursor.execute("PRAGMA table_info(users2)")
user_columns = cursor.fetchall()
subscription_fields = ['stripe_customer_id', 'subscription_tier', 'subscription_status',
                       'stripe_subscription_id', 'subscription_start_date', 'subscription_end_date']

for field in subscription_fields:
    if any(field in col[1] for col in user_columns):
        print(f"✅ {field:30} - Present")
    else:
        print(f"❌ {field:30} - MISSING!")

# Test 6: Check deal schema for advanced fields
print("\n6️⃣  DEAL ADVANCED FILTERING SCHEMA")
print("-" * 70)
cursor.execute("PRAGMA table_info(deal)")
deal_columns = cursor.fetchall()
advanced_fields = ['accepts_bad_credit', 'min_credit_score', 'accepts_low_income',
                   'min_income', 'lender_type', 'product_fee', 'cashback']

for field in advanced_fields:
    if any(field in col[1] for col in deal_columns):
        print(f"✅ {field:30} - Present")
    else:
        print(f"❌ {field:30} - MISSING!")

conn.close()

# Test 7: Check required files
print("\n7️⃣  REQUIRED FILES CHECK")
print("-" * 70)
required_files = {
    'main.py': 'Main application',
    'config.py': 'Configuration',
    'requirements.txt': 'Dependencies',
    'wsgi.py': 'WSGI entry point',
    'Procfile': 'Railway deployment',
    '.env.example': 'Environment template',
    'templates/index.html': 'Homepage',
    'templates/search_results.html': 'Search results',
    'templates/upgrade.html': 'Subscription page',
    'templates/base.html': 'Base template',
}

for file, description in required_files.items():
    if os.path.exists(file):
        print(f"✅ {file:35} - {description}")
    else:
        print(f"❌ {file:35} - MISSING!")

# Test 8: Check Python imports
print("\n8️⃣  PYTHON DEPENDENCIES CHECK")
print("-" * 70)
dependencies = [
    'flask',
    'flask_sqlalchemy',
    'flask_login',
    'flask_mail',
    'flask_wtf',
    'flask_limiter',
    'flask_talisman',
    'stripe',
    'bcrypt',
    'email_validator',
]

for dep in dependencies:
    try:
        __import__(dep)
        print(f"✅ {dep:30} - Installed")
    except ImportError:
        print(f"❌ {dep:30} - NOT INSTALLED!")

print("\n" + "=" * 70)
print("✅ TESTING COMPLETE")
print("=" * 70)
