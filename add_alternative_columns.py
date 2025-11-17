#!/usr/bin/env python3
"""
Add columns needed for alternative mortgage deals
"""
import sqlite3

DB_PATH = 'instance/database.db'

def add_columns():
    """Add new columns to deal table"""

    print("=" * 60)
    print("🔧 ADDING COLUMNS FOR ALTERNATIVE MORTGAGES")
    print("=" * 60)
    print()

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # List of columns to add
    new_columns = [
        ("lender_type", "VARCHAR(50)", "'standard'"),  # Type of lender
        ("min_credit_score", "INTEGER", "680"),  # Minimum credit score accepted
        ("min_income", "INTEGER", "0"),  # Minimum income (0 = no requirement)
        ("accepts_bad_credit", "BOOLEAN", "FALSE"),  # Accepts bad credit?
        ("accepts_low_income", "BOOLEAN", "FALSE"),  # Accepts low income?
        ("accepts_self_employed", "BOOLEAN", "FALSE"),  # Accepts self-employed?
    ]

    success_count = 0
    skip_count = 0

    for column_name, column_type, default_value in new_columns:
        try:
            # Try to add the column
            sql = f"ALTER TABLE deal ADD COLUMN {column_name} {column_type} DEFAULT {default_value}"
            cursor.execute(sql)
            print(f"✅ Added column: {column_name} ({column_type})")
            success_count += 1
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e).lower():
                print(f"⏭️  Column already exists: {column_name}")
                skip_count += 1
            else:
                print(f"❌ Error adding column {column_name}: {e}")

    # Commit changes
    conn.commit()

    print()
    print(f"📊 RESULTS:")
    print(f"   Columns added: {success_count}")
    print(f"   Already existed: {skip_count}")

    # Show updated schema
    print()
    print("📋 UPDATED SCHEMA:")
    cursor.execute("PRAGMA table_info(deal)")
    columns = cursor.fetchall()

    for col in columns:
        print(f"   - {col[1]} ({col[2]})")

    conn.close()

    print()
    print("=" * 60)
    print("✅ Database schema updated successfully!")
    print("=" * 60)

    return True

if __name__ == '__main__':
    add_columns()
