"""
PostgreSQL Database Module for Eagle Carrier Chatbot
Production-ready version with connection pooling and lazy initialization
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
    Production PostgreSQL database with lazy initialization

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
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            # Create carriers table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS carriers (
                    id SERIAL PRIMARY KEY,
                    uuid TEXT UNIQUE DEFAULT gen_random_uuid()::text,
                    dot_number VARCHAR(50),
                    mc_number VARCHAR(50),
                    legal_name TEXT NOT NULL,
                    phone VARCHAR(50) UNIQUE,
                    email VARCHAR(255),
                    contact_name VARCHAR(255),
                    company_name VARCHAR(255),
                    address TEXT,
                    city VARCHAR(100),
                    state VARCHAR(50),
                    zip VARCHAR(20),
                    preferred_lanes TEXT,
                    equipment_types TEXT,
                    notes TEXT,
                    total_queries INTEGER DEFAULT 0,
                    total_bookings INTEGER DEFAULT 0,
                    engagement_score REAL DEFAULT 0,
                    last_active_date TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # Create carrier_queries table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS carrier_queries (
                    id SERIAL PRIMARY KEY,
                    carrier_id INTEGER REFERENCES carriers(id),
                    origin VARCHAR(100),
                    destination VARCHAR(100),
                    equipment_type VARCHAR(100),
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    intent VARCHAR(50),
                    raw_message TEXT
                )
            ''')

            # Create booking_requests table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS booking_requests (
                    id SERIAL PRIMARY KEY,
                    carrier_id INTEGER REFERENCES carriers(id),
                    query_id INTEGER REFERENCES carrier_queries(id),
                    status VARCHAR(50) DEFAULT 'pending',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # Create indexes
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_carriers_dot ON carriers(dot_number)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_carriers_mc ON carriers(mc_number)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_carriers_phone ON carriers(phone)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_carriers_email ON carriers(email)')

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

    def add_carrier(self, carrier_data: Dict) -> int:
        """Add a new carrier"""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO carriers (
                    legal_name, phone, email, contact_name, company_name,
                    address, city, state, zip, dot_number, mc_number,
                    equipment_types, preferred_lanes, notes
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            ''', (
                carrier_data.get('legal_name', carrier_data.get('name', 'Unknown')),
                carrier_data.get('phone'),
                carrier_data.get('email'),
                carrier_data.get('contact_name'),
                carrier_data.get('company_name'),
                carrier_data.get('address'),
                carrier_data.get('city'),
                carrier_data.get('state'),
                carrier_data.get('zip'),
                carrier_data.get('dot_number'),
                carrier_data.get('mc_number'),
                carrier_data.get('equipment_types'),
                carrier_data.get('preferred_lanes'),
                carrier_data.get('notes')
            ))
            carrier_id = cursor.fetchone()[0]
            conn.commit()
            return carrier_id
        except Exception as e:
            conn.rollback()
            raise
        finally:
            self.return_connection(conn)

    def update_carrier(self, carrier_id: int, updates: Dict):
        """Update carrier information"""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            
            set_clauses = []
            values = []
            
            for key, value in updates.items():
                set_clauses.append(f"{key} = %s")
                values.append(value)
            
            values.append(carrier_id)
            
            query = f"UPDATE carriers SET {', '.join(set_clauses)}, updated_at = CURRENT_TIMESTAMP WHERE id = %s"
            cursor.execute(query, values)
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise
        finally:
            self.return_connection(conn)

    def log_query(self, carrier_id: int, query_data: Dict) -> int:
        """Log a carrier query"""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO carrier_queries (
                    carrier_id, origin, destination, equipment_type, intent, raw_message
                ) VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING id
            ''', (
                carrier_id,
                query_data.get('origin'),
                query_data.get('destination'),
                query_data.get('equipment_type'),
                query_data.get('intent'),
                query_data.get('raw_message')
            ))
            query_id = cursor.fetchone()[0]
            conn.commit()
            
            # Update carrier engagement
            self.update_carrier(carrier_id, {
                'total_queries': f"total_queries + 1",
                'last_active_date': datetime.now()
            })
            
            return query_id
        except Exception as e:
            conn.rollback()
            raise
        finally:
            self.return_connection(conn)


# For compatibility with existing code
Database = PostgresCarrierDatabase
