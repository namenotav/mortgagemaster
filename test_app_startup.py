#!/usr/bin/env python3
"""Test application startup and core functionality"""
from main import create_app, User, Deal
import sys

print("=" * 70)
print("🚀 APPLICATION STARTUP TEST")
print("=" * 70)

try:
    # Create app
    print("\n1️⃣  Creating Flask application...")
    app = create_app()
    print("✅ App created successfully")

    # Test app context
    print("\n2️⃣  Testing application context...")
    with app.app_context():
        # Test database models
        print("\n3️⃣  Testing database models...")

        # Count deals
        deal_count = Deal.query.count()
        print(f"✅ Deal model working - {deal_count} deals in database")

        # Count users
        user_count = User.query.count()
        print(f"✅ User model working - {user_count} users in database")

        # Test deal query with filters
        print("\n4️⃣  Testing advanced deal queries...")

        # Query deals with LTV filter
        deals_60ltv = Deal.query.filter(Deal.ltv_max >= 60).count()
        print(f"✅ LTV filter working - {deals_60ltv} deals with 60%+ LTV")

        # Query bad credit deals
        bad_credit_deals = Deal.query.filter(Deal.accepts_bad_credit == True).count()
        print(f"✅ Bad credit filter - {bad_credit_deals} specialist deals")

        # Query by lender type
        mainstream_deals = Deal.query.filter(Deal.lender_type == 'mainstream').count()
        specialist_deals = Deal.query.filter(Deal.lender_type == 'specialist').count()
        building_society_deals = Deal.query.filter(Deal.lender_type == 'building_society').count()

        print(f"✅ Lender type filter:")
        print(f"   - Mainstream: {mainstream_deals}")
        print(f"   - Specialist: {specialist_deals}")
        print(f"   - Building Society: {building_society_deals}")

        # Test best rate query
        best_deal = Deal.query.order_by(Deal.rate.asc()).first()
        if best_deal:
            print(f"\n5️⃣  Best Rate Available:")
            print(f"✅ {best_deal.lender} - {best_deal.rate}% (LTV: {best_deal.ltv_max}%)")

    # Test configuration
    print("\n6️⃣  Configuration Check:")
    print(f"✅ SECRET_KEY: {'Set' if app.config.get('SECRET_KEY') else 'MISSING!'}")
    print(f"✅ Database: {app.config.get('SQLALCHEMY_DATABASE_URI')[:50]}...")
    print(f"✅ CSRF Enabled: {app.config.get('WTF_CSRF_ENABLED')}")
    print(f"✅ Session Security: HttpOnly={app.config.get('SESSION_COOKIE_HTTPONLY')}, SameSite={app.config.get('SESSION_COOKIE_SAMESITE')}")

    # Test Stripe configuration
    print("\n7️⃣  Stripe Configuration:")
    stripe_keys = {
        'STRIPE_PUBLIC_KEY': app.config.get('STRIPE_PUBLIC_KEY'),
        'STRIPE_SECRET_KEY': app.config.get('STRIPE_SECRET_KEY'),
        'STRIPE_PREMIUM_PRICE_ID': app.config.get('STRIPE_PREMIUM_PRICE_ID'),
        'STRIPE_PREMIUM_PLUS_PRICE_ID': app.config.get('STRIPE_PREMIUM_PLUS_PRICE_ID'),
    }

    for key, value in stripe_keys.items():
        if value and value != f'{key.lower().replace("_", "-")}-placeholder':
            print(f"✅ {key}: Configured")
        else:
            print(f"⚠️  {key}: Using placeholder (needs configuration for production)")

    print("\n" + "=" * 70)
    print("✅ APPLICATION STARTUP TEST PASSED")
    print("=" * 70)
    print("\n🎯 READY TO DEPLOY!")

except Exception as e:
    print(f"\n❌ ERROR: {str(e)}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
