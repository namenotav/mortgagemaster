#!/usr/bin/env python3
"""Test application routes"""
from main import create_app

print("=" * 70)
print("🧪 TESTING APPLICATION ROUTES")
print("=" * 70)

try:
    app = create_app()
    print("\n✅ App created successfully!")

    print(f"\n📍 Total Routes: {len(list(app.url_map.iter_rules()))}")
    print("\n" + "=" * 70)
    print("REGISTERED ROUTES:")
    print("=" * 70)

    for rule in sorted(app.url_map.iter_rules(), key=lambda r: r.rule):
        methods = ', '.join(sorted(rule.methods - {'HEAD', 'OPTIONS'}))
        print(f"{rule.rule:45} [{methods:15}] -> {rule.endpoint}")

    print("\n" + "=" * 70)
    print("✅ ROUTE TEST COMPLETE")
    print("=" * 70)

except Exception as e:
    print(f"\n❌ ERROR: {str(e)}")
    import traceback
    traceback.print_exc()
