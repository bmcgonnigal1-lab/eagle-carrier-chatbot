"""
Main Application for Eagle Carrier Chatbot
Orchestrates all components: SMS, Database, AI, Google Sheets
"""

import sys
import os
from datetime import datetime
from typing import Dict, Optional

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from app.database import Database
from app.ai_engine import AIEngine
from channels.sms import SMSChannel, MockSMSChannel
from channels.email import EmailChannel, MockEmailChannel
from integrations.google_sheets import GoogleSheetsLoader, MockSheetsLoader, SqliteLoadsLoader


class CarrierChatbot:
    def __init__(self, config: Dict = None, use_mock_sms: bool = True,
                 use_mock_sheets: bool = True, use_mock_email: bool = True):
        """
        Initialize Eagle Carrier Chatbot

        Args:
            config: Configuration dictionary with API keys and settings (deprecated)
            use_mock_sms: Use mock SMS (True) or real Twilio (False)
            use_mock_sheets: Use mock sheets (True) or real Google Sheets (False)
            use_mock_email: Use mock email (True) or real Microsoft 365 (False)
        """
        # Handle both old config dict style and new parameter style
        if config:
            self.config = config
            use_mock_sms = config.get('use_mock_sms', True)
            use_mock_sheets = config.get('use_mock_sheets', True)
            use_mock_email = config.get('use_mock_email', True)
        else:
            self.config = {}

        # Initialize components
        print("\n🦅 Initializing Eagle Carrier Chatbot...")

        # Database
        db_path = self.config.get('database_path', 'data/carriers.db')
        self.database = Database(db_path)

        # AI Engine
        self.ai_engine = AIEngine(api_key=self.config.get('openai_api_key'))

        # SMS Channel
        if use_mock_sms:
            self.sms_channel = MockSMSChannel()
        else:
            self.sms_channel = SMSChannel(
                account_sid=self.config.get('twilio_account_sid'),
                auth_token=self.config.get('twilio_auth_token'),
                phone_number=self.config.get('twilio_phone_number')
            )

        # Email Channel (Phase 2)
        if use_mock_email:
            self.email_channel = MockEmailChannel()
        else:
            self.email_channel = EmailChannel(
                tenant_id=self.config.get('ms_tenant_id'),
                client_id=self.config.get('ms_client_id'),
                client_secret=self.config.get('ms_client_secret'),
                dispatch_email=self.config.get('dispatch_email')
            )

        # Load Data Source
        if use_mock_sheets:
            # Try SqliteLoadsLoader first, fall back to MockSheetsLoader
            # Check both static/loads.db and data/loads.db
            self.sheets_loader = SqliteLoadsLoader('static/loads.db')
            if not self.sheets_loader.connect():
                # Try data/loads.db
                self.sheets_loader = SqliteLoadsLoader('data/loads.db')
                if not self.sheets_loader.connect():
                    # If no database found, use mock data
                    self.sheets_loader = MockSheetsLoader()
                    self.sheets_loader.connect()
        else:
            self.sheets_loader = GoogleSheetsLoader(
                credentials_path=self.config.get('google_credentials_path'),
                sheet_url=self.config.get('google_sheet_url')
            )
            self.sheets_loader.connect()

        print("✅ Eagle Carrier Chatbot initialized!\n")

    def handle_sms(self, from_phone: str, message: str) -> str:
        """
        Handle incoming SMS from carrier

        Args:
            from_phone: Carrier phone number
            message: SMS message text

        Returns:
            Response message to send back
        """
        start_time = datetime.now()

        # Normalize phone
        from_phone = self.sms_channel.normalize_phone(from_phone)

        # Security check: US/Canada only
        if not self.sms_channel.is_us_phone(from_phone):
            return "We only serve US/Canada carriers. Contact dispatch@eagletransportation.com"

        # Get or create carrier
        carrier = self.database.get_carrier_by_phone(from_phone)
        if not carrier:
            # New carrier - create profile
            carrier_id = self.database.create_carrier(
                phone=from_phone,
                status='active',
                onboarding_complete=False
            )
            carrier = self.database.get_carrier_by_phone(from_phone)
            carrier_name = "there"
        else:
            carrier_id = carrier['id']
            carrier_name = carrier.get('name') or "there"

        # Parse message with AI
        parsed = self.ai_engine.parse_carrier_request(message)
        intent = parsed.get('intent', 'search_loads')

        response = ""

        if intent == 'book_load':
            # Booking request
            load_id = parsed.get('load_id')
            load = self.sheets_loader.get_load_by_id(load_id)

            if load:
                # Log booking request
                self.database.log_booking_request(carrier_id, load_id)

                # Alert dispatch (in production, send email/SMS to dispatch)
                self._alert_dispatch_booking(carrier, load)

                response = self.ai_engine.generate_response(
                    carrier_name, [], 'book_load', 'sms'
                )
            else:
                response = f"Load {load_id} not found. Reply LOADS to see available loads."

        elif intent == 'search_loads':
            # Search for loads
            loads = self.sheets_loader.search_loads(
                origin=parsed.get('origin'),
                destination=parsed.get('destination'),
                equipment_type=parsed.get('equipment_type'),
                pickup_date=parsed.get('pickup_date')
            )

            # Generate response
            response = self.ai_engine.generate_response(
                carrier_name, loads, 'search_loads', 'sms'
            )

            # Log query
            load_ids = [load.get('load_id') for load in loads]
            self.database.log_query(
                carrier_id=carrier_id,
                channel='sms',
                raw_message=message,
                intent=intent,
                origin=parsed.get('origin'),
                destination=parsed.get('destination'),
                equipment_type=parsed.get('equipment_type'),
                pickup_date=parsed.get('pickup_date'),
                loads_shown=len(loads),
                load_ids_shown=load_ids,
                response_time_seconds=(datetime.now() - start_time).seconds
            )

        else:
            # General question
            response = """Eagle Transportation here!

Text me:
• City names for loads (e.g., "Atlanta loads")
• "Atlanta to Dallas dry van"
• "Book L12345" to request a load

Questions? Call 770-965-1242"""

        return response

    def handle_email(self, from_email: str, from_name: str,
                    subject: str, body: str) -> str:
        """
        Handle incoming email from carrier (Phase 2)

        Args:
            from_email: Carrier email address
            from_name: Carrier name
            subject: Email subject
            body: Email body text

        Returns:
            Response message
        """
        # Get or create carrier
        carrier = self.database.get_carrier_by_email(from_email)
        if not carrier:
            carrier_id = self.database.create_carrier(
                email=from_email,
                name=from_name,
                status='active'
            )
            carrier_name = from_name
        else:
            carrier_id = carrier['id']
            carrier_name = carrier.get('name') or from_name

        # Parse email with AI
        parsed = self.ai_engine.parse_carrier_request(body)
        intent = parsed.get('intent', 'search_loads')

        if intent == 'search_loads':
            loads = self.sheets_loader.search_loads(
                origin=parsed.get('origin'),
                destination=parsed.get('destination'),
                equipment_type=parsed.get('equipment_type')
            )

            response = self.ai_engine.generate_response(
                carrier_name, loads, 'search_loads', 'email'
            )

            # Log query
            self.database.log_query(
                carrier_id=carrier_id,
                channel='email',
                raw_message=body,
                intent=intent,
                origin=parsed.get('origin'),
                destination=parsed.get('destination'),
                equipment_type=parsed.get('equipment_type'),
                loads_shown=len(loads)
            )

            return response

        return "Thank you for your message. Our dispatch team will respond shortly."

    def _alert_dispatch_booking(self, carrier: Dict, load: Dict):
        """
        Alert dispatch team of booking request (internal)
        In production, this would send email/SMS to dispatch
        """
        print(f"\n📬 BOOKING REQUEST ALERT")
        print(f"Carrier: {carrier.get('name', 'Unknown')} ({carrier.get('phone', carrier.get('email'))})")
        print(f"Load: {load['load_id']} - {load['origin']} to {load['destination']}")
        print(f"Rate: ${load['rate']:,}\n")
