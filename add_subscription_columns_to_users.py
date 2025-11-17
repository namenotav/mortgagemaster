"""
Safe migration script to add subscription columns to users2 table
Can be run multiple times safely (idempotent)
"""
import sqlite3
import os

def column_exists(cursor, table_name, column_name):
    """Check if a column exists in a table"""
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = [row[1] for row in cursor.fetchall()]
    return column_name in columns

def run_migration():
    db_path = 'instance/database.db'

    # Check if database exists
    if not os.path.exists(db_path):
        print(f"❌ Database not found at {db_path}")
        print("   Run the app first to create the database")
        return False

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        print("🔧 Adding subscription columns to users2 table...")

        # List of columns to add
        columns_to_add = [
            ("stripe_customer_id", "VARCHAR(255)"),
            ("subscription_tier", "VARCHAR(50) DEFAULT 'free'"),
            ("subscription_status", "VARCHAR(50) DEFAULT 'inactive'"),
            ("stripe_subscription_id", "VARCHAR(255)"),
            ("subscription_start_date", "TIMESTAMP"),
            ("subscription_end_date", "TIMESTAMP")
        ]

        # Add each column if it doesn't exist
        for column_name, column_type in columns_to_add:
            if not column_exists(cursor, 'users2', column_name):
                try:
                    cursor.execute(f"ALTER TABLE users2 ADD COLUMN {column_name} {column_type}")
                    print(f"✅ Added column: {column_name}")
                except Exception as e:
                    print(f"⚠️  Could not add {column_name}: {e}")
            else:
                print(f"ℹ️  Column already exists: {column_name}")

        # Set default values for existing users
        cursor.execute("""
            UPDATE users2
            SET subscription_tier = 'free',
                subscription_status = 'inactive'
            WHERE subscription_tier IS NULL OR subscription_status IS NULL
        """)
        updated_count = cursor.rowcount
        if updated_count > 0:
            print(f"✅ Updated {updated_count} existing users with default subscription values")

        conn.commit()
        conn.close()

        print("\n✅ All subscription columns added successfully!")
        return True

    except Exception as e:
        print(f"❌ Error during migration: {e}")
        if conn:
            conn.close()
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("USER SUBSCRIPTION COLUMNS MIGRATION")
    print("=" * 60)
    success = run_migration()
    if success:
        print("\n🎉 Migration completed successfully!")
        print("   New columns: stripe_customer_id, subscription_tier, subscription_status,")
        print("                stripe_subscription_id, subscription_start_date, subscription_end_date")
    else:
        print("\n❌ Migration failed - check errors above")
    print("=" * 60)
