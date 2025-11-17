#!/usr/bin/env python3
"""
Add blog table to database
"""
import sqlite3
from datetime import datetime

DB_PATH = 'instance/database.db'

def add_blog_table():
    """Create blog table"""

    print("=" * 60)
    print("📝 CREATING BLOG TABLE")
    print("=" * 60)
    print()

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Create blog table
    sql = """
    CREATE TABLE IF NOT EXISTS blog_post (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        slug VARCHAR(200) UNIQUE NOT NULL,
        title VARCHAR(500) NOT NULL,
        meta_description VARCHAR(500),
        content TEXT NOT NULL,
        author VARCHAR(100) DEFAULT 'MortgageDealsHub',
        category VARCHAR(100),
        keywords VARCHAR(500),
        featured_image VARCHAR(500),
        published BOOLEAN DEFAULT TRUE,
        views INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """

    try:
        cursor.execute(sql)
        print("✅ Blog table created successfully!")
    except sqlite3.OperationalError as e:
        if "already exists" in str(e).lower():
            print("⏭️  Blog table already exists")
        else:
            print(f"❌ Error: {e}")
            return False

    # Create index for faster lookups
    try:
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_blog_slug ON blog_post(slug)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_blog_published ON blog_post(published)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_blog_category ON blog_post(category)")
        print("✅ Indexes created")
    except Exception as e:
        print(f"⚠️  Index creation: {e}")

    conn.commit()

    # Show table schema
    print()
    print("📋 BLOG TABLE SCHEMA:")
    cursor.execute("PRAGMA table_info(blog_post)")
    columns = cursor.fetchall()
    for col in columns:
        print(f"   - {col[1]} ({col[2]})")

    conn.close()

    print()
    print("=" * 60)
    print("✅ Blog table ready!")
    print("=" * 60)

    return True

if __name__ == '__main__':
    add_blog_table()
