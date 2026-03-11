"""
Google Sheets integration for Eagle Carrier Chatbot
Reads available loads from Google Sheets
"""

from typing import List, Dict, Optional
from datetime import datetime

try:
    import gspread
    from google.oauth2.service_account import Credentials
except ImportError:
    gspread = None
    Credentials = None

import gspread
from google.oauth2.service_account import Credentials
from typing import List, Dict, Optional
from datetime import datetime

class GoogleSheetsLoader:
    def __init__(self, credentials_path: str, sheet_url: str):
        """
        Initialize Google Sheets connection

        Args:
            credentials_path: Path to service account JSON file
            sheet_url: Google Sheets URL or sheet ID
        """
        self.credentials_path = credentials_path
        self.sheet_url = sheet_url
        self.client = None
        self.sheet = None

    def connect(self):
        """Connect to Google Sheets"""
        try:
            scopes = [
                'https://www.googleapis.com/auth/spreadsheets.readonly',
                'https://www.googleapis.com/auth/drive.readonly'
            ]

            creds = Credentials.from_service_account_file(
                self.credentials_path,
                scopes=scopes
            )

            self.client = gspread.authorize(creds)
            self.sheet = self.client.open_by_url(self.sheet_url).sheet1

            print("✓ Connected to Google Sheets")
            return True

        except Exception as e:
            print(f"✗ Failed to connect to Google Sheets: {e}")
            return False

    def get_all_loads(self) -> List[Dict]:
        """Get all available loads from Google Sheets"""
        if not self.sheet:
            self.connect()

        try:
            # Get all records as dictionaries
            records = self.sheet.get_all_records()

            # Filter for available loads only
            available_loads = [
                load for load in records
                if load.get('status', '').lower() == 'available'
            ]

            return available_loads

        except Exception as e:
            print(f"Error fetching loads: {e}")
            return []

    def search_loads(self,
                     origin: Optional[str] = None,
                     destination: Optional[str] = None,
                     equipment_type: Optional[str] = None,
                     min_rate: Optional[int] = None,
                     max_rate: Optional[int] = None,
                     pickup_date: Optional[str] = None) -> List[Dict]:
        """
        Search loads with filters

        Args:
            origin: Origin city code (e.g., 'ATL')
            destination: Destination city code (e.g., 'DAL')
            equipment_type: Equipment type (e.g., 'Dry Van', 'Reefer')
            min_rate: Minimum rate
            max_rate: Maximum rate
            pickup_date: Pickup date (YYYY-MM-DD)

        Returns:
            List of matching loads
        """
        all_loads = self.get_all_loads()
        results = []

        for load in all_loads:
            # Check each filter
            if origin and load.get('origin', '').upper() != origin.upper():
                continue

            if destination and load.get('destination', '').upper() != destination.upper():
                continue

            if equipment_type:
                load_equipment = load.get('equipment_type', '').lower()
                search_equipment = equipment_type.lower()
                if search_equipment not in load_equipment:
                    continue

            if min_rate and load.get('rate', 0) < min_rate:
                continue

            if max_rate and load.get('rate', 0) > max_rate:
                continue

            if pickup_date and str(load.get('pickup_date', '')) != pickup_date:
                continue

            results.append(load)

        return results

    def get_load_by_id(self, load_id: str) -> Optional[Dict]:
        """Get specific load by ID"""
        all_loads = self.get_all_loads()

        for load in all_loads:
            if str(load.get('load_id', '')).upper() == load_id.upper():
                return load

        return None

    def format_load_for_sms(self, load: Dict) -> str:
        """Format load for SMS response (short and scannable)"""
        equipment = load.get('equipment_type', 'Unknown')
        length = load.get('trailer_length', '')
        length_str = f"{length}'" if length else ''

        special = load.get('special_instructions', '')
        special_str = f"\n   {special}" if special and special.lower() != 'no special' else ''

        return f"""{load.get('load_id')} - {equipment} {length_str}
   {load.get('origin')} → {load.get('destination')}
   {load.get('pickup_date')}, ${load.get('rate', 0):,}{special_str}"""

    def format_load_for_email(self, load: Dict) -> str:
        """Format load for email response (detailed)"""
        return f"""
━━━━━━━━━━━━━━━━━━━━━
LOAD: {load.get('load_id')}
━━━━━━━━━━━━━━━━━━━━━
Origin: {load.get('origin')}
Destination: {load.get('destination')}
Equipment: {load.get('equipment_type')}, {load.get('trailer_length')}'
Pickup: {load.get('pickup_date')}
Rate: ${load.get('rate', 0):,}
Weight: {load.get('weight', 'N/A')} lbs
Commodity: {load.get('commodity', 'General Freight')}
Special Instructions: {load.get('special_instructions', 'None')}
"""


# For development/testing without Google Sheets credentials
class MockSheetsLoader:
    """Mock loader with sample data for testing"""

    def __init__(self):
        self.sample_loads = [
            {
                'load_id': 'L12345',
                'origin': 'ATL',
                'destination': 'DAL',
                'equipment_type': 'Dry Van',
                'trailer_length': 53,
                'pickup_date': '2026-03-10',
                'rate': 2200,
                'weight': 40000,
                'commodity': 'General Freight',
                'special_instructions': 'No special',
                'status': 'available'
            },
            {
                'load_id': 'L12346',
                'origin': 'ATL',
                'destination': 'DAL',
                'equipment_type': 'Dry Van',
                'trailer_length': 53,
                'pickup_date': '2026-03-10',
                'rate': 2400,
                'weight': 35000,
                'commodity': 'Electronics',
                'special_instructions': 'Liftgate required',
                'status': 'available'
            },
            {
                'load_id': 'L12347',
                'origin': 'ATL',
                'destination': 'MIA',
                'equipment_type': 'Reefer',
                'trailer_length': 53,
                'pickup_date': '2026-03-11',
                'rate': 2800,
                'weight': 42000,
                'commodity': 'Frozen Food',
                'special_instructions': 'Keep frozen -10°F',
                'status': 'available'
            }
        ]

    def connect(self):
        print("✓ Using mock data (no Google Sheets connection)")
        return True

    def get_all_loads(self):
        return [load for load in self.sample_loads if load['status'] == 'available']

    def search_loads(self, origin=None, destination=None, equipment_type=None, **kwargs):
        results = self.get_all_loads()

        if origin:
            results = [l for l in results if l['origin'].upper() == origin.upper()]
        if destination:
            results = [l for l in results if l['destination'].upper() == destination.upper()]
        if equipment_type:
            results = [l for l in results if equipment_type.lower() in l['equipment_type'].lower()]

        return results

    def get_load_by_id(self, load_id):
        for load in self.sample_loads:
            if load['load_id'].upper() == load_id.upper():
                return load
        return None

    def format_load_for_sms(self, load):
        length_str = f"{load['trailer_length']}'" if load.get('trailer_length') else ''
        special = load.get('special_instructions', '')
        special_str = f"\n   {special}" if special and special.lower() != 'no special' else ''

        return f"""{load['load_id']} - {load['equipment_type']} {length_str}
   {load['origin']} → {load['destination']}
   {load['pickup_date']}, ${load['rate']:,}{special_str}"""

    def format_load_for_email(self, load):
        return f"""
━━━━━━━━━━━━━━━━━━━━━
LOAD: {load['load_id']}
━━━━━━━━━━━━━━━━━━━━━
Origin: {load['origin']}
Destination: {load['destination']}
Equipment: {load['equipment_type']}, {load.get('trailer_length', 'N/A')}'
Pickup: {load['pickup_date']}
Rate: ${load['rate']:,}
Weight: {load.get('weight', 'N/A')} lbs
Commodity: {load.get('commodity', 'General Freight')}
Special Instructions: {load.get('special_instructions', 'None')}
"""


class SqliteLoadsLoader:
    """Load data from SQLite database (Aljex import)"""

    def __init__(self, db_path: str = 'data/loads.db'):
        import sqlite3
        self.db_path = db_path
        self.conn = None

    def connect(self):
        """Connect to SQLite loads database"""
        try:
            import sqlite3
            import os

            # Debug: Show current directory and data folder contents
            print(f"🔍 Looking for database at: {self.db_path}")
            print(f"🔍 Current working directory: {os.getcwd()}")
            if os.path.exists('data'):
                print(f"🔍 Files in data/: {os.listdir('data')}")
            else:
                print(f"🔍 data/ folder does not exist!")

            if not os.path.exists(self.db_path):
                print(f"✗ Loads database not found: {self.db_path}")
                print("✓ Using mock data instead")
                return False

            self.conn = sqlite3.connect(self.db_path)
            self.conn.row_factory = sqlite3.Row
            print(f"✓ Connected to loads database: {self.db_path}")
            return True
        except Exception as e:
            print(f"✗ Failed to connect to loads database: {e}")
            print("✓ Using mock data instead")
            return False

    def get_all_loads(self):
        """Get all available loads from database"""
        if not self.conn:
            return []

        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                SELECT load_id, customer, origin_state, origin_city,
                       destination_state, destination_city, ship_date,
                       delivery_date, equipment_type, trailer_length,
                       weight, rate
                FROM loads
                ORDER BY ship_date
            ''')

            loads = []
            for row in cursor.fetchall():
                # Format to match expected structure
                origin = f"{row['origin_city']}, {row['origin_state']}" if row['origin_city'] else row['origin_state']
                destination = f"{row['destination_city']}, {row['destination_state']}" if row['destination_city'] else row['destination_state']

                loads.append({
                    'load_id': row['load_id'],
                    'origin': origin,
                    'origin_city': row['origin_city'],
                    'origin_state': row['origin_state'],
                    'destination': destination,
                    'destination_city': row['destination_city'],
                    'destination_state': row['destination_state'],
                    'equipment_type': row['equipment_type'],
                    'trailer_length': row['trailer_length'],
                    'pickup_date': row['ship_date'],
                    'delivery_date': row['delivery_date'],
                    'rate': row['rate'],
                    'weight': row['weight'],
                    'commodity': row['customer'],
                    'special_instructions': '',
                    'status': 'available'
                })

            return loads

        except Exception as e:
            print(f"Error fetching loads from database: {e}")
            return []

    def search_loads(self, origin=None, destination=None, equipment_type=None, **kwargs):
        """Search loads with filters"""
        all_loads = self.get_all_loads()
        results = []

        for load in all_loads:
            # Check origin (match against city or state)
            if origin:
                origin_upper = origin.upper()
                if (origin_upper not in load.get('origin_city', '').upper() and
                    origin_upper != load.get('origin_state', '').upper()):
                    continue

            # Check destination (match against city or state)
            if destination:
                dest_upper = destination.upper()
                if (dest_upper not in load.get('destination_city', '').upper() and
                    dest_upper != load.get('destination_state', '').upper()):
                    continue

            # Check equipment type
            if equipment_type:
                if equipment_type.lower() not in load.get('equipment_type', '').lower():
                    continue

            results.append(load)

        return results

    def get_load_by_id(self, load_id):
        """Get specific load by ID"""
        all_loads = self.get_all_loads()
        for load in all_loads:
            if load['load_id'].upper() == load_id.upper():
                return load
        return None

    def format_load_for_sms(self, load):
        """Format load for SMS response"""
        length_str = f"{load['trailer_length']}'" if load.get('trailer_length') else ''
        special = load.get('special_instructions', '')
        special_str = f"\n   {special}" if special else ''

        return f"""{load['load_id']} - {load['equipment_type']} {length_str}
   {load['origin']} → {load['destination']}
   {load['pickup_date']}, ${load['rate']:,}{special_str}"""

    def format_load_for_email(self, load):
        """Format load for email response"""
        return f"""
━━━━━━━━━━━━━━━━━━━━━
LOAD: {load['load_id']}
━━━━━━━━━━━━━━━━━━━━━
Origin: {load['origin']}
Destination: {load['destination']}
Equipment: {load['equipment_type']}, {load.get('trailer_length', 'N/A')}'
Pickup: {load['pickup_date']}
Rate: ${load['rate']:,}
Weight: {load.get('weight', 'N/A')} lbs
Commodity: {load.get('commodity', 'General Freight')}
Special Instructions: {load.get('special_instructions', 'None')}
"""
