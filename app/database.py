"""
Comprehensive Database Module for Eagle Carrier Chatbot
Supports complete carrier lifecycle from onboarding to performance tracking
Designed to scale from SQLite to PostgreSQL with zero code changes
"""

import sqlite3
import json
import uuid
from datetime import datetime
from typing import Optional, Dict, List
import os


class ComprehensiveCarrierDatabase:
    """
    Complete carrier database supporting:
    - FMCSA integration
    - Highway verification
    - TMS-level features
    - AI intelligence tracking
    - Performance analytics
    """

    def __init__(self, db_path: str = "data/carriers.db"):
        self.db_path = db_path

        # Create data directory if it doesn't exist
        if self.db_path:
            os.makedirs(os.path.dirname(db_path), exist_ok=True)

        self.init_database()

    def get_connection(self):
        """Get database connection"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Return rows as dictionaries
        return conn

    def init_database(self):
        """Initialize comprehensive database schema"""
        conn = self.get_connection()
        cursor = conn.cursor()

        # Database-agnostic syntax
        if self.is_postgres:
            pk = 'SERIAL PRIMARY KEY'
            now = 'CURRENT_TIMESTAMP'
        else:
            pk = 'INTEGER PRIMARY KEY AUTOINCREMENT'
            now = "datetime('now')"


        # ===== TABLE 1: CARRIERS (Core Identity) =====
        cursor.execute(f'''
            CREATE TABLE IF NOT EXISTS carriers (
                -- Primary Identification
                id {pk},
                uuid TEXT UNIQUE ,

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

                -- Engagement Metrics (for backward compatibility)
                total_queries INTEGER DEFAULT 0,
                total_bookings INTEGER DEFAULT 0,
                avg_response_time_seconds INTEGER,
                engagement_score REAL,
                last_active_date TEXT,

                -- Metadata
                source TEXT,
                source_reference TEXT,

                -- Timestamps
                created_at TEXT DEFAULT ({now}),
                updated_at TEXT DEFAULT ({now}),

            )
        ''')

        # ===== TABLE 2: CARRIER EQUIPMENT =====
        cursor.execute(f'''
            CREATE TABLE IF NOT EXISTS carrier_equipment (
                id {pk},
                carrier_id INTEGER NOT NULL,

                -- Fleet Size
                total_power_units INTEGER DEFAULT 0,
                total_drivers INTEGER DEFAULT 0,
                owner_operators_count INTEGER DEFAULT 0,
                company_drivers_count INTEGER DEFAULT 0,

                -- Dry Vans
                dry_van_53ft INTEGER DEFAULT 0,
                dry_van_48ft INTEGER DEFAULT 0,
                dry_van_other INTEGER DEFAULT 0,

                -- Reefers
                reefer_53ft INTEGER DEFAULT 0,
                reefer_48ft INTEGER DEFAULT 0,
                reefer_other INTEGER DEFAULT 0,

                -- Flatbeds
                flatbed_48ft INTEGER DEFAULT 0,
                flatbed_53ft INTEGER DEFAULT 0,
                stepdeck INTEGER DEFAULT 0,
                double_drop INTEGER DEFAULT 0,

                -- Specialized
                hopper INTEGER DEFAULT 0,
                tanker INTEGER DEFAULT 0,
                lowboy INTEGER DEFAULT 0,
                conestoga INTEGER DEFAULT 0,
                power_only INTEGER DEFAULT 0,
                auto_carrier INTEGER DEFAULT 0,

                -- Equipment Features (JSON)
                equipment_features TEXT,

                -- Capacity
                max_weight_capacity INTEGER,
                max_length_capacity INTEGER,

                -- Hazmat
                hazmat_certified INTEGER DEFAULT 0,
                hazmat_endorsements TEXT,

                -- Team Drivers
                team_drivers_available INTEGER DEFAULT 0,

                -- Tracking & Technology
                has_eld INTEGER DEFAULT 0,
                has_gps_tracking INTEGER DEFAULT 0,
                gps_provider TEXT,
                tracking_visibility_level TEXT,

                -- Timestamps
                last_updated TEXT DEFAULT ({now}),

                FOREIGN KEY (carrier_id) REFERENCES carriers(id) ON DELETE CASCADE
            )
        ''')

        # ===== TABLE 3: CARRIER INSURANCE =====
        cursor.execute(f'''
            CREATE TABLE IF NOT EXISTS carrier_insurance (
                id {pk},
                carrier_id INTEGER NOT NULL,

                -- Auto Liability
                auto_liability_carrier TEXT,
                auto_liability_policy_number TEXT,
                auto_liability_coverage_amount REAL,
                auto_liability_effective_date TEXT,
                auto_liability_expiration_date TEXT,
                auto_liability_status TEXT,

                -- Cargo Insurance
                cargo_insurance_carrier TEXT,
                cargo_insurance_policy_number TEXT,
                cargo_coverage_amount REAL,
                cargo_effective_date TEXT,
                cargo_expiration_date TEXT,
                cargo_status TEXT,

                -- General Liability
                general_liability_carrier TEXT,
                general_liability_policy_number TEXT,
                general_liability_coverage REAL,
                general_liability_effective_date TEXT,
                general_liability_expiration_date TEXT,

                -- Workers Comp
                workers_comp_carrier TEXT,
                workers_comp_policy_number TEXT,
                workers_comp_effective_date TEXT,
                workers_comp_expiration_date TEXT,

                -- Umbrella
                umbrella_coverage INTEGER DEFAULT 0,
                umbrella_amount REAL,

                -- Documents
                insurance_cert_url TEXT,
                insurance_cert_uploaded_date TEXT,

                -- Alerts
                expiration_alert_sent INTEGER DEFAULT 0,
                expiration_alert_date TEXT,
                days_until_expiration INTEGER,

                -- Timestamps
                created_at TEXT DEFAULT ({now}),
                updated_at TEXT DEFAULT ({now}),

                FOREIGN KEY (carrier_id) REFERENCES carriers(id) ON DELETE CASCADE
            )
        ''')

        # ===== TABLE 4: CARRIER SAFETY SCORES (FMCSA) =====
        cursor.execute(f'''
            CREATE TABLE IF NOT EXISTS carrier_safety_scores (
                id {pk},
                carrier_id INTEGER NOT NULL,

                -- FMCSA BASICS
                unsafe_driving_score REAL,
                unsafe_driving_percentile INTEGER,
                unsafe_driving_alert_status TEXT,

                hos_compliance_score REAL,
                hos_compliance_percentile INTEGER,
                hos_compliance_alert_status TEXT,

                driver_fitness_score REAL,
                driver_fitness_percentile INTEGER,
                driver_fitness_alert_status TEXT,

                substance_alcohol_score REAL,
                substance_alcohol_percentile INTEGER,
                substance_alcohol_alert_status TEXT,

                vehicle_maintenance_score REAL,
                vehicle_maintenance_percentile INTEGER,
                vehicle_maintenance_alert_status TEXT,

                crash_indicator_score REAL,
                crash_indicator_percentile INTEGER,
                crash_indicator_alert_status TEXT,

                -- Overall Ratings
                overall_safety_rating TEXT,
                safety_rating_date TEXT,
                iss_score INTEGER,

                -- Inspection Data
                total_inspections INTEGER DEFAULT 0,
                inspections_with_violations INTEGER DEFAULT 0,
                out_of_service_inspections INTEGER DEFAULT 0,
                driver_inspections INTEGER DEFAULT 0,
                driver_out_of_service INTEGER DEFAULT 0,
                vehicle_inspections INTEGER DEFAULT 0,
                vehicle_out_of_service INTEGER DEFAULT 0,

                -- Crash Data
                total_crashes INTEGER DEFAULT 0,
                fatal_crashes INTEGER DEFAULT 0,
                injury_crashes INTEGER DEFAULT 0,
                tow_away_crashes INTEGER DEFAULT 0,
                crash_data_start_date TEXT,
                crash_data_end_date TEXT,

                -- Carrier Operation
                carrier_operation TEXT,

                -- Data Freshness
                fmcsa_last_updated TEXT,
                snapshot_date TEXT DEFAULT ({now}),

                -- Compliance
                is_compliant INTEGER DEFAULT 1,
                compliance_issues TEXT,

                FOREIGN KEY (carrier_id) REFERENCES carriers(id) ON DELETE CASCADE
            )
        ''')

        # ===== TABLE 5: CARRIER PERFORMANCE (Broker's Internal Tracking) =====
        cursor.execute(f'''
            CREATE TABLE IF NOT EXISTS carrier_performance (
                id {pk},
                carrier_id INTEGER NOT NULL,

                -- Relationship Metrics
                first_load_date TEXT,
                last_load_date TEXT,
                total_loads_completed INTEGER DEFAULT 0,
                total_loads_cancelled INTEGER DEFAULT 0,
                total_loads_no_show INTEGER DEFAULT 0,

                -- Performance Scores
                on_time_pickup_percentage REAL,
                on_time_delivery_percentage REAL,
                avg_pickup_delay_minutes INTEGER,
                avg_delivery_delay_minutes INTEGER,

                -- Quality Metrics
                claims_filed INTEGER DEFAULT 0,
                claims_total_amount REAL,
                claims_resolved INTEGER DEFAULT 0,
                damage_incidents INTEGER DEFAULT 0,
                theft_incidents INTEGER DEFAULT 0,

                -- Communication Metrics
                avg_response_time_minutes INTEGER,
                check_calls_on_time_percentage REAL,
                proactive_updates_percentage REAL,

                -- Financial Metrics
                total_revenue_generated REAL,
                avg_margin_percentage REAL,
                quickpay_requests INTEGER DEFAULT 0,
                payment_issues INTEGER DEFAULT 0,

                -- Reliability Scores
                reliability_score REAL,
                preferred_carrier INTEGER DEFAULT 0,
                internal_rating REAL,

                -- Booking Behavior
                loads_offered INTEGER DEFAULT 0,
                loads_accepted INTEGER DEFAULT 0,
                acceptance_rate REAL,
                avg_time_to_accept_minutes INTEGER,

                -- Lane Performance
                favorite_lanes TEXT,
                blacklisted_lanes TEXT,

                -- Timestamps
                last_calculated TEXT DEFAULT ({now}),

                FOREIGN KEY (carrier_id) REFERENCES carriers(id) ON DELETE CASCADE
            )
        ''')

        # ===== TABLE 6: CARRIER LANES =====
        cursor.execute(f'''
            CREATE TABLE IF NOT EXISTS carrier_lanes (
                id {pk},
                carrier_id INTEGER NOT NULL,

                -- Lane Definition
                origin_city TEXT,
                origin_state TEXT,
                origin_region TEXT,
                destination_city TEXT,
                destination_state TEXT,
                destination_region TEXT,

                -- Lane Metadata
                lane_name TEXT,
                is_headhaul INTEGER DEFAULT 1,
                is_backhaul INTEGER DEFAULT 0,

                -- Frequency & Availability
                frequency TEXT,
                days_of_week TEXT,
                trucks_available INTEGER,

                -- Performance on Lane
                loads_completed_on_lane INTEGER DEFAULT 0,
                avg_rate_on_lane REAL,
                last_run_date TEXT,

                -- Preferences
                preferred_equipment_type TEXT,
                min_rate REAL,
                max_rate REAL,

                -- Source & Confidence
                source TEXT,
                confidence_score REAL,

                -- Timestamps
                created_at TEXT DEFAULT ({now}),
                last_updated TEXT DEFAULT ({now}),

                FOREIGN KEY (carrier_id) REFERENCES carriers(id) ON DELETE CASCADE
            )
        ''')

        # ===== TABLE 7: CARRIER DOCUMENTS =====
        cursor.execute(f'''
            CREATE TABLE IF NOT EXISTS carrier_documents (
                id {pk},
                carrier_id INTEGER NOT NULL,

                -- Document Classification
                document_type TEXT,
                document_subtype TEXT,

                -- File Information
                file_name TEXT,
                file_path TEXT,
                file_size INTEGER,
                mime_type TEXT,

                -- Validity
                effective_date TEXT,
                expiration_date TEXT,
                is_expired INTEGER DEFAULT 0,
                days_until_expiration INTEGER,

                -- Verification
                verified INTEGER DEFAULT 0,
                verified_by INTEGER,
                verified_date TEXT,
                verification_notes TEXT,

                -- Status
                status TEXT DEFAULT 'pending',
                rejection_reason TEXT,

                -- Metadata
                uploaded_by TEXT,
                upload_source TEXT,

                -- Timestamps
                uploaded_at TEXT DEFAULT ({now}),
                updated_at TEXT DEFAULT ({now}),

                FOREIGN KEY (carrier_id) REFERENCES carriers(id) ON DELETE CASCADE
            )
        ''')

        # ===== TABLE 8: CARRIER CONTACTS =====
        cursor.execute(f'''
            CREATE TABLE IF NOT EXISTS carrier_contacts (
                id {pk},
                carrier_id INTEGER NOT NULL,

                -- Contact Details
                first_name TEXT,
                last_name TEXT,
                title TEXT,

                -- Contact Information
                phone TEXT,
                phone_ext TEXT,
                mobile TEXT,
                email TEXT,

                -- Contact Type
                contact_type TEXT,
                is_primary INTEGER DEFAULT 0,

                -- Communication Preferences
                preferred_method TEXT DEFAULT 'SMS',
                send_load_offers INTEGER DEFAULT 1,
                send_invoices INTEGER DEFAULT 0,
                send_alerts INTEGER DEFAULT 1,

                -- Status
                status TEXT DEFAULT 'active',

                -- Notes
                notes TEXT,

                -- Timestamps
                created_at TEXT DEFAULT ({now}),
                updated_at TEXT DEFAULT ({now}),

                FOREIGN KEY (carrier_id) REFERENCES carriers(id) ON DELETE CASCADE
            )
        ''')

        # ===== TABLE 9: CARRIER BANKING =====
        cursor.execute(f'''
            CREATE TABLE IF NOT EXISTS carrier_banking (
                id {pk},
                carrier_id INTEGER NOT NULL,

                -- Bank Account Details
                bank_name TEXT,
                account_holder_name TEXT,
                account_type TEXT,
                routing_number TEXT,
                account_number_encrypted TEXT,
                account_number_last4 TEXT,

                -- Verification
                account_verified INTEGER DEFAULT 0,
                verification_method TEXT,
                verified_date TEXT,

                -- Payment Preferences
                payment_method TEXT DEFAULT 'ACH',
                quickpay_enrolled INTEGER DEFAULT 0,
                quickpay_fee_percentage REAL,

                -- Factoring
                uses_factoring INTEGER DEFAULT 0,
                factoring_company TEXT,
                factoring_company_email TEXT,
                factoring_company_phone TEXT,
                noa_on_file INTEGER DEFAULT 0,
                noa_expiration_date TEXT,
                noa_document_id INTEGER,

                -- Status
                status TEXT DEFAULT 'active',

                -- Timestamps
                created_at TEXT DEFAULT ({now}),
                updated_at TEXT DEFAULT ({now}),

                FOREIGN KEY (carrier_id) REFERENCES carriers(id) ON DELETE CASCADE
            )
        ''')

        # ===== TABLE 10: CARRIER RATES (Rate Intelligence) =====
        cursor.execute(f'''
            CREATE TABLE IF NOT EXISTS carrier_rates (
                id {pk},
                carrier_id INTEGER NOT NULL,
                load_id INTEGER,

                -- Lane Information
                origin_city TEXT,
                origin_state TEXT,
                destination_city TEXT,
                destination_state TEXT,

                -- Rate Details
                quoted_rate REAL,
                accepted_rate REAL,
                final_rate REAL,

                -- Load Characteristics
                miles INTEGER,
                equipment_type TEXT,
                weight INTEGER,
                commodity TEXT,

                -- Rate Breakdown
                linehaul_rate REAL,
                fuel_surcharge REAL,
                accessorials REAL,
                detention_charges REAL,
                layover_charges REAL,

                -- Market Conditions
                market_rate_low REAL,
                market_rate_high REAL,
                market_rate_avg REAL,
                rate_vs_market_percentage REAL,

                -- Negotiation Details
                initial_offer REAL,
                counter_offer REAL,
                rounds_of_negotiation INTEGER DEFAULT 0,

                -- Date & Time
                quote_date TEXT,
                booking_date TEXT,
                load_date TEXT,

                FOREIGN KEY (carrier_id) REFERENCES carriers(id) ON DELETE CASCADE
            )
        ''')

        # ===== EXISTING TABLES (Backward Compatibility) =====

        # Query log table
        cursor.execute(f'''
            CREATE TABLE IF NOT EXISTS carrier_queries (
                id {pk},
                carrier_id INTEGER,
                timestamp TEXT DEFAULT ({now}),
                channel TEXT,
                raw_message TEXT,

                -- Parsed intent
                intent TEXT,
                origin TEXT,
                destination TEXT,
                equipment_type TEXT,
                pickup_date TEXT,

                -- Response
                loads_shown INTEGER DEFAULT 0,
                load_ids_shown TEXT,
                action_taken TEXT,
                response_time_seconds INTEGER,

                FOREIGN KEY (carrier_id) REFERENCES carriers(id)
            )
        ''')

        # Booking requests table
        cursor.execute(f'''
            CREATE TABLE IF NOT EXISTS booking_requests (
                booking_id {pk},
                carrier_id INTEGER,
                load_id TEXT,
                timestamp TEXT DEFAULT ({now}),
                status TEXT DEFAULT 'pending',

                FOREIGN KEY (carrier_id) REFERENCES carriers(id)
            )
        ''')

        # ===== PHASE 1: CONVERSATION CONTEXT TABLES =====

        # Carrier profiles (AI Intelligence)
        cursor.execute(f'''
            CREATE TABLE IF NOT EXISTS carrier_profiles (
                id {pk},
                carrier_id INTEGER UNIQUE,
                current_location TEXT,
                next_empty_location TEXT,
                next_empty_date TEXT,
                equipment_types TEXT,
                preferred_lanes TEXT,
                typical_rate_ranges TEXT,
                last_updated TEXT DEFAULT ({now}),

                FOREIGN KEY (carrier_id) REFERENCES carriers(id)
            )
        ''')

        # Conversation context
        cursor.execute(f'''
            CREATE TABLE IF NOT EXISTS conversation_context (
                id {pk},
                carrier_id INTEGER UNIQUE,
                conversation_state TEXT,
                last_origin TEXT,
                last_destination TEXT,
                last_search_timestamp TEXT,
                context_data TEXT,

                FOREIGN KEY (carrier_id) REFERENCES carriers(id)
            )
        ''')

        # ===== CREATE INDEXES =====
        indexes = [
            'CREATE INDEX IF NOT EXISTS idx_carriers_dot ON carriers(dot_number)',
            'CREATE INDEX IF NOT EXISTS idx_carriers_mc ON carriers(mc_number)',
            'CREATE INDEX IF NOT EXISTS idx_carriers_phone ON carriers(phone)',
            'CREATE INDEX IF NOT EXISTS idx_carriers_email ON carriers(email)',
            'CREATE INDEX IF NOT EXISTS idx_carriers_status ON carriers(status)',
            'CREATE INDEX IF NOT EXISTS idx_carrier_queries ON carrier_queries(carrier_id)',
            'CREATE INDEX IF NOT EXISTS idx_queries_timestamp ON carrier_queries(timestamp)',
            'CREATE INDEX IF NOT EXISTS idx_carrier_profiles ON carrier_profiles(carrier_id)',
            'CREATE INDEX IF NOT EXISTS idx_conversation_context ON conversation_context(carrier_id)',
            'CREATE INDEX IF NOT EXISTS idx_carrier_lanes_origin ON carrier_lanes(origin_state, origin_city)',
            'CREATE INDEX IF NOT EXISTS idx_carrier_lanes_dest ON carrier_lanes(destination_state, destination_city)',
            'CREATE INDEX IF NOT EXISTS idx_insurance_expiration ON carrier_insurance(cargo_expiration_date)',
            'CREATE INDEX IF NOT EXISTS idx_documents_expiration ON carrier_documents(expiration_date)',
            'CREATE INDEX IF NOT EXISTS idx_performance_score ON carrier_performance(reliability_score DESC)',
            'CREATE INDEX IF NOT EXISTS idx_performance_preferred ON carrier_performance(preferred_carrier)',
        ]

        for index_sql in indexes:
            cursor.execute(index_sql)

        conn.commit()
        conn.close()

        print("✓ Comprehensive database initialized (12 tables)")

    # ===== EXISTING METHODS (Backward Compatibility) =====

    def get_carrier(self, carrier_id: int) -> Optional[Dict]:
        """Get carrier by ID"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM carriers WHERE id = ?', (carrier_id,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None

    def get_carrier_by_phone(self, phone: str) -> Optional[Dict]:
        """Get carrier by phone number"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM carriers WHERE phone = ?', (phone,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None

    def get_carrier_by_email(self, email: str) -> Optional[Dict]:
        """Get carrier by email address"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM carriers WHERE email = ?', (email,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None

    def create_carrier(self, phone: str = None, email: str = None, **kwargs) -> int:
        """Create new carrier profile"""
        conn = self.get_connection()
        cursor = conn.cursor()

        # Build fields list
        fields = []
        values = []

        if phone:
            fields.append('phone')
            values.append(phone)
        if email:
            fields.append('email')
            values.append(email)

        for key, value in kwargs.items():
            fields.append(key)
            values.append(value)

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

        kwargs['updated_at'] = datetime.now().isoformat()

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

        cursor.execute(f'''
            INSERT INTO carrier_queries
            (carrier_id, channel, raw_message, intent, origin, destination,
             equipment_type, pickup_date, loads_shown, load_ids_shown,
             action_taken, response_time_seconds)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            carrier_id, channel, raw_message, intent,
            kwargs.get('origin'), kwargs.get('destination'),
            kwargs.get('equipment_type'), kwargs.get('pickup_date'),
            kwargs.get('loads_shown', 0),
            json.dumps(kwargs.get('load_ids_shown', [])),
            kwargs.get('action_taken'),
            kwargs.get('response_time_seconds')
        ))

        cursor.execute(f'''
            UPDATE carriers
            SET total_queries = total_queries + 1,
                last_active_date = {now}
            WHERE id = ?
        ''', (carrier_id,))

        conn.commit()
        conn.close()

    def log_booking_request(self, carrier_id: int, load_id: str):
        """Log carrier booking request"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute(f'''
            INSERT INTO booking_requests (carrier_id, load_id)
            VALUES (?, ?)
        ''', (carrier_id, load_id))

        cursor.execute(f'''
            UPDATE carriers
            SET total_bookings = total_bookings + 1
            WHERE id = ?
        ''', (carrier_id,))

        conn.commit()
        conn.close()

    # ===== PHASE 1 METHODS =====

    def save_conversation_context(self, carrier_id: int, state: str,
                                  last_origin: str = None, last_destination: str = None,
                                  context_data: Dict = None):
        """Save conversation context for carrier"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT id FROM conversation_context WHERE carrier_id = ?', (carrier_id,))
        existing = cursor.fetchone()

        context_json = json.dumps(context_data) if context_data else None

        if existing:
            cursor.execute(f'''
                UPDATE conversation_context
                SET conversation_state = ?,
                    last_origin = COALESCE(?, last_origin),
                    last_destination = COALESCE(?, last_destination),
                    last_search_timestamp = {now},
                    context_data = COALESCE(?, context_data)
                WHERE carrier_id = ?
            ''', (state, last_origin, last_destination, context_json, carrier_id))
        else:
            cursor.execute(f'''
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

        cursor.execute('SELECT id FROM carrier_profiles WHERE carrier_id = ?', (carrier_id,))
        existing = cursor.fetchone()

        for key in ['equipment_types', 'preferred_lanes', 'typical_rate_ranges']:
            if key in kwargs and kwargs[key]:
                kwargs[key] = json.dumps(kwargs[key])

        if existing:
            set_clause = ', '.join([f"{k} = ?" for k in kwargs.keys()])
            set_clause += ', last_updated = datetime("now")'
            values = list(kwargs.values()) + [carrier_id]
            cursor.execute(f'UPDATE carrier_profiles SET {set_clause} WHERE carrier_id = ?', values)
        else:
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
            for key in ['equipment_types', 'preferred_lanes', 'typical_rate_ranges']:
                if profile.get(key):
                    try:
                        profile[key] = json.loads(profile[key])
                    except:
                        profile[key] = None
            return profile
        return None

    # ===== EQUIPMENT MANAGEMENT =====

    def add_carrier_equipment(self, carrier_id: int, **equipment_data) -> int:
        """Add equipment profile for carrier"""
        conn = self.get_connection()
        cursor = conn.cursor()

        # Check if carrier exists
        cursor.execute('SELECT id FROM carriers WHERE id = ?', (carrier_id,))
        if not cursor.fetchone():
            conn.close()
            raise ValueError(f"Carrier ID {carrier_id} not found")

        # Handle JSON fields
        if 'equipment_features' in equipment_data and isinstance(equipment_data['equipment_features'], (list, dict)):
            equipment_data['equipment_features'] = json.dumps(equipment_data['equipment_features'])

        equipment_data['carrier_id'] = carrier_id
        fields = ', '.join(equipment_data.keys())
        placeholders = ', '.join(['?' for _ in equipment_data])

        cursor.execute(
            f'INSERT INTO carrier_equipment ({fields}) VALUES ({placeholders})',
            list(equipment_data.values())
        )

        equipment_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return equipment_id

    def get_carrier_equipment(self, carrier_id: int) -> Optional[Dict]:
        """Get equipment profile for carrier"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM carrier_equipment WHERE carrier_id = ?', (carrier_id,))
        row = cursor.fetchone()
        conn.close()

        if row:
            equipment = dict(row)
            if equipment.get('equipment_features'):
                try:
                    equipment['equipment_features'] = json.loads(equipment['equipment_features'])
                except:
                    equipment['equipment_features'] = []
            return equipment
        return None

    def update_carrier_equipment(self, carrier_id: int, **updates) -> bool:
        """Update equipment profile"""
        conn = self.get_connection()
        cursor = conn.cursor()

        # Handle JSON fields
        if 'equipment_features' in updates and isinstance(updates['equipment_features'], (list, dict)):
            updates['equipment_features'] = json.dumps(updates['equipment_features'])

        updates['last_updated'] = datetime.now().isoformat()

        set_clause = ', '.join([f"{k} = ?" for k in updates.keys()])
        values = list(updates.values()) + [carrier_id]

        cursor.execute(
            f'UPDATE carrier_equipment SET {set_clause} WHERE carrier_id = ?',
            values
        )

        updated = cursor.rowcount > 0
        conn.commit()
        conn.close()
        return updated

    # ===== INSURANCE MANAGEMENT =====

    def add_carrier_insurance(self, carrier_id: int, **insurance_data) -> int:
        """Add insurance profile for carrier"""
        conn = self.get_connection()
        cursor = conn.cursor()

        # Check if carrier exists
        cursor.execute('SELECT id FROM carriers WHERE id = ?', (carrier_id,))
        if not cursor.fetchone():
            conn.close()
            raise ValueError(f"Carrier ID {carrier_id} not found")

        insurance_data['carrier_id'] = carrier_id
        fields = ', '.join(insurance_data.keys())
        placeholders = ', '.join(['?' for _ in insurance_data])

        cursor.execute(
            f'INSERT INTO carrier_insurance ({fields}) VALUES ({placeholders})',
            list(insurance_data.values())
        )

        insurance_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return insurance_id

    def get_carrier_insurance(self, carrier_id: int) -> Optional[Dict]:
        """Get insurance profile for carrier"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM carrier_insurance WHERE carrier_id = ?', (carrier_id,))
        row = cursor.fetchone()
        conn.close()

        return dict(row) if row else None

    def update_carrier_insurance(self, carrier_id: int, **updates) -> bool:
        """Update insurance profile"""
        conn = self.get_connection()
        cursor = conn.cursor()

        updates['updated_at'] = datetime.now().isoformat()

        set_clause = ', '.join([f"{k} = ?" for k in updates.keys()])
        values = list(updates.values()) + [carrier_id]

        cursor.execute(
            f'UPDATE carrier_insurance SET {set_clause} WHERE carrier_id = ?',
            values
        )

        updated = cursor.rowcount > 0
        conn.commit()
        conn.close()
        return updated

    def check_insurance_expiration(self, days_ahead: int = 30) -> List[Dict]:
        """Get carriers with insurance expiring soon"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute(f'''
            SELECT c.id, c.legal_name, c.phone, c.email,
                   i.auto_liability_expiration_date,
                   i.cargo_expiration_date
            FROM carriers c
            JOIN carrier_insurance i ON c.id = i.carrier_id
            WHERE julianday(i.auto_liability_expiration_date) - julianday('now') <= ?
               OR julianday(i.cargo_expiration_date) - julianday('now') <= ?
            ORDER BY i.auto_liability_expiration_date, i.cargo_expiration_date
        ''', (days_ahead, days_ahead))

        rows = cursor.fetchall()
        conn.close()

        return [dict(row) for row in rows]

    # ===== SAFETY SCORES =====

    def update_fmcsa_scores(self, carrier_id: int, **fmcsa_data) -> int:
        """Update or insert FMCSA safety scores"""
        conn = self.get_connection()
        cursor = conn.cursor()

        # Check if carrier exists
        cursor.execute('SELECT id FROM carriers WHERE id = ?', (carrier_id,))
        if not cursor.fetchone():
            conn.close()
            raise ValueError(f"Carrier ID {carrier_id} not found")

        # Check if scores already exist
        cursor.execute('SELECT id FROM carrier_safety_scores WHERE carrier_id = ?', (carrier_id,))
        existing = cursor.fetchone()

        fmcsa_data['fmcsa_last_updated'] = datetime.now().isoformat()

        if existing:
            set_clause = ', '.join([f"{k} = ?" for k in fmcsa_data.keys()])
            values = list(fmcsa_data.values()) + [carrier_id]
            cursor.execute(
                f'UPDATE carrier_safety_scores SET {set_clause} WHERE carrier_id = ?',
                values
            )
            score_id = existing[0]
        else:
            fmcsa_data['carrier_id'] = carrier_id
            fields = ', '.join(fmcsa_data.keys())
            placeholders = ', '.join(['?' for _ in fmcsa_data])
            cursor.execute(
                f'INSERT INTO carrier_safety_scores ({fields}) VALUES ({placeholders})',
                list(fmcsa_data.values())
            )
            score_id = cursor.lastrowid

        conn.commit()
        conn.close()
        return score_id

    def get_carrier_safety_score(self, carrier_id: int) -> Optional[Dict]:
        """Get FMCSA safety scores for carrier"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM carrier_safety_scores WHERE carrier_id = ?', (carrier_id,))
        row = cursor.fetchone()
        conn.close()

        return dict(row) if row else None

    def get_carriers_by_safety_rating(self, min_score: float = 70) -> List[Dict]:
        """Get carriers with safety score above threshold"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute(f'''
            SELECT c.*, s.overall_safety_rating, s.iss_score
            FROM carriers c
            JOIN carrier_safety_scores s ON c.id = s.carrier_id
            WHERE s.iss_score >= ?
            ORDER BY s.iss_score DESC
        ''', (min_score,))

        rows = cursor.fetchall()
        conn.close()

        return [dict(row) for row in rows]

    # ===== PERFORMANCE TRACKING =====

    def update_carrier_performance(self, carrier_id: int, **metrics) -> int:
        """Update or insert carrier performance metrics"""
        conn = self.get_connection()
        cursor = conn.cursor()

        # Check if carrier exists
        cursor.execute('SELECT id FROM carriers WHERE id = ?', (carrier_id,))
        if not cursor.fetchone():
            conn.close()
            raise ValueError(f"Carrier ID {carrier_id} not found")

        # Check if performance record exists
        cursor.execute('SELECT id FROM carrier_performance WHERE carrier_id = ?', (carrier_id,))
        existing = cursor.fetchone()

        metrics['last_calculated'] = datetime.now().isoformat()

        if existing:
            set_clause = ', '.join([f"{k} = ?" for k in metrics.keys()])
            values = list(metrics.values()) + [carrier_id]
            cursor.execute(
                f'UPDATE carrier_performance SET {set_clause} WHERE carrier_id = ?',
                values
            )
            performance_id = existing[0]
        else:
            metrics['carrier_id'] = carrier_id
            fields = ', '.join(metrics.keys())
            placeholders = ', '.join(['?' for _ in metrics])
            cursor.execute(
                f'INSERT INTO carrier_performance ({fields}) VALUES ({placeholders})',
                list(metrics.values())
            )
            performance_id = cursor.lastrowid

        conn.commit()
        conn.close()
        return performance_id

    def get_carrier_performance(self, carrier_id: int) -> Optional[Dict]:
        """Get performance metrics for carrier"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM carrier_performance WHERE carrier_id = ?', (carrier_id,))
        row = cursor.fetchone()
        conn.close()

        return dict(row) if row else None

    def get_top_performing_carriers(self, limit: int = 50) -> List[Dict]:
        """Get top performing carriers by reliability score"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute(f'''
            SELECT c.*, p.reliability_score, p.on_time_pickup_percentage,
                   p.on_time_delivery_percentage, p.total_loads_completed
            FROM carriers c
            JOIN carrier_performance p ON c.id = p.carrier_id
            WHERE p.reliability_score IS NOT NULL
            ORDER BY p.reliability_score DESC
            LIMIT ?
        ''', (limit,))

        rows = cursor.fetchall()
        conn.close()

        return [dict(row) for row in rows]

    def get_carrier_reliability_score(self, carrier_id: int) -> Optional[float]:
        """Get reliability score for a carrier"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute(
            'SELECT reliability_score FROM carrier_performance WHERE carrier_id = ?',
            (carrier_id,)
        )
        row = cursor.fetchone()
        conn.close()

        return row[0] if row and row[0] is not None else None

    # ===== LANE MANAGEMENT =====

    def add_carrier_lane(self, carrier_id: int, origin: str, destination: str, **lane_data) -> int:
        """Add a lane preference for carrier"""
        conn = self.get_connection()
        cursor = conn.cursor()

        # Check if carrier exists
        cursor.execute('SELECT id FROM carriers WHERE id = ?', (carrier_id,))
        if not cursor.fetchone():
            conn.close()
            raise ValueError(f"Carrier ID {carrier_id} not found")

        # Parse origin and destination (assuming "City, State" format)
        if ',' in origin:
            origin_city, origin_state = [x.strip() for x in origin.split(',')]
            lane_data['origin_city'] = origin_city
            lane_data['origin_state'] = origin_state

        if ',' in destination:
            dest_city, dest_state = [x.strip() for x in destination.split(',')]
            lane_data['destination_city'] = dest_city
            lane_data['destination_state'] = dest_state

        lane_data['carrier_id'] = carrier_id
        fields = ', '.join(lane_data.keys())
        placeholders = ', '.join(['?' for _ in lane_data])

        cursor.execute(
            f'INSERT INTO carrier_lanes ({fields}) VALUES ({placeholders})',
            list(lane_data.values())
        )

        lane_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return lane_id

    def get_carrier_lanes(self, carrier_id: int) -> List[Dict]:
        """Get all lane preferences for carrier"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute(f'''
            SELECT * FROM carrier_lanes
            WHERE carrier_id = ?
            ORDER BY loads_completed_on_lane DESC, confidence_score DESC
        ''', (carrier_id,))

        rows = cursor.fetchall()
        conn.close()

        return [dict(row) for row in rows]

    def find_carriers_for_lane(self, origin_state: str, destination_state: str,
                               origin_city: str = None, destination_city: str = None) -> List[Dict]:
        """Find carriers that service a specific lane"""
        conn = self.get_connection()
        cursor = conn.cursor()

        query = '''
            SELECT c.*, l.avg_rate_on_lane, l.loads_completed_on_lane, l.preferred_equipment_type
            FROM carriers c
            JOIN carrier_lanes l ON c.id = l.carrier_id
            WHERE l.origin_state = ? AND l.destination_state = ?
        '''
        params = [origin_state, destination_state]

        if origin_city:
            query += ' AND l.origin_city = ?'
            params.append(origin_city)

        if destination_city:
            query += ' AND l.destination_city = ?'
            params.append(destination_city)

        query += ' ORDER BY l.loads_completed_on_lane DESC, l.confidence_score DESC'

        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()

        return [dict(row) for row in rows]

    # ===== DOCUMENT MANAGEMENT =====

    def add_carrier_document(self, carrier_id: int, doc_type: str, file_path: str, **doc_data) -> int:
        """Add a document for carrier"""
        conn = self.get_connection()
        cursor = conn.cursor()

        # Check if carrier exists
        cursor.execute('SELECT id FROM carriers WHERE id = ?', (carrier_id,))
        if not cursor.fetchone():
            conn.close()
            raise ValueError(f"Carrier ID {carrier_id} not found")

        doc_data['carrier_id'] = carrier_id
        doc_data['document_type'] = doc_type
        doc_data['file_path'] = file_path

        # Extract filename if not provided
        if 'file_name' not in doc_data:
            doc_data['file_name'] = os.path.basename(file_path)

        fields = ', '.join(doc_data.keys())
        placeholders = ', '.join(['?' for _ in doc_data])

        cursor.execute(
            f'INSERT INTO carrier_documents ({fields}) VALUES ({placeholders})',
            list(doc_data.values())
        )

        doc_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return doc_id

    def get_carrier_documents(self, carrier_id: int, doc_type: str = None) -> List[Dict]:
        """Get documents for carrier"""
        conn = self.get_connection()
        cursor = conn.cursor()

        if doc_type:
            cursor.execute(f'''
                SELECT * FROM carrier_documents
                WHERE carrier_id = ? AND document_type = ?
                ORDER BY uploaded_at DESC
            ''', (carrier_id, doc_type))
        else:
            cursor.execute(f'''
                SELECT * FROM carrier_documents
                WHERE carrier_id = ?
                ORDER BY uploaded_at DESC
            ''', (carrier_id,))

        rows = cursor.fetchall()
        conn.close()

        return [dict(row) for row in rows]

    def get_expiring_documents(self, days_ahead: int = 30) -> List[Dict]:
        """Get documents expiring soon"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute(f'''
            SELECT c.id, c.legal_name, c.phone, c.email,
                   d.document_type, d.file_name, d.expiration_date
            FROM carriers c
            JOIN carrier_documents d ON c.id = d.carrier_id
            WHERE d.expiration_date IS NOT NULL
              AND julianday(d.expiration_date) - julianday('now') <= ?
              AND d.is_expired = 0
            ORDER BY d.expiration_date
        ''', (days_ahead,))

        rows = cursor.fetchall()
        conn.close()

        return [dict(row) for row in rows]

    # ===== CONTACT MANAGEMENT =====

    def add_carrier_contact(self, carrier_id: int, first_name: str, last_name: str,
                           phone: str = None, email: str = None, contact_type: str = None,
                           **contact_data) -> int:
        """Add a contact for carrier"""
        conn = self.get_connection()
        cursor = conn.cursor()

        # Check if carrier exists
        cursor.execute('SELECT id FROM carriers WHERE id = ?', (carrier_id,))
        if not cursor.fetchone():
            conn.close()
            raise ValueError(f"Carrier ID {carrier_id} not found")

        contact_data['carrier_id'] = carrier_id
        contact_data['first_name'] = first_name
        contact_data['last_name'] = last_name

        if phone:
            contact_data['phone'] = phone
        if email:
            contact_data['email'] = email
        if contact_type:
            contact_data['contact_type'] = contact_type

        fields = ', '.join(contact_data.keys())
        placeholders = ', '.join(['?' for _ in contact_data])

        cursor.execute(
            f'INSERT INTO carrier_contacts ({fields}) VALUES ({placeholders})',
            list(contact_data.values())
        )

        contact_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return contact_id

    def get_carrier_contacts(self, carrier_id: int) -> List[Dict]:
        """Get all contacts for carrier"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute(f'''
            SELECT * FROM carrier_contacts
            WHERE carrier_id = ?
            ORDER BY is_primary DESC, created_at
        ''', (carrier_id,))

        rows = cursor.fetchall()
        conn.close()

        return [dict(row) for row in rows]

    def get_primary_contact(self, carrier_id: int) -> Optional[Dict]:
        """Get primary contact for carrier"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute(f'''
            SELECT * FROM carrier_contacts
            WHERE carrier_id = ? AND is_primary = 1
            LIMIT 1
        ''', (carrier_id,))

        row = cursor.fetchone()
        conn.close()

        return dict(row) if row else None

    # ===== BANKING =====

    def add_carrier_banking(self, carrier_id: int, **banking_data) -> int:
        """Add banking information for carrier"""
        conn = self.get_connection()
        cursor = conn.cursor()

        # Check if carrier exists
        cursor.execute('SELECT id FROM carriers WHERE id = ?', (carrier_id,))
        if not cursor.fetchone():
            conn.close()
            raise ValueError(f"Carrier ID {carrier_id} not found")

        banking_data['carrier_id'] = carrier_id
        fields = ', '.join(banking_data.keys())
        placeholders = ', '.join(['?' for _ in banking_data])

        cursor.execute(
            f'INSERT INTO carrier_banking ({fields}) VALUES ({placeholders})',
            list(banking_data.values())
        )

        banking_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return banking_id

    def get_carrier_banking(self, carrier_id: int) -> Optional[Dict]:
        """Get banking information for carrier"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM carrier_banking WHERE carrier_id = ?', (carrier_id,))
        row = cursor.fetchone()
        conn.close()

        return dict(row) if row else None

    def update_carrier_banking(self, carrier_id: int, **updates) -> bool:
        """Update banking information"""
        conn = self.get_connection()
        cursor = conn.cursor()

        updates['updated_at'] = datetime.now().isoformat()

        set_clause = ', '.join([f"{k} = ?" for k in updates.keys()])
        values = list(updates.values()) + [carrier_id]

        cursor.execute(
            f'UPDATE carrier_banking SET {set_clause} WHERE carrier_id = ?',
            values
        )

        updated = cursor.rowcount > 0
        conn.commit()
        conn.close()
        return updated

    # ===== RATE INTELLIGENCE =====

    def log_carrier_rate(self, carrier_id: int, load_id: int, origin: str, destination: str,
                        rate: float, **rate_data) -> int:
        """Log a rate quote/booking for carrier"""
        conn = self.get_connection()
        cursor = conn.cursor()

        # Check if carrier exists
        cursor.execute('SELECT id FROM carriers WHERE id = ?', (carrier_id,))
        if not cursor.fetchone():
            conn.close()
            raise ValueError(f"Carrier ID {carrier_id} not found")

        rate_data['carrier_id'] = carrier_id
        rate_data['load_id'] = load_id

        # Parse origin and destination
        if ',' in origin:
            origin_city, origin_state = [x.strip() for x in origin.split(',')]
            rate_data['origin_city'] = origin_city
            rate_data['origin_state'] = origin_state

        if ',' in destination:
            dest_city, dest_state = [x.strip() for x in destination.split(',')]
            rate_data['destination_city'] = dest_city
            rate_data['destination_state'] = dest_state

        # Add rate
        if 'accepted_rate' not in rate_data:
            rate_data['accepted_rate'] = rate

        rate_data['quote_date'] = datetime.now().isoformat()

        fields = ', '.join(rate_data.keys())
        placeholders = ', '.join(['?' for _ in rate_data])

        cursor.execute(
            f'INSERT INTO carrier_rates ({fields}) VALUES ({placeholders})',
            list(rate_data.values())
        )

        rate_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return rate_id

    def get_carrier_rate_history(self, carrier_id: int, origin_state: str = None,
                                 destination_state: str = None) -> List[Dict]:
        """Get rate history for carrier, optionally filtered by lane"""
        conn = self.get_connection()
        cursor = conn.cursor()

        query = 'SELECT * FROM carrier_rates WHERE carrier_id = ?'
        params = [carrier_id]

        if origin_state:
            query += ' AND origin_state = ?'
            params.append(origin_state)

        if destination_state:
            query += ' AND destination_state = ?'
            params.append(destination_state)

        query += ' ORDER BY quote_date DESC'

        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()

        return [dict(row) for row in rows]

    def get_average_rate_for_lane(self, origin_state: str, destination_state: str,
                                  days: int = 90) -> Optional[Dict]:
        """Get average rate for a lane across all carriers"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute(f'''
            SELECT
                AVG(accepted_rate) as avg_rate,
                MIN(accepted_rate) as min_rate,
                MAX(accepted_rate) as max_rate,
                COUNT(*) as sample_size
            FROM carrier_rates
            WHERE origin_state = ? AND destination_state = ?
              AND julianday('now') - julianday(quote_date) <= ?
        ''', (origin_state, destination_state, days))

        row = cursor.fetchone()
        conn.close()

        if row and row[0] is not None:
            return {
                'avg_rate': row[0],
                'min_rate': row[1],
                'max_rate': row[2],
                'sample_size': row[3],
                'origin_state': origin_state,
                'destination_state': destination_state,
                'days_analyzed': days
            }
        return None


# Alias for backward compatibility
Database = ComprehensiveCarrierDatabase
