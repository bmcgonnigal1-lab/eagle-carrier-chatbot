"""
Email Channel for Eagle Carrier Chatbot
Handles Microsoft Graph API integration for email communication
"""

import os
import re
from typing import Dict, List, Optional
from datetime import datetime
import json

# Microsoft Graph API
try:
    from msal import ConfidentialClientApplication
    import requests
    MSAL_AVAILABLE = True
except ImportError:
    MSAL_AVAILABLE = False
    print("⚠ msal not installed - email features will use mock mode")


class EmailChannel:
    def __init__(self, tenant_id: str = None, client_id: str = None,
                 client_secret: str = None, dispatch_email: str = None):
        """
        Initialize Microsoft Graph API email channel

        Args:
            tenant_id: Microsoft 365 Tenant ID
            client_id: Azure App Registration Client ID
            client_secret: Azure App Registration Client Secret
            dispatch_email: Your dispatch email (e.g., dispatch@eagletrans.com)
        """
        self.tenant_id = tenant_id or os.getenv('MS_TENANT_ID')
        self.client_id = client_id or os.getenv('MS_CLIENT_ID')
        self.client_secret = client_secret or os.getenv('MS_CLIENT_SECRET')
        self.dispatch_email = dispatch_email or os.getenv('DISPATCH_EMAIL', 'dispatch@eagletrans.com')

        self.client = None
        self.token = None

        if MSAL_AVAILABLE and self.tenant_id and self.client_id and self.client_secret:
            authority = f"https://login.microsoftonline.com/{self.tenant_id}"
            self.client = ConfidentialClientApplication(
                self.client_id,
                authority=authority,
                client_credential=self.client_secret
            )
            self._get_token()
            print("✓ Microsoft Graph API client initialized")
        else:
            print("✓ Using mock email (no Microsoft 365 connection)")

    def _get_token(self):
        """Get access token from Microsoft Graph API"""
        if not self.client:
            return None

        result = self.client.acquire_token_for_client(
            scopes=["https://graph.microsoft.com/.default"]
        )

        if "access_token" in result:
            self.token = result["access_token"]
            return self.token
        else:
            print(f"✗ Failed to get token: {result.get('error_description')}")
            return None

    def normalize_email(self, email: str) -> str:
        """
        Normalize email address

        Args:
            email: Email in any format

        Returns:
            Normalized lowercase email
        """
        return email.strip().lower()

    def is_valid_email(self, email: str) -> bool:
        """Check if email address is valid"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))

    def send_email(self, to_email: str, subject: str, body: str,
                   body_type: str = "HTML") -> bool:
        """
        Send email to carrier

        Args:
            to_email: Carrier email address
            subject: Email subject
            body: Email body (HTML or plain text)
            body_type: "HTML" or "Text"

        Returns:
            True if sent successfully
        """
        if not self.token:
            print(f"\n[Mock Email to {to_email}]")
            print(f"Subject: {subject}")
            print(f"Body:\n{body}")
            print("="*50)
            return True

        try:
            headers = {
                'Authorization': f'Bearer {self.token}',
                'Content-Type': 'application/json'
            }

            message = {
                "message": {
                    "subject": subject,
                    "body": {
                        "contentType": body_type,
                        "content": body
                    },
                    "toRecipients": [
                        {
                            "emailAddress": {
                                "address": to_email
                            }
                        }
                    ]
                },
                "saveToSentItems": "true"
            }

            url = f"https://graph.microsoft.com/v1.0/users/{self.dispatch_email}/sendMail"
            response = requests.post(url, headers=headers, json=message)

            if response.status_code == 202:
                print(f"✓ Email sent to {to_email}")
                return True
            else:
                print(f"✗ Failed to send email: {response.status_code} - {response.text}")
                return False

        except Exception as e:
            print(f"✗ Failed to send email to {to_email}: {e}")
            return False

    def get_recent_emails(self, max_count: int = 10,
                         unread_only: bool = False) -> List[Dict]:
        """
        Get recent emails from inbox

        Args:
            max_count: Maximum number of emails to retrieve
            unread_only: Only get unread emails

        Returns:
            List of email dictionaries
        """
        if not self.token:
            # Return mock data
            return [
                {
                    'id': 'mock_1',
                    'from_email': 'carrier@example.com',
                    'from_name': 'John Carrier',
                    'subject': 'RE: Atlanta loads',
                    'body': 'I can take ATL to DAL on the 15th',
                    'received_time': datetime.now().isoformat(),
                    'is_read': False
                }
            ]

        try:
            headers = {
                'Authorization': f'Bearer {self.token}',
                'Content-Type': 'application/json'
            }

            filter_query = "$filter=isRead eq false" if unread_only else ""
            url = f"https://graph.microsoft.com/v1.0/users/{self.dispatch_email}/messages?$top={max_count}&{filter_query}&$orderby=receivedDateTime desc"

            response = requests.get(url, headers=headers)

            if response.status_code == 200:
                data = response.json()
                emails = []

                for msg in data.get('value', []):
                    from_addr = msg.get('from', {}).get('emailAddress', {})

                    emails.append({
                        'id': msg.get('id'),
                        'from_email': from_addr.get('address', ''),
                        'from_name': from_addr.get('name', ''),
                        'subject': msg.get('subject', ''),
                        'body': msg.get('body', {}).get('content', ''),
                        'received_time': msg.get('receivedDateTime', ''),
                        'is_read': msg.get('isRead', False)
                    })

                return emails
            else:
                print(f"✗ Failed to get emails: {response.status_code}")
                return []

        except Exception as e:
            print(f"✗ Failed to get emails: {e}")
            return []

    def mark_as_read(self, message_id: str) -> bool:
        """Mark email as read"""
        if not self.token:
            print(f"[Mock] Marked message {message_id} as read")
            return True

        try:
            headers = {
                'Authorization': f'Bearer {self.token}',
                'Content-Type': 'application/json'
            }

            url = f"https://graph.microsoft.com/v1.0/users/{self.dispatch_email}/messages/{message_id}"
            data = {"isRead": True}

            response = requests.patch(url, headers=headers, json=data)
            return response.status_code == 200

        except Exception as e:
            print(f"✗ Failed to mark as read: {e}")
            return False

    def parse_email_body(self, html_body: str) -> str:
        """
        Extract plain text from HTML email body

        Args:
            html_body: HTML email body

        Returns:
            Plain text content
        """
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', '', html_body)

        # Decode HTML entities
        text = text.replace('&nbsp;', ' ')
        text = text.replace('&amp;', '&')
        text = text.replace('&lt;', '<')
        text = text.replace('&gt;', '>')
        text = text.replace('&quot;', '"')

        # Clean up whitespace
        text = '\n'.join(line.strip() for line in text.split('\n') if line.strip())

        return text

    def format_load_list_email(self, loads: List[Dict], carrier_name: str = None) -> str:
        """
        Format loads as HTML email

        Args:
            loads: List of load dictionaries
            carrier_name: Carrier name for personalization

        Returns:
            HTML email body
        """
        greeting = f"Hi {carrier_name}," if carrier_name else "Hi,"

        html = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; }}
                .header {{ background-color: #003366; color: white; padding: 15px; }}
                .load {{ border: 1px solid #ddd; padding: 15px; margin: 10px 0; }}
                .load-header {{ font-size: 18px; font-weight: bold; color: #003366; }}
                .detail {{ margin: 5px 0; }}
                .rate {{ font-size: 20px; color: #009900; font-weight: bold; }}
                .footer {{ margin-top: 20px; font-size: 12px; color: #666; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h2>🦅 Eagle Transportation Services, Inc.</h2>
            </div>

            <p>{greeting}</p>
            <p>Here are the available loads that match your search:</p>
        """

        for i, load in enumerate(loads, 1):
            html += f"""
            <div class="load">
                <div class="load-header">Load #{i}: {load.get('origin', '')} → {load.get('destination', '')}</div>
                <div class="detail"><strong>Equipment:</strong> {load.get('equipment_type', 'Dry Van')}</div>
                <div class="detail"><strong>Pickup:</strong> {load.get('pickup_date', '')}</div>
                <div class="detail"><strong>Rate:</strong> <span class="rate">${load.get('rate', 0):,}</span></div>
                {f'<div class="detail"><strong>Notes:</strong> {load.get("notes", "")}</div>' if load.get('notes') else ''}
            </div>
            """

        html += f"""
            <p>Interested? Reply to this email or call/text dispatch at <strong>770-965-1242</strong></p>

            <div class="footer">
                <p>Eagle Transportation Services, Inc.<br>
                Dispatch: 770-965-1242<br>
                {self.dispatch_email}</p>
            </div>
        </body>
        </html>
        """

        return html


# For development/testing without Microsoft 365
class MockEmailChannel:
    """Mock email channel for testing without Microsoft Graph API"""

    def __init__(self):
        print("✓ Using mock email (no Microsoft 365 connection)")
        self.dispatch_email = "dispatch@eagletrans.com"

    def normalize_email(self, email):
        return email.strip().lower()

    def is_valid_email(self, email):
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))

    def send_email(self, to_email, subject, body, body_type="HTML"):
        print(f"\n{'='*60}")
        print(f"MOCK EMAIL TO: {to_email}")
        print(f"SUBJECT: {subject}")
        print(f"{'='*60}")
        print(body)
        print(f"{'='*60}\n")
        return True

    def get_recent_emails(self, max_count=10, unread_only=False):
        return [
            {
                'id': 'mock_1',
                'from_email': 'carrier@example.com',
                'from_name': 'John Carrier',
                'subject': 'RE: Atlanta loads',
                'body': 'I can take ATL to DAL on the 15th',
                'received_time': datetime.now().isoformat(),
                'is_read': False
            }
        ]

    def mark_as_read(self, message_id):
        print(f"[Mock] Marked message {message_id} as read")
        return True

    def parse_email_body(self, html_body):
        # Simple HTML tag removal
        text = re.sub(r'<[^>]+>', '', html_body)
        return text.strip()

    def format_load_list_email(self, loads, carrier_name=None):
        greeting = f"Hi {carrier_name}," if carrier_name else "Hi,"

        html = f"<h2>Eagle Transportation Services, Inc.</h2>\n"
        html += f"<p>{greeting}</p>\n"
        html += f"<p>Here are the available loads:</p>\n\n"

        for i, load in enumerate(loads, 1):
            html += f"<h3>Load #{i}: {load.get('origin', '')} → {load.get('destination', '')}</h3>\n"
            html += f"<p>Equipment: {load.get('equipment_type', 'Dry Van')}</p>\n"
            html += f"<p>Pickup: {load.get('pickup_date', '')}</p>\n"
            html += f"<p>Rate: ${load.get('rate', 0):,}</p>\n\n"

        html += f"<p>Interested? Call/text dispatch at 770-965-1242</p>\n"

        return html
