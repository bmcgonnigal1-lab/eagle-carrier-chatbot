"""
RingCentral SMS Channel with JWT Authentication
"""

from ringcentral import SDK
import os


class RingCentralSMSChannel:
    """RingCentral SMS integration using JWT auth"""

    def __init__(self, client_id=None, client_secret=None, server=None, phone_number=None, jwt_token=None):
        """Initialize RingCentral SMS with JWT"""
        self.client_id = client_id or os.getenv('RC_APP_CLIENT_ID')
        self.client_secret = client_secret or os.getenv('RC_APP_CLIENT_SECRET')
        self.server = server or os.getenv('RC_SERVER_URL', 'https://platform.ringcentral.com')
        self.phone_number = phone_number or os.getenv('RC_PHONE_NUMBER')
        self.jwt_token = jwt_token or os.getenv('RC_USER_JWT')

        if not all([self.client_id, self.client_secret, self.phone_number, self.jwt_token]):
            raise ValueError("Missing RingCentral credentials. Need RC_APP_CLIENT_ID, RC_APP_CLIENT_SECRET, RC_PHONE_NUMBER, and RC_USER_JWT")

        self.sdk = SDK(self.client_id, self.client_secret, self.server)
        self.platform = self.sdk.platform()
        print("✓ RingCentral SMS client initialized")

    def login(self):
        """Login to RingCentral using JWT"""
        try:
            self.platform.login(jwt=self.jwt_token)
            print("✓ RingCentral JWT authentication successful")
        except Exception as e:
            print(f"✗ RingCentral JWT authentication failed: {e}")
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

    def normalize_phone(self, phone: str) -> str:
        """Normalize phone number to E.164 format (+1XXXXXXXXXX)"""
        digits = ''.join(filter(str.isdigit, phone))
        if len(digits) == 10:
            return f'+1{digits}'
        elif len(digits) == 11 and digits.startswith('1'):
            return f'+{digits}'
        else:
            return phone

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

    def normalize_phone(self, phone: str) -> str:
        """Normalize phone number to E.164 format (+1XXXXXXXXXX)"""
        digits = ''.join(filter(str.isdigit, phone))
        if len(digits) == 10:
            return f'+1{digits}'
        elif len(digits) == 11 and digits.startswith('1'):
            return f'+{digits}'
        else:
            return phone

    def is_us_phone(self, phone: str) -> bool:
        """Check if phone is US or Canada"""
        return phone.startswith('+1')
