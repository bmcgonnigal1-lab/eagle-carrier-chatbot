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

        # Lazy initialization - only connect when first needed
        self.connection_pool = None
        self._initialized = False

    def _ensure_connected(self):
        """Lazy initialization - connect to database only when first needed"""
        if self.connection_pool is None:
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

        if not self._initialized:
            self.init_database()
            self._initialized = True

    def get_connection(self):
        """Get connection from pool"""
        self._ensure_connected()
        return self.connection_pool.getconn()

    def return_connection(self, conn):
        """Return connection to pool"""
        self.connection_pool.putconn(conn)

    def init_database(self):
        """Initialize comprehensive database schema"""
        # Use pool directly to avoid recursion (get_connection calls _ensure_connected which calls this)
        conn = self.connection_pool.getconn()
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

            # ===== TABLE 2: CONVERSATIONS =====
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS conversations (
                    id SERIAL PRIMARY KEY,
                    carrier_id INTEGER REFERENCES carriers(id),
                    channel TEXT,
                    direction TEXT,
                    message TEXT,
                    sender TEXT,
                    intent TEXT,
                    entities TEXT,
                    response TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # ===== TABLE 3: QUERIES (Carrier Search History) =====
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS queries (
                    id SERIAL PRIMARY KEY,
                    carrier_id INTEGER REFERENCES carriers(id),
                    channel TEXT,
                    raw_message TEXT,
                    parsed_intent TEXT,
                    parsed_entities TEXT,
                    search_criteria TEXT,
                    results_count INTEGER,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # ===== TABLE 4: BOOKING REQUESTS =====
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS booking_requests (
                    id SERIAL PRIMARY KEY,
                    carrier_id INTEGER REFERENCES carriers(id),
                    load_id TEXT,
                    status TEXT DEFAULT 'pending',
                    requested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    completed_at TIMESTAMP
                )
            ''')

            # Create indexes for performance
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_carriers_dot ON carriers(dot_number)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_carriers_mc ON carriers(mc_number)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_carriers_phone ON carriers(phone)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_carriers_email ON carriers(email)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_carriers_status ON carriers(status)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_conversations_carrier ON conversations(carrier_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_queries_carrier ON queries(carrier_id)')

            conn.commit()
            print("✓ Database schema initialized")

        except Exception as e:
            conn.rollback()
            print(f"✗ Database initialization failed: {e}")
            raise
        finally:
            self.connection_pool.putconn(conn)

    def close(self):
        """Close all connections in pool"""
        if self.connection_pool:
            self.connection_pool.closeall()
            print("✓ Database connections closed")

    # ===== CORE CARRIER METHODS =====

    def get_carrier(self, carrier_id: int) -> Optional[Dict]:
        """Get carrier by ID"""
        conn = self.get_connection()
        try:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute("SELECT * FROM carriers WHERE id = %s", (carrier_id,))
            result = cursor.fetchone()
            return dict(result) if result else None
        finally:
            self.return_connection(conn)

    def get_carrier_by_phone(self, phone: str) -> Optional[Dict]:
        """Get carrier by phone number"""
        conn = self.get_connection()
        try:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute("SELECT * FROM carriers WHERE phone = %s", (phone,))
            result = cursor.fetchone()
            return dict(result) if result else None
        finally:
            self.return_connection(conn)

    def get_carrier_by_email(self, email: str) -> Optional[Dict]:
        """Get carrier by email address"""
        conn = self.get_connection()
        try:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute("SELECT * FROM carriers WHERE email = %s", (email,))
            result = cursor.fetchone()
            return dict(result) if result else None
        finally:
            self.return_connection(conn)

    def create_carrier(self, phone: str = None, email: str = None, **kwargs) -> int:
        """
        Create new carrier

        Args:
            phone: Phone number
            email: Email address
            **kwargs: Additional fields

        Returns:
            carrier_id
        """
        conn = self.get_connection()
        try:
            cursor = conn.cursor()

            # Build dynamic INSERT based on provided fields
            fields = ['phone', 'email']
            values = [phone, email]

            for key, value in kwargs.items():
                if value is not None:
                    fields.append(key)
                    values.append(value)

            placeholders = ', '.join(['%s'] * len(values))
            field_names = ', '.join(fields)

            query = f"""
                INSERT INTO carriers ({field_names})
                VALUES ({placeholders})
                RETURNING id
            """

            cursor.execute(query, values)
            carrier_id = cursor.fetchone()[0]
            conn.commit()

            return carrier_id
        except Exception as e:
            conn.rollback()
            raise
        finally:
            self.return_connection(conn)

    def log_query(self, carrier_id: int, channel: str, raw_message: str,
                  parsed_intent: str = None, parsed_entities: dict = None,
                  search_criteria: dict = None, results_count: int = 0):
        """Log carrier search query"""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO queries (
                    carrier_id, channel, raw_message, parsed_intent,
                    parsed_entities, search_criteria, results_count
                ) VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (
                carrier_id, channel, raw_message, parsed_intent,
                json.dumps(parsed_entities) if parsed_entities else None,
                json.dumps(search_criteria) if search_criteria else None,
                results_count
            ))
            conn.commit()

            # Update carrier engagement metrics
            cursor.execute("""
                UPDATE carriers
                SET total_queries = total_queries + 1,
                    last_active_date = CURRENT_TIMESTAMP
                WHERE id = %s
            """, (carrier_id,))
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise
        finally:
            self.return_connection(conn)

    def log_booking_request(self, carrier_id: int, load_id: str):
        """Log carrier booking request"""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO booking_requests (carrier_id, load_id, status)
                VALUES (%s, %s, 'pending')
            """, (carrier_id, load_id))
            conn.commit()

            # Update carrier metrics
            cursor.execute("""
                UPDATE carriers
                SET total_bookings = total_bookings + 1
                WHERE id = %s
            """, (carrier_id,))
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise
        finally:
            self.return_connection(conn)


# For compatibility with existing code
Database = PostgresCarrierDatabase
