#!/usr/bin/env python3
"""
Railway PostgreSQL Backup Script (Python)
This downloads all your data from Railway to local JSON files
NO pg_dump required!
"""

import psycopg2
import json
from datetime import datetime
import os

def backup_database():
    print("=" * 50)
    print("Railway PostgreSQL Backup (Python)")
    print("=" * 50)
    print()

    # Get DATABASE_URL from user
    print("Go to Railway Dashboard > Your Project > PostgreSQL > Variables")
    print("Copy the DATABASE_URL value")
    print()
    database_url = input("Paste your DATABASE_URL here: ")

    if not database_url:
        print("❌ ERROR: No DATABASE_URL provided")
        return

    try:
        # Connect to Railway PostgreSQL
        print("\n🔄 Connecting to Railway database...")
        conn = psycopg2.connect(database_url)
        cursor = conn.cursor()
        print("✅ Connected successfully!")

        # Create backup directory
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = f"backup_{timestamp}"
        os.makedirs(backup_dir, exist_ok=True)
        print(f"\n📁 Creating backup in: {backup_dir}/")

        # List of tables to backup
        tables = ['users2', 'deal', 'blog_post', 'comparison_snapshot']

        total_records = 0

        for table in tables:
            try:
                print(f"\n🔄 Backing up table: {table}")

                # Get all data from table
                cursor.execute(f"SELECT * FROM {table}")
                rows = cursor.fetchall()

                # Get column names
                cursor.execute(f"""
                    SELECT column_name
                    FROM information_schema.columns
                    WHERE table_name = '{table}'
                    ORDER BY ordinal_position
                """)
                columns = [col[0] for col in cursor.fetchall()]

                # Convert to list of dictionaries
                data = []
                for row in rows:
                    row_dict = {}
                    for i, col in enumerate(columns):
                        value = row[i]
                        # Convert datetime to string
                        if isinstance(value, datetime):
                            value = value.isoformat()
                        row_dict[col] = value
                    data.append(row_dict)

                # Save to JSON file
                filename = f"{backup_dir}/{table}.json"
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, default=str)

                print(f"   ✅ {len(data)} records saved to {filename}")
                total_records += len(data)

            except Exception as e:
                print(f"   ⚠️  Warning: Could not backup {table}: {e}")
                continue

        # Close connection
        cursor.close()
        conn.close()

        # Create summary file
        summary = {
            'backup_date': datetime.now().isoformat(),
            'database_url': database_url.split('@')[1] if '@' in database_url else 'hidden',
            'total_records': total_records,
            'tables_backed_up': tables
        }

        with open(f"{backup_dir}/backup_summary.json", 'w') as f:
            json.dump(summary, f, indent=2)

        print("\n" + "=" * 50)
        print("✅ BACKUP COMPLETE!")
        print("=" * 50)
        print(f"📊 Total records backed up: {total_records}")
        print(f"📁 Location: {os.path.abspath(backup_dir)}/")
        print()
        print("Files created:")
        for file in os.listdir(backup_dir):
            filepath = os.path.join(backup_dir, file)
            size = os.path.getsize(filepath)
            print(f"   - {file} ({size:,} bytes)")
        print()

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        print("\nMake sure:")
        print("1. DATABASE_URL is correct")
        print("2. You have internet connection")
        print("3. Railway database is running")

if __name__ == '__main__':
    # Check if psycopg2 is installed
    try:
        import psycopg2
    except ImportError:
        print("❌ ERROR: psycopg2 not installed")
        print("\nInstall it with:")
        print("   pip install psycopg2-binary")
        exit(1)

    backup_database()
