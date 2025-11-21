#!/bin/bash
#
# Meraki Magic MCP - SSE Server Startup Script
# Works on macOS and Linux
#

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=========================================="
echo "Meraki Magic MCP - SSE Server"
echo -e "==========================================${NC}"
echo ""

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Load environment variables from .env file if it exists
if [ -f .env ]; then
    echo -e "${GREEN}✓${NC} Loading environment variables from .env"
    export $(cat .env | grep -v '^#' | grep -v '^$' | xargs)
else
    echo -e "${YELLOW}⚠${NC} Warning: .env file not found"
    echo "  Please create .env with MERAKI_API_KEY and MERAKI_ORG_ID"
fi

# Default configuration
PORT=${MCP_PORT:-8000}
HOST=${MCP_HOST:-0.0.0.0}

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo -e "${RED}✗${NC} Virtual environment not found"
    echo "  Creating virtual environment..."
    python3 -m venv .venv
    echo -e "${GREEN}✓${NC} Virtual environment created"
fi

# Activate virtual environment
echo -e "${GREEN}✓${NC} Activating virtual environment"
source .venv/bin/activate

# Check if dependencies are installed
if ! python -c "import fastmcp" 2>/dev/null; then
    echo -e "${YELLOW}⚠${NC} Dependencies not installed"
    echo "  Installing requirements..."
    pip install -r requirements.txt
    echo -e "${GREEN}✓${NC} Dependencies installed"
fi

# Verify required environment variables
if [ -z "$MERAKI_API_KEY" ]; then
    echo -e "${RED}✗${NC} ERROR: MERAKI_API_KEY not set in .env"
    exit 1
fi

if [ -z "$MERAKI_ORG_ID" ]; then
    echo -e "${RED}✗${NC} ERROR: MERAKI_ORG_ID not set in .env"
    exit 1
fi

echo ""
echo -e "${BLUE}=========================================="
echo "Server Configuration"
echo -e "==========================================${NC}"
echo "Host:               $HOST"
echo "Port:               $PORT"
echo "SSE Endpoint:       http://$HOST:$PORT/sse"
echo "Messages Endpoint:  http://$HOST:$PORT/messages"
echo "Caching:            ${ENABLE_CACHING:-true}"
echo "Read-Only Mode:     ${READ_ONLY_MODE:-false}"
echo -e "${BLUE}==========================================${NC}"
echo ""

# Check if port is available
if lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null 2>&1 ; then
    echo -e "${RED}✗${NC} ERROR: Port $PORT is already in use"
    echo "  Either stop the process using that port or choose a different port:"
    echo "  MCP_PORT=8001 ./start-sse-server.sh"
    exit 1
fi

echo -e "${GREEN}✓${NC} Starting SSE server..."
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Start the server
python3 meraki-mcp-dynamic-sse.py --sse --port $PORT
