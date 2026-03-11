"""
Database module for Eagle Carrier Chatbot
Handles carrier profiles, query logging, and intelligence tracking
"""

import sqlite3
import json
from datetime import datetime
from typing import Optional, Dict, List
import os

class Database:
    def __init__(self, db_path: str = "data/carriers.db"):
        self.db_path = db_path

        # Create data directory if it doesn't exist
        os.makedirs(os.path.dirname(db_path), exist_ok=True)

        self.init_database()

    def get_connection(self):
        """Get database connection"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Return rows as dictionaries
        return conn

    def init_database(self):
        """Initialize database schema"""
        conn = self.get_connection()
        cursor = conn.cursor()

        # Carriers table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS carriers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                phone VARCHAR(20) UNIQUE,
                email VARCHAR(200) UNIQUE,
                name VARCHAR(200),
                company_name VARCHAR(200),
                mc_number VARCHAR(20),

                -- Aljex integration
                aljex_carrier_id VARCHAR(50),
                aljex_sync_status VARCHAR(20) DEFAULT 'not_synced',
                last_aljex_sync TIMESTAMP,

                -- Auto-learned preferences
                equipment_types TEXT,  -- JSON array
                preferred_origins TEXT,  -- JSON array
                preferred_destinations TEXT,  -- JSON array

                -- Engagement metrics
                total_queries INTEGER DEFAULT 0,
                total_bookings INTEGER DEFAULT 0,
                avg_response_time_seconds INTEGER,
                engagement_score DECIMAL(3,2),
                last_active_date TIMESTAMP,

                -- Status
                status VARCHAR(20) DEFAULT 'active',
                onboarding_complete BOOLEAN DEFAULT 0,

                -- Timestamps
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                -- Ensure at least one contact method exists
                CHECK (phone IS NOT NULL OR email IS NOT NULL)
            )
        ''')

        # Query log table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS carrier_queries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                carrier_id INTEGER,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                channel VARCHAR(20),  -- 'sms' or 'email'
                raw_message TEXT,

                -- Parsed intent
                intent VARCHAR(50),
                origin VARCHAR(10),
                destination VARCHAR(10),
                equipment_type VARCHAR(50),
                pickup_date VARCHAR(20),

                -- Response
                loads_shown INTEGER DEFAULT 0,
                load_ids_shown TEXT,  -- JSON array
                action_taken VARCHAR(50),
                response_time_seconds INTEGER,

                FOREIGN KEY (carrier_id) REFERENCES carriers(carrier_id)
            )
        ''')

        # Booking requests table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS booking_requests (
                booking_id INTEGER PRIMARY KEY AUTOINCREMENT,
                carrier_id INTEGER,
                load_id VARCHAR(50),
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status VARCHAR(20) DEFAULT 'pending',  -- pending, confirmed, cancelled

                FOREIGN KEY (carrier_id) REFERENCES carriers(carrier_id)
            )
        ''')

        # ===== PHASE 1: CONVERSATION CONTEXT TABLES =====

        # Carrier profiles - Enhanced tracking for intelligent conversations
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS carrier_profiles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                carrier_id INTEGER UNIQUE,
                current_location VARCHAR(50),
                next_empty_location VARCHAR(50),
                next_empty_date DATE,
                equipment_types TEXT,  -- JSON array
                preferred_lanes TEXT,  -- JSON array of {origin, destination}
                typical_rate_ranges TEXT,  -- JSON object of lane: rate_range
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (carrier_id) REFERENCES carriers(id)
            )
        ''')

        # Conversation context - Track conversation state per carrier
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS conversation_context (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                carrier_id INTEGER UNIQUE,
                conversation_state VARCHAR(50),  -- 'active', 'waiting_destination', 'waiting_equipment', 'waiting_mc_number'
                last_origin VARCHAR(50),
                last_destination VARCHAR(50),
                last_search_timestamp TIMESTAMP,
                context_data TEXT,  -- JSON for additional context

                FOREIGN KEY (carrier_id) REFERENCES carriers(id)
            )
        ''')

        # Create indexes
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_phone ON carriers(phone)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_carrier_queries ON carrier_queries(carrier_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_timestamp ON carrier_queries(timestamp)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_carrier_profiles ON carrier_profiles(carrier_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_conversation_context ON conversation_context(carrier_id)')

        conn.commit()
        conn.close()

        print("✓ Database initialized")

    def get_carrier(self, carrier_id: int) -> Optional[Dict]:
        """Get carrier by ID"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM carriers WHERE id = ?', (carrier_id,))
        row = cursor.fetchone()
        conn.close()

        if row:
            return dict(row)
        return None

    def get_carrier_by_phone(self, phone: str) -> Optional[Dict]:
        """Get carrier by phone number"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM carriers WHERE phone = ?', (phone,))
        row = cursor.fetchone()
        conn.close()

        if row:
            return dict(row)
        return None

    def get_carrier_by_email(self, email: str) -> Optional[Dict]:
        """Get carrier by email address"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM carriers WHERE email = ?', (email,))
        row = cursor.fetchone()
        conn.close()

        if row:
            return dict(row)
        return None

    def create_carrier(self, phone: str, **kwargs) -> int:
        """Create new carrier profile"""
        conn = self.get_connection()
        cursor = conn.cursor()

        fields = ['phone'] + list(kwargs.keys())
        values = [phone] + list(kwargs.values())
        placeholders = ','.join(['?' for _ in values])

        query = f"INSERT INTO carriers ({','.join(fields)}) VALUES ({placeholders})"
        cursor.execute(query, values)

        carrier_id = cursor.lastrowid
        conn.commit()
        conn.close()

        return carrier_id

    def update_carrier(self, phone: str, **kwargs):
        """Update carrier profile"""
        conn = self.get_connection()
        cursor = conn.cursor()

        # Add updated_at
        kwargs['updated_at'] = datetime.now()

        set_clause = ','.join([f"{k} = ?" for k in kwargs.keys()])
        values = list(kwargs.values()) + [phone]

        query = f"UPDATE carriers SET {set_clause} WHERE phone = ?"
        cursor.execute(query, values)

        conn.commit()
        conn.close()

    def log_query(self, carrier_id: int, channel: str, raw_message: str,
                  intent: str = None, **kwargs):
        """Log carrier query"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO carrier_queries
            (carrier_id, channel, raw_message, intent, origin, destination,
             equipment_type, pickup_date, loads_shown, load_ids_shown,
             action_taken, response_time_seconds)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            carrier_id,
            channel,
            raw_message,
            intent,
            kwargs.get('origin'),
            kwargs.get('destination'),
            kwargs.get('equipment_type'),
            kwargs.get('pickup_date'),
            kwargs.get('loads_shown', 0),
            json.dumps(kwargs.get('load_ids_shown', [])),
            kwargs.get('action_taken'),
            kwargs.get('response_time_seconds')
        ))

        # Update carrier stats
        cursor.execute('''
            UPDATE carriers
            SET total_queries = total_queries + 1,
                last_active_date = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (carrier_id,))

        conn.commit()
        conn.close()

    def log_booking_request(self, carrier_id: int, load_id: str):
        """Log carrier booking request"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO booking_requests (carrier_id, load_id)
            VALUES (?, ?)
        ''', (carrier_id, load_id))

        # Update carrier stats
        cursor.execute('''
            UPDATE carriers
            SET total_bookings = total_bookings + 1
            WHERE carrier_id = ?
        ''', (carrier_id,))

        conn.commit()
        conn.close()

    def get_carrier_stats(self, carrier_id: int) -> Dict:
        """Get carrier statistics"""
        conn = self.get_connection()
        cursor = conn.cursor()

        # Basic stats
        cursor.execute('SELECT * FROM carriers WHERE carrier_id = ?', (carrier_id,))
        carrier = dict(cursor.fetchone())

        # Recent queries
        cursor.execute('''
            SELECT origin, destination, equipment_type, COUNT(*) as count
            FROM carrier_queries
            WHERE carrier_id = ? AND origin IS NOT NULL
            GROUP BY origin, destination, equipment_type
            ORDER BY count DESC
            LIMIT 10
        ''', (carrier_id,))

        carrier['top_searches'] = [dict(row) for row in cursor.fetchall()]

        conn.close()
        return carrier

    # ===== PHASE 1: CONVERSATION CONTEXT METHODS =====

    def save_conversation_context(self, carrier_id: int, state: str,
                                  last_origin: str = None, last_destination: str = None,
                                  context_data: Dict = None):
        """Save conversation context for carrier"""
        conn = self.get_connection()
        cursor = conn.cursor()

        # Check if context exists
        cursor.execute('SELECT id FROM conversation_context WHERE carrier_id = ?', (carrier_id,))
        existing = cursor.fetchone()

        context_json = json.dumps(context_data) if context_data else None

        if existing:
            # Update existing
            cursor.execute('''
                UPDATE conversation_context
                SET conversation_state = ?,
                    last_origin = COALESCE(?, last_origin),
                    last_destination = COALESCE(?, last_destination),
                    last_search_timestamp = CURRENT_TIMESTAMP,
                    context_data = COALESCE(?, context_data)
                WHERE carrier_id = ?
            ''', (state, last_origin, last_destination, context_json, carrier_id))
        else:
            # Insert new
            cursor.execute('''
                INSERT INTO conversation_context
                (carrier_id, conversation_state, last_origin, last_destination, context_data)
                VALUES (?, ?, ?, ?, ?)
            ''', (carrier_id, state, last_origin, last_destination, context_json))

        conn.commit()
        conn.close()

    def get_conversation_context(self, carrier_id: int) -> Optional[Dict]:
        """Get conversation context for carrier"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM conversation_context WHERE carrier_id = ?', (carrier_id,))
        row = cursor.fetchone()
        conn.close()

        if row:
            context = dict(row)
            # Parse JSON context_data
            if context.get('context_data'):
                try:
                    context['context_data'] = json.loads(context['context_data'])
                except:
                    context['context_data'] = {}
            return context
        return None

    def update_carrier_profile(self, carrier_id: int, **kwargs):
        """Update carrier profile with learned preferences"""
        conn = self.get_connection()
        cursor = conn.cursor()

        # Check if profile exists
        cursor.execute('SELECT id FROM carrier_profiles WHERE carrier_id = ?', (carrier_id,))
        existing = cursor.fetchone()

        # Convert lists/dicts to JSON
        for key in ['equipment_types', 'preferred_lanes', 'typical_rate_ranges']:
            if key in kwargs and kwargs[key]:
                kwargs[key] = json.dumps(kwargs[key])

        if existing:
            # Update existing
            set_clause = ', '.join([f"{k} = ?" for k in kwargs.keys()])
            set_clause += ', last_updated = CURRENT_TIMESTAMP'
            values = list(kwargs.values()) + [carrier_id]
            cursor.execute(f'UPDATE carrier_profiles SET {set_clause} WHERE carrier_id = ?', values)
        else:
            # Insert new
            kwargs['carrier_id'] = carrier_id
            fields = ', '.join(kwargs.keys())
            placeholders = ', '.join(['?' for _ in kwargs])
            cursor.execute(f'INSERT INTO carrier_profiles ({fields}) VALUES ({placeholders})',
                         list(kwargs.values()))

        conn.commit()
        conn.close()

    def get_carrier_profile(self, carrier_id: int) -> Optional[Dict]:
        """Get carrier profile with learned preferences"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM carrier_profiles WHERE carrier_id = ?', (carrier_id,))
        row = cursor.fetchone()
        conn.close()

        if row:
            profile = dict(row)
            # Parse JSON fields
            for key in ['equipment_types', 'preferred_lanes', 'typical_rate_ranges']:
                if profile.get(key):
                    try:
                        profile[key] = json.loads(profile[key])
                    except:
                        profile[key] = None
            return profile
        return None
