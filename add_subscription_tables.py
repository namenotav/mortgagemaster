#!/usr/bin/env python3
"""
Add subscription tables to database
SAFE: Only adds new tables, doesn't modify existing ones
"""
import sqlite3

DB_PATH = 'instance/database.db'

def add_subscription_tables():
    """Add subscription-related tables"""

    print("=" * 60)
    print("🔧 ADDING SUBSCRIPTION TABLES")
    print("=" * 60)
    print()

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        # 1. Subscription users table
        print("Creating subscription_user table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS subscription_user (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email VARCHAR(255) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                name VARCHAR(255),
                stripe_customer_id VARCHAR(255),
                subscription_tier VARCHAR(50) DEFAULT 'free',
                subscription_status VARCHAR(50) DEFAULT 'inactive',
                stripe_subscription_id VARCHAR(255),
                subscription_start_date TIMESTAMP,
                subscription_end_date TIMESTAMP,
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
        print("✅ subscription_user table created")

        # 2. Saved deals table
        print("\nCreating saved_deal table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS saved_deal (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                deal_id INTEGER NOT NULL,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES subscription_user(id),
                FOREIGN KEY (deal_id) REFERENCES deal(id),
                UNIQUE(user_id, deal_id)
            )
        """)
        conn.commit()
        print("✅ saved_deal table created")

        # 3. Deal alerts table
        print("\nCreating deal_alert table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS deal_alert (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                alert_name VARCHAR(255),
                search_params TEXT,
                alert_frequency VARCHAR(50) DEFAULT 'daily',
                last_sent TIMESTAMP,
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES subscription_user(id)
            )
        """)
        conn.commit()
        print("✅ deal_alert table created")

        # 4. Uploaded documents table (Premium+)
        print("\nCreating uploaded_document table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS uploaded_document (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                document_type VARCHAR(50),
                original_filename VARCHAR(255),
                stored_filename VARCHAR(255),
                file_path VARCHAR(500),
                file_size INTEGER,
                uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES subscription_user(id)
            )
        """)
        conn.commit()
        print("✅ uploaded_document table created")

        # 5. AI eligibility results table (Premium+)
        print("\nCreating eligibility_result table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS eligibility_result (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                deal_id INTEGER NOT NULL,
                approval_score INTEGER,
                approval_likelihood VARCHAR(50),
                reasons TEXT,
                ai_model VARCHAR(50),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES subscription_user(id),
                FOREIGN KEY (deal_id) REFERENCES deal(id)
            )
        """)
        conn.commit()
        print("✅ eligibility_result table created")

        # 6. Consultation bookings table (Premium+)
        print("\nCreating consultation_booking table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS consultation_booking (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                booking_date TIMESTAMP,
                calendly_event_id VARCHAR(255),
                status VARCHAR(50) DEFAULT 'scheduled',
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES subscription_user(id)
            )
        """)
        conn.commit()
        print("✅ consultation_booking table created")

        # Create indexes for performance
        print("\nCreating indexes...")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_sub_user_email ON subscription_user(email)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_sub_user_tier ON subscription_user(subscription_tier)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_sub_user_stripe ON subscription_user(stripe_customer_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_saved_deal_user ON saved_deal(user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_deal_alert_user ON deal_alert(user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_deal_alert_active ON deal_alert(is_active)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_uploaded_doc_user ON uploaded_document(user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_eligibility_user ON eligibility_result(user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_consultation_user ON consultation_booking(user_id)")
        conn.commit()
        print("✅ Indexes created")

        # Verify tables were created
        print("\n" + "=" * 60)
        print("VERIFICATION")
        print("=" * 60)
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '%subscription%' OR name LIKE '%saved%' OR name LIKE '%alert%' OR name LIKE '%eligibility%' OR name LIKE '%consultation%' OR name LIKE '%uploaded%'")
        tables = cursor.fetchall()
        print(f"\n✅ Found {len(tables)} subscription-related tables:")
        for table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table[0]}")
            count = cursor.fetchone()[0]
            print(f"   - {table[0]}: {count} rows")

        conn.close()

        print("\n" + "=" * 60)
        print("✅ SUBSCRIPTION TABLES ADDED SUCCESSFULLY!")
        print("=" * 60)
        print("\nNext step: Add subscription models to main.py")

        return True

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        print("\nThis is safe - your existing database is untouched.")
        conn.close()
        return False

if __name__ == '__main__':
    add_subscription_tables()
