"""
FMCSA API Integration
Fetches carrier safety data, authority status, and BASICS scores from FMCSA
"""

import requests
import os
from typing import Dict, Optional
from datetime import datetime


class FMCSAIntegration:
    """
    Integration with FMCSA QCMobile API

    Documentation: https://mobile.fmcsa.dot.gov/QCDevsite/docs/qcApi

    Features:
    - Lookup carrier by DOT or MC number
    - Retrieve BASICS safety scores
    - Check authority status
    - Get operation classifications
    - Fetch cargo carried info
    """

    BASE_URL = "https://mobile.fmcsa.dot.gov/qc/services/carriers"

    def __init__(self, api_key: str = None):
        """
        Initialize FMCSA API client

        Args:
            api_key: FMCSA API webkey (get from mobile.fmcsa.dot.gov)
        """
        self.api_key = api_key or os.getenv('FMCSA_API_KEY')

        if not self.api_key:
            print("⚠️  FMCSA API key not found. Set FMCSA_API_KEY env variable.")
            print("   Get a key at: https://mobile.fmcsa.dot.gov/QCDevsite/")

    def _make_request(self, endpoint: str) -> Optional[Dict]:
        """
        Make request to FMCSA API

        Args:
            endpoint: API endpoint (without base URL)

        Returns:
            JSON response or None if error
        """
        if not self.api_key:
            return {
                'error': 'FMCSA API key not configured',
                'message': 'Set FMCSA_API_KEY environment variable'
            }

        url = f"{self.BASE_URL}/{endpoint}"
        params = {'webKey': self.api_key}

        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            if response.status_code == 401:
                return {'error': 'Unauthorized', 'message': 'Invalid API key'}
            elif response.status_code == 404:
                return {'error': 'Not Found', 'message': 'Carrier not found'}
            else:
                return {'error': f'HTTP {response.status_code}', 'message': str(e)}
        except requests.exceptions.RequestException as e:
            return {'error': 'Request Failed', 'message': str(e)}

    def get_carrier_by_dot(self, dot_number: str) -> Optional[Dict]:
        """
        Get carrier information by DOT number

        Args:
            dot_number: USDOT number (e.g., "44110")

        Returns:
            Carrier data dictionary or None
        """
        return self._make_request(f"{dot_number}")

    def get_carrier_by_mc(self, mc_number: str) -> Optional[Dict]:
        """
        Get carrier information by MC (docket) number

        Args:
            mc_number: MC docket number (e.g., "MC123456" or "123456")

        Returns:
            Carrier data dictionary or None
        """
        # Strip "MC" prefix if present
        docket_num = mc_number.replace('MC', '').replace('-', '').strip()
        return self._make_request(f"docket-number/{docket_num}")

    def get_basics_scores(self, dot_number: str) -> Optional[Dict]:
        """
        Get BASICS safety scores by DOT number

        Args:
            dot_number: USDOT number

        Returns:
            BASICS scores dictionary
        """
        return self._make_request(f"{dot_number}/basics")

    def get_authority_status(self, dot_number: str) -> Optional[Dict]:
        """
        Get operating authority status

        Args:
            dot_number: USDOT number

        Returns:
            Authority information
        """
        return self._make_request(f"{dot_number}/authority")

    def get_cargo_carried(self, dot_number: str) -> Optional[Dict]:
        """
        Get cargo types carried

        Args:
            dot_number: USDOT number

        Returns:
            Cargo carried information
        """
        return self._make_request(f"{dot_number}/cargo-carried")

    def get_operation_classification(self, dot_number: str) -> Optional[Dict]:
        """
        Get operation classification

        Args:
            dot_number: USDOT number

        Returns:
            Operation classification info
        """
        return self._make_request(f"{dot_number}/operation-classification")

    def verify_carrier(self, mc_number: str = None, dot_number: str = None) -> Dict:
        """
        Comprehensive carrier verification
        Fetches all available data and returns normalized structure

        Args:
            mc_number: MC number (optional)
            dot_number: DOT number (optional)

        Returns:
            Dictionary with all carrier data ready for database insertion
        """
        # Lookup carrier
        if dot_number:
            carrier_data = self.get_carrier_by_dot(dot_number)
        elif mc_number:
            carrier_data = self.get_carrier_by_mc(mc_number)
        else:
            return {'error': 'Must provide MC or DOT number'}

        if not carrier_data or 'error' in carrier_data:
            return carrier_data

        # Extract DOT number from response for additional queries
        dot_num = carrier_data.get('content', {}).get('carrier', {}).get('dotNumber')

        result = {
            'verified': True,
            'verified_at': datetime.now().isoformat(),
            'carrier_info': self._normalize_carrier_data(carrier_data),
        }

        # Fetch additional data if DOT number available
        if dot_num:
            result['basics_scores'] = self.get_basics_scores(dot_num)
            result['authority'] = self.get_authority_status(dot_num)
            result['cargo_carried'] = self.get_cargo_carried(dot_num)
            result['operation_classification'] = self.get_operation_classification(dot_num)

        return result

    def _normalize_carrier_data(self, raw_data: Dict) -> Dict:
        """
        Normalize FMCSA API response to match our database schema

        Args:
            raw_data: Raw API response

        Returns:
            Normalized dictionary matching database fields
        """
        if 'error' in raw_data:
            return raw_data

        content = raw_data.get('content', {})
        carrier = content.get('carrier', {})

        # Extract address
        phys_addr = carrier.get('phyStreet', '')
        phys_city = carrier.get('phyCity', '')
        phys_state = carrier.get('phyState', '')
        phys_zip = carrier.get('phyZipcode', '')
        phys_country = carrier.get('phyCountry', '')

        mail_addr = carrier.get('maiStreet', '')
        mail_city = carrier.get('maiCity', '')
        mail_state = carrier.get('maiState', '')
        mail_zip = carrier.get('maiZipcode', '')
        mail_country = carrier.get('maiCountry', '')

        # Build normalized structure
        normalized = {
            # Government Registration
            'dot_number': carrier.get('dotNumber'),
            'mc_number': carrier.get('docketNumber'),  # This might be MC number
            'legal_name': carrier.get('legalName'),
            'dba_name': carrier.get('dbaName'),

            # Contact Information
            'phone': carrier.get('telephone'),
            'email': carrier.get('emailAddress'),

            # Physical Address
            'physical_address_line1': phys_addr,
            'physical_city': phys_city,
            'physical_state': phys_state,
            'physical_zip': phys_zip,
            'physical_country': phys_country or 'US',

            # Mailing Address
            'mailing_address_line1': mail_addr,
            'mailing_city': mail_city,
            'mailing_state': mail_state,
            'mailing_zip': mail_zip,
            'mailing_country': mail_country or 'US',

            # Authority & Status
            'authority_status': carrier.get('carrierOperationDesc'),
            'operating_status': carrier.get('statusCode'),
            'out_of_service_date': carrier.get('oosDate'),

            # Business Details
            'employees_count': carrier.get('totalDrivers'),

            # Verification
            'fmcsa_verified': 1,
            'fmcsa_verified_date': datetime.now().isoformat(),

            # Raw data for reference
            'fmcsa_raw_data': carrier
        }

        return normalized

    def _normalize_basics_scores(self, basics_data: Dict) -> Dict:
        """
        Normalize BASICS scores to match database schema

        Args:
            basics_data: Raw BASICS API response

        Returns:
            Normalized safety scores dictionary
        """
        if 'error' in basics_data or not basics_data:
            return {}

        basics = basics_data.get('content', {}).get('basics', {})

        # Map BASICS categories to database fields
        normalized = {
            # Unsafe Driving
            'unsafe_driving_score': basics.get('unsafeDriving', {}).get('measure'),
            'unsafe_driving_percentile': basics.get('unsafeDriving', {}).get('percentile'),
            'unsafe_driving_alert_status': basics.get('unsafeDriving', {}).get('alertStatus'),

            # HOS Compliance
            'hos_compliance_score': basics.get('hoursOfServiceCompliance', {}).get('measure'),
            'hos_compliance_percentile': basics.get('hoursOfServiceCompliance', {}).get('percentile'),
            'hos_compliance_alert_status': basics.get('hoursOfServiceCompliance', {}).get('alertStatus'),

            # Driver Fitness
            'driver_fitness_score': basics.get('driverFitness', {}).get('measure'),
            'driver_fitness_percentile': basics.get('driverFitness', {}).get('percentile'),
            'driver_fitness_alert_status': basics.get('driverFitness', {}).get('alertStatus'),

            # Substance/Alcohol
            'substance_alcohol_score': basics.get('controlledSubstancesAlcohol', {}).get('measure'),
            'substance_alcohol_percentile': basics.get('controlledSubstancesAlcohol', {}).get('percentile'),
            'substance_alcohol_alert_status': basics.get('controlledSubstancesAlcohol', {}).get('alertStatus'),

            # Vehicle Maintenance
            'vehicle_maintenance_score': basics.get('vehicleMaintenance', {}).get('measure'),
            'vehicle_maintenance_percentile': basics.get('vehicleMaintenance', {}).get('percentile'),
            'vehicle_maintenance_alert_status': basics.get('vehicleMaintenance', {}).get('alertStatus'),

            # Crash Indicator
            'crash_indicator_score': basics.get('crashIndicator', {}).get('measure'),
            'crash_indicator_percentile': basics.get('crashIndicator', {}).get('percentile'),
            'crash_indicator_alert_status': basics.get('crashIndicator', {}).get('alertStatus'),

            # Inspection/Crash Data
            'total_inspections': basics.get('totalInspections'),
            'inspections_with_violations': basics.get('inspectionsWithViolations'),
            'total_crashes': basics.get('totalCrashes'),

            # Timestamps
            'fmcsa_last_updated': datetime.now().isoformat(),
            'snapshot_date': datetime.now().isoformat(),
        }

        return normalized


class MockFMCSAIntegration:
    """Mock FMCSA API for testing"""

    def __init__(self, api_key: str = None):
        print("📋 Using Mock FMCSA API (for testing)")

    def get_carrier_by_dot(self, dot_number: str) -> Dict:
        """Return mock carrier data"""
        return {
            'content': {
                'carrier': {
                    'dotNumber': dot_number,
                    'legalName': f'Test Carrier {dot_number}',
                    'dbaName': 'Test Transport',
                    'telephone': '404-555-1234',
                    'emailAddress': 'test@carrier.com',
                    'phyStreet': '123 Freight St',
                    'phyCity': 'Atlanta',
                    'phyState': 'GA',
                    'phyZipcode': '30303',
                    'carrierOperationDesc': 'Interstate',
                    'statusCode': 'ACTIVE',
                    'totalDrivers': 25
                }
            }
        }

    def get_carrier_by_mc(self, mc_number: str) -> Dict:
        """Return mock carrier data"""
        return self.get_carrier_by_dot('123456')

    def get_basics_scores(self, dot_number: str) -> Dict:
        """Return mock BASICS scores"""
        return {
            'content': {
                'basics': {
                    'unsafeDriving': {'measure': 55, 'percentile': 30, 'alertStatus': 'None'},
                    'hoursOfServiceCompliance': {'measure': 60, 'percentile': 35, 'alertStatus': 'None'},
                    'driverFitness': {'measure': 50, 'percentile': 25, 'alertStatus': 'None'},
                    'controlledSubstancesAlcohol': {'measure': 0, 'percentile': 0, 'alertStatus': 'None'},
                    'vehicleMaintenance': {'measure': 65, 'percentile': 40, 'alertStatus': 'None'},
                    'crashIndicator': {'measure': 45, 'percentile': 20, 'alertStatus': 'None'},
                    'totalInspections': 120,
                    'inspectionsWithViolations': 15,
                    'totalCrashes': 2
                }
            }
        }

    def get_authority_status(self, dot_number: str) -> Dict:
        """Return mock authority data"""
        return {
            'content': {
                'authority': {
                    'status': 'Active',
                    'authorityTypes': ['Property', 'Household Goods']
                }
            }
        }

    def get_cargo_carried(self, dot_number: str) -> Dict:
        """Return mock cargo data"""
        return {
            'content': {
                'cargoCarried': ['General Freight', 'Logs, Poles, Beams, Lumber']
            }
        }

    def get_operation_classification(self, dot_number: str) -> Dict:
        """Return mock operation classification"""
        return {
            'content': {
                'operationClassification': ['Interstate']
            }
        }

    def verify_carrier(self, mc_number: str = None, dot_number: str = None) -> Dict:
        """Return comprehensive mock data"""
        fmcsa = FMCSAIntegration()
        carrier_data = self.get_carrier_by_dot(dot_number or '123456')

        return {
            'verified': True,
            'verified_at': datetime.now().isoformat(),
            'carrier_info': fmcsa._normalize_carrier_data(carrier_data),
            'basics_scores': self.get_basics_scores(dot_number or '123456'),
            'authority': self.get_authority_status(dot_number or '123456'),
            'cargo_carried': self.get_cargo_carried(dot_number or '123456'),
            'operation_classification': self.get_operation_classification(dot_number or '123456')
        }
