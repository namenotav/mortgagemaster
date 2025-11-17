#!/usr/bin/env python3
"""
Load alternative mortgage deals into the database
"""
import sqlite3
import os

# Database path
DB_PATH = 'instance/database.db'
SQL_FILE = 'seed_alternative_mortgages.sql'

def load_deals():
    """Load alternative mortgage deals from SQL file"""

    # Check if database exists
    if not os.path.exists(DB_PATH):
        print(f"❌ Database not found at {DB_PATH}")
        return False

    # Check if SQL file exists
    if not os.path.exists(SQL_FILE):
        print(f"❌ SQL file not found at {SQL_FILE}")
        return False

    # Connect to database
    print(f"📂 Connecting to database: {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Read SQL file
    print(f"📄 Reading SQL file: {SQL_FILE}")
    with open(SQL_FILE, 'r') as f:
        sql_content = f.read()

    # Split by semicolons to get individual statements
    statements = [s.strip() for s in sql_content.split(';') if s.strip() and not s.strip().startswith('--')]

    print(f"📊 Found {len(statements)} SQL statements to execute")

    # Execute each statement
    success_count = 0
    error_count = 0

    for i, statement in enumerate(statements, 1):
        # Skip comments and empty lines
        if statement.startswith('--') or not statement.strip():
            continue

        try:
            cursor.execute(statement)
            success_count += 1
            print(f"✅ Statement {i}/{len(statements)} executed successfully")
        except sqlite3.Error as e:
            error_count += 1
            print(f"❌ Error executing statement {i}: {e}")
            print(f"   Statement: {statement[:100]}...")

    # Commit changes
    conn.commit()
    print(f"\n💾 Changes committed to database")

    # Verify insertion - count deals
    cursor.execute("SELECT COUNT(*) FROM deals")
    total_deals = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM deals WHERE lender_type IN ('bank_statement', 'asset_based', 'bridging', 'credit_union', 'guarantor', 'shared_ownership', 'alternative_finance')")
    alternative_deals = cursor.fetchone()[0]

    print(f"\n📊 RESULTS:")
    print(f"   Total deals in database: {total_deals}")
    print(f"   Alternative deals: {alternative_deals}")
    print(f"   Success: {success_count} statements")
    print(f"   Errors: {error_count} statements")

    # Close connection
    conn.close()

    if error_count == 0:
        print(f"\n🎉 SUCCESS! All {alternative_deals} alternative mortgage deals loaded!")
        return True
    else:
        print(f"\n⚠️  Completed with {error_count} errors")
        return False

if __name__ == '__main__':
    print("=" * 60)
    print("🚀 LOADING ALTERNATIVE MORTGAGE DEALS")
    print("=" * 60)
    print()

    success = load_deals()

    print()
    print("=" * 60)

    if success:
        print("✅ All alternative deals are now available in your database!")
        print()
        print("🎯 Test it now:")
        print("   1. Go to your website")
        print("   2. Search with Credit Score: 400")
        print("   3. You should now see 7+ deals!")
    else:
        print("❌ There were some errors. Check the output above.")

    print("=" * 60)
