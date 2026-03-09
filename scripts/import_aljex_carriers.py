#!/usr/bin/env python3
"""
Import carriers from Aljex CSV export
Run this once to populate your carrier database
"""

import sys
import os
import csv

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from app.database import Database
from channels.sms import SMSChannel

def normalize_phone(phone):
    """Normalize phone number"""
    if not phone:
        return None
    digits = ''.join(filter(str.isdigit, str(phone)))
    if len(digits) == 10:
        digits = '1' + digits
    if digits:
        return '+' + digits
    return None

def import_carriers(csv_file):
    """Import carriers from CSV"""
    db = Database()
    sms = SMSChannel()

    print(f"\n🦅 Importing carriers from {csv_file}...\n")

    imported = 0
    skipped = 0
    errors = 0

    with open(csv_file, 'r') as f:
        reader = csv.DictReader(f)

        for row in reader:
            try:
                # Get phone number
                phone_raw = row.get('Phone') or row.get('phone') or row.get('PHONE')
                phone = normalize_phone(phone_raw)

                if not phone:
                    print(f"⚠️  Skipped {row.get('Company Name', 'Unknown')}: No phone number")
                    skipped += 1
                    continue

                # Check if US/Canada
                if not sms.is_us_phone(phone):
                    print(f"⚠️  Skipped {phone}: International number (fraud protection)")
                    skipped += 1
                    continue

                # Check if already exists
                existing = db.get_carrier_by_phone(phone)
                if existing:
                    print(f"⚠️  Skipped {phone}: Already in database")
                    skipped += 1
                    continue

                # Get other fields
                company_name = (row.get('Company Name') or row.get('company_name') or
                              row.get('Name') or row.get('name') or 'Unknown')
                mc_number = row.get('MC Number') or row.get('mc_number') or row.get('MC')
                email = row.get('Email') or row.get('email')
                aljex_id = row.get('Carrier ID') or row.get('carrier_id') or row.get('ID')

                # Create carrier
                db.create_carrier(
                    phone=phone,
                    company_name=company_name,
                    mc_number=mc_number,
                    email=email,
                    aljex_carrier_id=aljex_id,
                    aljex_sync_status='synced',
                    onboarding_complete=True
                )

                print(f"✓ Imported: {company_name} ({phone})")
                imported += 1

            except Exception as e:
                print(f"✗ Error importing row: {e}")
                errors += 1

    print(f"\n" + "="*60)
    print(f"Import Complete!")
    print(f"="*60)
    print(f"✓ Imported: {imported} carriers")
    print(f"⚠️  Skipped: {skipped} carriers")
    print(f"✗ Errors: {errors}")
    print(f"="*60 + "\n")

def main():
    if len(sys.argv) < 2:
        print("""
Usage: python3 scripts/import_aljex_carriers.py <csv_file>

Export carriers from Aljex and run:
  python3 scripts/import_aljex_carriers.py aljex_carriers.csv

CSV should have columns:
  - Company Name (or Name)
  - Phone
  - Email (optional)
  - MC Number (optional)
  - Carrier ID (optional)
""")
        sys.exit(1)

    csv_file = sys.argv[1]

    if not os.path.exists(csv_file):
        print(f"Error: File not found: {csv_file}")
        sys.exit(1)

    import_carriers(csv_file)

if __name__ == '__main__':
    main()
