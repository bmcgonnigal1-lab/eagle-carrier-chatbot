# Eagle Carrier Chatbot - Setup Guide

## Phase 1: Quick Test (15 minutes)

Get the chatbot working with sample data - NO API keys needed!

### Step 1: Install Python (if needed)

**Mac:**
```bash
# Check if Python is installed
python3 --version

# If not installed, download from python.org
# Or install via Homebrew:
brew install python3
```

**Windows:**
- Download from python.org
- Make sure to check "Add Python to PATH" during installation

### Step 2: Install Dependencies

Open Terminal (Mac) or Command Prompt (Windows):

```bash
# Navigate to the chatbot folder
cd ~/Downloads/eagle-carrier-chatbot

# Install required packages
pip3 install -r requirements.txt
```

### Step 3: Run Test

```bash
# Run the test
python3 app/main.py
```

You should see:
```
🦅 Initializing Eagle Carrier Chatbot...
✓ Database initialized
✓ Using mock SMS (no Twilio connection)
✓ Using mock data (no Google Sheets connection)
✅ Eagle Carrier Chatbot initialized!

TESTING EAGLE CARRIER CHATBOT
...
```

**Congratulations! The chatbot is working!** 🎉

---

## Phase 2: Add Real SMS (Twilio)

### Step 1: Create Twilio Account

1. Go to https://www.twilio.com/try-twilio
2. Sign up (free trial gives you $15 credit)
3. Verify your phone number

### Step 2: Get Phone Number

1. In Twilio Console, go to Phone Numbers → Buy a Number
2. Choose SMS-enabled number ($1/month)
3. Note your phone number (e.g., +17709651242)

### Step 3: Get Credentials

1. In Twilio Console, find:
   - **Account SID** (starts with AC...)
   - **Auth Token** (click to reveal)
2. Save these - you'll need them next

### Step 4: Configure Chatbot

1. Copy `config.example.py` to `config.py`:
   ```bash
   cp config.example.py config.py
   ```

2. Edit `config.py` and fill in:
   ```python
   USE_MOCK_SMS = False  # Use real Twilio now

   TWILIO_ACCOUNT_SID = 'AC...'  # Your Account SID
   TWILIO_AUTH_TOKEN = '...'     # Your Auth Token
   TWILIO_PHONE_NUMBER = '+17709651242'  # Your Twilio number
   ```

### Step 5: Test Real SMS

```bash
# Send test SMS
python3 scripts/test_sms.py
```

---

## Phase 3: Add Google Sheets (Load Data)

### Step 1: Create Google Sheet

1. Copy this template: [Template Link]
2. Rename: "Eagle - Available Loads"
3. Add your loads (or use sample data for testing)

### Step 2: Set Up Google Cloud

1. Go to https://console.cloud.google.com
2. Create new project: "Eagle Chatbot"
3. Enable Google Sheets API:
   - APIs & Services → Library
   - Search "Google Sheets API"
   - Click Enable

### Step 3: Create Service Account

1. APIs & Services → Credentials
2. Create Credentials → Service Account
3. Name: "eagle-chatbot"
4. Create and Continue
5. Skip optional steps
6. Click on the service account email
7. Keys → Add Key → Create New Key → JSON
8. Download the JSON file
9. Move it to: `config/google-service-account.json`

### Step 4: Share Sheet with Service Account

1. Open the JSON file
2. Find `client_email` (looks like: eagle-chatbot@PROJECT.iam.gserviceaccount.com)
3. Go to your Google Sheet
4. Click Share
5. Paste the service account email
6. Set permission: Viewer
7. Share

### Step 5: Configure Chatbot

Edit `config.py`:
```python
USE_MOCK_SHEETS = False  # Use real Google Sheets now

GOOGLE_CREDENTIALS_PATH = 'config/google-service-account.json'
GOOGLE_SHEET_URL = 'https://docs.google.com/spreadsheets/d/YOUR_SHEET_ID/edit'
```

### Step 6: Test

```bash
python3 scripts/test_sheets.py
```

---

## Phase 4: Add OpenAI (Better AI, Optional)

### Step 1: Get API Key

1. Go to https://platform.openai.com/api-keys
2. Create account / Sign in
3. Create new API key
4. Copy the key (starts with sk-...)

### Step 2: Configure

Edit `config.py`:
```python
OPENAI_API_KEY = 'sk-...'
```

**Note:** Chatbot works WITHOUT OpenAI (uses regex parsing). OpenAI makes it smarter but costs ~$20/month.

---

## Phase 5: Deploy Web Server (for Twilio Webhooks)

Coming in next version! For now, test locally with scripts.

---

## Troubleshooting

### "Module not found" error
```bash
pip3 install -r requirements.txt
```

### "Permission denied" error
```bash
chmod +x scripts/*.py
```

### Twilio SMS not sending
- Check Account SID and Auth Token are correct
- Check phone number format: +17709651242 (with +1)
- Check you have credit in Twilio account

### Google Sheets not connecting
- Check service account JSON path is correct
- Check you shared sheet with service account email
- Check sheet URL is correct

---

## Support

Questions? Issues?

1. Check the troubleshooting section above
2. Review the code comments
3. Contact: [Your support email]

---

**Built for Eagle Transportation Services, Inc.**
Dispatch: 770-965-1242
