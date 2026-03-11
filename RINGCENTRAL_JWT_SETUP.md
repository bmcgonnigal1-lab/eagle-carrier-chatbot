# RingCentral JWT Setup Guide - READY FOR TOMORROW

## ✅ What's Already Done

1. ✅ RingCentral app created
2. ✅ App configured for JWT authentication
3. ✅ Updated Python code ready (`ringcentral_sms_jwt.py`)
4. ✅ RingCentral SDK installed in requirements.txt

## 🚀 Tomorrow's Steps (15 minutes max)

### Step 1: Get Your JWT Token (5 minutes)

1. Go to https://developers.ringcentral.com/
2. Click **"Login"** (top right)
3. Click **"Console"** or **"My Apps"**
4. Click on **"Eagle Carrier Chatbot"**
5. Look for **"Credentials"** or **"JWT"** tab
6. Click **"Create JWT"** or **"Generate JWT Token"**
7. **Copy the JWT token** (long string starting with `eyJ...`)

**IMPORTANT:** Save this token somewhere safe - you'll only see it once!

### Step 2: Update Environment Variables on Render (5 minutes)

**Remove these old variables:**
- ❌ `RC_USERNAME`
- ❌ `RC_PASSWORD`
- ❌ `RC_EXTENSION`

**Update these variables:**

| Key | Value |
|-----|-------|
| `USE_RINGCENTRAL` | `true` |
| `RC_APP_CLIENT_ID` | `AIvZF95FgGBcfsw6gy3mCa` |
| `RC_APP_CLIENT_SECRET` | `6LBwacHQYyvenxVI7KP3O0bTR7O56xaqof8EybVtT1MO` |
| `RC_SERVER_URL` | `https://platform.ringcentral.com` |
| `RC_PHONE_NUMBER` | `+17702093631` |
| `RC_USER_JWT` | `[Your JWT token from Step 1]` |

**Note:** The variable names changed from `RC_CLIENT_ID` to `RC_APP_CLIENT_ID` (adds `_APP_`) to match RingCentral's standard naming.

### Step 3: Update Code on GitHub (5 minutes)

1. **Delete old file:**
   - Go to `channels/ringcentral_sms.py` on GitHub
   - Delete it (trash icon)

2. **Upload new file:**
   - The new file is: `channels/ringcentral_sms_jwt.py`
   - **Rename it to:** `ringcentral_sms.py` when uploading
   - Or edit `app/main.py` to import from `ringcentral_sms_jwt` instead

3. **Commit and deploy**

### Step 4: Test (2 minutes)

1. Check Render logs for:
```
✓ RingCentral SMS client initialized
✓ RingCentral JWT authentication successful
✓ Connected to loads database: static/loads.db
```

2. Send test SMS to `+17702093631` from your phone:
```
van from GA to FL
```

3. **You should receive SMS reply with real Aljex loads!** 🎉

---

## 📋 Quick Checklist

- [ ] Get JWT token from RingCentral console
- [ ] Update Render environment variables
- [ ] Remove old ringcentral_sms.py
- [ ] Upload ringcentral_sms_jwt.py (rename to ringcentral_sms.py)
- [ ] Deploy and check logs
- [ ] Test SMS end-to-end

---

## 🔧 Troubleshooting

**If you see "Missing RingCentral credentials":**
- Check that all 6 environment variables are set correctly
- Make sure `RC_USER_JWT` has your JWT token

**If you see "JWT authentication failed":**
- JWT token might be expired (they expire after a period)
- Generate a new JWT token from RingCentral console
- Update `RC_USER_JWT` environment variable

**If you see "Unauthorized for this grant type":**
- Make sure your RingCentral app is configured for JWT (not OAuth)
- Check that you're using the correct app credentials

---

## 📚 References

- [RingCentral JWT Quick Start](https://developers.ringcentral.com/guide/authentication/jwt/quick-start)
- [Creating JWT Credentials](https://developers.ringcentral.com/guide/getting-started/create-credential)
- [JWT Authentication Flow](https://developers.ringcentral.com/guide/authentication/jwt-flow)

---

## 🎯 Expected Result

**After completing these steps, your bot will:**
- ✅ Receive SMS from carriers
- ✅ Respond with 51 real Aljex loads
- ✅ Send SMS via RingCentral (no A2P wait!)
- ✅ Full end-to-end SMS working

**Total time: ~15 minutes**
