#!/bin/bash

# Startup script for Twilio Call Agent with MCP Architecture
# This script starts both the MCP server and the FastAPI application

set -e

echo "============================================================"
echo "🚀 Starting Twilio Call Agent with MCP Architecture"
echo "============================================================"

# Check if .env file exists
if [ ! -f .env ]; then
    echo "❌ Error: .env file not found"
    echo "Please copy .env.example to .env and configure your credentials"
    exit 1
fi

# Load environment variables
export $(cat .env | grep -v '^#' | xargs)

# Check if Python virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating Python virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📥 Installing Python dependencies..."
pip install -q --upgrade pip
pip install -q -r requirements.txt

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "🛑 Shutting down servers..."
    kill $MCP_PID $APP_PID 2>/dev/null
    echo "✓ Servers stopped"
    exit 0
}

trap cleanup SIGINT SIGTERM

# Start MCP server in background
echo ""
echo "🔷 Starting MCP Server on port 8000..."
python mcp_server.py &
MCP_PID=$!
echo "✓ MCP Server started (PID: $MCP_PID)"

# Wait for MCP server to be ready
sleep 2

# Start FastAPI application
echo ""
echo "🔶 Starting FastAPI Application on port ${PORT:-3000}..."
python -m uvicorn app:app --host ${HOST:-0.0.0.0} --port ${PORT:-3000} &
APP_PID=$!
echo "✓ FastAPI Application started (PID: $APP_PID)"

echo ""
echo "============================================================"
echo "✅ All servers running!"
echo "============================================================"
echo "📍 MCP Server:    http://localhost:8000"
echo "📍 API Server:    http://${HOST:-0.0.0.0}:${PORT:-3000}"
echo "📍 Public URL:    ${PUBLIC_URL:-Not configured}"
echo ""
echo "📋 Twilio Webhook URLs:"
echo "   Incoming Call: ${PUBLIC_URL}/twilio/incoming-call"
echo "   Call Status:   ${PUBLIC_URL}/twilio/call-status"
echo ""
echo "Press Ctrl+C to stop all servers"
echo "============================================================"

# Wait for both processes
wait $MCP_PID $APP_PID
