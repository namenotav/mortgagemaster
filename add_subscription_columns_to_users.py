#!/usr/bin/env python3
"""
Add subscription columns to existing users2 table
SAFE: Only adds new columns, doesn't modify existing data
"""
import sqlite3

DB_PATH = 'instance/database.db'

def add_subscription_columns():
    """Add subscription columns to users2 table"""

    print("=" * 60)
    print("🔧 ADDING SUBSCRIPTION COLUMNS TO users2 TABLE")
    print("=" * 60)
    print()

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        # Check if users2 table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users2'")
        if not cursor.fetchone():
            print("❌ users2 table doesn't exist yet - will be created on app startup")
            conn.close()
            return False

        # Get existing columns
        cursor.execute("PRAGMA table_info(users2)")
        existing_columns = [col[1] for col in cursor.fetchall()]
        print(f"Found {len(existing_columns)} existing columns in users2 table")

        # Columns to add
        new_columns = [
            ('stripe_customer_id', 'VARCHAR(255)', 'NULL'),
            ('subscription_tier', 'VARCHAR(50)', "'free'"),
            ('subscription_status', 'VARCHAR(50)', "'inactive'"),
            ('stripe_subscription_id', 'VARCHAR(255)', 'NULL'),
            ('subscription_start_date', 'TIMESTAMP', 'NULL'),
            ('subscription_end_date', 'TIMESTAMP', 'NULL'),
        ]

        print("\nAdding subscription columns...")
        for col_name, col_type, default_val in new_columns:
            if col_name not in existing_columns:
                sql = f"ALTER TABLE users2 ADD COLUMN {col_name} {col_type} DEFAULT {default_val}"
                cursor.execute(sql)
                conn.commit()
                print(f"   ✅ Added column: {col_name}")
            else:
                print(f"   ⏭️  Column already exists: {col_name}")

        # Verify
        print("\n" + "=" * 60)
        print("VERIFICATION")
        print("=" * 60)
        cursor.execute("PRAGMA table_info(users2)")
        all_columns = cursor.fetchall()
        print(f"\n✅ users2 table now has {len(all_columns)} columns:")
        for col in all_columns:
            print(f"   - {col[1]} ({col[2]})")

        conn.close()

        print("\n" + "=" * 60)
        print("✅ SUBSCRIPTION COLUMNS ADDED SUCCESSFULLY!")
        print("=" * 60)

        return True

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        print("\nThis is safe - your existing data is untouched.")
        conn.close()
        return False

if __name__ == '__main__':
    add_subscription_columns()
