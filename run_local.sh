#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "=================================================="
echo "   COMPLIANCE AI PLATFORM - LOCAL RUNNER"
echo "=================================================="
echo ""

# Check Python
echo -e "${YELLOW}Checking Python installation...${NC}"
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Python 3 is not installed!${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Python 3 found${NC}"

# Check Node
echo -e "${YELLOW}Checking Node.js installation...${NC}"
if ! command -v node &> /dev/null; then
    echo -e "${RED}Node.js is not installed!${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Node.js found${NC}"

# Create virtual environment if not exists
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}Creating Python virtual environment...${NC}"
    python3 -m venv venv
fi

# Activate virtual environment
echo -e "${YELLOW}Activating virtual environment...${NC}"
source venv/bin/activate

# Install backend dependencies
echo -e "${YELLOW}Installing backend dependencies...${NC}"
pip install --quiet -r requirements-minimal.txt

# Check if .env exists, create if not
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}Creating .env file...${NC}"
    cp .env.example .env
    echo -e "${YELLOW}⚠️  Please add your OPENAI_API_KEY to .env file${NC}"
fi

# Start backend
echo -e "${GREEN}Starting backend server on port 8001...${NC}"
python -m uvicorn src.api.main_simple:app --host 0.0.0.0 --port 8001 --reload &
BACKEND_PID=$!

# Wait for backend to start
sleep 3

# Check if backend is running
if curl -s http://localhost:8001/health > /dev/null; then
    echo -e "${GREEN}✓ Backend is running${NC}"
else
    echo -e "${RED}✗ Backend failed to start${NC}"
    kill $BACKEND_PID 2>/dev/null
    exit 1
fi

# Install frontend dependencies
echo -e "${YELLOW}Installing frontend dependencies...${NC}"
cd frontend
npm install --legacy-peer-deps --silent

# Start frontend
echo -e "${GREEN}Starting frontend on port 3000...${NC}"
REACT_APP_API_URL=http://localhost:8001 npm start &
FRONTEND_PID=$!

cd ..

# Wait for frontend to start
echo -e "${YELLOW}Waiting for frontend to start...${NC}"
sleep 10

echo ""
echo "=================================================="
echo -e "${GREEN}✓ PLATFORM IS RUNNING!${NC}"
echo "=================================================="
echo ""
echo "Access the application at:"
echo "  - Frontend: http://localhost:3000"
echo "  - Backend API: http://localhost:8001"
echo "  - API Documentation: http://localhost:8001/docs"
echo ""
echo "Press Ctrl+C to stop all services"
echo ""

# Function to cleanup on exit
cleanup() {
    echo ""
    echo -e "${YELLOW}Shutting down services...${NC}"
    kill $BACKEND_PID 2>/dev/null
    kill $FRONTEND_PID 2>/dev/null
    echo -e "${GREEN}Services stopped${NC}"
    exit 0
}

# Set trap to cleanup on Ctrl+C
trap cleanup INT

# Keep script running
wait