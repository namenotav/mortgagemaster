#!/usr/bin/env python3
"""
Test if blog system is working
"""

print("=" * 60)
print("🧪 TESTING BLOG SYSTEM")
print("=" * 60)
print()

# Test 1: Check if blog table exists
print("TEST 1: Blog table exists?")
try:
    import sqlite3
    conn = sqlite3.connect('instance/database.db')
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='blog_post'")
    result = cursor.fetchone()
    if result:
        print("   ✅ blog_post table exists")
    else:
        print("   ❌ blog_post table NOT found")
        exit(1)
except Exception as e:
    print(f"   ❌ Error: {e}")
    exit(1)

# Test 2: Check if blog posts exist
print()
print("TEST 2: Blog posts exist?")
try:
    cursor.execute("SELECT COUNT(*) FROM blog_post")
    count = cursor.fetchone()[0]
    print(f"   ✅ Found {count} blog posts")

    if count == 0:
        print("   ❌ No blog posts in database!")
        exit(1)
except Exception as e:
    print(f"   ❌ Error: {e}")
    exit(1)

# Test 3: Check bad-credit-mortgage post
print()
print("TEST 3: Bad credit mortgage post exists?")
try:
    cursor.execute("SELECT slug, title, published FROM blog_post WHERE slug = 'bad-credit-mortgage'")
    post = cursor.fetchone()

    if post:
        print(f"   ✅ Post found:")
        print(f"      Slug: {post[0]}")
        print(f"      Title: {post[1][:60]}...")
        print(f"      Published: {post[2]}")

        if not post[2]:
            print("   ⚠️  WARNING: Post is NOT published!")
    else:
        print("   ❌ Post NOT found in database!")
        exit(1)
except Exception as e:
    print(f"   ❌ Error: {e}")
    exit(1)

conn.close()

# Test 4: Check if template files exist
print()
print("TEST 4: Template files exist?")
import os

templates = [
    'templates/guide_post.html',
    'templates/guides_index.html',
    'templates/base.html'
]

all_exist = True
for tmpl in templates:
    if os.path.exists(tmpl):
        print(f"   ✅ {tmpl}")
    else:
        print(f"   ❌ {tmpl} NOT FOUND")
        all_exist = False

if not all_exist:
    exit(1)

# Test 5: Check if routes exist in main.py
print()
print("TEST 5: Routes exist in main.py?")

with open('main.py', 'r') as f:
    content = f.read()

routes_to_check = [
    ("@app.route('/guides/<slug>')", "guide_post route"),
    ("@app.route('/guides')", "guides index route"),
    ("def guide_post(slug):", "guide_post function"),
    ("def guides_index():", "guides_index function"),
]

all_routes_exist = True
for route_pattern, route_name in routes_to_check:
    if route_pattern in content:
        print(f"   ✅ {route_name}")
    else:
        print(f"   ❌ {route_name} NOT FOUND")
        all_routes_exist = False

if not all_routes_exist:
    exit(1)

print()
print("=" * 60)
print("✅ ALL TESTS PASSED!")
print("=" * 60)
print()
print("🔥 Blog system is ready to work!")
print()
print("⚠️  BUT - You need to RESTART the Flask app for changes to take effect!")
print()
print("📝 NEXT STEPS:")
print()
print("   IF RUNNING LOCALLY:")
print("   1. Stop the Flask app (Ctrl+C)")
print("   2. Start it again: python main.py")
print()
print("   IF DEPLOYED ON RAILWAY/RENDER:")
print("   1. Push your changes (already done!)")
print("   2. Railway will auto-redeploy")
print("   3. Wait 2-3 minutes")
print("   4. Try the link again")
print()
print("   THEN TEST:")
print("   - Visit: /guides/bad-credit-mortgage")
print("   - Click link from search results")
print()
print("=" * 60)
