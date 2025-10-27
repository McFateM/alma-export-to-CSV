#!/bin/bash

# Alma Digital Title Export to CSV - Quick Launch Script
# This script sets up the virtual environment and runs the Flet application

set -e

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Alma Digital Title Export to CSV${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Error: Python 3 is not installed${NC}"
    echo "Please install Python 3.8 or higher"
    exit 1
fi

# Check Python version
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo -e "${GREEN}Found Python ${PYTHON_VERSION}${NC}"

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo -e "${BLUE}Creating virtual environment...${NC}"
    python3 -m venv .venv
    echo -e "${GREEN}Virtual environment created${NC}"
else
    echo -e "${GREEN}Virtual environment already exists${NC}"
fi

# Activate virtual environment
echo -e "${BLUE}Activating virtual environment...${NC}"
source .venv/bin/activate

# Upgrade pip
echo -e "${BLUE}Upgrading pip...${NC}"
pip install --upgrade pip -q

# Install requirements
echo -e "${BLUE}Installing dependencies...${NC}"
pip install -r requirements.txt -q

echo -e "${GREEN}Dependencies installed${NC}"
echo ""

# Check for .env file
if [ ! -f ".env" ]; then
    echo -e "${BLUE}No .env file found${NC}"
    echo "You can create a .env file with your ALMA_API_KEY to avoid entering it each time:"
    echo "  echo 'ALMA_API_KEY=your_api_key_here' > .env"
    echo ""
fi

# Run the application
echo -e "${GREEN}Starting application...${NC}"
echo ""
python3 app.py
