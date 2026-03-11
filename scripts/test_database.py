#!/usr/bin/env python3
"""
Test Database Connection and Schema
Run after deploying to verify everything works
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_database():
    """Test database connection and basic operations"""
    print("\n" + "="*60)
    print("🧪 TESTING DATABASE CONNECTION")
    print("="*60 + "\n")

    # Check if DATABASE_URL is set
    database_url = os.getenv('DATABASE_URL')

    if not database_url:
        print("❌ DATABASE_URL environment variable not set")
        print("\nSet it with:")
        print("  export DATABASE_URL='postgresql://user:pass@host:port/db'")
        print("  or")
        print("  export DATABASE_URL='sqlite:///data/carriers.db'")
        return False

    print(f"✅ DATABASE_URL found")

    # Determine database type
    is_postgres = database_url.startswith('postgres')
    db_type = "PostgreSQL" if is_postgres else "SQLite"
    print(f"📊 Database Type: {db_type}\n")

    try:
        if is_postgres:
            import psycopg2
            print("✅ psycopg2 installed")

            # Test connection
            print("📡 Connecting to PostgreSQL...")
            conn = psycopg2.connect(database_url)
            cursor = conn.cursor()
            print("✅ Connection successful\n")

            # Check tables
            cursor.execute("""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                ORDER BY table_name
            """)
            tables = [row[0] for row in cursor.fetchall()]

        else:
            import sqlite3
            print("✅ sqlite3 available")

            # Extract path from URL
            db_path = database_url.replace('sqlite:///', '')
            print(f"📡 Connecting to SQLite: {db_path}...")
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            print("✅ Connection successful\n")

            # Check tables
            cursor.execute("""
                SELECT name FROM sqlite_master
                WHERE type='table' AND name NOT LIKE 'sqlite_%'
                ORDER BY name
            """)
            tables = [row[0] for row in cursor.fetchall()]

        # Verify expected tables
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

        print("📋 Table Verification:")
        print(f"   Found {len(tables)} tables")
        print(f"   Expected {len(expected_tables)} tables\n")

        missing_tables = []
        for table in expected_tables:
            if table in tables:
                # Get row count
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                print(f"   ✅ {table:30} ({count} records)")
            else:
                print(f"   ❌ {table:30} MISSING")
                missing_tables.append(table)

        if missing_tables:
            print(f"\n⚠️  Missing tables: {', '.join(missing_tables)}")
            print("   Run: ./scripts/deploy_production_database.sh")
            return False

        print("")

        # Test carrier creation
        print("🧪 Testing Carrier Operations...")

        # Import database module
        from app.database import Database
        db = Database(database_url if is_postgres else db_path)

        # Create test carrier
        print("   Creating test carrier...")
        test_carrier_id = db.create_carrier(
            phone='+19999999999',
            email='test@example.com',
            legal_name='Test Carrier LLC',
            mc_number='MC999999',
            status='active'
        )
        print(f"   ✅ Carrier created: ID #{test_carrier_id}")

        # Retrieve carrier
        print("   Retrieving carrier...")
        carrier = db.get_carrier(test_carrier_id)
        assert carrier['legal_name'] == 'Test Carrier LLC'
        print(f"   ✅ Carrier retrieved: {carrier['legal_name']}")

        # Test helper methods
        print("   Testing helper methods...")

        # Equipment
        equipment_id = db.add_carrier_equipment(
            test_carrier_id,
            total_power_units=10,
            dry_van_53ft=5
        )
        print(f"   ✅ Equipment added: ID #{equipment_id}")

        # Performance
        perf_id = db.update_carrier_performance(
            test_carrier_id,
            total_loads_completed=0,
            reliability_score=3.0
        )
        print(f"   ✅ Performance record: ID #{perf_id}")

        # Lane
        lane_id = db.add_carrier_lane(
            test_carrier_id,
            origin='Atlanta, GA',
            destination='Charlotte, NC',
            confidence_score=0.8
        )
        print(f"   ✅ Lane added: ID #{lane_id}")

        # Clean up test data
        print("\n   Cleaning up test data...")
        cursor.execute("DELETE FROM carriers WHERE mc_number = 'MC999999'")
        conn.commit()
        print("   ✅ Test data removed")

        conn.close()

        print("\n" + "="*60)
        print("✅ ALL TESTS PASSED")
        print("="*60 + "\n")

        print("Database is ready for production!\n")
        print("Next steps:")
        print("  1. Import FMCSA data: python3 scripts/import_fmcsa_carriers.py")
        print("  2. Import Aljex loads: python3 scripts/sync_aljex_loads.py")
        print("  3. Deploy app: railway up")
        print("")

        return True

    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("\nInstall with:")
        if is_postgres:
            print("  pip install psycopg2-binary")
        return False

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    success = test_database()
    sys.exit(0 if success else 1)
