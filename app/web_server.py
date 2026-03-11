"""
Web Server for Eagle Carrier Chatbot
Flask application with dashboard and webhooks
"""

from flask import Flask, request, render_template, jsonify
from datetime import datetime, timedelta
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.main import CarrierChatbot
from app.database import Database
from app.intelligence import IntelligenceEngine

# Initialize Flask app
app = Flask(__name__,
            template_folder='../templates',
            static_folder='../static')

# Initialize chatbot
chatbot = None

def init_chatbot():
    """Initialize chatbot instance"""
    global chatbot
    if chatbot is None:
        # Read from environment variables first, then fall back to config file
        use_mock_sms = os.getenv('USE_MOCK_SMS', 'true').lower() == 'true'
        use_mock_email = os.getenv('USE_MOCK_EMAIL', 'true').lower() == 'true'
        use_mock_sheets = os.getenv('USE_MOCK_SHEETS', 'true').lower() == 'true'

        try:
            # Try to import config (for local development)
            import config
            use_mock_sms = config.USE_MOCK_SMS
            use_mock_sheets = config.USE_MOCK_SHEETS
            use_mock_email = config.USE_MOCK_EMAIL
        except ImportError:
            # Use environment variables (for production/Render)
            pass

        chatbot = CarrierChatbot(
            use_mock_sms=use_mock_sms,
            use_mock_sheets=use_mock_sheets,
            use_mock_email=use_mock_email
        )
    return chatbot


# ===== WEBHOOK ROUTES =====

@app.route('/webhook/sms', methods=['POST'])
def sms_webhook():
    """
    Twilio SMS webhook handler
    Receives incoming SMS messages and responds
    """
    bot = init_chatbot()

    # Parse incoming SMS
    from_phone = request.form.get('From', '')
    message = request.form.get('Body', '')

    # Process message
    response = bot.handle_sms(from_phone, message)

    # Return TwiML response
    return bot.sms_channel.create_twiml_response(response)


@app.route('/webhook/ringcentral', methods=['POST'])
def ringcentral_webhook():
    """
    RingCentral SMS webhook handler
    Receives incoming SMS messages from RingCentral
    """
    bot = init_chatbot()

    # Parse RingCentral webhook payload (JSON format)
    data = request.json

    # RingCentral sends data in a specific format
    # Extract SMS details from the webhook payload
    try:
        # RingCentral webhook structure
        body = data.get('body', {})
        from_phone = body.get('from', {}).get('phoneNumber', '')
        message_text = body.get('subject', '')  # SMS text is in 'subject' field

        if from_phone and message_text:
            # Process the message
            response = bot.handle_sms(from_phone, message_text)

            # Send response via RingCentral
            bot.sms_channel.send_sms(from_phone, response)

        return jsonify({'status': 'success'}), 200

    except Exception as e:
        print(f"✗ RingCentral webhook error: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/webhook/email', methods=['POST'])
def email_webhook():
    """
    Microsoft Graph API webhook handler (for future use)
    Receives email notifications from Microsoft 365
    """
    # This would handle webhook notifications from Microsoft Graph
    # For now, we'll poll emails instead
    return jsonify({'status': 'received'}), 200


# ===== DASHBOARD ROUTES =====

@app.route('/')
def dashboard():
    """Main dashboard page"""
    bot = init_chatbot()
    db = bot.database
    intel = IntelligenceEngine(db)

    # Get statistics
    stats = intel.get_overall_stats()

    # Get top carriers
    top_carriers = intel.get_top_carriers(limit=10)

    # Get hot lanes
    hot_lanes = intel.get_hot_lanes(days=30, min_queries=3)

    # Get recent activity
    recent_queries = intel.get_recent_queries(limit=20)

    return render_template('dashboard.html',
                         stats=stats,
                         top_carriers=top_carriers,
                         hot_lanes=hot_lanes,
                         recent_queries=recent_queries)


@app.route('/carriers')
def carriers():
    """Carriers list page"""
    bot = init_chatbot()
    db = bot.database
    intel = IntelligenceEngine(db)

    # Get all carriers
    all_carriers = intel.get_top_carriers(limit=1000)

    return render_template('carriers.html',
                         carriers=all_carriers)


@app.route('/carrier/<int:carrier_id>')
def carrier_detail(carrier_id):
    """Carrier detail page"""
    bot = init_chatbot()
    db = bot.database
    intel = IntelligenceEngine(db)

    # Get carrier info
    carrier = db.get_carrier(carrier_id)
    if not carrier:
        return "Carrier not found", 404

    # Get carrier insights
    insights = intel.get_carrier_insights(carrier_id)

    # Get carrier history
    history = intel.get_carrier_history(carrier_id, days=90)

    return render_template('carrier_detail.html',
                         carrier=carrier,
                         insights=insights,
                         history=history)


@app.route('/analytics')
def analytics():
    """Analytics page"""
    bot = init_chatbot()
    db = bot.database
    intel = IntelligenceEngine(db)

    # Get analytics data
    daily_activity = intel.get_daily_activity(days=30)
    equipment_breakdown = intel.get_equipment_breakdown()
    geography_stats = intel.get_geography_stats()

    return render_template('analytics.html',
                         daily_activity=daily_activity,
                         equipment_breakdown=equipment_breakdown,
                         geography_stats=geography_stats)


# ===== API ROUTES =====

@app.route('/api/search', methods=['POST'])
def api_search():
    """
    API endpoint for searching loads
    POST /api/search
    {
        "origin": "ATL",
        "destination": "DAL",
        "equipment_type": "Dry Van"
    }
    """
    bot = init_chatbot()

    data = request.json
    loads = bot.sheets_loader.search_loads(
        origin=data.get('origin'),
        destination=data.get('destination'),
        equipment_type=data.get('equipment_type'),
        pickup_date=data.get('pickup_date')
    )

    return jsonify({'loads': loads})


@app.route('/api/carrier/<int:carrier_id>', methods=['GET'])
def api_carrier(carrier_id):
    """Get carrier information"""
    bot = init_chatbot()
    carrier = bot.database.get_carrier(carrier_id)

    if carrier:
        return jsonify(carrier)
    else:
        return jsonify({'error': 'Carrier not found'}), 404


@app.route('/api/stats', methods=['GET'])
def api_stats():
    """Get overall statistics"""
    bot = init_chatbot()
    intel = IntelligenceEngine(bot.database)
    stats = intel.get_overall_stats()

    return jsonify(stats)


# ===== ADMIN ROUTES =====

@app.route('/admin/setup-ringcentral-webhook', methods=['GET'])
def setup_ringcentral_webhook():
    """
    One-time setup: Create RingCentral webhook subscription
    Visit this URL once to set up SMS forwarding
    """
    bot = init_chatbot()

    # Check if using RingCentral
    if not hasattr(bot.sms_channel, 'platform'):
        return jsonify({
            'status': 'error',
            'message': 'RingCentral SMS not configured'
        }), 400

    webhook_url = "https://eagle-carrier-chatbot.onrender.com/webhook/ringcentral"

    try:
        # Create webhook subscription
        response = bot.sms_channel.platform.post('/restapi/v1.0/subscription', {
            'eventFilters': [
                '/restapi/v1.0/account/~/extension/~/message-store/instant?type=SMS'
            ],
            'deliveryMode': {
                'transportType': 'WebHook',
                'address': webhook_url
            }
        })

        subscription = response.json()

        return jsonify({
            'status': 'success',
            'message': 'RingCentral webhook created successfully!',
            'subscription_id': subscription.get('id'),
            'webhook_url': webhook_url,
            'subscription_status': subscription.get('status')
        })

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Failed to create webhook: {str(e)}'
        }), 500


@app.route('/admin/process-emails', methods=['POST'])
def admin_process_emails():
    """
    Manually trigger email processing
    This would normally run on a schedule
    """
    bot = init_chatbot()

    # Get recent unread emails
    emails = bot.email_channel.get_recent_emails(max_count=50, unread_only=True)

    processed = 0
    for email in emails:
        # Process each email
        response = bot.handle_email(
            from_email=email['from_email'],
            from_name=email['from_name'],
            subject=email['subject'],
            body=bot.email_channel.parse_email_body(email['body'])
        )

        # Mark as read
        bot.email_channel.mark_as_read(email['id'])
        processed += 1

    return jsonify({
        'status': 'success',
        'processed': processed
    })


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat()
    })


# ===== RUN SERVER =====

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('FLASK_ENV') == 'development'

    print(f"""
    ╔═══════════════════════════════════════════════════════════╗
    ║  🦅 Eagle Carrier Chatbot - Web Dashboard                ║
    ║                                                           ║
    ║  Dashboard:  http://localhost:{port}/                       ║
    ║  Carriers:   http://localhost:{port}/carriers               ║
    ║  Analytics:  http://localhost:{port}/analytics              ║
    ║                                                           ║
    ║  SMS Webhook: http://localhost:{port}/webhook/sms           ║
    ║                                                           ║
    ║  Press Ctrl+C to stop                                     ║
    ╚═══════════════════════════════════════════════════════════╝
    """)

    app.run(host='0.0.0.0', port=port, debug=debug)
