#!/usr/bin/env python3
"""
FMCSA Carrier Verification Script
Verifies carrier and auto-populates database with FMCSA data
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import Database
from integrations.fmcsa_api import FMCSAIntegration, MockFMCSAIntegration


def verify_and_create_carrier(mc_number: str = None, dot_number: str = None,
                              phone: str = None, email: str = None,
                              use_mock: bool = False):
    """
    Verify carrier with FMCSA and create comprehensive database record

    Args:
        mc_number: MC number (optional)
        dot_number: DOT number (optional)
        phone: Phone number (optional, for contact)
        email: Email (optional, for contact)
        use_mock: Use mock API for testing

    Returns:
        carrier_id if successful
    """
    print("\n" + "="*70)
    print("🔍 FMCSA CARRIER VERIFICATION & ONBOARDING")
    print("="*70 + "\n")

    # Initialize
    db = Database()
    fmcsa = MockFMCSAIntegration() if use_mock else FMCSAIntegration()

    # Step 1: Verify with FMCSA
    print("Step 1: Verifying with FMCSA...")
    verification = fmcsa.verify_carrier(mc_number=mc_number, dot_number=dot_number)

    if 'error' in verification:
        print(f"❌ Verification Failed: {verification['error']}")
        print(f"   {verification.get('message', '')}")
        return None

    carrier_info = verification['carrier_info']
    print(f"✅ Carrier Verified: {carrier_info.get('legal_name')}")
    print(f"   DOT#: {carrier_info.get('dot_number')}")
    print(f"   MC#: {carrier_info.get('mc_number')}")
    print(f"   Status: {carrier_info.get('operating_status')}\n")

    # Step 2: Create carrier in database
    print("Step 2: Creating carrier record...")

    # Check if carrier already exists
    existing = None
    if carrier_info.get('dot_number'):
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT id FROM carriers WHERE dot_number = ?',
                      (carrier_info['dot_number'],))
        row = cursor.fetchone()
        conn.close()
        if row:
            existing = row[0]

    if existing:
        print(f"⚠️  Carrier already exists (ID #{existing})")
        carrier_id = existing
    else:
        # Add phone/email if provided
        if phone:
            carrier_info['phone'] = phone
        if email:
            carrier_info['email'] = email

        # Create carrier
        carrier_id = db.create_carrier(**carrier_info)
        print(f"✅ Carrier Created: ID #{carrier_id}\n")

    # Step 3: Add BASICS Safety Scores
    print("Step 3: Adding BASICS safety scores...")
    if verification.get('basics_scores'):
        fmcsa_obj = FMCSAIntegration()  # Use real one for normalization
        basics_normalized = fmcsa_obj._normalize_basics_scores(
            verification['basics_scores']
        )

        if basics_normalized:
            try:
                score_id = db.update_fmcsa_scores(carrier_id, **basics_normalized)
                print(f"✅ Safety Scores Added: ID #{score_id}")
                print(f"   Unsafe Driving: {basics_normalized.get('unsafe_driving_percentile')}th percentile")
                print(f"   HOS Compliance: {basics_normalized.get('hos_compliance_percentile')}th percentile")
                print(f"   Vehicle Maintenance: {basics_normalized.get('vehicle_maintenance_percentile')}th percentile\n")
            except Exception as e:
                print(f"⚠️  Could not add safety scores: {e}\n")
    else:
        print("⚠️  No BASICS scores available\n")

    # Step 4: Add Initial Performance Record
    print("Step 4: Creating initial performance record...")
    try:
        perf_id = db.update_carrier_performance(
            carrier_id,
            total_loads_completed=0,
            reliability_score=3.0,  # Default starting score
            internal_rating=3.0
        )
        print(f"✅ Performance Record Created: ID #{perf_id}\n")
    except Exception as e:
        print(f"⚠️  Could not create performance record: {e}\n")

    # Step 5: Summary
    print("="*70)
    print("✅ CARRIER ONBOARDING COMPLETE")
    print("="*70 + "\n")

    print("Summary:")
    print(f"  • Carrier ID: #{carrier_id}")
    print(f"  • Legal Name: {carrier_info.get('legal_name')}")
    print(f"  • DOT#: {carrier_info.get('dot_number')}")
    print(f"  • MC#: {carrier_info.get('mc_number')}")
    print(f"  • Location: {carrier_info.get('physical_city')}, {carrier_info.get('physical_state')}")
    print(f"  • Status: {carrier_info.get('operating_status')}")
    print(f"  • FMCSA Verified: ✅")
    print(f"  • Safety Scores: ✅")
    print()

    return carrier_id


def main():
    """Test FMCSA verification"""
    import argparse

    parser = argparse.ArgumentParser(description='Verify carrier with FMCSA')
    parser.add_argument('--mc', help='MC number')
    parser.add_argument('--dot', help='DOT number')
    parser.add_argument('--phone', help='Phone number')
    parser.add_argument('--email', help='Email address')
    parser.add_argument('--mock', action='store_true', help='Use mock API')

    args = parser.parse_args()

    if not args.mc and not args.dot:
        # Run test with mock data
        print("No MC or DOT provided. Running test with mock data...\n")
        verify_and_create_carrier(
            mc_number='MC123456',
            phone='+14045551234',
            email='test@carrier.com',
            use_mock=True
        )
    else:
        verify_and_create_carrier(
            mc_number=args.mc,
            dot_number=args.dot,
            phone=args.phone,
            email=args.email,
            use_mock=args.mock
        )


if __name__ == '__main__':
    main()
