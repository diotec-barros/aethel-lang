#!/bin/bash
# Start script for Railway deployment

# Activate virtual environment if it exists
if [ -d "/opt/venv" ]; then
    source /opt/venv/bin/activate
    echo "Virtual environment activated"
fi

# Set default port if not provided
PORT=${PORT:-8000}

echo "Starting Aethel API on port $PORT"
echo "Working directory: $(pwd)"
echo "Python version: $(python --version)"
echo "Python path: $(which python)"
echo "Uvicorn path: $(which uvicorn)"

# Start uvicorn
exec uvicorn api.main:app --host 0.0.0.0 --port $PORT --log-level info
