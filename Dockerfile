dockerfile
# Dockerfile for Eagle Carrier Chatbot
# Supports deployment to Railway, Fly.io, or any container platform

FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create data directory
RUN mkdir -p data

# Expose port (Railway uses 8080)
EXPOSE 8080

# Set environment variables
ENV FLASK_APP=app.web_server
ENV PYTHONUNBUFFERED=1
ENV PORT=8080

# Health check (using correct port)
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8080/health')"

# Run the application
CMD ["/bin/sh", "-c", "gunicorn app.web_server:app --bind 0.0.0.0:${PORT} --workers 2 --timeout 120"]
