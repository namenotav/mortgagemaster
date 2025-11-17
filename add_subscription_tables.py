"""
Safe migration script to add subscription-related tables
Can be run multiple times safely (idempotent)
"""
import sqlite3
import os
from datetime import datetime

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

        print("🔧 Adding subscription tables...")

        # Table 1: Saved deals (Premium feature)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS saved_deal (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                deal_id INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users2(id) ON DELETE CASCADE,
                UNIQUE(user_id, deal_id)
            )
        """)
        print("✅ saved_deal table ready")

        # Table 2: Deal alerts (Premium feature)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS deal_alert (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                search_params TEXT,
                alert_frequency VARCHAR(20) DEFAULT 'daily',
                is_active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users2(id) ON DELETE CASCADE
            )
        """)
        print("✅ deal_alert table ready")

        # Table 3: Uploaded documents (Premium+ feature)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS uploaded_document (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                document_type VARCHAR(50),
                file_path VARCHAR(500),
                uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users2(id) ON DELETE CASCADE
            )
        """)
        print("✅ uploaded_document table ready")

        # Table 4: AI eligibility results (Premium+ feature)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS eligibility_result (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                deal_id INTEGER NOT NULL,
                approval_score INTEGER,
                reasons TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users2(id) ON DELETE CASCADE
            )
        """)
        print("✅ eligibility_result table ready")

        # Table 5: Consultation bookings (Premium+ feature)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS consultation_booking (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                calendly_event_id VARCHAR(255),
                booking_time TIMESTAMP,
                status VARCHAR(50) DEFAULT 'scheduled',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users2(id) ON DELETE CASCADE
            )
        """)
        print("✅ consultation_booking table ready")

        conn.commit()
        conn.close()

        print("\n✅ All subscription tables created successfully!")
        print("   Tables: saved_deal, deal_alert, uploaded_document, eligibility_result, consultation_booking")
        return True

    except Exception as e:
        print(f"❌ Error during migration: {e}")
        if conn:
            conn.close()
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("SUBSCRIPTION TABLES MIGRATION")
    print("=" * 60)
    success = run_migration()
    if success:
        print("\n🎉 Migration completed successfully!")
    else:
        print("\n❌ Migration failed - check errors above")
    print("=" * 60)
