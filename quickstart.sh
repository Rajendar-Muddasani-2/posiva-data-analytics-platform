#!/bin/bash

# POSIVA Analytics Platform - Quick Start Script

set -e  # Exit on error

echo "=================================================="
echo "  POSIVA Analytics Platform - Quick Start"
echo "=================================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check Python version
echo -e "${BLUE}Checking Python version...${NC}"
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "Python version: $python_version"

if ! python3 -c 'import sys; assert sys.version_info >= (3, 10)' 2>/dev/null; then
    echo -e "${YELLOW}Warning: Python 3.10+ recommended${NC}"
fi

# Create virtual environment
echo -e "\n${BLUE}Creating virtual environment...${NC}"
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo -e "${GREEN}✓ Virtual environment created${NC}"
else
    echo -e "${GREEN}✓ Virtual environment exists${NC}"
fi

# Activate virtual environment
echo -e "\n${BLUE}Activating virtual environment...${NC}"
source venv/bin/activate

# Upgrade pip
echo -e "\n${BLUE}Upgrading pip...${NC}"
pip install --upgrade pip

# Install dependencies
echo -e "\n${BLUE}Installing dependencies...${NC}"
pip install -r requirements.txt
echo -e "${GREEN}✓ Dependencies installed${NC}"

# Create directories
echo -e "\n${BLUE}Creating directories...${NC}"
mkdir -p data models logs notebooks outputs
echo -e "${GREEN}✓ Directories created${NC}"

# Generate sample data
echo -e "\n${BLUE}Generating sample data...${NC}"
if [ ! -f "data/sample_data.csv" ]; then
    python3 src/utils/data_generator.py
    echo -e "${GREEN}✓ Sample data generated${NC}"
else
    echo -e "${GREEN}✓ Sample data exists${NC}"
fi

# Setup environment file
echo -e "\n${BLUE}Setting up environment...${NC}"
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo -e "${GREEN}✓ Created .env file (please update with your settings)${NC}"
else
    echo -e "${GREEN}✓ .env file exists${NC}"
fi

# Run quick demo
echo -e "\n${BLUE}Running quick demo...${NC}"
python3 demo.py

echo -e "\n=================================================="
echo -e "${GREEN}Setup complete!${NC}"
echo "=================================================="
echo ""
echo "Next steps:"
echo ""
echo "1. Start the dashboard:"
echo "   streamlit run webapp/Home.py"
echo ""
echo "2. Start the API (in another terminal):"
echo "   python src/api/main.py"
echo ""
echo "3. Access:"
echo "   - Dashboard: http://localhost:8501"
echo "   - API docs: http://localhost:8000/api/docs"
echo ""
echo "4. For production deployment:"
echo "   docker-compose -f docker-compose.prod.yml up -d"
echo ""
echo "5. Read documentation:"
echo "   - README.md - Project overview"
echo "   - DEPLOYMENT.md - Deployment guide"
echo "   - BUILD_STATUS.md - Build progress"
echo ""
echo "=================================================="
