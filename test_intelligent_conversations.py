#!/usr/bin/env python
"""
Test Intelligent Conversation Engine with Real Scenarios
Simulates actual carrier conversations to test Phase 1 intelligence
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.main import CarrierChatbot


class ConversationTester:
    """Test realistic carrier conversation flows"""

    def __init__(self):
        # Initialize chatbot with mock services
        self.bot = CarrierChatbot(
            use_mock_sms=True,
            use_mock_sheets=True,  # Uses SqliteLoadsLoader with 51 real loads
            use_mock_email=True
        )

    def print_message(self, sender: str, message: str, response: str = None):
        """Pretty print conversation"""
        print("\n" + "="*70)
        print(f"📱 {sender}: {message}")
        print("-"*70)
        if response:
            print(f"🦅 Bot: {response}")
        print("="*70)

    def test_scenario_1_empty_location(self):
        """
        Scenario 1: Carrier says 'I'm empty in Atlanta'
        Bot should ask where they want to go + equipment type
        """
        print("\n\n" + "🎬 "*20)
        print("SCENARIO 1: Carrier Empty in Location")
        print("🎬 "*20)

        phone = "+14045551111"

        # Message 1: "I'm empty in Atlanta"
        msg1 = "I'm empty in Atlanta"
        response1 = self.bot.handle_sms(phone, msg1)
        self.print_message("Carrier Mike", msg1, response1)

        # Message 2: Provide destination
        msg2 = "Florida"
        response2 = self.bot.handle_sms(phone, msg2)
        self.print_message("Carrier Mike", msg2, response2)

        # Message 3: Ask about specific load
        msg3 = "tell me about #1"
        response3 = self.bot.handle_sms(phone, msg3)
        self.print_message("Carrier Mike", msg3, response3)

        # Message 4: Provide MC#
        msg4 = "MC123456"
        response4 = self.bot.handle_sms(phone, msg4)
        self.print_message("Carrier Mike", msg4, response4)

    def test_scenario_2_direct_search(self):
        """
        Scenario 2: Carrier directly searches for loads
        'Any loads in Atlanta?'
        """
        print("\n\n" + "🎬 "*20)
        print("SCENARIO 2: Direct Load Search (No MC# on file)")
        print("🎬 "*20)

        phone = "+17705552222"

        # Message 1: "Any loads in Atlanta?"
        msg1 = "Any loads in Atlanta?"
        response1 = self.bot.handle_sms(phone, msg1)
        self.print_message("Carrier Joe", msg1, response1)

        # Message 2: Provide MC# right away
        msg2 = "MC789012"
        response2 = self.bot.handle_sms(phone, msg2)
        self.print_message("Carrier Joe", msg2, response2)

        # Message 3: Search again - should show rates now
        msg3 = "Atlanta loads"
        response3 = self.bot.handle_sms(phone, msg3)
        self.print_message("Carrier Joe", msg3, response3)

    def test_scenario_3_lane_search(self):
        """
        Scenario 3: Carrier searches specific lane
        'Atlanta to Dallas dry van'
        """
        print("\n\n" + "🎬 "*20)
        print("SCENARIO 3: Specific Lane Search")
        print("🎬 "*20)

        phone = "+13105553333"

        # Message 1: Specific lane
        msg1 = "Atlanta to Dallas dry van"
        response1 = self.bot.handle_sms(phone, msg1)
        self.print_message("Carrier Sarah", msg1, response1)

        # Message 2: Different search without MC#
        msg2 = "Miami to Chicago"
        response2 = self.bot.handle_sms(phone, msg2)
        self.print_message("Carrier Sarah", msg2, response2)

    def test_scenario_4_returning_carrier(self):
        """
        Scenario 4: Carrier who already has MC# on file
        Should immediately show rates
        """
        print("\n\n" + "🎬 "*20)
        print("SCENARIO 4: Returning Carrier (MC# Already on File)")
        print("🎬 "*20)

        phone = "+14045551111"  # Same as Scenario 1 (Mike)

        # Mike already provided MC# in Scenario 1
        # This search should immediately show rates
        msg1 = "Any loads in Dallas?"
        response1 = self.bot.handle_sms(phone, msg1)
        self.print_message("Carrier Mike (returning)", msg1, response1)

    def test_scenario_5_no_matches(self):
        """
        Scenario 5: No loads available in requested location
        """
        print("\n\n" + "🎬 "*20)
        print("SCENARIO 5: No Matches Found")
        print("🎬 "*20)

        phone = "+16025554444"

        msg1 = "Any loads in Boise?"
        response1 = self.bot.handle_sms(phone, msg1)
        self.print_message("Carrier Tom", msg1, response1)

    def test_scenario_6_just_mc_number(self):
        """
        Scenario 6: Carrier just texts MC number (after being asked)
        """
        print("\n\n" + "🎬 "*20)
        print("SCENARIO 6: MC# Format Variations")
        print("🎬 "*20)

        phone = "+19175555555"

        # Message 1: Search
        msg1 = "loads in Chicago"
        response1 = self.bot.handle_sms(phone, msg1)
        self.print_message("Carrier Lisa", msg1, response1)

        # Message 2: Just digits (bot is waiting for MC#)
        msg2 = "456789"
        response2 = self.bot.handle_sms(phone, msg2)
        self.print_message("Carrier Lisa", msg2, response2)

        # Message 3: Search again with MC# verified
        msg3 = "Chicago loads"
        response3 = self.bot.handle_sms(phone, msg3)
        self.print_message("Carrier Lisa", msg3, response3)

    def run_all_tests(self):
        """Run all conversation scenarios"""
        print("\n\n")
        print("╔" + "="*68 + "╗")
        print("║" + " "*15 + "INTELLIGENT CONVERSATION TESTING" + " "*21 + "║")
        print("║" + " "*15 + "Phase 1: Load Discovery & Inquiry" + " "*18 + "║")
        print("╚" + "="*68 + "╝")

        self.test_scenario_1_empty_location()
        self.test_scenario_2_direct_search()
        self.test_scenario_3_lane_search()
        self.test_scenario_4_returning_carrier()
        self.test_scenario_5_no_matches()
        self.test_scenario_6_just_mc_number()

        print("\n\n")
        print("╔" + "="*68 + "╗")
        print("║" + " "*22 + "TESTING COMPLETE" + " "*30 + "║")
        print("╚" + "="*68 + "╝")
        print("\n")


if __name__ == '__main__':
    tester = ConversationTester()
    tester.run_all_tests()
