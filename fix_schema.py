"""
Quick schema fix - adds missing columns to carriers table
Run this once to update the database schema
"""
import os
import psycopg2

DATABASE_URL = os.getenv('DATABASE_URL')

if not DATABASE_URL:
    print("ERROR: DATABASE_URL not set")
    exit(1)

conn = psycopg2.connect(DATABASE_URL)
cursor = conn.cursor()

# Add missing columns to carriers table
try:
    cursor.execute("""
        ALTER TABLE carriers 
        ADD COLUMN IF NOT EXISTS dot_number VARCHAR(50),
        ADD COLUMN IF NOT EXISTS mc_number VARCHAR(50),
        ADD COLUMN IF NOT EXISTS email VARCHAR(255),
        ADD COLUMN IF NOT EXISTS phone VARCHAR(50),
        ADD COLUMN IF NOT EXISTS contact_name VARCHAR(255),
        ADD COLUMN IF NOT EXISTS company_name VARCHAR(255),
        ADD COLUMN IF NOT EXISTS address TEXT,
        ADD COLUMN IF NOT EXISTS city VARCHAR(100),
        ADD COLUMN IF NOT EXISTS state VARCHAR(50),
        ADD COLUMN IF NOT EXISTS zip VARCHAR(20),
        ADD COLUMN IF NOT EXISTS preferred_lanes TEXT,
        ADD COLUMN IF NOT EXISTS equipment_types TEXT,
        ADD COLUMN IF NOT EXISTS notes TEXT,
        ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    """)
    
    conn.commit()
    print("✓ Schema updated successfully")
    
    # Check carrier count
    cursor.execute("SELECT COUNT(*) FROM carriers")
    count = cursor.fetchone()[0]
    print(f"✓ Database has {count} carriers")
    
except Exception as e:
    print(f"✗ Error: {e}")
    conn.rollback()
finally:
    cursor.close()
    conn.close()
