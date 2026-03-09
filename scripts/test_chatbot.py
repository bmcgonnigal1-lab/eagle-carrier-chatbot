#!/usr/bin/env python3
"""
Test the carrier chatbot interactively
"""

import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

# Import config
try:
    import config
    USE_MOCK_SMS = config.USE_MOCK_SMS
    USE_MOCK_SHEETS = config.USE_MOCK_SHEETS
    OPENAI_API_KEY = getattr(config, 'OPENAI_API_KEY', '')
    TWILIO_ACCOUNT_SID = getattr(config, 'TWILIO_ACCOUNT_SID', '')
    TWILIO_AUTH_TOKEN = getattr(config, 'TWILIO_AUTH_TOKEN', '')
    TWILIO_PHONE_NUMBER = getattr(config, 'TWILIO_PHONE_NUMBER', '')
    GOOGLE_CREDENTIALS_PATH = getattr(config, 'GOOGLE_CREDENTIALS_PATH', '')
    GOOGLE_SHEET_URL = getattr(config, 'GOOGLE_SHEET_URL', '')
except ImportError:
    print("⚠️  No config.py found. Using mock mode.")
    USE_MOCK_SMS = True
    USE_MOCK_SHEETS = True
    OPENAI_API_KEY = ''
    TWILIO_ACCOUNT_SID = ''
    TWILIO_AUTH_TOKEN = ''
    TWILIO_PHONE_NUMBER = ''
    GOOGLE_CREDENTIALS_PATH = ''
    GOOGLE_SHEET_URL = ''

from app.main import CarrierChatbot

def main():
    print("\n" + "="*60)
    print("🦅 EAGLE CARRIER CHATBOT - INTERACTIVE TEST")
    print("="*60)

    # Configuration
    config = {
        'database_path': 'data/carriers.db',
        'use_mock_sms': USE_MOCK_SMS,
        'use_mock_sheets': USE_MOCK_SHEETS,
        'openai_api_key': OPENAI_API_KEY,
        'twilio_account_sid': TWILIO_ACCOUNT_SID,
        'twilio_auth_token': TWILIO_AUTH_TOKEN,
        'twilio_phone_number': TWILIO_PHONE_NUMBER,
        'google_credentials_path': GOOGLE_CREDENTIALS_PATH,
        'google_sheet_url': GOOGLE_SHEET_URL
    }

    # Create chatbot
    chatbot = CarrierChatbot(config)

    print("\n" + "="*60)
    print("Test the chatbot! Type carrier messages below.")
    print("="*60)
    print("\nExamples:")
    print("  - Atlanta loads")
    print("  - Atlanta to Dallas dry van")
    print("  - Book L12345")
    print("  - Miami reefer")
    print("\nType 'quit' to exit\n")
    print("="*60 + "\n")

    test_phone = "+14045551234"

    while True:
        try:
            message = input("📱 Carrier message: ")

            if message.lower() in ['quit', 'exit', 'q']:
                print("\n👋 Goodbye!\n")
                break

            if not message.strip():
                continue

            # Process message
            response = chatbot.handle_sms(test_phone, message)

            print(f"\n🦅 Eagle Response:")
            print("-" * 60)
            print(response)
            print("-" * 60 + "\n")

        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!\n")
            break
        except Exception as e:
            print(f"\n✗ Error: {e}\n")

if __name__ == '__main__':
    main()
