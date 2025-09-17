#!/bin/bash

# Set environment variable to run as FastAPI server
export RUN_SERVER=true

# Start the voice agent in Twilio server mode
echo "🚀 Starting Voice Agent in Twilio Server Mode..."
echo "📞 Twilio webhook endpoint: http://localhost:8000/incoming-call"
echo "🔍 Health check: http://localhost:8000/health"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

python demo/main.py
