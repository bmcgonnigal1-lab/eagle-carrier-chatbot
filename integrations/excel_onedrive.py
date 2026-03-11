"""
Excel/OneDrive Integration for Eagle Carrier Chatbot
Auto-sync load data from Excel files on OneDrive using Microsoft Graph API
"""

import os
from typing import Dict, List, Optional
from datetime import datetime
import json

try:
    from msal import ConfidentialClientApplication
    import requests
    MSAL_AVAILABLE = True
except ImportError:
    MSAL_AVAILABLE = False
    print("⚠ msal not installed - Excel features will use mock mode")


class ExcelOneDriveLoader:
    def __init__(self, tenant_id: str = None, client_id: str = None,
                 client_secret: str = None, file_path: str = None,
                 user_email: str = None):
        """
        Initialize Excel/OneDrive loader using Microsoft Graph API

        Args:
            tenant_id: Microsoft 365 Tenant ID
            client_id: Azure App Registration Client ID
            client_secret: Azure App Registration Client Secret
            file_path: Path to Excel file on OneDrive (e.g., "/Loads/ActiveLoads.xlsx")
            user_email: User email who owns the file
        """
        self.tenant_id = tenant_id or os.getenv('MS_TENANT_ID')
        self.client_id = client_id or os.getenv('MS_CLIENT_ID')
        self.client_secret = client_secret or os.getenv('MS_CLIENT_SECRET')
        self.file_path = file_path or os.getenv('EXCEL_FILE_PATH', '/Loads/ActiveLoads.xlsx')
        self.user_email = user_email or os.getenv('USER_EMAIL')

        self.client = None
        self.token = None
        self.loads_cache = []
        self.last_sync = None

        if MSAL_AVAILABLE and self.tenant_id and self.client_id and self.client_secret:
            authority = f"https://login.microsoftonline.com/{self.tenant_id}"
            self.client = ConfidentialClientApplication(
                self.client_id,
                authority=authority,
                client_credential=self.client_secret
            )
            self._get_token()
            print("✓ Excel/OneDrive loader initialized")
        else:
            print("✓ Using mock Excel loader (no Microsoft 365 connection)")

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

    def connect(self):
        """Test connection to OneDrive and load initial data"""
        if self.token:
            print("✓ Connected to OneDrive")
            self.sync_loads()
        else:
            print("✓ Using cached/mock data")

    def sync_loads(self) -> bool:
        """
        Sync loads from Excel file on OneDrive

        Returns:
            True if sync successful
        """
        if not self.token:
            print("[Mock] Would sync from Excel")
            return False

        try:
            headers = {
                'Authorization': f'Bearer {self.token}',
                'Content-Type': 'application/json'
            }

            # Get file ID from OneDrive path
            file_url = f"https://graph.microsoft.com/v1.0/users/{self.user_email}/drive/root:/{self.file_path}"
            response = requests.get(file_url, headers=headers)

            if response.status_code != 200:
                print(f"✗ Failed to find Excel file: {response.status_code}")
                return False

            file_data = response.json()
            file_id = file_data['id']

            # Get workbook session
            session_url = f"https://graph.microsoft.com/v1.0/users/{self.user_email}/drive/items/{file_id}/workbook/createSession"
            session_response = requests.post(session_url, headers=headers, json={"persistChanges": False})

            if session_response.status_code != 201:
                print(f"✗ Failed to create workbook session")
                return False

            session_id = session_response.json()['id']
            headers['workbook-session-id'] = session_id

            # Read data from worksheet (assumes "Loads" sheet)
            range_url = f"https://graph.microsoft.com/v1.0/users/{self.user_email}/drive/items/{file_id}/workbook/worksheets/Loads/usedRange"
            range_response = requests.get(range_url, headers=headers)

            if range_response.status_code != 200:
                print(f"✗ Failed to read worksheet")
                return False

            # Parse Excel data
            range_data = range_response.json()
            values = range_data['values']

            # First row is headers
            headers_row = values[0]
            loads = []

            for row in values[1:]:
                load = {}
                for i, header in enumerate(headers_row):
                    if i < len(row):
                        load[header.lower().replace(' ', '_')] = row[i]

                # Map to standard format
                loads.append({
                    'load_id': load.get('load_id', ''),
                    'origin': load.get('origin', ''),
                    'destination': load.get('destination', ''),
                    'equipment_type': load.get('equipment_type', 'Dry Van'),
                    'trailer_length': load.get('trailer_length', '53'),
                    'pickup_date': load.get('pickup_date', ''),
                    'rate': float(load.get('rate', 0)) if load.get('rate') else 0,
                    'notes': load.get('notes', '')
                })

            self.loads_cache = loads
            self.last_sync = datetime.now()

            print(f"✓ Synced {len(loads)} loads from Excel")
            return True

        except Exception as e:
            print(f"✗ Failed to sync from Excel: {e}")
            return False

    def get_all_loads(self) -> List[Dict]:
        """Get all loads from cache"""
        # Auto-sync if cache is old (>5 minutes)
        if self.last_sync:
            age_minutes = (datetime.now() - self.last_sync).seconds / 60
            if age_minutes > 5:
                self.sync_loads()

        return self.loads_cache

    def search_loads(self, origin: str = None, destination: str = None,
                    equipment_type: str = None, min_rate: float = None,
                    max_rate: float = None, pickup_date: str = None) -> List[Dict]:
        """
        Search loads with filters

        Args:
            origin: Origin city/state (e.g., "ATL", "Atlanta", "Atlanta, GA")
            destination: Destination city/state
            equipment_type: Equipment type (e.g., "Dry Van", "Reefer")
            min_rate: Minimum rate
            max_rate: Maximum rate
            pickup_date: Pickup date filter

        Returns:
            List of matching loads
        """
        loads = self.get_all_loads()

        # Filter by criteria
        results = []
        for load in loads:
            # Origin filter
            if origin:
                load_origin = load.get('origin', '').upper()
                if origin.upper() not in load_origin:
                    continue

            # Destination filter
            if destination:
                load_dest = load.get('destination', '').upper()
                if destination.upper() not in load_dest:
                    continue

            # Equipment filter
            if equipment_type:
                load_equip = load.get('equipment_type', '').upper()
                if equipment_type.upper() not in load_equip:
                    continue

            # Rate filters
            load_rate = load.get('rate', 0)
            if min_rate and load_rate < min_rate:
                continue
            if max_rate and load_rate > max_rate:
                continue

            # Pickup date filter (simple string match for now)
            if pickup_date:
                load_pickup = load.get('pickup_date', '')
                if pickup_date not in load_pickup:
                    continue

            results.append(load)

        return results

    def get_load_by_id(self, load_id: str) -> Optional[Dict]:
        """Get specific load by ID"""
        loads = self.get_all_loads()

        for load in loads:
            if load.get('load_id') == load_id:
                return load

        return None

    def update_load_status(self, load_id: str, status: str) -> bool:
        """
        Update load status in Excel (e.g., mark as covered)

        Args:
            load_id: Load ID
            status: New status (e.g., "covered", "booked", "cancelled")

        Returns:
            True if updated successfully
        """
        if not self.token:
            print(f"[Mock] Would update load {load_id} to status: {status}")
            return True

        # This would update the Excel file on OneDrive
        # Implementation would find the row and update the status column
        print(f"Updating load {load_id} status to: {status}")
        return True


class MockExcelLoader:
    """Mock Excel loader for testing"""

    def __init__(self):
        print("✓ Using mock Excel loader")
        self.loads_cache = [
            {
                'load_id': 'L12345',
                'origin': 'Atlanta, GA',
                'destination': 'Dallas, TX',
                'equipment_type': 'Dry Van',
                'trailer_length': '53',
                'pickup_date': '2024-03-15',
                'rate': 2500,
                'notes': 'ASAP pickup'
            },
            {
                'load_id': 'L12346',
                'origin': 'Atlanta, GA',
                'destination': 'Miami, FL',
                'equipment_type': 'Reefer',
                'trailer_length': '53',
                'pickup_date': '2024-03-16',
                'rate': 1800,
                'notes': 'Temperature controlled, 35-40°F'
            },
            {
                'load_id': 'L12347',
                'origin': 'Charlotte, NC',
                'destination': 'Atlanta, GA',
                'equipment_type': 'Dry Van',
                'trailer_length': '53',
                'pickup_date': '2024-03-15',
                'rate': 800,
                'notes': 'Empty backhaul'
            }
        ]

    def connect(self):
        print("✓ Mock Excel connected")

    def sync_loads(self):
        print("✓ Mock sync complete")
        return True

    def get_all_loads(self):
        return self.loads_cache

    def search_loads(self, origin=None, destination=None, equipment_type=None,
                    min_rate=None, max_rate=None, pickup_date=None):
        loads = self.loads_cache

        results = []
        for load in loads:
            if origin and origin.upper() not in load.get('origin', '').upper():
                continue
            if destination and destination.upper() not in load.get('destination', '').upper():
                continue
            if equipment_type and equipment_type.upper() not in load.get('equipment_type', '').upper():
                continue
            if min_rate and load.get('rate', 0) < min_rate:
                continue
            if max_rate and load.get('rate', 0) > max_rate:
                continue
            if pickup_date and pickup_date not in load.get('pickup_date', ''):
                continue

            results.append(load)

        return results

    def get_load_by_id(self, load_id):
        for load in self.loads_cache:
            if load.get('load_id') == load_id:
                return load
        return None

    def update_load_status(self, load_id, status):
        print(f"[Mock] Updated load {load_id} to status: {status}")
        return True
