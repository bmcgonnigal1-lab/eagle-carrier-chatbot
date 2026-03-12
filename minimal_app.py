from flask import Flask, jsonify
from datetime import datetime
import os

app = Flask(__name__)

@app.route('/health')
def health():
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'port': os.getenv('PORT'),
        'db_url_set': bool(os.getenv('DATABASE_URL'))
    })

@app.route('/')
def home():
    return jsonify({
        'message': 'Eagle Carrier Chatbot - Running!',
        'status': 'online'
    })
