#!/bin/bash
# Startup script for Railway deployment
# Ensures PORT variable is properly set

PORT=${PORT:-8080}
echo "Starting gunicorn on port $PORT"
exec gunicorn app.web_server:app --bind 0.0.0.0:$PORT --workers 2 --timeout 120
