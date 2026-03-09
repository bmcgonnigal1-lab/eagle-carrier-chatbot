# 🚀 Deployment Guide - Eagle Carrier Chatbot Phase 2

## Quick Deploy Options

### Option 1: Railway (Recommended - Easiest)

**Why Railway?**
- ✅ Easiest deployment (one command)
- ✅ $5/month (includes everything)
- ✅ Auto SSL certificates
- ✅ Simple environment variables
- ✅ Automatic deploys from Git

**Steps:**

```bash
# 1. Install Railway CLI
npm install -g @railway/cli

# 2. Login
railway login

# 3. Initialize project
cd eagle-carrier-chatbot
railway init

# 4. Deploy
railway up

# 5. Add environment variables via dashboard
# Go to: railway.app/dashboard
# Click your project → Variables
# Add all from .env file

# 6. Get your URL
railway domain
```

**Done!** Your app is live at `https://yourapp.railway.app`

---

### Option 2: Heroku

**Why Heroku?**
- ✅ Established platform
- ✅ Good documentation
- ✅ $7/month (Eco dyno)
- ✅ Easy database add-ons

**Steps:**

```bash
# 1. Install Heroku CLI
# Mac: brew tap heroku/brew && brew install heroku
# Windows: Download from heroku.com

# 2. Login
heroku login

# 3. Create app
cd eagle-carrier-chatbot
heroku create eagle-carrier-bot

# 4. Set environment variables
heroku config:set USE_MOCK_SMS=false
heroku config:set USE_MOCK_EMAIL=false
heroku config:set MS_TENANT_ID=your-tenant-id
heroku config:set MS_CLIENT_ID=your-client-id
heroku config:set MS_CLIENT_SECRET=your-client-secret
# ... add all other variables

# 5. Deploy
git push heroku main

# 6. Open your app
heroku open
```

**Done!** Your app is live at `https://eagle-carrier-bot.herokuapp.com`

---

### Option 3: Docker (Any Platform)

**Why Docker?**
- ✅ Works anywhere (AWS, DigitalOcean, your own server)
- ✅ Full control
- ✅ Portable

**Steps:**

```bash
# 1. Build image
docker build -t eagle-carrier-bot .

# 2. Run locally to test
docker run -p 5000:5000 \
  -e MS_TENANT_ID=your-tenant-id \
  -e MS_CLIENT_ID=your-client-id \
  -e MS_CLIENT_SECRET=your-client-secret \
  eagle-carrier-bot

# 3. Test
open http://localhost:5000

# 4. Push to registry (if deploying to cloud)
docker tag eagle-carrier-bot your-registry/eagle-carrier-bot
docker push your-registry/eagle-carrier-bot
```

---

## Environment Variables Checklist

Make sure to set these in your deployment platform:

### Core Settings
- [ ] `USE_MOCK_SMS=false` (for production)
- [ ] `USE_MOCK_EMAIL=false` (for production)
- [ ] `USE_MOCK_SHEETS=true` (unless using real Google Sheets)

### Microsoft 365 (Required for Email/Excel)
- [ ] `MS_TENANT_ID`
- [ ] `MS_CLIENT_ID`
- [ ] `MS_CLIENT_SECRET`
- [ ] `DISPATCH_EMAIL`
- [ ] `USER_EMAIL`
- [ ] `EXCEL_FILE_PATH`

### Twilio (Required for SMS)
- [ ] `TWILIO_ACCOUNT_SID`
- [ ] `TWILIO_AUTH_TOKEN`
- [ ] `TWILIO_PHONE_NUMBER`

### Optional
- [ ] `OPENAI_API_KEY` (for better AI parsing)
- [ ] `PORT` (auto-set by Railway/Heroku)

---

## Post-Deployment Steps

### 1. Configure Twilio Webhook

1. Go to: https://console.twilio.com
2. Click on your phone number
3. Under "Messaging Configuration":
   - Webhook: `https://your-app-url.com/webhook/sms`
   - Method: POST
4. Save

**Test:** Send SMS to your Twilio number, should get response!

---

### 2. Test Email Processing

Send test email to your dispatch email:

```
To: dispatch@eagletrans.com
Subject: Test loads

Looking for Atlanta to Dallas loads
```

Then check: `https://your-app-url.com/admin/process-emails`

Should process and respond!

---

### 3. Access Dashboard

Open: `https://your-app-url.com`

You should see:
- Statistics dashboard
- Carrier list
- Analytics page

---

### 4. Set Up Automatic Email Processing (Optional)

**Railway:**
```bash
# Add cron job in Railway dashboard
# Cron: 0 * * * * (every hour)
# Command: curl https://your-app-url.com/admin/process-emails -X POST
```

**Heroku:**
```bash
# Add Scheduler add-on
heroku addons:create scheduler:standard

# Configure in dashboard:
# Task: curl https://your-app-url.com/admin/process-emails -X POST
# Frequency: Every hour
```

---

## Monitoring & Logs

### Railway
```bash
railway logs
```

### Heroku
```bash
heroku logs --tail
```

### Docker
```bash
docker logs -f container-id
```

---

## Database Backup

Your database is in `/data/carriers.db`

**Railway/Heroku:** Use their backup tools
**Docker:** Volume mount for persistence

**Manual backup:**
```bash
# Download from Railway
railway run "cat data/carriers.db" > backup.db

# Download from Heroku
heroku ps:exec
cat data/carriers.db > /tmp/backup.db
exit
heroku ps:copy /tmp/backup.db backup.db
```

---

## Scaling

### Current Setup
- 2 web workers (gunicorn)
- Handles ~100 simultaneous requests
- Good for 500-1000 carriers

### To Scale
**Railway/Heroku:**
- Increase dyno/instance size
- Add more workers in Procfile

**Docker:**
- Increase replicas
- Add load balancer

---

## Security Checklist

- [ ] Environment variables set (not in code)
- [ ] HTTPS enabled (auto on Railway/Heroku)
- [ ] Azure API permissions minimal (only what's needed)
- [ ] Database not publicly accessible
- [ ] Twilio webhook signature validation (future enhancement)
- [ ] Rate limiting enabled in config
- [ ] International SMS blocked

---

## Troubleshooting

### App Won't Start

**Check logs:**
```bash
railway logs  # or heroku logs
```

**Common issues:**
- Missing environment variable
- Python dependency failed to install
- Port binding error (check PORT env var)

**Fix:**
- Add missing variables
- Check requirements.txt
- Ensure PORT is set by platform

---

### SMS Not Working

**Check:**
1. Twilio webhook URL is correct
2. Webhook is POST method
3. App is running (check health: `/health`)
4. Logs show incoming request

**Test webhook manually:**
```bash
curl -X POST https://your-app-url.com/webhook/sms \
  -d "From=+14045551234" \
  -d "Body=Atlanta loads"
```

---

### Email Not Working

**Check:**
1. Azure permissions granted
2. Client secret not expired
3. Email address in M365 tenant
4. Token successfully generated

**Test token:**
```bash
railway run "python -c 'from channels.email import EmailChannel; e = EmailChannel(); print(e.token)'"
```

Should print long token, not `None`.

---

### Dashboard Shows 404

**Check:**
- Templates folder deployed (`/templates/*.html`)
- Flask routes loading correctly
- Check logs for errors

**Fix:**
```bash
# Ensure templates are included
git add templates/
git commit -m "Add templates"
git push heroku main  # or railway up
```

---

## Cost Optimization

### Free Tier Options
- Railway: $5/month (no free tier)
- Heroku: $7/month Eco dyno
- Fly.io: Free tier available
- Render: Free tier available

### Reduce Costs
- Turn off OpenAI (use regex parsing)
- Use Google Sheets instead of Excel (avoid M365 costs)
- Deploy to free tier platform

### Minimum Viable Setup
- Railway free trial
- Mock mode for everything
- Just use dashboard for demo
**Cost: $0 for 30 days**

---

## Production Checklist

Before going live with carriers:

- [ ] All environment variables set
- [ ] Twilio webhook configured
- [ ] Email processing tested
- [ ] Dashboard accessible
- [ ] Database persistent (not in container)
- [ ] Logs monitoring set up
- [ ] Backup strategy in place
- [ ] Error alerts configured
- [ ] Rate limiting tested
- [ ] Sent test SMS and got response
- [ ] Sent test email and got response
- [ ] Dashboard shows real data

**All checked?** You're ready for production! 🚀

---

## Next Steps After Deployment

1. **Test with real carriers**
   - Give number to 2-3 trusted carriers
   - Monitor dashboard
   - Check for issues

2. **Monitor for 1 week**
   - Check logs daily
   - Review dashboard metrics
   - Fix any issues

3. **Scale up**
   - Add more carriers
   - Promote widely
   - Build consulting offers

4. **Iterate**
   - Add requested features
   - Improve responses
   - Enhance intelligence

---

## Support

**Issues?**
- Check logs first
- Review PHASE2_GUIDE.md
- Test components individually
- Check environment variables

**Platform-Specific Help:**
- Railway: https://docs.railway.app
- Heroku: https://devcenter.heroku.com
- Docker: https://docs.docker.com
