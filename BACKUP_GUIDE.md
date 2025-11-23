# Complete Backup Guide for MortgageMaster

This guide shows you how to backup EVERYTHING from Railway to your computer.

## What Gets Backed Up

✅ PostgreSQL Database (all users, deals, blog posts)
✅ All code files
✅ All templates
✅ All configuration

---

## OPTION 1: Quick Python Backup (Recommended - Easiest)

### Step 1: Install Python Package

```bash
pip install psycopg2-binary
```

### Step 2: Run Backup Script

```bash
python backup_database.py
```

### Step 3: Follow the prompts

1. Go to Railway Dashboard: https://railway.app
2. Click your project → PostgreSQL service → Variables tab
3. Copy the `DATABASE_URL`
4. Paste it when prompted

### Result

You'll get a folder like `backup_20250123_143022/` containing:

```
backup_20250123_143022/
├── users2.json          (all your users)
├── deal.json            (all 30,000 deals)
├── blog_post.json       (all blog posts)
├── comparison_snapshot.json  (all saved comparisons)
└── backup_summary.json  (backup info)
```

**All data saved as JSON files you can open and read!**

---

## OPTION 2: Professional SQL Backup (Advanced)

### Requires: PostgreSQL client tools installed

**Windows:** Download from https://www.postgresql.org/download/windows/
**Mac:** `brew install postgresql`
**Linux:** `sudo apt-get install postgresql-client`

### Step 1: Get Railway DATABASE_URL

1. Railway Dashboard → Your Project → PostgreSQL → Variables
2. Copy `DATABASE_URL`

### Step 2: Run Backup

```bash
./backup_database.sh
```

Or manually:

```bash
pg_dump "YOUR_DATABASE_URL" > mortgagemaster_backup.sql
```

### Result

You get a `.sql` file that can restore the ENTIRE database perfectly.

**To restore later:**
```bash
psql your_local_database < mortgagemaster_backup.sql
```

---

## OPTION 3: Manual Database Export (Via Railway UI)

### If you don't want to use command line:

1. Go to Railway Dashboard
2. Click PostgreSQL service
3. Click "Data" tab
4. Click on each table (users2, deal, blog_post)
5. Export to CSV manually

**Slower, but works without any tools**

---

## Backing Up Code Files

### Your code is already on your computer in this folder!

Check if you have the latest:

```bash
git status
git pull origin claude/review-site-monetization-01KvAKjBt7WCHJPjVPPreCUq
```

### To create a complete copy:

**Option A: Git Clone (creates new folder)**
```bash
cd ~/Desktop
git clone https://github.com/namenotav/mortgagemaster.git mortgagemaster_backup
```

**Option B: Copy Current Folder**
```bash
cp -r /home/user/mortgagemaster ~/Desktop/mortgagemaster_backup_$(date +%Y%m%d)
```

**Option C: Create ZIP Archive**
```bash
cd /home/user
tar -czf mortgagemaster_backup_$(date +%Y%m%d).tar.gz mortgagemaster/
# Creates: mortgagemaster_backup_20250123.tar.gz
```

---

## Complete Backup Checklist

- [ ] Database backup (Python script OR pg_dump)
- [ ] Code files copied/cloned
- [ ] Verify backup files exist and aren't empty
- [ ] Store in safe location (external drive, cloud storage)
- [ ] Test restore on local PostgreSQL (optional but recommended)

---

## How to Restore Backup Later

### Restore Database (from JSON files):

```python
# You'd write a simple restore script:
import json
import psycopg2

conn = psycopg2.connect("your_local_database_url")
cursor = conn.cursor()

# For each table
with open('backup_20250123/users2.json') as f:
    users = json.load(f)
    for user in users:
        cursor.execute("INSERT INTO users2 (...) VALUES (...)", user.values())

conn.commit()
```

### Restore Database (from .sql file):

```bash
psql your_local_database < mortgagemaster_backup.sql
```

---

## File Sizes (Approximate)

- `users2.json`: 10-100 KB (depends on user count)
- `deal.json`: 5-20 MB (30,000 deals)
- `blog_post.json`: 50-500 KB (depends on blog count)
- `comparison_snapshot.json`: 100 KB - 5 MB (depends on saves)

**Total backup size: ~10-30 MB**

---

## Backup Schedule Recommendation

- **Daily**: If actively developing (run Python backup script)
- **Weekly**: If stable (run full pg_dump)
- **Before major changes**: Always backup before big updates

---

## Questions?

Run the backup and check:
1. Files are created in backup folder
2. Files are not empty (check file sizes)
3. You can open JSON files and see your data

**Your data is safe when you can see it in the backup files!**
