# 🚀 Phase 2 Setup Guide - Eagle Carrier Chatbot

## What's New in Phase 2?

Phase 2 adds professional features that transform your chatbot into a complete carrier intelligence platform:

### ✨ New Features

1. **📧 Email Channel** - Two-way email conversations with carriers via Microsoft 365
2. **📊 Web Dashboard** - Real-time intelligence dashboard with carrier analytics
3. **🧠 Intelligence Engine** - Carrier scoring, lane analytics, and recommendations
4. **📈 Excel/OneDrive Integration** - Auto-sync loads from Excel files
5. **☁️ Cloud Deployment** - Deploy to Heroku, Railway, or any container platform

---

## 🎯 Quick Start Options

### Option 1: Test Everything Locally (15 minutes)
- No API keys needed
- See the dashboard and features working with mock data
- Perfect for demos and understanding the system

### Option 2: Production Setup (1-2 hours)
- Configure Microsoft 365 for email + Excel
- Deploy to Railway or Heroku
- Go live with real carriers

---

## 📋 Prerequisites

**What You Need:**
- ✅ Phase 1 working (SMS chatbot)
- ✅ Microsoft 365 account (for email/Excel features)
- ✅ Azure account (free tier is fine)

**What You'll Set Up:**
- Azure App Registration (5 minutes)
- Microsoft 365 API permissions (5 minutes)
- Web server deployment (15 minutes)

---

## 🔧 Step-by-Step Setup

### Step 1: Test Locally (No Setup Required!)

```bash
# Start the web dashboard
python3 app/web_server.py
```

Open browser to `http://localhost:5000`

You'll see:
- ✅ Dashboard with sample data
- ✅ Carrier intelligence analytics
- ✅ Hot lanes tracking
- ✅ Recent activity feed

**This works immediately with no configuration!**

---

### Step 2: Azure App Registration (For Email/Excel)

**Why:** Microsoft Graph API needs authentication to access your M365 account.

1. **Go to Azure Portal**
   - Visit: https://portal.azure.com
   - Sign in with your Microsoft 365 account

2. **Create App Registration**
   - Search for "App registrations"
   - Click "New registration"
   - Name: `Eagle Carrier Chatbot`
   - Supported account types: "Single tenant"
   - Click "Register"

3. **Note Your IDs**
   - Copy `Application (client) ID` → This is your `MS_CLIENT_ID`
   - Copy `Directory (tenant) ID` → This is your `MS_TENANT_ID`

4. **Create Client Secret**
   - Go to "Certificates & secrets"
   - Click "New client secret"
   - Description: "Eagle Chatbot Secret"
   - Expires: 24 months
   - Click "Add"
   - Copy the **Value** (not Secret ID!) → This is your `MS_CLIENT_SECRET`
   - ⚠️ Copy it NOW - you can't see it again!

5. **Add API Permissions**
   - Go to "API permissions"
   - Click "Add a permission"
   - Choose "Microsoft Graph"
   - Choose "Application permissions"
   - Add these permissions:
     - `Mail.ReadWrite` - Read/send email
     - `Mail.Send` - Send email
     - `Files.ReadWrite.All` - Access Excel files
     - `User.Read.All` - Read user info
   - Click "Grant admin consent for [Your Org]"

**Done!** You now have your three keys.

---

### Step 3: Configure Environment Variables

Create `.env` file in your project root:

```bash
# Copy the example file
cp .env.example .env

# Edit .env with your credentials
nano .env
```

**Add your Azure credentials:**

```ini
# Microsoft 365 (Email & Excel)
MS_TENANT_ID=your-tenant-id-here
MS_CLIENT_ID=your-client-id-here
MS_CLIENT_SECRET=your-client-secret-here
DISPATCH_EMAIL=dispatch@eagletrans.com
USER_EMAIL=bruce@eagletrans.com

# Excel/OneDrive
EXCEL_FILE_PATH=/Loads/ActiveLoads.xlsx

# Switch to production mode
USE_MOCK_EMAIL=false
# Keep SMS and Sheets in mock mode for now
USE_MOCK_SMS=true
USE_MOCK_SHEETS=true
```

**Save the file.**

---

### Step 4: Test Email Integration

```bash
# Test email sending
python3 -c "
from channels.email import EmailChannel
email = EmailChannel()
email.send_email(
    to_email='your-test@email.com',
    subject='Test from Eagle Bot',
    body='It works!'
)
"
```

You should receive a test email!

---

### Step 5: Set Up Excel File on OneDrive

1. **Create Excel File**
   - Open Excel (Office 365 version)
   - Create new workbook: `ActiveLoads.xlsx`
   - Create sheet named: `Loads`

2. **Add Column Headers** (First row):
   ```
   Load ID | Origin | Destination | Equipment Type | Trailer Length | Pickup Date | Rate | Notes
   ```

3. **Add Sample Loads:**
   ```
   L12345 | Atlanta, GA | Dallas, TX | Dry Van | 53 | 2024-03-15 | 2500 | ASAP pickup
   L12346 | Atlanta, GA | Miami, FL | Reefer | 53 | 2024-03-16 | 1800 | Temp controlled
   ```

4. **Save to OneDrive**
   - Save As → OneDrive
   - Save to: `/Loads/ActiveLoads.xlsx`

5. **Test Sync:**
   ```bash
   python3 -c "
   from integrations.excel_onedrive import ExcelOneDriveLoader
   loader = ExcelOneDriveLoader()
   loader.connect()
   loader.sync_loads()
   print(f'Synced {len(loader.get_all_loads())} loads')
   "
   ```

---

### Step 6: Deploy to Production

#### Option A: Deploy to Railway (Recommended - Easiest)

1. **Install Railway CLI**
   ```bash
   npm install -g @railway/cli
   railway login
   ```

2. **Create New Project**
   ```bash
   railway init
   railway up
   ```

3. **Add Environment Variables**
   ```bash
   # Go to Railway dashboard
   # Click on your project
   # Go to "Variables" tab
   # Add all variables from your .env file
   ```

4. **Deploy**
   ```bash
   railway up
   ```

Your app will be live at `https://yourapp.railway.app`

**Cost:** $5/month (includes database, hosting, SSL)

---

#### Option B: Deploy to Heroku

1. **Install Heroku CLI**
   ```bash
   brew install heroku/brew/heroku  # Mac
   # or download from heroku.com
   ```

2. **Login and Create App**
   ```bash
   heroku login
   heroku create eagle-carrier-bot
   ```

3. **Add Environment Variables**
   ```bash
   heroku config:set MS_TENANT_ID=your-tenant-id
   heroku config:set MS_CLIENT_ID=your-client-id
   heroku config:set MS_CLIENT_SECRET=your-client-secret
   # ... add all other variables
   ```

4. **Deploy**
   ```bash
   git push heroku main
   ```

Your app will be live at `https://eagle-carrier-bot.herokuapp.com`

**Cost:** $7/month (Eco dyno)

---

### Step 7: Configure Twilio Webhook (For SMS)

Once deployed, update your Twilio webhook:

1. Go to Twilio Console
2. Click on your phone number
3. Under "Messaging", set webhook to:
   ```
   https://your-app-url.com/webhook/sms
   ```
4. Method: `POST`
5. Save

**SMS messages will now trigger your cloud-deployed chatbot!**

---

### Step 8: Test Email Processing

You can manually process emails via the web dashboard:

1. Open: `https://your-app-url.com/admin/process-emails`
2. This checks inbox for new carrier emails
3. Processes them and sends responses

**Or schedule automatic processing:**

Add to your deployment platform:
- Cron job: `0 * * * *` (every hour)
- Command: `curl https://your-app-url.com/admin/process-emails -X POST`

---

## 📊 Using the Dashboard

### Main Dashboard (`/`)
- Overall statistics
- Top carriers by engagement
- Hot lanes (most searched)
- Recent activity feed

### Carriers Page (`/carriers`)
- Complete carrier list
- Engagement scores
- Contact information
- Booking history

### Analytics Page (`/analytics`)
- Daily activity trends
- Equipment type breakdown
- Geography analysis
- Lane patterns

### API Endpoints
- `GET /api/stats` - Overall statistics
- `POST /api/search` - Search loads programmatically
- `GET /api/carrier/:id` - Get carrier details

---

## 🧪 Testing Phase 2

### Test Email Conversations

1. **Send email to dispatch@eagletrans.com:**
   ```
   Subject: Atlanta loads

   Hi, looking for loads from Atlanta to Dallas.
   Prefer dry van, 53ft.

   Thanks,
   John Carrier
   ```

2. **Check your inbox** - You should get back:
   - HTML formatted email
   - List of matching loads
   - Eagle branding
   - Dispatch contact info

### Test Intelligence Tracking

1. Send multiple queries from the same email
2. Check dashboard at `/carriers`
3. You'll see:
   - Carrier profile auto-created
   - Query count incrementing
   - Preferred lanes tracked
   - Engagement score calculated

### Test Excel Sync

1. Add a new load to your Excel file
2. Wait 5 minutes (or force sync)
3. Query for that load via SMS/email
4. It should appear in results!

---

## 🔄 Data Flow Architecture

```
Carrier SMS/Email
      ↓
Web Server (Flask)
      ↓
AI Engine (Parse intent)
      ↓
Excel/Sheets Loader (Search loads)
      ↓
Intelligence Engine (Track patterns)
      ↓
Database (Log everything)
      ↓
Response via SMS/Email
```

---

## 💰 Phase 2 Costs

| Service | Cost | Purpose |
|---------|------|---------|
| Railway/Heroku | $5-7/mo | Web hosting |
| Twilio | $1/mo + usage | SMS (from Phase 1) |
| Microsoft 365 | $0 | Using your existing account |
| OpenAI | $0-20/mo | Optional AI parsing |
| **Total** | **$6-28/mo** | Full platform |

**Compare to buying Parade:** $2,000-4,000/month
**Your savings:** $1,972+/month = $23,664/year

---

## 🎓 Consulting IP Value

**What You Can Now Demo:**

1. ✅ Multi-channel communication (SMS + Email)
2. ✅ Carrier intelligence tracking
3. ✅ Automated load matching
4. ✅ Real-time analytics dashboard
5. ✅ Microsoft 365 integration
6. ✅ Cloud deployment
7. ✅ Carrier scoring algorithm

**Pitch to Other Brokers:**

> "I built an AI carrier chatbot that handles SMS and email, tracks carrier intelligence, and cost me $25/month instead of $2,000. Let me build one for your brokerage."

**Pricing Ideas:**
- Setup fee: $2,500 (one-time)
- Monthly management: $200/mo
- Their savings vs Parade: $1,800/mo
- Your profit: $2,700 first month, $200/mo after

**10 clients = $2,000/mo recurring revenue**

---

## 🐛 Troubleshooting

### Email Not Working?

**Check:**
1. ✅ Azure API permissions granted
2. ✅ Client secret not expired
3. ✅ `DISPATCH_EMAIL` set correctly
4. ✅ Email address is in your M365 tenant

**Test:**
```bash
python3 -c "from channels.email import EmailChannel; e = EmailChannel(); print(e.token)"
```

Should print a long token, not `None`.

### Excel Sync Failing?

**Check:**
1. ✅ File exists at exact path: `/Loads/ActiveLoads.xlsx`
2. ✅ Sheet is named exactly `Loads`
3. ✅ `USER_EMAIL` is the file owner
4. ✅ API permission `Files.ReadWrite.All` granted

### Dashboard Shows No Data?

**Normal!** You need to:
1. Send some test SMS/emails
2. Database will populate automatically
3. Refresh dashboard

**Or load test data:**
```bash
python3 scripts/generate_test_data.py
```

---

## 📚 Next Steps

**Phase 2 Complete!** You now have:
- ✅ Email + SMS channels
- ✅ Web dashboard
- ✅ Intelligence tracking
- ✅ Cloud deployment
- ✅ Excel integration

**Phase 3 Preview:**
- Proactive carrier alerts ("Hey, I have a load you might want")
- Predictive capacity modeling
- Automated carrier outreach
- Load board integration
- Mobile app for dispatch

**Want Phase 3?** Let me know!

---

## 🆘 Support

**Need help?**
- Check the logs: `railway logs` or `heroku logs --tail`
- Review ARCHITECTURE.md for system design
- Test components individually (see scripts folder)
- Reach out to me with specific error messages

**Common Issues:**
- Token errors → Check Azure permissions
- Database errors → Delete `data/carriers.db` and restart
- Import errors → Run `pip install -r requirements.txt`

---

## 🎉 Success Checklist

- [ ] Dashboard loads at `http://localhost:5000`
- [ ] Azure app registration created
- [ ] Email test successful
- [ ] Excel file syncing
- [ ] Deployed to Railway/Heroku
- [ ] Twilio webhook configured
- [ ] Received email reply from chatbot
- [ ] Dashboard shows real data

**All checked?** You're live with Phase 2! 🦅
