"""
Configuration for Eagle Carrier Chatbot
Copy this file to config.py and fill in your API keys
"""

# =============================================================================
# TESTING MODE (Start here!)
# =============================================================================
# Set these to True to test without API keys
USE_MOCK_SMS = True      # True = Test without Twilio, False = Use real Twilio
USE_MOCK_EMAIL = True    # True = Test without M365, False = Use real email (Phase 2)
USE_MOCK_SHEETS = True   # True = Use sample data, False = Use Google Sheets

# =============================================================================
# DATABASE
# =============================================================================
DATABASE_PATH = 'data/carriers.db'

# =============================================================================
# OPENAI (Optional for Phase 1)
# =============================================================================
# Get API key from: https://platform.openai.com/api-keys
# Cost: ~$20/month for 1,000 conversations
OPENAI_API_KEY = ''  # Leave empty to use regex parsing (works fine!)

# =============================================================================
# TWILIO SMS (Required for real SMS)
# =============================================================================
# Get credentials from: https://console.twilio.com
# Cost: $1/month for phone number + ~$0.0079 per SMS

# Your Twilio Account SID (starts with AC...)
TWILIO_ACCOUNT_SID = ''

# Your Twilio Auth Token
TWILIO_AUTH_TOKEN = ''

# Your Twilio phone number (format: +17709651242)
TWILIO_PHONE_NUMBER = ''

# =============================================================================
# GOOGLE SHEETS (Required for load data)
# =============================================================================
# 1. Create a Google Cloud project: https://console.cloud.google.com
# 2. Enable Google Sheets API
# 3. Create Service Account and download JSON credentials
# 4. Share your Google Sheet with the service account email

# Path to your service account JSON file
GOOGLE_CREDENTIALS_PATH = 'config/google-service-account.json'

# Your Google Sheet URL
GOOGLE_SHEET_URL = ''

# =============================================================================
# EAGLE BRANDING
# =============================================================================
COMPANY_NAME = 'Eagle Transportation Services, Inc.'
COMPANY_SHORT_NAME = 'Eagle'
DISPATCH_PHONE = '770-965-1242'
DISPATCH_EMAIL = 'dispatch@eagletransportation.com'

# =============================================================================
# MICROSOFT 365 (Phase 2 - Email & Excel)
# =============================================================================
# Get these from Azure Portal: https://portal.azure.com
# See PHASE2_GUIDE.md for detailed setup instructions

# Azure Active Directory (Tenant) ID
MS_TENANT_ID = ''

# Azure App Registration (Client) ID
MS_CLIENT_ID = ''

# Azure App Registration Client Secret
MS_CLIENT_SECRET = ''

# Your dispatch email address (must be in your M365 tenant)
DISPATCH_EMAIL = 'dispatch@eagletrans.com'

# User email who owns the Excel file on OneDrive
USER_EMAIL = 'bruce@eagletrans.com'

# Path to Excel file on OneDrive (e.g., /Loads/ActiveLoads.xlsx)
EXCEL_FILE_PATH = '/Loads/ActiveLoads.xlsx'

# =============================================================================
# SECURITY
# =============================================================================
# Block international carriers (fraud protection)
ALLOW_INTERNATIONAL = False

# Rate limiting (max messages per hour per carrier)
MAX_MESSAGES_PER_HOUR = 20
