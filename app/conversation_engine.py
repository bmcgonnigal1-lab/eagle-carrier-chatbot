"""
Intelligent Conversation Engine for Phase 1: Load Discovery & Inquiry
Makes the bot feel like a real human freight broker
"""

import re
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import json


class ConversationState:
    """Track conversation context for a carrier"""

    WAITING_DESTINATION = 'waiting_destination'
    WAITING_EQUIPMENT = 'waiting_equipment'
    WAITING_MC_NUMBER = 'waiting_mc_number'
    ACTIVE = 'active'

    def __init__(self, carrier_id: int, db):
        self.carrier_id = carrier_id
        self.db = db
        self.state = self.ACTIVE
        self.last_origin = None
        self.last_destination = None
        self.last_search_time = None

    def set_waiting_destination(self, origin: str):
        """Carrier told us where they are, waiting for where they want to go"""
        self.state = self.WAITING_DESTINATION
        self.last_origin = origin
        self.last_search_time = datetime.now()

    def set_waiting_equipment(self):
        """Waiting to learn equipment type"""
        self.state = self.WAITING_EQUIPMENT

    def set_waiting_mc(self):
        """Waiting for MC# verification"""
        self.state = self.WAITING_MC_NUMBER

    def set_active(self):
        """Back to normal active state"""
        self.state = self.ACTIVE

    def save_search(self, origin: str = None, destination: str = None):
        """Save the last search for context"""
        if origin:
            self.last_origin = origin
        if destination:
            self.last_destination = destination
        self.last_search_time = datetime.now()


class IntelligentConversationEngine:
    """
    Phase 1 Intelligent Conversation Engine

    Design Principles:
    1. Casual/Friendly Tone - Sound like a real broker texting
    2. Smart Questioning - Ask qualifying questions
    3. Contextual Memory - Remember locations, preferences
    4. MC# Gating - No rates/details without MC# verification
    5. Concise Responses - Show 2-3 best matches
    """

    def __init__(self, database, sheets_loader):
        self.db = database
        self.sheets_loader = sheets_loader
        self.conversation_states = {}  # In-memory cache

    def get_conversation_state(self, carrier_id: int) -> ConversationState:
        """Get or create conversation state for carrier"""
        if carrier_id not in self.conversation_states:
            self.conversation_states[carrier_id] = ConversationState(carrier_id, self.db)
        return self.conversation_states[carrier_id]

    def detect_intent(self, message: str, carrier: Dict, state: ConversationState) -> Dict:
        """
        Enhanced intent detection for intelligent conversation

        Returns:
            {
                'intent': 'empty_location' | 'search_loads' | 'provide_mc' |
                          'provide_destination' | 'provide_equipment' | 'load_details' | 'other',
                'origin': str,
                'destination': str,
                'equipment_type': str,
                'mc_number': str,
                'load_reference': str,
                'confidence': float
            }
        """
        message_upper = message.upper()
        message_clean = message.strip()

        result = {
            'intent': 'other',
            'origin': None,
            'destination': None,
            'equipment_type': None,
            'mc_number': None,
            'load_reference': None,
            'confidence': 0.5
        }

        # 1. Detect MC# provision
        mc_match = re.search(r'MC\s*[#:-]?\s*(\d{4,7})', message_upper)
        if mc_match:
            result['intent'] = 'provide_mc'
            result['mc_number'] = mc_match.group(1)
            result['confidence'] = 0.95
            return result

        # Check for just digits (carrier might just send MC number)
        if re.match(r'^\d{4,7}$', message_clean) and state.state == ConversationState.WAITING_MC_NUMBER:
            result['intent'] = 'provide_mc'
            result['mc_number'] = message_clean
            result['confidence'] = 0.9
            return result

        # 2. Detect "I'm empty in X" or "Empty in X"
        empty_patterns = [
            r"(?:I'M|I AM|IM)\s+EMPTY\s+(?:IN|AT|@)\s+([A-Z\s]+)",
            r"EMPTY\s+(?:IN|AT|@)\s+([A-Z\s]+)",
            r"(?:I'M|I AM|IM)\s+(?:IN|AT|@)\s+([A-Z\s]+)\s+EMPTY",
            r"(?:CURRENTLY|NOW)\s+(?:IN|AT|@)\s+([A-Z\s]+)"
        ]

        for pattern in empty_patterns:
            match = re.search(pattern, message_upper)
            if match:
                location = match.group(1).strip()
                result['intent'] = 'empty_location'
                result['origin'] = self._parse_location(location)
                result['confidence'] = 0.9
                return result

        # 3. Detect destination response (when waiting for destination)
        if state.state == ConversationState.WAITING_DESTINATION:
            # They're answering "where do you want to go?"
            location = self._parse_location(message_upper)
            if location:
                result['intent'] = 'provide_destination'
                result['origin'] = state.last_origin
                result['destination'] = location
                result['confidence'] = 0.85
                return result

        # 4. Detect equipment type response (when waiting for equipment)
        if state.state == ConversationState.WAITING_EQUIPMENT:
            equipment = self._parse_equipment(message_upper)
            if equipment:
                result['intent'] = 'provide_equipment'
                result['equipment_type'] = equipment
                result['confidence'] = 0.85
                return result

        # 5. Detect load detail requests ("tell me about #1", "more details on L12345")
        detail_patterns = [
            r'(?:TELL ME )?(?:MORE |DETAILS )?(?:ABOUT |ON |FOR )?(?:#|NUMBER |LOAD )?(\d+)',
            r'(?:MORE INFO|DETAILS|INFO)\s+(?:ON\s+)?(?:#|LOAD\s+)?(L?\d+)',
            r'(L\d{4,6})',  # Just the load ID
        ]

        for pattern in detail_patterns:
            match = re.search(pattern, message_upper)
            if match:
                result['intent'] = 'load_details'
                result['load_reference'] = match.group(1).strip('#')
                result['confidence'] = 0.9
                return result

        # 6. Standard load search patterns
        # "loads in Atlanta", "Atlanta loads", "any loads ATL to DAL"
        search_patterns = [
            r'(?:ANY\s+)?LOADS?\s+(?:IN|FROM|OUT OF|@)\s+([A-Z\s]+)',
            r'([A-Z\s]+)\s+LOADS?',
            r'([A-Z\s]+)\s+TO\s+([A-Z\s]+)',
        ]

        for pattern in search_patterns:
            match = re.search(pattern, message_upper)
            if match:
                result['intent'] = 'search_loads'
                if len(match.groups()) == 1:
                    # Just origin
                    result['origin'] = self._parse_location(match.group(1))
                else:
                    # Origin and destination
                    result['origin'] = self._parse_location(match.group(1))
                    result['destination'] = self._parse_location(match.group(2))

                # Check for equipment in the same message
                equipment = self._parse_equipment(message_upper)
                if equipment:
                    result['equipment_type'] = equipment

                result['confidence'] = 0.8
                return result

        # 7. NEW: City + Equipment patterns (no "loads" keyword needed)
        # "Miami reefer", "Atlanta van", "Dallas flatbed"
        location = self._parse_location(message_upper)
        equipment = self._parse_equipment(message_upper)

        if location and equipment:
            # Both city and equipment detected
            result['intent'] = 'search_loads'
            result['origin'] = location
            result['equipment_type'] = equipment
            result['confidence'] = 0.75
            return result

        # 8. NEW: Just equipment (ask for location)
        # "Van", "Reefer", "Flatbed"
        if equipment and len(message_clean.split()) <= 2:
            result['intent'] = 'empty_location'
            result['equipment_type'] = equipment
            result['confidence'] = 0.6
            return result

        # 9. NEW: Just city name (ask for equipment/destination)
        # "Miami", "Atlanta", "Dallas"
        if location and len(message_clean.split()) <= 2:
            result['intent'] = 'search_loads'
            result['origin'] = location
            result['confidence'] = 0.6
            return result

        return result

    def _parse_location(self, location: str) -> Optional[str]:
        """Parse location to city code or state"""
        location = location.strip()

        # City codes mapping
        city_map = {
            'ATLANTA': 'ATL', 'ATL': 'ATL',
            'DALLAS': 'DAL', 'DAL': 'DAL',
            'HOUSTON': 'HOU', 'HOU': 'HOU', 'HTX': 'HOU',
            'MIAMI': 'MIA', 'MIA': 'MIA',
            'CHICAGO': 'CHI', 'CHI': 'CHI',
            'LOS ANGELES': 'LAX', 'LA': 'LAX', 'LAX': 'LAX',
            'PHOENIX': 'PHX', 'PHX': 'PHX',
            'NASHVILLE': 'BNA', 'BNA': 'BNA',
            'MEMPHIS': 'MEM', 'MEM': 'MEM',
            'JACKSONVILLE': 'JAX', 'JAX': 'JAX',
            'TAMPA': 'TPA', 'TPA': 'TPA',
        }

        # State codes mapping
        state_map = {
            'FLORIDA': 'FL', 'FL': 'FL',
            'TEXAS': 'TX', 'TX': 'TX',
            'GEORGIA': 'GA', 'GA': 'GA',
            'CALIFORNIA': 'CA', 'CA': 'CA', 'CALI': 'CA',
            'TENNESSEE': 'TN', 'TN': 'TN',
            'NORTH CAROLINA': 'NC', 'NC': 'NC',
        }

        # Check city first
        if location in city_map:
            return city_map[location]

        # Check state
        if location in state_map:
            return state_map[location]

        # Try to extract first 3 letters as code
        if len(location) >= 3:
            return location[:3].upper()

        return None

    def _parse_equipment(self, text: str) -> Optional[str]:
        """Parse equipment type from text (handles misspellings)"""
        # Dry Van variations
        if 'DRY' in text or 'VAN' in text:
            return 'Dry Van'
        # Reefer variations (including common misspellings)
        elif 'REEFER' in text or 'REFRIG' in text or 'RIEFFER' in text or 'REFER' in text or 'REFFER' in text:
            return 'Reefer'
        # Flatbed variations
        elif 'FLAT' in text or 'FLATBED' in text:
            return 'Flatbed'
        return None

    def generate_response(self, carrier: Dict, intent_data: Dict,
                         state: ConversationState, channel: str = 'sms') -> str:
        """
        Generate intelligent, context-aware response

        This is the heart of Phase 1 - making responses feel HUMAN
        """
        intent = intent_data['intent']

        # Get carrier info
        carrier_name = carrier.get('name') or None
        has_mc = carrier.get('mc_number') is not None

        # Route to appropriate response generator
        if intent == 'provide_mc':
            return self._handle_mc_provision(carrier, intent_data, state)

        elif intent == 'empty_location':
            return self._handle_empty_location(carrier, intent_data, state)

        elif intent == 'provide_destination':
            return self._handle_destination_provided(carrier, intent_data, state, has_mc)

        elif intent == 'search_loads':
            return self._handle_load_search(carrier, intent_data, state, has_mc)

        elif intent == 'load_details':
            return self._handle_load_details(carrier, intent_data, state, has_mc)

        else:
            return self._handle_general_help(carrier)

    def _handle_mc_provision(self, carrier: Dict, intent_data: Dict, state: ConversationState) -> str:
        """Handle MC# provision"""
        mc_number = intent_data['mc_number']

        # Save MC# to carrier profile
        self.db.update_carrier(carrier['phone'], mc_number=mc_number)

        # Reset state
        state.set_active()

        # If they were asking about a specific load, show it now
        return f"""Thanks! Verified ✓

Now I can show you full details. What are you looking for?"""

    def _handle_empty_location(self, carrier: Dict, intent_data: Dict, state: ConversationState) -> str:
        """Handle 'I'm empty in X' - save location and ask qualifying questions"""
        origin = intent_data['origin']

        # Save location to state
        state.set_waiting_destination(origin)

        # Update carrier profile with current location
        self.db.update_carrier(carrier['phone'],
                              equipment_types=json.dumps([]))  # We'll learn this next

        # Friendly response asking where they want to go
        return f"""Cool! Where do you want to go from {origin}?

Also, what equipment you running?"""

    def _handle_destination_provided(self, carrier: Dict, intent_data: Dict,
                                     state: ConversationState, has_mc: bool) -> str:
        """Handle destination response after asking 'where do you want to go?'"""
        origin = intent_data['origin'] or state.last_origin
        destination = intent_data['destination']

        if not origin:
            return "Where are you empty at?"

        # Search for loads
        loads = self.sheets_loader.search_loads(
            origin=origin,
            destination=destination
        )

        # Save search context
        state.save_search(origin, destination)
        state.set_active()

        # Return formatted response
        return self._format_load_list(origin, destination, loads, carrier, has_mc)

    def _handle_load_search(self, carrier: Dict, intent_data: Dict,
                           state: ConversationState, has_mc: bool) -> str:
        """Handle standard load search"""
        origin = intent_data['origin']
        destination = intent_data.get('destination')
        equipment = intent_data.get('equipment_type')

        # Search for loads
        loads = self.sheets_loader.search_loads(
            origin=origin,
            destination=destination,
            equipment_type=equipment
        )

        # Save search context
        state.save_search(origin, destination)

        # Return formatted response
        return self._format_load_list(origin, destination, loads, carrier, has_mc)

    def _handle_load_details(self, carrier: Dict, intent_data: Dict,
                            state: ConversationState, has_mc: bool) -> str:
        """Handle request for more details on a specific load"""
        load_ref = intent_data['load_reference']

        # CRITICAL: MC# gate - no details without MC#
        if not has_mc:
            state.set_waiting_mc()
            return """Before I can give you more details, I need your MC#.

What's your MC number?"""

        # Find the load (could be index like "1" or load ID like "L12345")
        load = None

        # Try as load ID first
        if load_ref.startswith('L'):
            load = self.sheets_loader.get_load_by_id(load_ref)
        else:
            # Try as index from last search
            try:
                index = int(load_ref) - 1
                # Get last search results (simplified - in production, cache this)
                origin = state.last_origin
                destination = state.last_destination
                if origin:
                    loads = self.sheets_loader.search_loads(origin=origin, destination=destination)
                    if 0 <= index < len(loads):
                        load = loads[index]
            except:
                pass

        if not load:
            return f"Couldn't find that load. Reply with load # or ID."

        # Format detailed response
        return self._format_load_details(load, carrier)

    def _format_load_list(self, origin: str, destination: Optional[str],
                         loads: List[Dict], carrier: Dict, has_mc: bool) -> str:
        """
        Format load list response

        CRITICAL: Show NO RATE without MC# verification
        """
        carrier_name = carrier.get('name')
        greeting = f"Hey {carrier_name}!" if carrier_name else "Hey!"

        # No matches found
        if not loads:
            lane_desc = f"{origin}→{destination}" if destination else origin
            return f"""Nothing out of {origin} right now 😕

Where else you got trucks? I'll keep an eye out for you."""

        # Limit to 2-3 best matches (Phase 1 design principle)
        top_loads = loads[:3]

        # Build response
        if has_mc:
            # WITH MC# - show rates
            response = f"{greeting} Got {len(top_loads)} good ones out of {origin}:\n\n"

            for i, load in enumerate(top_loads, 1):
                equipment = load.get('equipment_type', 'Van')
                length = load.get('trailer_length', 53)
                pickup = load.get('pickup_date', 'TBD')
                dest = load.get('destination', '???')
                rate = load.get('rate', 0)

                # Calculate miles (simplified - in production, use actual distance)
                miles = load.get('miles', '???')

                response += f"{i}. {origin}→{dest}, {length}' {equipment}, picks {pickup}, {miles}mi, ${rate:,}\n"

            response += "\nAny of these work?"

        else:
            # WITHOUT MC# - NO RATES, ask for MC#
            response = f"{greeting} Got {len(top_loads)} good ones out of {origin}:\n\n"

            for i, load in enumerate(top_loads, 1):
                equipment = load.get('equipment_type', 'Van')
                length = load.get('trailer_length', 53)
                pickup = load.get('pickup_date', 'TBD')
                dest = load.get('destination', '???')
                miles = load.get('miles', '???')

                # NO RATE shown
                response += f"{i}. {origin}→{dest}, {length}' {equipment}, picks {pickup}, {miles}mi\n"

            response += "\nInterested? What's your MC#?"

        return response

    def _format_load_details(self, load: Dict, carrier: Dict) -> str:
        """Format detailed load information (MC# already verified)"""
        origin = load.get('origin', '???')
        destination = load.get('destination', '???')

        return f"""{origin}→{destination} Details:
📍 Pickup: {load.get('origin', '???')} - {load.get('pickup_date', 'TBD')}
📍 Delivery: {load.get('destination', '???')} - {load.get('delivery_date', 'TBD')}
📏 {load.get('miles', '???')} miles
💰 ${load.get('rate', 0):,}
🚛 {load.get('equipment_type', 'Van')}, {load.get('weight', '???')} lbs

Works for you?"""

    def _handle_general_help(self, carrier: Dict) -> str:
        """General help message"""
        return """Eagle here! 👋

Text me:
• "Loads in Atlanta"
• "I'm empty in Dallas"
• "Atlanta to Miami"

Questions? Call 770-965-1242"""
