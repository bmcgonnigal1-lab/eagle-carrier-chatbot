#!/usr/bin/env python3
"""
Migrate SQLite Database Schema to PostgreSQL
Converts SQLite DDL to PostgreSQL-compatible DDL
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    import psycopg2
    from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
except ImportError:
    print("❌ psycopg2 not installed. Run: pip install psycopg2-binary")
    sys.exit(1)


def convert_sqlite_to_postgres(sqlite_sql):
    """Convert SQLite DDL to PostgreSQL DDL"""
    # Replace SQLite-specific syntax with PostgreSQL
    postgres_sql = sqlite_sql

    # AUTOINCREMENT → SERIAL
    postgres_sql = postgres_sql.replace('INTEGER PRIMARY KEY AUTOINCREMENT', 'SERIAL PRIMARY KEY')

    # UUID generation
    postgres_sql = postgres_sql.replace(
        "uuid TEXT UNIQUE DEFAULT (lower(hex(randomblob(16))))",
        "uuid TEXT UNIQUE DEFAULT gen_random_uuid()::text"
    )

    # Datetime
    postgres_sql = postgres_sql.replace("datetime('now')", 'CURRENT_TIMESTAMP')
    postgres_sql = postgres_sql.replace('TEXT DEFAULT (datetime', 'TIMESTAMP DEFAULT (CURRENT_TIMESTAMP')
    postgres_sql = postgres_sql.replace('TIMESTAMP DEFAULT CURRENT_TIMESTAMP', 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP')

    return postgres_sql


def create_postgres_schema():
    """Create complete PostgreSQL schema"""

    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print("❌ DATABASE_URL not set")
        return False

    print(f"📡 Connecting to PostgreSQL...")

    try:
        # Connect to PostgreSQL
        conn = psycopg2.connect(database_url)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()

        print("✅ Connected to PostgreSQL")
        print("")

        # Read SQLite schema from database.py
        print("📖 Loading schema from database.py...")

        # Import to get schema
        from app.database import Database

        # Create temporary SQLite database to extract schema
        import sqlite3
        import tempfile

        temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        temp_db_path = temp_db.name
        temp_db.close()

        # Initialize SQLite database to generate schema
        sqlite_db = Database(temp_db_path)
        sqlite_conn = sqlite3.connect(temp_db_path)
        sqlite_cursor = sqlite_conn.cursor()

        # Get all CREATE TABLE statements
        sqlite_cursor.execute(
            "SELECT sql FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
        )
        tables = sqlite_cursor.fetchall()

        sqlite_cursor.execute(
            "SELECT sql FROM sqlite_master WHERE type='index' AND name NOT LIKE 'sqlite_%'"
        )
        indexes = sqlite_cursor.fetchall()

        sqlite_conn.close()
        os.unlink(temp_db_path)

        print(f"✅ Found {len(tables)} tables and {len(indexes)} indexes")
        print("")

        # Create tables
        print("🔨 Creating tables...")
        for i, (sql,) in enumerate(tables, 1):
            if sql:
                postgres_sql = convert_sqlite_to_postgres(sql)
                try:
                    cursor.execute(postgres_sql)
                    # Extract table name
                    table_name = postgres_sql.split('CREATE TABLE IF NOT EXISTS ')[1].split(' (')[0]
                    print(f"  ✅ {i}/{len(tables)}: {table_name}")
                except Exception as e:
                    print(f"  ⚠️  Error creating table: {e}")
                    print(f"     SQL: {postgres_sql[:100]}...")

        print("")

        # Create indexes
        print("📇 Creating indexes...")
        for i, (sql,) in enumerate(indexes, 1):
            if sql:
                postgres_sql = convert_sqlite_to_postgres(sql)
                try:
                    cursor.execute(postgres_sql)
                    print(f"  ✅ {i}/{len(indexes)}")
                except Exception as e:
                    # Indexes might already exist, that's OK
                    if 'already exists' not in str(e):
                        print(f"  ⚠️  Error creating index: {e}")

        print("")

        # Verify tables
        print("🔍 Verifying schema...")
        cursor.execute("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            ORDER BY table_name
        """)
        pg_tables = cursor.fetchall()

        print(f"✅ {len(pg_tables)} tables created:")
        for table_name, in pg_tables:
            print(f"   • {table_name}")

        cursor.close()
        conn.close()

        print("")
        print("="*60)
        print("✅ POSTGRESQL SCHEMA CREATED SUCCESSFULLY")
        print("="*60)
        print("")

        return True

    except Exception as e:
        print(f"❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    success = create_postgres_schema()
    sys.exit(0 if success else 1)
