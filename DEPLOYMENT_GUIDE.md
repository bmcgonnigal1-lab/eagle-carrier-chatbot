# 🚀 Production Deployment Guide

**Goal:** Deploy PostgreSQL database → Import FMCSA data → Import Aljex data → Deploy chatbot

---

## Step 1: Create PostgreSQL Database (5 minutes)

### Option A: Railway (Recommended)

1. Go to https://railway.app/
2. Sign up with GitHub
3. Click "New Project"
4. Click "Provision PostgreSQL"
5. Wait 30 seconds for database to spin up
6. Click on PostgreSQL service
7. Go to "Variables" tab
8. Copy `DATABASE_URL` (looks like `postgresql://postgres:password@...`)

**Cost:** $5/month

### Option B: Render

1. Go to https://render.com/
2. Sign up
3. Click "New +" → "PostgreSQL"
4. Name: `eagle-carrier-db`
5. Choose "Free" or "Starter ($7/mo)"
6. Click "Create Database"
7. Copy "External Database URL"

---

## Step 2: Configure Local Environment

Create `.env` file in project root:

```bash
# Production Database
DATABASE_URL=postgresql://user:password@host:port/database

# FMCSA API
FMCSA_API_KEY=your_fmcsa_api_key_here

# RingCentral SMS
RINGCENTRAL_CLIENT_ID=your_client_id
RINGCENTRAL_CLIENT_SECRET=your_client_secret
RINGCENTRAL_JWT_TOKEN=your_jwt_token
RINGCENTRAL_PHONE_NUMBER=+1234567890

# Aljex API
ALJEX_TENANT=your_tenant_name
ALJEX_USERNAME=your_username
ALJEX_PASSWORD=your_password

# Optional: OpenAI for AI features
OPENAI_API_KEY=sk-...
```

**Load environment:**
```bash
export $(cat .env | xargs)
```

---

## Step 3: Deploy Database Schema

```bash
# Install PostgreSQL adapter
pip install psycopg2-binary

# Run migration
./scripts/deploy_production_database.sh
```

**Expected output:**
```
🚀 EAGLE CARRIER CHATBOT - DATABASE DEPLOYMENT
================================================

✅ DATABASE_URL found
📦 Installing PostgreSQL adapter...
✅ PostgreSQL adapter installed

🔄 Running database migration...
📡 Connecting to PostgreSQL...
✅ Connected to PostgreSQL

📖 Loading schema from database.py...
✅ Found 14 tables and 15 indexes

🔨 Creating tables...
  ✅ 1/14: carriers
  ✅ 2/14: carrier_equipment
  ✅ 3/14: carrier_insurance
  ...
  ✅ 14/14: conversation_context

📇 Creating indexes...
  ✅ 1/15
  ...
  ✅ 15/15

🔍 Verifying schema...
✅ 14 tables created:
   • carriers
   • carrier_equipment
   • carrier_insurance
   • carrier_safety_scores
   • carrier_performance
   • carrier_lanes
   • carrier_documents
   • carrier_contacts
   • carrier_banking
   • carrier_rates
   • carrier_queries
   • booking_requests
   • carrier_profiles
   • conversation_context

================================================
✅ POSTGRESQL SCHEMA CREATED SUCCESSFULLY
================================================
```

---

## Step 4: Import FMCSA Data (Optional - Start Fresh)

If you want to pre-populate with verified carriers:

```bash
# Create import script
python3 scripts/import_fmcsa_carriers.py --mc-list mc_numbers.txt
```

**mc_numbers.txt format:**
```
MC123456
MC789012
MC456789
```

This will:
1. Verify each MC# with FMCSA API
2. Pull safety scores
3. Create carrier profile
4. Store in database

---

## Step 5: Import Aljex Data

### Option A: One-time CSV Import (Quick Start)

```bash
# Export loads from Aljex to CSV
# Then import:
python3 scripts/import_aljex_loads.py aljex_loads.csv
```

### Option B: API Integration (Recommended)

1. Get Aljex API credentials
2. Add to `.env`:
```bash
ALJEX_TENANT=your_tenant
ALJEX_USERNAME=your_user
ALJEX_PASSWORD=your_password
```

3. Run sync:
```bash
python3 scripts/sync_aljex_loads.py
```

This will:
- Pull all available loads
- Store in `loads` table
- Keep syncing every 15 minutes (optional background service)

---

## Step 6: Test Database Connection

```bash
python3 scripts/test_database.py
```

**Expected output:**
```
🧪 Testing PostgreSQL Connection...

✅ Connection successful
✅ Carriers table exists (0 records)
✅ Loads table exists (0 records)
✅ Helper methods working

Database is ready for production!
```

---

## Step 7: Deploy Application

### Option A: Railway

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login
railway login

# Link project
railway link

# Deploy
railway up
```

### Option B: Render

1. Go to https://render.com/
2. Click "New +" → "Web Service"
3. Connect GitHub repository
4. Name: `eagle-carrier-chatbot`
5. Build Command: `pip install -r requirements.txt`
6. Start Command: `gunicorn app.main:app`
7. Add environment variables (from `.env`)
8. Click "Create Web Service"

### Option C: AWS/DigitalOcean

```bash
# SSH to server
ssh user@your-server

# Clone repository
git clone https://github.com/yourusername/eagle-carrier-chatbot.git
cd eagle-carrier-chatbot

# Install dependencies
pip3 install -r requirements.txt

# Set environment variables
nano .env

# Run with systemd
sudo cp deploy/eagle-carrier.service /etc/systemd/system/
sudo systemctl enable eagle-carrier
sudo systemctl start eagle-carrier
```

---

## Verification Checklist

After deployment, verify:

- [ ] Database accessible via DATABASE_URL
- [ ] All 14 tables created
- [ ] All indexes created
- [ ] Can create test carrier
- [ ] Can retrieve test carrier
- [ ] FMCSA integration working (if configured)
- [ ] Aljex sync working (if configured)
- [ ] RingCentral SMS receiving messages
- [ ] Chatbot responding correctly

---

## Monitoring

### Database Health

```sql
-- Check table sizes
SELECT
    table_name,
    pg_size_pretty(pg_total_relation_size(quote_ident(table_name))) AS size
FROM information_schema.tables
WHERE table_schema = 'public'
ORDER BY pg_total_relation_size(quote_ident(table_name)) DESC;

-- Check carrier count
SELECT status, COUNT(*) FROM carriers GROUP BY status;

-- Check recent activity
SELECT DATE(created_at) as date, COUNT(*) as new_carriers
FROM carriers
WHERE created_at > NOW() - INTERVAL '7 days'
GROUP BY DATE(created_at)
ORDER BY date DESC;
```

### Application Logs

```bash
# Railway
railway logs

# Render
# View in web dashboard

# Manual server
tail -f /var/log/eagle-carrier/app.log
```

---

## Backup Strategy

### Automatic Backups (Railway/Render)

Both providers automatically backup PostgreSQL:
- **Railway:** Daily backups, 7-day retention
- **Render:** Daily backups, 7-day retention (paid plans)

### Manual Backup

```bash
# Backup to file
pg_dump $DATABASE_URL > backup_$(date +%Y%m%d).sql

# Restore from backup
psql $DATABASE_URL < backup_20260311.sql
```

### Scheduled Backups (Cron)

```bash
# Add to crontab
0 2 * * * pg_dump $DATABASE_URL > /backups/eagle_$(date +\%Y\%m\%d).sql
```

---

## Scaling

### When to Scale

**Current setup (SQLite → PostgreSQL):** Good for:
- 0-10,000 carriers
- 0-50,000 loads
- 0-100 concurrent users

**Scale up when:**
- Database size > 10 GB
- Query response time > 1 second
- Concurrent connections > 50

### Scaling Options

1. **Vertical Scaling (Easier)**
   - Railway: Upgrade plan ($20/mo → $50/mo)
   - Render: Upgrade plan ($7/mo → $20/mo → $50/mo)

2. **Read Replicas** (Advanced)
   - Add read-only replica for reporting
   - Keep primary for writes

3. **Connection Pooling** (Already implemented)
   - PgBouncer for connection management
   - Already using `psycopg2.pool` in code

---

## Troubleshooting

### "Connection refused"

```bash
# Check DATABASE_URL format
echo $DATABASE_URL

# Should look like:
# postgresql://user:password@host:port/database

# Test connection
psql $DATABASE_URL -c "SELECT 1"
```

### "Table already exists"

```bash
# Drop all tables and recreate
python3 scripts/reset_database.py --confirm

# Then run migration again
./scripts/deploy_production_database.sh
```

### "psycopg2 not found"

```bash
# Install PostgreSQL adapter
pip3 install psycopg2-binary

# Or on Ubuntu/Debian:
sudo apt-get install python3-psycopg2
```

### Slow Queries

```sql
-- Enable slow query logging
ALTER DATABASE your_database SET log_min_duration_statement = 1000;

-- Find slow queries
SELECT query, calls, mean_exec_time
FROM pg_stat_statements
ORDER BY mean_exec_time DESC
LIMIT 10;
```

---

## Environment-Specific Configurations

### Development

```bash
# Use SQLite locally
DATABASE_URL=sqlite:///data/carriers.db
```

### Staging

```bash
# Separate staging database
DATABASE_URL=postgresql://...staging.railway.app...
```

### Production

```bash
# Production database with backups
DATABASE_URL=postgresql://...production.railway.app...
```

---

## Cost Summary

**Minimal Setup:**
- Railway PostgreSQL: $5/month
- Railway App Hosting: $5/month
- **Total: $10/month**

**Recommended Setup:**
- Railway PostgreSQL (Starter): $20/month
- Railway App Hosting: $5/month
- FMCSA API: Free
- Aljex API: Included in TMS
- **Total: $25/month**

**Enterprise Setup:**
- AWS RDS PostgreSQL: $30/month
- AWS EC2 (app): $20/month
- Load Balancer: $20/month
- CloudFlare (CDN): $20/month
- **Total: $90/month**

---

## Next Steps After Deployment

1. **Import Initial Data**
   - Add 5-10 test carriers manually
   - Import Aljex loads
   - Verify FMCSA integration

2. **Test SMS Flow**
   - Text RingCentral number
   - Verify bot responds
   - Test MC# verification
   - Test booking flow

3. **Monitor for 48 Hours**
   - Check logs for errors
   - Verify database connections
   - Monitor response times

4. **Onboard Real Carriers**
   - Start with 2-3 friendly carriers
   - Collect feedback
   - Iterate on responses

5. **Build Dashboard UI**
   - See what brokers need to see
   - Approve bookings
   - View analytics

---

## Quick Start Commands

```bash
# Full deployment from scratch
export DATABASE_URL='postgresql://...'
./scripts/deploy_production_database.sh
python3 scripts/sync_aljex_loads.py
railway up

# Verify everything works
python3 scripts/test_database.py
python3 app/main.py  # Test locally

# Monitor
railway logs --tail
```

---

## Support

**Issues?**
- Check logs: `railway logs`
- Verify DATABASE_URL is set
- Test connection: `psql $DATABASE_URL`
- Review error messages

**Database questions:**
- Railway support: https://railway.app/help
- PostgreSQL docs: https://www.postgresql.org/docs/
