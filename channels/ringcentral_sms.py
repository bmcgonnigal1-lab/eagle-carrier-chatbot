RingCentral SMS Channel
Handles sending and receiving SMS via RingCentral API
"""

from ringcentral import SDK
import os


class RingCentralSMSChannel:
    """RingCentral SMS integration"""

    def __init__(self, client_id=None, client_secret=None, server=None, phone_number=None):
        """
        Initialize RingCentral SMS

        Args:
            client_id: RingCentral Client ID
            client_secret: RingCentral Client Secret
            server: API server URL (default: https://platform.ringcentral.com)
            phone_number: Your RingCentral phone number
        """
        # Get from environment variables if not provided
        self.client_id = client_id or os.getenv('RC_CLIENT_ID')
        self.client_secret = client_secret or os.getenv('RC_CLIENT_SECRET')
        self.server = server or os.getenv('RC_SERVER_URL', 'https://platform.ringcentral.com')
        self.phone_number = phone_number or os.getenv('RC_PHONE_NUMBER')

        if not all([self.client_id, self.client_secret, self.phone_number]):
            raise ValueError("Missing RingCentral credentials. Set RC_CLIENT_ID, RC_CLIENT_SECRET, and RC_PHONE_NUMBER")

        # Initialize SDK
        self.sdk = SDK(self.client_id, self.client_secret, self.server)
        self.platform = self.sdk.platform()

        # Authenticate using JWT (will need username/password for first-time setup)
        # For production, you'll need to get a JWT token or use password auth
        print("✓ RingCentral SMS client initialized")

    def login(self, username=None, extension=None, password=None):
        """
        Login to RingCentral (required before sending messages)

        Args:
            username: RingCentral phone number or username
            extension: Extension number (optional)
            password: Account password
        """
        username = username or os.getenv('RC_USERNAME')
        password = password or os.getenv('RC_PASSWORD')
        extension = extension or os.getenv('RC_EXTENSION', '')

        if not username or not password:
            raise ValueError("Missing RC_USERNAME or RC_PASSWORD environment variables")

        try:
            self.platform.login(username, extension, password)
            print("✓ RingCentral authentication successful")
        except Exception as e:
            print(f"✗ RingCentral authentication failed: {e}")
            raise

    def send_sms(self, to_phone: str, message: str) -> bool:
        """
        Send SMS via RingCentral

        Args:
            to_phone: Recipient phone number in E.164 format
            message: Message text

        Returns:
            True if sent successfully
        """
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
        """Check if phone number is US/Canada (+1)"""
        return phone.startswith('+1')


class MockRingCentralSMSChannel:
    """Mock RingCentral SMS for testing"""

    def __init__(self, *args, **kwargs):
        print("✓ Using mock RingCentral SMS (test mode)")

    def login(self, *args, **kwargs):
        print("✓ Mock RingCentral login successful")

    def send_sms(self, to_phone: str, message: str) -> bool:
        """Simulate sending SMS"""
        print(f"\n📱 [MOCK SMS to {to_phone}]")
        print(f"Message: {message}\n")
        return True

    def is_us_phone(self, phone: str) -> bool:
        """Check if phone number is US/Canada (+1)"""
        return phone.startswith('+1')
