#!/usr/bin/env python3
"""
Import loads from Aljex CSV export
Converts Aljex load board CSV to database loads
"""

import sys
import os
import csv
import sqlite3
from datetime import datetime

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

def convert_equipment_type(aljex_type):
    """Convert Aljex equipment codes to readable names"""
    mapping = {
        'V': 'Dry Van',
        'R': 'Reefer',
        'VR': 'Reefer',
        'BOX': 'Box Truck',
        'F': 'Flatbed',
        'FB': 'Flatbed',
        'SD': 'Step Deck',
        'RGN': 'RGN',
        'DD': 'Double Drop',
        'LB': 'Lowboy',
        'TANK': 'Tanker',
        'PO': 'Power Only',
        'HB': 'Hotshot'
    }
    return mapping.get(aljex_type.upper(), 'Dry Van')

def parse_date(date_str):
    """Parse Aljex date format (MM/DD/YY) to YYYY-MM-DD"""
    if not date_str or date_str.strip() == '':
        return None
    try:
        # Handle MM/DD/YY format
        dt = datetime.strptime(date_str, '%m/%d/%y')
        return dt.strftime('%Y-%m-%d')
    except:
        return None

def import_loads(csv_file, db_path='data/loads.db'):
    """Import loads from Aljex CSV"""

    print(f"\n🦅 Importing loads from {csv_file}...\n")

    # Create database if needed
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Create loads table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS loads (
            load_id TEXT PRIMARY KEY,
            customer TEXT,
            origin_state TEXT,
            origin_city TEXT,
            destination_state TEXT,
            destination_city TEXT,
            ship_date TEXT,
            delivery_date TEXT,
            equipment_type TEXT,
            trailer_length TEXT,
            weight INTEGER,
            rate INTEGER,
            status TEXT,
            commodity TEXT,
            special_instructions TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ')

    imported = 0
    skipped = 0
    errors = 0

    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)

        for row in reader:
            try:
                # Skip covered loads
                status = row.get('Status', '').upper()
                if status == 'COVERED':
                    skipped += 1
                    continue

                # Get load ID (Pro number)
                load_id = row.get('Pro', '').strip()
                if not load_id:
                    skipped += 1
                    continue

                # Check if already exists
                cursor.execute('SELECT load_id FROM loads WHERE load_id = ?', (load_id,))
                if cursor.fetchone():
                    skipped += 1
                    continue

                # Parse data
                customer = row.get('Customer', '').strip()
                origin_state = row.get('Pick Up', '').strip()
                origin_city = row.get('PU City', '').strip()
                dest_state = row.get('Consignee', '').strip()
                dest_city = row.get('Cons City', '').strip()
                ship_date = parse_date(row.get('Ship Date', ''))
                del_date = parse_date(row.get('Del Date', ''))
                equipment_code = row.get('Type', 'V').strip()
                equipment_type = convert_equipment_type(equipment_code)
                trailer_length = row.get('Deck Space', '53').strip()

                # Parse weight
                weight_str = row.get('Weight', '0').replace(',', '').strip()
                try:
                    weight = int(weight_str) if weight_str else 0
                except:
                    weight = 0

                # Estimate rate (you'll need to add a rate column to your Aljex export)
                # For now, using a simple estimate based on distance/weight
                rate = 2000  # Default rate

                # Insert load
                cursor.execute('''
                    INSERT INTO loads
                    (load_id, customer, origin_state, origin_city, destination_state,
                     destination_city, ship_date, delivery_date, equipment_type,
                     trailer_length, weight, rate, status, commodity)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    load_id,
                    customer,
                    origin_state,
                    origin_city,
                    dest_state,
                    dest_city,
                    ship_date,
                    del_date,
                    equipment_type,
                    trailer_length,
                    weight,
                    rate,
                    'available',
                    customer  # Use customer as commodity for now
                ))

                print(f"✓ Imported: {load_id} - {origin_city}, {origin_state} → {dest_city}, {dest_state}")
                imported += 1

            except Exception as e:
                print(f"✗ Error importing {row.get('Pro', 'unknown')}: {e}")
                errors += 1

    conn.commit()
    conn.close()

    print(f"\n" + "="*60)
    print(f"Import Complete!")
    print(f"="*60)
    print(f"✓ Imported: {imported} loads")
    print(f"⚠️  Skipped: {skipped} loads (covered or duplicate)")
    print(f"✗ Errors: {errors}")
    print(f"="*60 + "\n")

def main():
    if len(sys.argv) < 2:
        print("""
Usage: python3 scripts/import_aljex_loads.py <csv_file>

Export loads from Aljex and run:
  python3 scripts/import_aljex_loads.py aljex_loads.csv

This will import all OPEN loads into the database.
""")
        sys.exit(1)

    csv_file = sys.argv[1]

    if not os.path.exists(csv_file):
        print(f"Error: File not found: {csv_file}")
        sys.exit(1)

    import_loads(csv_file)

if __name__ == '__main__':
    main()
