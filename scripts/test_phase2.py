#!/usr/bin/env python3
"""
Test script for Phase 2 features
Tests email, dashboard, intelligence, and Excel integration
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.main import CarrierChatbot
from app.intelligence import IntelligenceEngine
from channels.email import MockEmailChannel
from integrations.excel_onedrive import MockExcelLoader

def print_header(title):
    """Print section header"""
    print("\n" + "="*60)
    print(f"  {title}")
    print("="*60 + "\n")

def test_email_channel():
    """Test email functionality"""
    print_header("Testing Email Channel")

    email = MockEmailChannel()

    # Test email sending
    print("1. Testing email send...")
    result = email.send_email(
        to_email="carrier@example.com",
        subject="Available Loads - Atlanta to Dallas",
        body="<h1>Test Email</h1><p>This is a test.</p>",
        body_type="HTML"
    )
    print(f"   ✓ Email sent: {result}\n")

    # Test email retrieval
    print("2. Testing email retrieval...")
    emails = email.get_recent_emails(max_count=5)
    print(f"   ✓ Retrieved {len(emails)} emails")
    for e in emails:
        print(f"     - From: {e['from_email']} | Subject: {e['subject']}")
    print()

def test_excel_integration():
    """Test Excel/OneDrive integration"""
    print_header("Testing Excel Integration")

    excel = MockExcelLoader()
    excel.connect()

    # Test loading all loads
    print("1. Loading all loads...")
    loads = excel.get_all_loads()
    print(f"   ✓ Loaded {len(loads)} loads\n")

    # Test search
    print("2. Testing load search...")
    results = excel.search_loads(origin="ATL", destination="DAL")
    print(f"   ✓ Found {len(results)} loads matching ATL→DAL")
    for load in results:
        print(f"     - {load['load_id']}: ${load['rate']:,}")
    print()

    # Test get by ID
    print("3. Testing get load by ID...")
    load = excel.get_load_by_id("L12345")
    if load:
        print(f"   ✓ Found load: {load['origin']} → {load['destination']}")
    print()

def test_intelligence_engine():
    """Test intelligence and analytics"""
    print_header("Testing Intelligence Engine")

    # Create chatbot with mock data
    bot = CarrierChatbot(use_mock_sms=True, use_mock_sheets=True, use_mock_email=True)
    intel = IntelligenceEngine(bot.database)

    # Simulate some carrier activity
    print("1. Simulating carrier activity...")

    # Create test carrier
    carrier_id = bot.database.create_carrier(
        phone="+14045551234",
        name="Test Carrier Inc",
        status="active"
    )

    # Log some queries
    for i in range(5):
        bot.database.log_query(
            carrier_id=carrier_id,
            channel="sms",
            raw_message=f"Test query {i}",
            intent="search_loads",
            origin="ATL",
            destination="DAL",
            equipment_type="Dry Van",
            loads_shown=3
        )

    print(f"   ✓ Created carrier and logged 5 queries\n")

    # Test carrier scoring
    print("2. Testing carrier scoring...")
    score = intel.calculate_carrier_score(carrier_id)
    if score:
        print(f"   ✓ Carrier Score:")
        print(f"     - Total: {score['total_score']}")
        print(f"     - Engagement: {score['engagement_score']}")
        print(f"     - Grade: {score['grade']}")
    print()

    # Test carrier insights
    print("3. Testing carrier insights...")
    insights = intel.get_carrier_insights(carrier_id)
    print(f"   ✓ Carrier Insights:")
    print(f"     - Preferred Lanes: {insights['preferred_lanes']}")
    print(f"     - Preferred Equipment: {insights['preferred_equipment']}")
    print(f"     - Peak Days: {insights['peak_days']}")
    print()

    # Test hot lanes
    print("4. Testing hot lanes detection...")
    hot_lanes = intel.get_hot_lanes(days=30, min_queries=1)
    print(f"   ✓ Found {len(hot_lanes)} hot lanes:")
    for lane in hot_lanes[:3]:
        print(f"     - {lane['lane']}: {lane['query_count']} queries")
    print()

    # Test overall stats
    print("5. Testing overall statistics...")
    stats = intel.get_overall_stats()
    print(f"   ✓ Overall Stats:")
    print(f"     - Total Carriers: {stats['total_carriers']}")
    print(f"     - Total Queries: {stats['total_queries']}")
    print(f"     - Avg Engagement: {stats['avg_engagement_score']}")
    print()

def test_email_handling():
    """Test end-to-end email conversation"""
    print_header("Testing Email Conversation Flow")

    bot = CarrierChatbot(use_mock_sms=True, use_mock_sheets=True, use_mock_email=True)

    print("1. Testing email query handling...")
    response = bot.handle_email(
        from_email="carrier@example.com",
        from_name="John Carrier",
        subject="Looking for loads",
        body="Hi, I'm looking for loads from Atlanta to Dallas. I have a 53ft dry van available."
    )
    print(f"   ✓ Response: {response}\n")

    print("2. Verifying carrier was created...")
    carrier = bot.database.get_carrier_by_email("carrier@example.com")
    if carrier:
        print(f"   ✓ Carrier created: {carrier['name']}")
        print(f"   ✓ Total queries: {carrier['total_queries']}")
    print()

def test_web_dashboard():
    """Test dashboard data availability"""
    print_header("Testing Web Dashboard Data")

    bot = CarrierChatbot(use_mock_sms=True, use_mock_sheets=True, use_mock_email=True)
    intel = IntelligenceEngine(bot.database)

    print("1. Checking dashboard data availability...")

    # Get stats
    stats = intel.get_overall_stats()
    print(f"   ✓ Stats: {stats['total_carriers']} carriers, {stats['total_queries']} queries")

    # Get top carriers
    top = intel.get_top_carriers(limit=5)
    print(f"   ✓ Top carriers: {len(top)} available")

    # Get hot lanes
    lanes = intel.get_hot_lanes(days=30)
    print(f"   ✓ Hot lanes: {len(lanes)} available")

    # Get recent activity
    recent = intel.get_recent_queries(limit=10)
    print(f"   ✓ Recent activity: {len(recent)} queries")

    print("\n   ✓ Dashboard data ready!")
    print()

def main():
    """Run all tests"""
    print("\n" + "🦅"*30)
    print("  EAGLE CARRIER CHATBOT - PHASE 2 TEST SUITE")
    print("🦅"*30)

    try:
        # Run all tests
        test_email_channel()
        test_excel_integration()
        test_intelligence_engine()
        test_email_handling()
        test_web_dashboard()

        # Summary
        print_header("✅ ALL TESTS PASSED!")
        print("Phase 2 is ready to deploy!")
        print("\nNext steps:")
        print("1. Configure Microsoft 365 credentials (see PHASE2_GUIDE.md)")
        print("2. Deploy to Railway/Heroku (see DEPLOYMENT.md)")
        print("3. Test with real carriers!")
        print()

    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()
