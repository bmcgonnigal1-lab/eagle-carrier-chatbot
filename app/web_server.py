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
from app.database_factory import get_database
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
    # CRITICAL: Handle validation token during webhook subscription setup
    # RingCentral sends this header once when creating the subscription
    validation_token = request.headers.get('Validation-Token')
    if validation_token:
        print(f"✓ Received validation token, echoing back: {validation_token[:20]}...")
        response = jsonify({'status': 'validation_ok'})
        response.headers['Validation-Token'] = validation_token
        return response, 200

    # Handle actual SMS notifications
    bot = init_chatbot()

    # Parse RingCentral webhook payload (JSON format)
    data = request.json

    print(f"📱 Received RingCentral webhook: {data}")

    # RingCentral sends data in a specific format
    # Extract SMS details from the webhook payload
    try:
        # RingCentral webhook structure
        body = data.get('body', {})
        from_phone = body.get('from', {}).get('phoneNumber', '')
        message_text = body.get('subject', '')  # SMS text is in 'subject' field

        print(f"📨 SMS from {from_phone}: {message_text}")

        if from_phone and message_text:
            # Process the message
            response = bot.handle_sms(from_phone, message_text)

            print(f"📤 Sending response: {response}")

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

@app.route('/admin/list-ringcentral-webhooks', methods=['GET'])
def list_ringcentral_webhooks():
    """List all RingCentral webhook subscriptions"""
    bot = init_chatbot()

    # Check if using RingCentral
    if not hasattr(bot.sms_channel, 'platform'):
        return jsonify({
            'status': 'error',
            'message': 'RingCentral SMS not configured'
        }), 400

    try:
        response = bot.sms_channel.platform.get('/restapi/v1.0/subscription')
        subscriptions = response.json()

        return jsonify({
            'status': 'success',
            'subscriptions': subscriptions.get('records', [])
        })

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Failed to list webhooks: {str(e)}'
        }), 500


@app.route('/admin/delete-ringcentral-webhook/<subscription_id>', methods=['DELETE', 'GET'])
def delete_ringcentral_webhook(subscription_id):
    """Delete a RingCentral webhook subscription"""
    bot = init_chatbot()

    # Check if using RingCentral
    if not hasattr(bot.sms_channel, 'platform'):
        return jsonify({
            'status': 'error',
            'message': 'RingCentral SMS not configured'
        }), 400

    try:
        bot.sms_channel.platform.delete(f'/restapi/v1.0/subscription/{subscription_id}')

        return jsonify({
            'status': 'success',
            'message': f'Webhook {subscription_id} deleted successfully'
        })

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Failed to delete webhook: {str(e)}'
        }), 500


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

    webhook_url = "https://eagle-carrier-chatbot-production-3994.up.railway.app/webhook/ringcentral"

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


@app.route('/admin/unparsed-messages', methods=['GET'])
def unparsed_messages():
    """
    Show all messages that couldn't be parsed (intent = 'other')
    Helps identify patterns to add to the conversation engine
    """
    db = get_database()
    conn = db.get_connection()
    try:
        cursor = conn.cursor()

        # Get unparsed messages grouped by raw_message
        cursor.execute("""
            SELECT
                raw_message,
                COUNT(*) as count,
                MAX(timestamp) as last_seen,
                parsed_entities
            FROM queries
            WHERE parsed_intent = 'other' OR parsed_intent IS NULL
            GROUP BY raw_message, parsed_entities
            ORDER BY count DESC, last_seen DESC
            LIMIT 100
        """)

        unparsed = []
        for row in cursor.fetchall():
            unparsed.append({
                'message': row[0],
                'count': row[1],
                'last_seen': row[2].isoformat() if row[2] else None,
                'entities': row[3]
            })

        # Get parsing success rate
        cursor.execute("""
            SELECT
                COUNT(*) FILTER (WHERE parsed_intent != 'other' AND parsed_intent IS NOT NULL) as parsed,
                COUNT(*) FILTER (WHERE parsed_intent = 'other' OR parsed_intent IS NULL) as unparsed,
                COUNT(*) as total
            FROM queries
        """)

        stats = cursor.fetchone()
        success_rate = (stats[0] / stats[2] * 100) if stats[2] > 0 else 0

        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Unparsed Messages - Eagle Carrier Chatbot</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }}
                .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px; }}
                h1 {{ color: #2c3e50; }}
                .stats {{ background: #3498db; color: white; padding: 20px; border-radius: 5px; margin: 20px 0; }}
                .stats h2 {{ margin: 0 0 10px 0; }}
                .stats .metric {{ font-size: 24px; font-weight: bold; }}
                table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
                th {{ background: #34495e; color: white; padding: 12px; text-align: left; }}
                td {{ padding: 12px; border-bottom: 1px solid #ddd; }}
                tr:hover {{ background: #f8f9fa; }}
                .count {{ background: #e74c3c; color: white; padding: 4px 8px; border-radius: 3px; font-weight: bold; }}
                .back-link {{ display: inline-block; margin-bottom: 20px; color: #3498db; text-decoration: none; }}
                .back-link:hover {{ text-decoration: underline; }}
            </style>
        </head>
        <body>
            <div class="container">
                <a href="/" class="back-link">← Back to Dashboard</a>

                <h1>🔍 Unparsed Messages</h1>

                <div class="stats">
                    <h2>Parsing Success Rate</h2>
                    <div class="metric">{success_rate:.1f}%</div>
                    <p>Parsed: {stats[0]:,} | Unparsed: {stats[1]:,} | Total: {stats[2]:,}</p>
                </div>

                <p>These messages couldn't be understood by the conversation engine. Use them to identify new patterns to add!</p>

                <table>
                    <thead>
                        <tr>
                            <th>Message</th>
                            <th>Times Received</th>
                            <th>Last Seen</th>
                            <th>Detected Entities</th>
                        </tr>
                    </thead>
                    <tbody>
        """

        for msg in unparsed:
            html += f"""
                        <tr>
                            <td><strong>{msg['message']}</strong></td>
                            <td><span class="count">{msg['count']}</span></td>
                            <td>{msg['last_seen'] or 'N/A'}</td>
                            <td>{msg['entities'] or 'None'}</td>
                        </tr>
            """

        if not unparsed:
            html += """
                        <tr>
                            <td colspan="4" style="text-align: center; color: #27ae60; padding: 40px;">
                                🎉 Great! All messages are being parsed successfully!
                            </td>
                        </tr>
            """

        html += """
                    </tbody>
                </table>

                <div style="margin-top: 40px; padding: 20px; background: #ecf0f1; border-radius: 5px;">
                    <h3>💡 How to Use This Data:</h3>
                    <ol>
                        <li>Look for common patterns in unparsed messages</li>
                        <li>Add new regex patterns to <code>conversation_engine.py</code></li>
                        <li>Update <code>_parse_location()</code> and <code>_parse_equipment()</code> methods</li>
                        <li>Test the new patterns</li>
                        <li>Watch the parsing success rate improve!</li>
                    </ol>
                </div>
            </div>
        </body>
        </html>
        """

        return html

    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        db.return_connection(conn)


@app.route('/health', methods=['GET'])
def health():
    """
    Comprehensive health check endpoint
    Returns detailed status of all system components
    """
    health_status = {
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'checks': {}
    }

    # Check database connectivity
    try:
        db = get_database()
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM carriers')
        carrier_count = cursor.fetchone()[0]
        db.return_connection(conn)

        health_status['checks']['database'] = {
            'status': 'connected',
            'type': 'PostgreSQL' if os.getenv('DATABASE_URL') else 'SQLite',
            'carrier_count': carrier_count
        }
    except Exception as e:
        health_status['status'] = 'unhealthy'
        health_status['checks']['database'] = {
            'status': 'error',
            'error': str(e)
        }

    # Check RingCentral configuration
    if os.getenv('RINGCENTRAL_CLIENT_ID'):
        health_status['checks']['ringcentral'] = {
            'status': 'configured',
            'phone': os.getenv('RINGCENTRAL_PHONE_NUMBER', 'not set')
        }
    else:
        health_status['checks']['ringcentral'] = {
            'status': 'not configured'
        }

    # Check environment variables
    health_status['checks']['environment'] = {
        'database_url': 'set' if os.getenv('DATABASE_URL') else 'not set',
        'port': os.getenv('PORT', '5000'),
        'use_mock_sms': os.getenv('USE_MOCK_SMS', 'true')
    }

    # Overall health based on critical checks
    if health_status['checks']['database']['status'] != 'connected':
        health_status['status'] = 'unhealthy'

    return jsonify(health_status)


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
