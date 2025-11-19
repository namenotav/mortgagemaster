#!/usr/bin/env python3
"""Test security features"""
import sys
import os

print("=" * 70)
print("🔒 SECURITY FEATURES TEST")
print("=" * 70)

# Test 1: Check .env file exists and is gitignored
print("\n1️⃣  ENVIRONMENT SECURITY")
print("-" * 70)
if os.path.exists('.env'):
    print("✅ .env file exists")
else:
    print("⚠️  .env file not found (may be using Railway env vars)")

if os.path.exists('.gitignore'):
    with open('.gitignore', 'r') as f:
        gitignore = f.read()
        if '.env' in gitignore:
            print("✅ .env is in .gitignore")
        else:
            print("❌ .env is NOT in .gitignore - SECURITY RISK!")
else:
    print("❌ .gitignore not found!")

# Test 2: Check password validation
print("\n2️⃣  PASSWORD VALIDATION")
print("-" * 70)
from main import validate_password_strength

test_passwords = [
    ("weak", False),
    ("Weak123", True),
    ("Short1A", False),
    ("NoNumber!", False),
    ("nonumber1", False),
    ("NOLOWERCASE1", False),
    ("ValidPass123", True),
    ("SuperSecure2024!", True),
]

for password, expected_valid in test_passwords:
    is_valid, msg = validate_password_strength(password)
    status = "✅" if is_valid == expected_valid else "❌"
    print(f"{status} '{password:20}' -> Valid: {is_valid} ({msg if not is_valid else 'OK'})")

# Test 3: Check email validation
print("\n3️⃣  EMAIL VALIDATION")
print("-" * 70)
from main import validate_email_address

test_emails = [
    ("valid@example.com", True),
    ("user.name@example.co.uk", True),
    ("invalid.email", False),
    ("@example.com", False),
    ("user@", False),
    ("plaintext", False),
]

for email, should_be_valid in test_emails:
    result = validate_email_address(email)
    is_valid = result is not None
    status = "✅" if is_valid == should_be_valid else "❌"
    print(f"{status} '{email:30}' -> {'Valid' if is_valid else 'Invalid'}")

# Test 4: Check CSRF protection
print("\n4️⃣  CSRF PROTECTION")
print("-" * 70)
from main import create_app
app = create_app()
if app.config.get('WTF_CSRF_ENABLED'):
    print("✅ CSRF protection is ENABLED")
else:
    print("❌ CSRF protection is DISABLED - SECURITY RISK!")

# Test 5: Check session security
print("\n5️⃣  SESSION SECURITY")
print("-" * 70)
if app.config.get('SESSION_COOKIE_HTTPONLY'):
    print("✅ HttpOnly cookies enabled (prevents XSS)")
else:
    print("❌ HttpOnly cookies disabled - SECURITY RISK!")

if app.config.get('SESSION_COOKIE_SAMESITE'):
    print(f"✅ SameSite cookies: {app.config.get('SESSION_COOKIE_SAMESITE')}")
else:
    print("⚠️  SameSite not set")

# Test 6: Check database security
print("\n6️⃣  DATABASE SECURITY")
print("-" * 70)
db_uri = app.config.get('SQLALCHEMY_DATABASE_URI')
if 'sqlite' in db_uri:
    print("⚠️  Using SQLite (OK for development, use PostgreSQL in production)")
elif 'postgresql' in db_uri:
    print("✅ Using PostgreSQL (production-ready)")
    # Check if password is in URI (should use env vars)
    if '@' in db_uri and ':' in db_uri:
        print("✅ Database credentials detected (ensure using env vars)")
else:
    print(f"⚠️  Unknown database type: {db_uri}")

# Test 7: Check rate limiting
print("\n7️⃣  RATE LIMITING")
print("-" * 70)
from main import limiter
if limiter:
    print("✅ Flask-Limiter enabled")
    print(f"   Default limits: {limiter._default_limits}")
else:
    print("❌ Rate limiting not configured!")

print("\n" + "=" * 70)
print("✅ SECURITY TEST COMPLETE")
print("=" * 70)
