#!/bin/bash
# Quick test script for Eagle Carrier Chatbot

echo ""
echo "🦅 Eagle Carrier Chatbot - Quick Test"
echo "======================================"
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed"
    echo "Please install Python from python.org"
    exit 1
fi

echo "✓ Python 3 found"

# Check if dependencies are installed
if ! python3 -c "import twilio" 2>/dev/null; then
    echo ""
    echo "📦 Installing dependencies..."
    pip3 install -r requirements.txt
fi

echo "✓ Dependencies installed"
echo ""

# Run test
echo "🧪 Running chatbot test..."
echo ""
python3 scripts/test_chatbot.py
