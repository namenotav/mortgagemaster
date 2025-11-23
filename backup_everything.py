#!/usr/bin/env python3
"""
Complete Backup Script - Backs up EVERYTHING
- PostgreSQL database (all tables to JSON)
- All code files
- Creates a complete archive
"""

import os
import shutil
import json
from datetime import datetime
import sys

def backup_everything():
    print("=" * 60)
    print("   COMPLETE MORTGAGEMASTER BACKUP")
    print("=" * 60)
    print()

    # Create main backup directory
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_root = f"COMPLETE_BACKUP_{timestamp}"
    os.makedirs(backup_root, exist_ok=True)

    print(f"📁 Creating backup in: {backup_root}/")
    print()

    # ==========================================
    # PART 1: Backup Code Files
    # ==========================================
    print("STEP 1: Backing up code files...")
    print("-" * 60)

    code_backup_dir = os.path.join(backup_root, "code")
    os.makedirs(code_backup_dir, exist_ok=True)

    # List of important files/folders to backup
    items_to_backup = [
        'main.py',
        'config.py',
        'requirements.txt',
        'templates/',
        'static/',
        '.env.example',
        'BACKUP_GUIDE.md',
        'backup_database.py',
        'backup_database.sh'
    ]

    files_backed_up = 0
    for item in items_to_backup:
        if os.path.exists(item):
            dest = os.path.join(code_backup_dir, item)
            try:
                if os.path.isdir(item):
                    shutil.copytree(item, dest)
                    print(f"   ✅ Copied folder: {item}")
                else:
                    shutil.copy2(item, dest)
                    print(f"   ✅ Copied file: {item}")
                files_backed_up += 1
            except Exception as e:
                print(f"   ⚠️  Warning: Could not copy {item}: {e}")
        else:
            print(f"   ⚠️  Not found: {item}")

    print(f"\n✅ Code backup complete: {files_backed_up} items backed up")
    print()

    # ==========================================
    # PART 2: Backup Database
    # ==========================================
    print("STEP 2: Backing up PostgreSQL database...")
    print("-" * 60)

    db_backup_dir = os.path.join(backup_root, "database")
    os.makedirs(db_backup_dir, exist_ok=True)

    print("\nOption 1: Database backup via Python (recommended)")
    print("Option 2: Skip database backup (code only)")
    print()
    choice = input("Enter choice (1 or 2): ").strip()

    if choice == "1":
        try:
            import psycopg2

            print("\nGo to Railway Dashboard > Your Project > PostgreSQL > Variables")
            print("Copy the DATABASE_URL value")
            print()
            database_url = input("Paste your DATABASE_URL here (or press Enter to skip): ").strip()

            if database_url:
                print("\n🔄 Connecting to Railway database...")
                conn = psycopg2.connect(database_url)
                cursor = conn.cursor()
                print("✅ Connected!")

                tables = ['users2', 'deal', 'blog_post', 'comparison_snapshot']
                total_records = 0

                for table in tables:
                    try:
                        print(f"\n🔄 Backing up: {table}")
                        cursor.execute(f"SELECT * FROM {table}")
                        rows = cursor.fetchall()

                        cursor.execute(f"""
                            SELECT column_name
                            FROM information_schema.columns
                            WHERE table_name = '{table}'
                            ORDER BY ordinal_position
                        """)
                        columns = [col[0] for col in cursor.fetchall()]

                        data = []
                        for row in rows:
                            row_dict = {}
                            for i, col in enumerate(columns):
                                value = row[i]
                                if isinstance(value, datetime):
                                    value = value.isoformat()
                                row_dict[col] = value
                            data.append(row_dict)

                        filename = os.path.join(db_backup_dir, f"{table}.json")
                        with open(filename, 'w', encoding='utf-8') as f:
                            json.dump(data, f, indent=2, default=str)

                        print(f"   ✅ {len(data)} records saved")
                        total_records += len(data)

                    except Exception as e:
                        print(f"   ⚠️  Could not backup {table}: {e}")

                cursor.close()
                conn.close()

                # Save summary
                summary = {
                    'backup_date': datetime.now().isoformat(),
                    'total_records': total_records,
                    'tables': tables
                }
                with open(os.path.join(db_backup_dir, 'database_summary.json'), 'w') as f:
                    json.dump(summary, f, indent=2)

                print(f"\n✅ Database backup complete: {total_records} total records")
            else:
                print("\n⚠️  Skipped database backup")

        except ImportError:
            print("\n⚠️  psycopg2 not installed. Run: pip install psycopg2-binary")
            print("   Skipping database backup")
        except Exception as e:
            print(f"\n⚠️  Database backup failed: {e}")
    else:
        print("\n⚠️  Skipped database backup (code only)")

    print()

    # ==========================================
    # PART 3: Create Summary
    # ==========================================
    print("STEP 3: Creating backup summary...")
    print("-" * 60)

    summary_file = os.path.join(backup_root, "BACKUP_INFO.txt")
    with open(summary_file, 'w') as f:
        f.write("=" * 60 + "\n")
        f.write("   MORTGAGEMASTER COMPLETE BACKUP\n")
        f.write("=" * 60 + "\n\n")
        f.write(f"Backup Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Backup Location: {os.path.abspath(backup_root)}\n\n")
        f.write("Contents:\n")
        f.write("-" * 60 + "\n")
        f.write(f"✅ Code files: {files_backed_up} items\n")
        f.write(f"✅ Database: JSON exports in database/ folder\n\n")
        f.write("To restore:\n")
        f.write("1. Copy code files to new location\n")
        f.write("2. Run: pip install -r requirements.txt\n")
        f.write("3. Import database JSON files to PostgreSQL\n")
        f.write("4. Configure .env with new DATABASE_URL\n\n")
        f.write("Files included:\n")
        for root, dirs, files in os.walk(backup_root):
            level = root.replace(backup_root, '').count(os.sep)
            indent = ' ' * 2 * level
            f.write(f"{indent}{os.path.basename(root)}/\n")
            sub_indent = ' ' * 2 * (level + 1)
            for file in files[:10]:  # First 10 files per directory
                f.write(f"{sub_indent}{file}\n")
            if len(files) > 10:
                f.write(f"{sub_indent}... and {len(files) - 10} more files\n")

    # Calculate total backup size
    total_size = 0
    for root, dirs, files in os.walk(backup_root):
        for file in files:
            filepath = os.path.join(root, file)
            total_size += os.path.getsize(filepath)

    # ==========================================
    # FINAL SUMMARY
    # ==========================================
    print()
    print("=" * 60)
    print("   ✅ BACKUP COMPLETE!")
    print("=" * 60)
    print()
    print(f"📁 Backup location: {os.path.abspath(backup_root)}/")
    print(f"📊 Total size: {total_size / 1024 / 1024:.2f} MB")
    print()
    print("Backup contains:")
    print(f"   ✅ Code files backed up")
    print(f"   ✅ Database backed up (if you provided DATABASE_URL)")
    print(f"   ✅ Summary file: BACKUP_INFO.txt")
    print()
    print("Next steps:")
    print("   1. Copy this folder to safe location (USB drive, cloud, etc.)")
    print("   2. Keep multiple backups (daily/weekly)")
    print(f"   3. Test restore to verify backup works")
    print()
    print(f"🎉 Your MortgageMaster data is now safely backed up!")
    print()

if __name__ == '__main__':
    try:
        backup_everything()
    except KeyboardInterrupt:
        print("\n\n⚠️  Backup cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ ERROR: {e}")
        sys.exit(1)
