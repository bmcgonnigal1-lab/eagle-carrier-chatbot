#!/usr/bin/env python3
import os
import sys
import csv
import psycopg2
from datetime import datetime

DATABASE_URL = os.environ.get('DATABASE_URL')
if not DATABASE_URL:
    print("❌ ERROR: DATABASE_URL not set")
    sys.exit(1)

csv_file = sys.argv[1] if len(sys.argv) > 1 else 'carrier 30 days.csv'
print(f"📊 Importing from: {csv_file}")

conn = psycopg2.connect(DATABASE_URL)
added = 0
skipped = 0
errors = 0

with open(csv_file, 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        cursor = conn.cursor()
        try:
            name = row.get('Carrier', '').strip()
            mc = row.get('MC #', '').strip()
            dot = row.get('DOT #', '').strip()
            
            if not name:
                skipped += 1
                cursor.close()
                continue
            
            # Check if exists
            cursor.execute("SELECT id FROM carriers WHERE (mc_number = %s AND mc_number IS NOT NULL) OR (dot_number = %s AND dot_number IS NOT NULL)", (mc if mc else None, dot if dot else None))
            if cursor.fetchone():
                skipped += 1
                cursor.close()
                continue
            
            # Insert carrier only (skip contacts/insurance for now)
            cursor.execute("""
                INSERT INTO carriers (
                    legal_name, dba_name, mc_number, dot_number, 
                    physical_address_line1, physical_city, physical_state, physical_zip,
                    phone, email, ein, status, source, created_at, updated_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                name, 
                name,
                mc if mc else None, 
                dot if dot else None,
                row.get('Address', '').strip() or None,
                row.get('City', '').strip() or None,
                row.get('State', '').strip() or None,
                row.get('Zip', '').strip() or None,
                row.get('Phone', '').strip() or None,
                row.get('Email', '').strip() or None,
                row.get('FED ID', '').strip() or None,
                'active',
                'aljex_import',
                datetime.now(),
                datetime.now()
            ))
            
            conn.commit()
            print(f"  ✅ {name} (MC: {mc}, DOT: {dot})")
            added += 1
            
        except Exception as e:
            conn.rollback()
            print(f"  ❌ {row.get('Carrier', '?')}: {str(e)[:60]}")
            errors += 1
        finally:
            cursor.close()

conn.close()
print(f"\n🎉 Import complete!")
print(f"   • Carriers added: {added}")
print(f"   • Skipped: {skipped}")
print(f"   • Errors: {errors}")
