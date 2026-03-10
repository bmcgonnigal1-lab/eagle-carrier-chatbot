"""
RingCentral SMS Channel
"""

from ringcentral import SDK
import os


class RingCentralSMSChannel:
    """RingCentral SMS integration"""

    def __init__(self, client_id=None, client_secret=None, server=None, phone_number=None):
        """Initialize RingCentral SMS"""
        self.client_id = client_id or os.getenv('RC_CLIENT_ID')
        self.client_secret = client_secret or os.getenv('RC_CLIENT_SECRET')
        self.server = server or os.getenv('RC_SERVER_URL', 'https://platform.ringcentral.com')
        self.phone_number = phone_number or os.getenv('RC_PHONE_NUMBER')

        if not all([self.client_id, self.client_secret, self.phone_number]):
            raise ValueError("Missing RingCentral credentials")

        self.sdk = SDK(self.client_id, self.client_secret, self.server)
        self.platform = self.sdk.platform()
        print("✓ RingCentral SMS client initialized")

    def login(self, username=None, extension=None, password=None):
        """Login to RingCentral"""
        username = username or os.getenv('RC_USERNAME')
        password = password or os.getenv('RC_PASSWORD')
        extension = extension or os.getenv('RC_EXTENSION', '')

        if not username or not password:
            raise ValueError("Missing RC_USERNAME or RC_PASSWORD")

        try:
            self.platform.login(username, extension, password)
            print("✓ RingCentral authentication successful")
        except Exception as e:
            print(f"✗ RingCentral authentication failed: {e}")
            raise

    def send_sms(self, to_phone: str, message: str) -> bool:
        """Send SMS via RingCentral"""
        try:
            response = self.platform.post('/restapi/v1.0/account/~/extension/~/sms', {
                'from': {'phoneNumber': self.phone_number},
                'to': [{'phoneNumber': to_phone}],
                'text': message
            })
            print(f"✓ SMS sent to {to_phone}")
            return True
        except Exception as e:
            print(f"✗ Failed to send SMS to {to_phone}: {e}")
            return False

    def is_us_phone(self, phone: str) -> bool:
        """Check if phone is US or Canada"""
        return phone.startswith('+1')


class MockRingCentralSMSChannel:
    """Mock RingCentral SMS"""

    def __init__(self, *args, **kwargs):
        print("✓ Using mock RingCentral SMS")

    def login(self, *args, **kwargs):
        print("✓ Mock RingCentral login")

    def send_sms(self, to_phone: str, message: str) -> bool:
        """Simulate SMS"""
        print(f"\n📱 [MOCK SMS to {to_phone}]")
        print(f"Message: {message}\n")
        return True

    def is_us_phone(self, phone: str) -> bool:
        """Check if phone is US or Canada"""
        return phone.startswith('+1')
