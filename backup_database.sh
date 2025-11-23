#!/bin/bash

# Railway PostgreSQL Backup Script
# Usage: ./backup_database.sh

echo "==================================="
echo "Railway PostgreSQL Backup Script"
echo "==================================="
echo ""

# Ask for Railway DATABASE_URL
echo "Go to Railway Dashboard > Your Project > PostgreSQL > Variables"
echo "Copy the DATABASE_URL value"
echo ""
read -p "Paste your DATABASE_URL here: " DATABASE_URL

# Generate backup filename with timestamp
BACKUP_FILE="mortgagemaster_backup_$(date +%Y%m%d_%H%M%S).sql"

echo ""
echo "Creating backup: $BACKUP_FILE"
echo ""

# Run pg_dump
pg_dump "$DATABASE_URL" > "$BACKUP_FILE"

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ SUCCESS! Database backed up to:"
    echo "   $BACKUP_FILE"
    echo ""
    echo "File size: $(ls -lh $BACKUP_FILE | awk '{print $5}')"
    echo ""
    echo "To restore later:"
    echo "   psql YOUR_LOCAL_DATABASE < $BACKUP_FILE"
else
    echo ""
    echo "❌ ERROR: Backup failed"
    echo "Make sure PostgreSQL client tools are installed"
fi
