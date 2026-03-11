#!/usr/bin/env python3
"""
Verify Comprehensive Database Schema
Tests that all 12 tables are created correctly
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import Database


def verify_schema():
    """Verify comprehensive database schema"""
    print("\n" + "="*70)
    print("COMPREHENSIVE CARRIER DATABASE SCHEMA VERIFICATION")
    print("="*70 + "\n")

    # Initialize database
    db = Database("data/carriers_test.db")
    conn = db.get_connection()
    cursor = conn.cursor()

    # Get all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = [row[0] for row in cursor.fetchall()]

    expected_tables = [
        'carriers',
        'carrier_equipment',
        'carrier_insurance',
        'carrier_safety_scores',
        'carrier_performance',
        'carrier_lanes',
        'carrier_documents',
        'carrier_contacts',
        'carrier_banking',
        'carrier_rates',
        'carrier_queries',
        'booking_requests',
        'carrier_profiles',
        'conversation_context'
    ]

    print(f"✅ Total Tables Created: {len(tables)}\n")

    # Verify each table
    for table_name in expected_tables:
        if table_name in tables:
            # Get column count
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()

            print(f"✅ {table_name}")
            print(f"   └─ {len(columns)} columns")

            # Show sample columns
            sample_cols = [col[1] for col in columns[:5]]
            if len(columns) > 5:
                print(f"      {', '.join(sample_cols)}... (+{len(columns)-5} more)")
            else:
                print(f"      {', '.join(sample_cols)}")
        else:
            print(f"❌ {table_name} - MISSING")

    print("\n" + "="*70)

    # Get indexes
    cursor.execute("SELECT name FROM sqlite_master WHERE type='index' ORDER BY name")
    indexes = [row[0] for row in cursor.fetchall()]

    print(f"\n✅ Total Indexes Created: {len(indexes)}\n")

    # Show some key indexes
    key_indexes = [idx for idx in indexes if 'carriers' in idx or 'performance' in idx]
    for idx in key_indexes[:10]:
        print(f"   • {idx}")

    if len(indexes) > 10:
        print(f"   ... and {len(indexes)-10} more")

    print("\n" + "="*70)

    # Test carrier creation
    print("\n🧪 Testing Carrier Creation...\n")

    try:
        carrier_id = db.create_carrier(
            phone='+14045551234',
            email='test@example.com',
            legal_name='Test Carrier LLC',
            mc_number='MC123456',
            dot_number='DOT789012',
            status='active'
        )

        print(f"✅ Carrier Created: ID #{carrier_id}")

        # Retrieve carrier
        carrier = db.get_carrier(carrier_id)
        print(f"✅ Carrier Retrieved: {carrier['legal_name']}")
        print(f"   • MC#: {carrier['mc_number']}")
        print(f"   • DOT#: {carrier['dot_number']}")
        print(f"   • Phone: {carrier['phone']}")

    except Exception as e:
        print(f"❌ Carrier Creation Failed: {e}")

    print("\n" + "="*70)
    print("✅ DATABASE VERIFICATION COMPLETE")
    print("="*70 + "\n")

    conn.close()

    # Cleanup test database
    import os
    if os.path.exists("data/carriers_test.db"):
        os.remove("data/carriers_test.db")
        print("🧹 Test database cleaned up\n")


if __name__ == '__main__':
    verify_schema()
