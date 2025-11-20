#!/usr/bin/env python3
"""
Full data update script - Run this to populate all missing data
1. Add 40 alternative mortgage deals
2. Add lender application URLs to all deals
"""

print("=" * 70)
print("🚀 FULL DATA UPDATE - MORTGAGEMASTER")
print("=" * 70)
print()

# Step 1: Add alternative deals
print("STEP 1/2: Adding 40 alternative mortgage deals...")
print("-" * 70)
exec(open('add_alternative_deals.py').read())

print()
print()

# Step 2: Add lender URLs
print("STEP 2/2: Adding lender application URLs...")
print("-" * 70)
exec(open('update_deals_with_urls.py').read())

print()
print("=" * 70)
print("✅ FULL DATA UPDATE COMPLETE!")
print("=" * 70)
print()
print("Next steps:")
print("1. Deploy to Railway (git push)")
print("2. Test deal search on the live site")
print("3. Sign up for affiliate programs to replace direct URLs")
print()
