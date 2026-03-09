"""
SMS Channel for Eagle Carrier Chatbot
Handles Twilio integration for SMS communication
"""

import os
from twilio.rest import Client
from twilio.twiml.messaging_response import MessagingResponse
from typing import Dict

class SMSChannel:
    def __init__(self, account_sid: str = None, auth_token: str = None, phone_number: str = None):
        """
        Initialize Twilio SMS channel

        Args:
            account_sid: Twilio Account SID
            auth_token: Twilio Auth Token
            phone_number: Your Twilio phone number (format: +17705551234)
        """
        self.account_sid = account_sid or os.getenv('TWILIO_ACCOUNT_SID')
        self.auth_token = auth_token or os.getenv('TWILIO_AUTH_TOKEN')
        self.phone_number = phone_number or os.getenv('TWILIO_PHONE_NUMBER')

        self.client = None
        if self.account_sid and self.auth_token:
            self.client = Client(self.account_sid, self.auth_token)
            print("✓ Twilio client initialized")

    def normalize_phone(self, phone: str) -> str:
        """
        Normalize phone number to E.164 format

        Args:
            phone: Phone number in any format

        Returns:
            Normalized phone like +14045551234
        """
        # Remove all non-digits
        digits = ''.join(filter(str.isdigit, phone))

        # Add +1 for US numbers
        if len(digits) == 10:
            digits = '1' + digits

        return '+' + digits

    def is_us_phone(self, phone: str) -> bool:
        """Check if phone number is US/Canada"""
        normalized = self.normalize_phone(phone)
        return normalized.startswith('+1')

    def send_sms(self, to_phone: str, message: str) -> bool:
        """
        Send SMS to carrier

        Args:
            to_phone: Carrier phone number
            message: Message text

        Returns:
            True if sent successfully
        """
        if not self.client:
            print(f"[Mock SMS to {to_phone}]: {message}")
            return True

        try:
            to_normalized = self.normalize_phone(to_phone)

            message = self.client.messages.create(
                from_=self.phone_number,
                to=to_normalized,
                body=message
            )

            print(f"✓ SMS sent to {to_normalized}: {message.sid}")
            return True

        except Exception as e:
            print(f"✗ Failed to send SMS to {to_phone}: {e}")
            return False

    def parse_incoming_sms(self, request_data: Dict) -> Dict:
        """
        Parse incoming Twilio webhook request

        Args:
            request_data: POST data from Twilio webhook

        Returns:
            {
                'from_phone': '+14045551234',
                'to_phone': '+17705551234',
                'message': 'Atlanta loads',
                'message_sid': 'SM...',
                'from_city': 'Atlanta',
                'from_state': 'GA'
            }
        """
        return {
            'from_phone': request_data.get('From', ''),
            'to_phone': request_data.get('To', ''),
            'message': request_data.get('Body', ''),
            'message_sid': request_data.get('MessageSid', ''),
            'from_city': request_data.get('FromCity', ''),
            'from_state': request_data.get('FromState', ''),
            'from_country': request_data.get('FromCountry', '')
        }

    def create_twiml_response(self, message: str) -> str:
        """
        Create TwiML response for Twilio webhook

        Args:
            message: Response message to send

        Returns:
            TwiML XML string
        """
        resp = MessagingResponse()
        resp.message(message)
        return str(resp)


# For development/testing without Twilio credentials
class MockSMSChannel:
    """Mock SMS channel for testing without Twilio"""

    def __init__(self):
        print("✓ Using mock SMS (no Twilio connection)")

    def normalize_phone(self, phone):
        digits = ''.join(filter(str.isdigit, phone))
        if len(digits) == 10:
            digits = '1' + digits
        return '+' + digits

    def is_us_phone(self, phone):
        return True

    def send_sms(self, to_phone, message):
        print(f"\n{'='*50}")
        print(f"MOCK SMS TO: {to_phone}")
        print(f"{'='*50}")
        print(message)
        print(f"{'='*50}\n")
        return True

    def parse_incoming_sms(self, request_data):
        return {
            'from_phone': request_data.get('From', '+14045551234'),
            'to_phone': request_data.get('To', '+17709651242'),
            'message': request_data.get('Body', ''),
            'message_sid': 'SM_MOCK_' + str(hash(request_data.get('Body', '')))[:8],
            'from_city': 'Atlanta',
            'from_state': 'GA',
            'from_country': 'US'
        }

    def create_twiml_response(self, message):
        return f'<?xml version="1.0" encoding="UTF-8"?><Response><Message>{message}</Message></Response>'
