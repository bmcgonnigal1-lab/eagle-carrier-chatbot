#!/usr/bin/env python
"""
Setup RingCentral Webhook for SMS
Run this once to subscribe to incoming SMS events
"""

from ringcentral import SDK
import os

# Initialize RingCentral SDK
client_id = os.getenv('RC_APP_CLIENT_ID')
client_secret = os.getenv('RC_APP_CLIENT_SECRET')
server = os.getenv('RC_SERVER_URL', 'https://platform.ringcentral.com')
jwt_token = os.getenv('RC_USER_JWT')

sdk = SDK(client_id, client_secret, server)
platform = sdk.platform()

# Login with JWT
try:
    platform.login(jwt=jwt_token)
    print("✓ Authenticated to RingCentral")
except Exception as e:
    print(f"✗ Authentication failed: {e}")
    exit(1)

# Create webhook subscription
webhook_url = "https://eagle-carrier-chatbot.onrender.com/webhook/ringcentral"

try:
    response = platform.post('/restapi/v1.0/subscription', {
        'eventFilters': [
            '/restapi/v1.0/account/~/extension/~/message-store/instant?type=SMS'
        ],
        'deliveryMode': {
            'transportType': 'WebHook',
            'address': webhook_url
        }
    })

    subscription = response.json()
    print(f"✓ Webhook created successfully!")
    print(f"  Subscription ID: {subscription['id']}")
    print(f"  Status: {subscription['status']}")
    print(f"  Webhook URL: {webhook_url}")
    print(f"\n✅ RingCentral will now forward SMS to your bot!")

except Exception as e:
    print(f"✗ Failed to create webhook: {e}")
    exit(1)
