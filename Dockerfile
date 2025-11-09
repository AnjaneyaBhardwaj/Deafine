FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    portaudio19-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Install package
RUN pip install -e .

# Create uploads directory
RUN mkdir -p uploads

# Expose API port (Render will use PORT env var)
EXPOSE 8000

# Health check (disabled for Render compatibility)
# HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
#     CMD python -c "import requests; requests.get('http://localhost:8000/health')"

# Run API server (Render provides PORT env var)
CMD uvicorn audio_access.api:app --host ${HOST:-127.0.0.1} --port ${PORT:-8000}

