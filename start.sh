#!/bin/bash

# This script runs on Render.com after deployment

echo "Starting deployment setup..."

# Run database migrations/initialization if needed
# Note: You'll need to manually run init.sql and load_data.py after first deployment

echo "Starting FastAPI server..."
uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
