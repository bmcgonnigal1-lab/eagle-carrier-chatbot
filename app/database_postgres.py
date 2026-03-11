"""
PostgreSQL Database Module for Eagle Carrier Chatbot
Production-ready version with connection pooling
"""

import psycopg2
from psycopg2 import pool
from psycopg2.extras import RealDictCursor
import json
import os
from datetime import datetime
from typing import Optional, Dict, List


class PostgresCarrierDatabase:
    """
    Production PostgreSQL database

    Environment variables needed:
    - DATABASE_URL: PostgreSQL connection string
      Format: postgresql://user:password@host:port/database
    """

    def __init__(self, database_url: str = None):
        self.database_url = database_url or os.getenv('DATABASE_URL')

        if not self.database_url:
            raise ValueError("DATABASE_URL environment variable not set")

        # Create connection pool (reuse connections for performance)
        try:
            self.connection_pool = psycopg2.pool.SimpleConnectionPool(
                1,  # Min connections
                20,  # Max connections
                self.database_url
            )
            print("✓ Connected to PostgreSQL database")
        except Exception as e:
            print(f"✗ Database connection failed: {e}")
            raise

        self.init_database()

    def get_connection(self):
        """Get connection from pool"""
        return self.connection_pool.getconn()

    def return_connection(self, conn):
        """Return connection to pool"""
        self.connection_pool.putconn(conn)

    def init_database(self):
        """Initialize comprehensive database schema"""
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            # ===== TABLE 1: CARRIERS (Core Identity) =====
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS carriers (
                    -- Primary Identification
                    id SERIAL PRIMARY KEY,
                    uuid TEXT UNIQUE DEFAULT gen_random_uuid()::text,

                    -- Government Registration
                    dot_number TEXT UNIQUE,
                    mc_number TEXT UNIQUE,
                    ff_number TEXT,
                    mx_number TEXT,
                    scac_code TEXT,
                    ein TEXT,

                    -- Company Information
                    legal_name TEXT NOT NULL,
                    dba_name TEXT,
                    company_type TEXT,

                    -- Contact Information
                    phone TEXT UNIQUE,
                    phone_verified INTEGER DEFAULT 0,
                    email TEXT UNIQUE,
                    email_verified INTEGER DEFAULT 0,
                    dispatch_phone TEXT,
                    dispatch_email TEXT,
                    accounting_email TEXT,
                    emergency_phone TEXT,

                    -- Physical Address
                    physical_address_line1 TEXT,
                    physical_address_line2 TEXT,
                    physical_city TEXT,
                    physical_state TEXT,
                    physical_zip TEXT,
                    physical_country TEXT DEFAULT 'US',

                    -- Mailing Address
                    mailing_address_line1 TEXT,
                    mailing_address_line2 TEXT,
                    mailing_city TEXT,
                    mailing_state TEXT,
                    mailing_zip TEXT,
                    mailing_country TEXT DEFAULT 'US',

                    -- Authority & Operating Status
                    authority_status TEXT,
                    operating_status TEXT,
                    out_of_service_date TEXT,
                    authority_types TEXT,
                    operating_classifications TEXT,
                    cargo_carried TEXT,

                    -- Business Details
                    year_established INTEGER,
                    business_started_date TEXT,
                    employees_count INTEGER,

                    -- Status & Onboarding
                    status TEXT DEFAULT 'pending',
                    onboarding_status TEXT DEFAULT 'not_started',
                    onboarding_complete INTEGER DEFAULT 0,
                    approved_date TEXT,
                    approved_by INTEGER,

                    -- Verification Status
                    fmcsa_verified INTEGER DEFAULT 0,
                    fmcsa_verified_date TEXT,
                    highway_verified INTEGER DEFAULT 0,
                    highway_verified_date TEXT,

                    -- Aljex Integration
                    aljex_carrier_id TEXT,
                    aljex_sync_status TEXT DEFAULT 'not_synced',
                    last_aljex_sync TEXT,

                    -- Preferences
                    preferred_payment_terms TEXT,
                    payment_method TEXT,
                    preferred_load_types TEXT,
                    blacklisted_lanes TEXT,
                    preferred_contact_method TEXT DEFAULT 'SMS',
                    send_load_alerts INTEGER DEFAULT 1,
                    send_rate_confirmations INTEGER DEFAULT 1,

                    -- Internal Notes & Tags
                    internal_notes TEXT,
                    tags TEXT,

                    -- Engagement Metrics
                    total_queries INTEGER DEFAULT 0,
                    total_bookings INTEGER DEFAULT 0,
                    avg_response_time_seconds INTEGER,
                    engagement_score REAL,
                    last_active_date TEXT,

                    -- Metadata
                    source TEXT,
                    source_reference TEXT,

                    -- Timestamps
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                    CHECK (phone IS NOT NULL OR email IS NOT NULL)
                )
            ''')

            # Continue with other tables (same as SQLite but with SERIAL instead of AUTOINCREMENT)
            # I'll create a migration script for the rest...

            # Create indexes
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_carriers_dot ON carriers(dot_number)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_carriers_mc ON carriers(mc_number)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_carriers_phone ON carriers(phone)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_carriers_email ON carriers(email)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_carriers_status ON carriers(status)')

            conn.commit()
            print("✓ Database schema initialized")

        except Exception as e:
            conn.rollback()
            print(f"✗ Database initialization failed: {e}")
            raise
        finally:
            self.return_connection(conn)

    def close(self):
        """Close all connections in pool"""
        if self.connection_pool:
            self.connection_pool.closeall()
            print("✓ Database connections closed")


# For compatibility with existing code
Database = PostgresCarrierDatabase
