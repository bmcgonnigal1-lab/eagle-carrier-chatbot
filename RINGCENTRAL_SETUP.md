# RingCentral SMS Setup Guide

## What You Have

✅ RingCentral app created
✅ Client ID: `AIvZF95FgGBcfsw6gy3mCa`
✅ Client Secret: `6LBwacHQYyvenxVI7KP3O0bTR7O56xaqof8EybVtT1MO`
✅ Phone Number: `+17702093631`
✅ API Server: `https://platform.ringcentral.com`

## Environment Variables for Render

Add these to your Render environment variables:

```
USE_RINGCENTRAL=true
RC_CLIENT_ID=AIvZF95FgGBcfsw6gy3mCa
RC_CLIENT_SECRET=6LBwacHQYyvenxVI7KP3O0bTR7O56xaqof8EybVtT1MO
RC_SERVER_URL=https://platform.ringcentral.com
RC_PHONE_NUMBER=+17702093631
RC_USERNAME=[Your RingCentral main phone number, e.g., +17702093631]
RC_PASSWORD=[Your RingCentral account password]
RC_EXTENSION=[Leave empty if main line, or extension number]
```

## Local Testing (config.py)

```python
# RingCentral SMS
USE_RINGCENTRAL = True
RC_CLIENT_ID = 'AIvZF95FgGBcfsw6gy3mCa'
RC_CLIENT_SECRET = '6LBwacHQYyvenxVI7KP3O0bTR7O56xaqof8EybVtT1MO'
RC_SERVER_URL = 'https://platform.ringcentral.com'
RC_PHONE_NUMBER = '+17702093631'
RC_USERNAME = '+17702093631'  # Your main RingCentral number
RC_PASSWORD = 'your-password-here'
RC_EXTENSION = ''  # Leave empty for main line
```

## Setting Up Webhooks (Receive SMS)

1. Go to RingCentral Developer Console
2. Click on your app
3. Add webhook subscription:
   - Event: **SMS Received**
   - Webhook URL: `https://eagle-carrier-chatbot.onrender.com/webhook/ringcentral`

## Benefits Over Twilio

✅ **Faster A2P Registration** (1-2 days vs 1-2 weeks)
✅ **Voice Support** (future: carriers can call dispatch)
✅ **You Already Have It** (no new number needed)
✅ **Similar Pricing** (~$0.007 per SMS)

## Next Steps

1. Add environment variables to Render
2. Deploy updated code
3. Set up webhook in RingCentral console
4. Test with a carrier!
