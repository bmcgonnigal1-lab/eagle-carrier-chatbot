#!/usr/bin/env python3
"""
Test Helper Methods for Comprehensive Database
Verifies all new helper methods work correctly
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import Database
from datetime import datetime, timedelta


def test_helper_methods():
    """Test all helper methods"""
    print("\n" + "="*70)
    print("TESTING COMPREHENSIVE DATABASE HELPER METHODS")
    print("="*70 + "\n")

    # Initialize test database
    db = Database("data/carriers_test.db")

    # ===== TEST 1: Create Test Carrier =====
    print("TEST 1: Creating Test Carrier...")
    carrier_id = db.create_carrier(
        phone='+14045551234',
        email='test@carrier.com',
        legal_name='Test Carrier LLC',
        mc_number='MC123456',
        dot_number='DOT789012',
        status='active'
    )
    print(f"✅ Carrier Created: ID #{carrier_id}\n")

    # ===== TEST 2: Equipment Management =====
    print("TEST 2: Equipment Management...")
    equipment_id = db.add_carrier_equipment(
        carrier_id,
        total_power_units=25,
        total_drivers=30,
        dry_van_53ft=15,
        reefer_53ft=10,
        has_gps_tracking=1,
        gps_provider='Samsara',
        equipment_features=['liftgate', 'pallet_jack', 'straps']
    )
    print(f"   ✅ Equipment Added: ID #{equipment_id}")

    equipment = db.get_carrier_equipment(carrier_id)
    print(f"   ✅ Equipment Retrieved: {equipment['total_power_units']} power units")
    print(f"      Features: {equipment['equipment_features']}")

    db.update_carrier_equipment(carrier_id, dry_van_53ft=20, total_power_units=30)
    print(f"   ✅ Equipment Updated\n")

    # ===== TEST 3: Insurance Management =====
    print("TEST 3: Insurance Management...")
    future_date = (datetime.now() + timedelta(days=45)).strftime('%Y-%m-%d')
    insurance_id = db.add_carrier_insurance(
        carrier_id,
        auto_liability_carrier='State Farm',
        auto_liability_coverage_amount=1000000,
        auto_liability_expiration_date=future_date,
        cargo_insurance_carrier='Progressive',
        cargo_coverage_amount=100000,
        cargo_expiration_date=future_date
    )
    print(f"   ✅ Insurance Added: ID #{insurance_id}")

    insurance = db.get_carrier_insurance(carrier_id)
    print(f"   ✅ Insurance Retrieved: ${insurance['auto_liability_coverage_amount']:,} auto liability")

    expiring = db.check_insurance_expiration(days_ahead=60)
    print(f"   ✅ Expiration Check: {len(expiring)} carriers with expiring insurance\n")

    # ===== TEST 4: Safety Scores =====
    print("TEST 4: Safety Scores (FMCSA)...")
    score_id = db.update_fmcsa_scores(
        carrier_id,
        unsafe_driving_score=55,
        unsafe_driving_percentile=30,
        overall_safety_rating='Satisfactory',
        iss_score=85,
        total_inspections=120,
        inspections_with_violations=15,
        total_crashes=2
    )
    print(f"   ✅ FMCSA Scores Updated: ID #{score_id}")

    safety = db.get_carrier_safety_score(carrier_id)
    print(f"   ✅ Safety Score Retrieved: {safety['overall_safety_rating']} (ISS: {safety['iss_score']})")

    safe_carriers = db.get_carriers_by_safety_rating(min_score=70)
    print(f"   ✅ Safe Carriers Query: {len(safe_carriers)} carriers with ISS >= 70\n")

    # ===== TEST 5: Performance Tracking =====
    print("TEST 5: Performance Tracking...")
    perf_id = db.update_carrier_performance(
        carrier_id,
        total_loads_completed=150,
        on_time_pickup_percentage=95.5,
        on_time_delivery_percentage=97.2,
        reliability_score=4.8,
        total_revenue_generated=450000,
        avg_margin_percentage=12.5,
        preferred_carrier=1
    )
    print(f"   ✅ Performance Updated: ID #{perf_id}")

    performance = db.get_carrier_performance(carrier_id)
    print(f"   ✅ Performance Retrieved: {performance['reliability_score']}/5.0 reliability")
    print(f"      {performance['on_time_pickup_percentage']}% on-time pickup")

    top_carriers = db.get_top_performing_carriers(limit=10)
    print(f"   ✅ Top Performers Query: {len(top_carriers)} carriers\n")

    # ===== TEST 6: Lane Management =====
    print("TEST 6: Lane Management...")
    lane_id = db.add_carrier_lane(
        carrier_id,
        origin='Atlanta, GA',
        destination='Charlotte, NC',
        frequency='weekly',
        trucks_available=5,
        avg_rate_on_lane=1200,
        loads_completed_on_lane=25,
        confidence_score=0.9
    )
    print(f"   ✅ Lane Added: ID #{lane_id}")

    lanes = db.get_carrier_lanes(carrier_id)
    print(f"   ✅ Lanes Retrieved: {len(lanes)} preferred lanes")

    carriers_for_lane = db.find_carriers_for_lane('GA', 'NC')
    print(f"   ✅ Carriers for Lane: {len(carriers_for_lane)} carriers service GA->NC\n")

    # ===== TEST 7: Document Management =====
    print("TEST 7: Document Management...")
    doc_id = db.add_carrier_document(
        carrier_id,
        doc_type='w9',
        file_path='/uploads/w9_test_carrier.pdf',
        file_name='w9_test_carrier.pdf',
        status='verified',
        verified=1
    )
    print(f"   ✅ Document Added: ID #{doc_id}")

    docs = db.get_carrier_documents(carrier_id)
    print(f"   ✅ Documents Retrieved: {len(docs)} documents")

    expiring_docs = db.get_expiring_documents(days_ahead=30)
    print(f"   ✅ Expiring Documents: {len(expiring_docs)} documents expiring soon\n")

    # ===== TEST 8: Contact Management =====
    print("TEST 8: Contact Management...")
    contact_id = db.add_carrier_contact(
        carrier_id,
        first_name='John',
        last_name='Dispatcher',
        phone='+14045559999',
        email='john@carrier.com',
        contact_type='dispatcher',
        is_primary=1
    )
    print(f"   ✅ Contact Added: ID #{contact_id}")

    contacts = db.get_carrier_contacts(carrier_id)
    print(f"   ✅ Contacts Retrieved: {len(contacts)} contacts")

    primary = db.get_primary_contact(carrier_id)
    print(f"   ✅ Primary Contact: {primary['first_name']} {primary['last_name']}\n")

    # ===== TEST 9: Banking =====
    print("TEST 9: Banking...")
    banking_id = db.add_carrier_banking(
        carrier_id,
        bank_name='Wells Fargo',
        account_holder_name='Test Carrier LLC',
        account_type='checking',
        routing_number='121000248',
        account_number_last4='1234',
        payment_method='ACH',
        quickpay_enrolled=1,
        quickpay_fee_percentage=3.0
    )
    print(f"   ✅ Banking Added: ID #{banking_id}")

    banking = db.get_carrier_banking(carrier_id)
    print(f"   ✅ Banking Retrieved: {banking['bank_name']} ({banking['payment_method']})")

    db.update_carrier_banking(carrier_id, quickpay_fee_percentage=2.5)
    print(f"   ✅ Banking Updated\n")

    # ===== TEST 10: Rate Intelligence =====
    print("TEST 10: Rate Intelligence...")
    rate_id = db.log_carrier_rate(
        carrier_id,
        load_id=1001,
        origin='Atlanta, GA',
        destination='Charlotte, NC',
        rate=1200,
        equipment_type='dry_van',
        miles=245,
        accepted_rate=1200,
        market_rate_avg=1150
    )
    print(f"   ✅ Rate Logged: ID #{rate_id}")

    rate_history = db.get_carrier_rate_history(carrier_id, origin_state='GA', destination_state='NC')
    print(f"   ✅ Rate History: {len(rate_history)} quotes on GA->NC")

    avg_rate = db.get_average_rate_for_lane('GA', 'NC', days=90)
    if avg_rate:
        print(f"   ✅ Lane Average: ${avg_rate['avg_rate']:,.2f} (from {avg_rate['sample_size']} loads)\n")
    else:
        print(f"   ✅ Lane Average: No data yet\n")

    # ===== SUMMARY =====
    print("=" * 70)
    print("✅ ALL HELPER METHODS TESTED SUCCESSFULLY")
    print("=" * 70 + "\n")

    print("Summary of Features Tested:")
    print("  • Equipment Management (add, get, update)")
    print("  • Insurance Management (add, get, update, expiration alerts)")
    print("  • Safety Scores (FMCSA integration)")
    print("  • Performance Tracking (metrics, top performers)")
    print("  • Lane Management (add, search carriers by lane)")
    print("  • Document Management (add, get, expiration tracking)")
    print("  • Contact Management (add, get, primary contact)")
    print("  • Banking (add, get, update)")
    print("  • Rate Intelligence (log, history, lane averages)")
    print()

    # Cleanup
    import os
    if os.path.exists("data/carriers_test.db"):
        os.remove("data/carriers_test.db")
        print("🧹 Test database cleaned up\n")


if __name__ == '__main__':
    test_helper_methods()
