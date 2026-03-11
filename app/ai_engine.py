"""
AI Conversation Engine for Eagle Carrier Chatbot
Handles natural language understanding and response generation
"""

import os
import json
import re
from typing import Dict, List, Optional, Tuple

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None  # Will fall back to regex parsing
from openai import OpenAI

class AIEngine:
    def __init__(self, api_key: str = None):
        """Initialize AI engine with OpenAI"""
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        if OpenAI and self.api_key:
            self.client = OpenAI(api_key=self.api_key)
        else:
            self.client = None
        self.client = OpenAI(api_key=self.api_key) if self.api_key else None

    def parse_carrier_request(self, message: str) -> Dict:
        """
        Parse carrier message to extract intent and parameters

        Returns:
            {
                'intent': 'search_loads' | 'book_load' | 'ask_question' | 'other',
                'origin': 'ATL',
                'destination': 'DAL',
                'equipment_type': 'Dry Van',
                'pickup_date': '2026-03-10',
                'load_id': 'L12345' (if booking),
                'confidence': 0.85
            }
        """
        if not self.client:
            # Fallback to regex if no OpenAI key
            return self._parse_with_regex(message)

        try:
            system_prompt = """You are an AI assistant for Eagle Transportation Services, a freight brokerage.
Parse carrier messages to extract their intent and search parameters.

Return JSON ONLY with this structure:
{
    "intent": "search_loads" or "book_load" or "ask_question",
    "origin": "city code like ATL, DAL" or null,
    "destination": "city code" or null,
    "equipment_type": "Dry Van" or "Reefer" or "Flatbed" or null,
    "pickup_date": "YYYY-MM-DD" or null,
    "load_id": "L12345" or null (if booking),
    "confidence": 0.0 to 1.0
}

Examples:
- "Atlanta loads" → {"intent": "search_loads", "origin": "ATL", ...}
- "Atlanta to Dallas dry van" → {"intent": "search_loads", "origin": "ATL", "destination": "DAL", "equipment_type": "Dry Van", ...}
- "Book L12345" → {"intent": "book_load", "load_id": "L12345", ...}
- "What are your hours?" → {"intent": "ask_question", ...}
"""

            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": message}
                ],
                temperature=0.3,
                max_tokens=200
            )

            result_text = response.choices[0].message.content.strip()

            # Extract JSON from response (handles markdown code blocks)
            json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', result_text, re.DOTALL)
            if json_match:
                result_text = json_match.group(1)

            parsed = json.loads(result_text)
            return parsed

        except Exception as e:
            print(f"AI parsing error: {e}")
            return self._parse_with_regex(message)

    def _parse_with_regex(self, message: str) -> Dict:
        """Fallback regex-based parsing"""
        message_upper = message.upper()
        result = {
            'intent': 'search_loads',
            'origin': None,
            'destination': None,
            'equipment_type': None,
            'pickup_date': None,
            'load_id': None,
            'confidence': 0.6
        }

        # Check for booking intent
        book_match = re.search(r'BOOK\s+([A-Z0-9]+)', message_upper)
        if book_match:
            result['intent'] = 'book_load'
            result['load_id'] = book_match.group(1)
            result['confidence'] = 0.9
            return result

        # Common city codes
        cities = {
            'ATLANTA': 'ATL', 'ATL': 'ATL',
            'DALLAS': 'DAL', 'DAL': 'DAL',
            'HOUSTON': 'HOU', 'HOU': 'HOU',
            'MIAMI': 'MIA', 'MIA': 'MIA',
            'CHICAGO': 'CHI', 'CHI': 'CHI',
            'LOS ANGELES': 'LAX', 'LA': 'LAX', 'LAX': 'LAX'
        }

        # Extract origin/destination
        for city_name, code in cities.items():
            if city_name in message_upper:
                if not result['origin']:
                    result['origin'] = code
                elif result['origin'] and result['origin'] != code:
                    result['destination'] = code

        # Check for "to" pattern (Atlanta to Dallas)
        to_match = re.search(r'(\w+)\s+TO\s+(\w+)', message_upper)
        if to_match:
            origin_word = to_match.group(1)
            dest_word = to_match.group(2)
            result['origin'] = cities.get(origin_word, origin_word[:3])
            result['destination'] = cities.get(dest_word, dest_word[:3])

        # Equipment types
        if 'DRY VAN' in message_upper or 'DRY' in message_upper:
            result['equipment_type'] = 'Dry Van'
        elif 'REEFER' in message_upper or 'REFRIGERATED' in message_upper:
            result['equipment_type'] = 'Reefer'
        elif 'FLATBED' in message_upper or 'FLAT' in message_upper:
            result['equipment_type'] = 'Flatbed'

        return result

    def generate_response(self, carrier_name: str, loads: List[Dict],
                         intent: str, channel: str = 'sms') -> str:
        """
        Generate conversational response

        Args:
            carrier_name: Carrier company name or "there" if unknown
            loads: List of matching loads
            intent: search_loads, book_load, etc.
            channel: 'sms' or 'email'
        """
        if intent == 'book_load':
            return self._generate_booking_response(carrier_name, channel)

        if not loads:
            return self._generate_no_results_response(carrier_name, channel)

        return self._generate_load_list_response(carrier_name, loads, channel)

    def _generate_load_list_response(self, carrier_name: str, loads: List[Dict],
                                     channel: str) -> str:
        """Generate load list response"""
        greeting = f"Hi {carrier_name}!" if carrier_name != "there" else "Eagle here! 👋"

        count = len(loads)
        plural = "loads" if count > 1 else "load"

        if channel == 'sms':
            # Short SMS format
            response = f"{greeting}\n\nI have {count} {plural}:\n\n"

            for i, load in enumerate(loads[:5], 1):  # Limit to 5 for SMS
                equipment = load.get('equipment_type', 'Unknown')
                length = load.get('trailer_length', '')
                length_str = f"{length}'" if length else ''

                special = load.get('special_instructions', '')
                special_line = f"\n   {special}" if special and special.lower() not in ['no special', 'none', ''] else ''

                response += f"""{i}. {load.get('load_id')} - {equipment} {length_str}
   {load.get('origin')} → {load.get('destination')}
   {load.get('pickup_date')}, ${load.get('rate', 0):,}{special_line}

"""

            if count > 5:
                response += f"\n+ {count - 5} more loads available\n"

            response += "\nReply with # to book or DETAILS for more info\n"
            response += "Questions? Call 770-965-1242"

        else:
            # Detailed email format
            response = f"{greeting}\n\nI found {count} {plural} matching your request:\n\n"

            for load in loads:
                response += f"""━━━━━━━━━━━━━━━━━━━━━
LOAD: {load.get('load_id')}
━━━━━━━━━━━━━━━━━━━━━
Origin: {load.get('origin')}
Destination: {load.get('destination')}
Equipment: {load.get('equipment_type')}, {load.get('trailer_length', 'N/A')}'
Pickup: {load.get('pickup_date')}
Rate: ${load.get('rate', 0):,}
Weight: {load.get('weight', 'N/A')} lbs
Commodity: {load.get('commodity', 'General Freight')}
Special Instructions: {load.get('special_instructions', 'None')}

"""

            response += """━━━━━━━━━━━━━━━━━━━━━

To book a load, reply with the load number (e.g., "L12345")
or call dispatch at 770-965-1242

---
Eagle Transportation Services, Inc.
Dispatch: 770-965-1242
"""

        return response

    def _generate_no_results_response(self, carrier_name: str, channel: str) -> str:
        """Generate no results response"""
        greeting = f"Hi {carrier_name}!" if carrier_name != "there" else "Eagle here!"

        if channel == 'sms':
            return f"""{greeting}

No loads matching your search right now.

Try:
• Different cities
• Different dates
• Call 770-965-1242 for more options"""
        else:
            return f"""{greeting}

I don't have any loads matching your search criteria at the moment.

Here are some options:
• Try different origin/destination cities
• Adjust your date range
• Contact dispatch directly at 770-965-1242

We get new loads daily, so check back soon!

---
Eagle Transportation Services, Inc.
Dispatch: 770-965-1242"""

    def _generate_booking_response(self, carrier_name: str, channel: str) -> str:
        """Generate booking confirmation response"""
        greeting = f"Thanks {carrier_name}!" if carrier_name != "there" else "Great!"

        if channel == 'sms':
            return f"""{greeting}

I've alerted dispatch about your booking request.

They'll call you at this number within 5 minutes to confirm.

Questions? Call 770-965-1242"""
        else:
            return f"""{greeting}

Your booking request has been received and forwarded to our dispatch team.

What happens next:
1. Dispatch will call you within 5 minutes
2. They'll confirm load details and rate
3. You'll receive rate confirmation via email

If you have any questions, call 770-965-1242

---
Eagle Transportation Services, Inc.
Dispatch: 770-965-1242"""
