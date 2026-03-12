#!/usr/bin/env python3
"""
Migrate carrier data from SQLite to PostgreSQL on Railway
"""
import os
import sys
import sqlite3
import psycopg2
from psycopg2.extras import execute_values

# Railway PostgreSQL connection URL
DATABASE_URL = os.getenv('DATABASE_URL')

if not DATABASE_URL:
    print("❌ Error: DATABASE_URL environment variable not set")
    sys.exit(1)

# Path to SQLite database
SQLITE_DB = 'data/carriers.db'

if not os.path.exists(SQLITE_DB):
    print(f"❌ Error: SQLite database not found at {SQLITE_DB}")
    print(f"Current directory: {os.getcwd()}")
    print(f"Looking for: {os.path.abspath(SQLITE_DB)}")
    sys.exit(1)

print("🔄 Connecting to databases...")

# Connect to SQLite
sqlite_conn = sqlite3.connect(SQLITE_DB)
sqlite_conn.row_factory = sqlite3.Row
sqlite_cur = sqlite_conn.cursor()

# Connect to PostgreSQL
pg_conn = psycopg2.connect(DATABASE_URL)
pg_cur = pg_conn.cursor()

print("✅ Connected to both databases")

# Create tables in PostgreSQL
print("\n📋 Creating PostgreSQL tables...")

create_tables_sql = """
CREATE TABLE IF NOT EXISTS carriers (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    mc_number VARCHAR(50),
    dot_number VARCHAR(50),
    contact_name VARCHAR(255),
    phone VARCHAR(50),
    email VARCHAR(255),
    address TEXT,
    city VARCHAR(100),
    state VARCHAR(2),
    zip VARCHAR(10),
    equipment_types TEXT,
    service_areas TEXT,
    insurance_amount DECIMAL(15,2),
    insurance_expiry DATE,
    preferred_lanes TEXT,
    notes TEXT,
    rating DECIMAL(3,2),
    total_loads INTEGER DEFAULT 0,
    on_time_percentage DECIMAL(5,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS loads (
    id SERIAL PRIMARY KEY,
    carrier_id INTEGER REFERENCES carriers(id),
    load_number VARCHAR(100) UNIQUE,
    pickup_location TEXT,
    pickup_city VARCHAR(100),
    pickup_state VARCHAR(2),
    pickup_date DATE,
    delivery_location TEXT,
    delivery_city VARCHAR(100),
    delivery_state VARCHAR(2),
    delivery_date DATE,
    equipment_type VARCHAR(50),
    weight DECIMAL(10,2),
    rate DECIMAL(10,2),
    status VARCHAR(50),
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS conversations (
    id SERIAL PRIMARY KEY,
    carrier_id INTEGER REFERENCES carriers(id),
    message TEXT,
    sender VARCHAR(50),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

pg_cur.execute(create_tables_sql)
pg_conn.commit()
print("✅ Tables created")

# Migrate carriers
print("\n📦 Migrating carriers...")
sqlite_cur.execute("SELECT * FROM carriers")
carriers = sqlite_cur.fetchall()

if carriers:
    carrier_data = []
    for row in carriers:
        carrier_data.append((
            row['name'],
            row['mc_number'],
            row['dot_number'],
            row['contact_name'],
            row['phone'],
            row['email'],
            row['address'],
            row['city'],
            row['state'],
            row['zip'],
            row['equipment_types'],
            row['service_areas'],
            row['insurance_amount'],
            row['insurance_expiry'],
            row['preferred_lanes'],
            row['notes'],
            row['rating'],
            row['total_loads'],
            row['on_time_percentage']
        ))

    insert_sql = """
        INSERT INTO carriers (
            name, mc_number, dot_number, contact_name, phone, email,
            address, city, state, zip, equipment_types, service_areas,
            insurance_amount, insurance_expiry, preferred_lanes, notes,
            rating, total_loads, on_time_percentage
        ) VALUES %s
    """

    execute_values(pg_cur, insert_sql, carrier_data)
    pg_conn.commit()
    print(f"✅ Migrated {len(carriers)} carriers")
else:
    print("⚠️  No carriers found in SQLite database")

# Close connections
sqlite_conn.close()
pg_conn.close()

print("\n✅ Migration complete!")
