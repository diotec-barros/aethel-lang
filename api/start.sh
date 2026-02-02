#!/bin/bash
# Start script for Railway deployment

# Set default port if not provided
PORT=${PORT:-8000}

echo "Starting Aethel API on port $PORT"
echo "Working directory: $(pwd)"
echo "Python version: $(python --version)"
echo "Uvicorn version: $(uvicorn --version)"

# Start uvicorn
exec uvicorn api.main:app --host 0.0.0.0 --port $PORT --log-level info
