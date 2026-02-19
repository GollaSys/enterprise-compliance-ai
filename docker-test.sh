#!/bin/bash

echo "=========================================="
echo "  Docker Compose Test Script"
echo "=========================================="
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Check Docker is running
echo -e "${YELLOW}Checking Docker...${NC}"
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}Docker is not running! Please start Docker Desktop.${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Docker is running${NC}"

# Stop any existing containers
echo -e "${YELLOW}Stopping existing containers...${NC}"
docker-compose down 2>/dev/null
docker-compose -f docker-compose.minimal.yml down 2>/dev/null
docker-compose -f docker-compose-working.yml down 2>/dev/null

# Remove old containers and images
echo -e "${YELLOW}Cleaning up old builds...${NC}"
docker rm compliance-backend compliance-frontend 2>/dev/null
docker rmi enterprise-compliance-ai_backend enterprise-compliance-ai_frontend 2>/dev/null

# Build fresh
echo -e "${YELLOW}Building containers...${NC}"
docker-compose build --no-cache

# Start containers
echo -e "${YELLOW}Starting containers...${NC}"
docker-compose up -d

# Wait for services
echo -e "${YELLOW}Waiting for services to start...${NC}"
sleep 10

# Test backend
echo -e "${YELLOW}Testing backend...${NC}"
if curl -s http://localhost:8001/health | grep -q "healthy"; then
    echo -e "${GREEN}✓ Backend is running${NC}"
else
    echo -e "${RED}✗ Backend is not responding${NC}"
    echo "Checking logs:"
    docker logs compliance-backend --tail 20
    exit 1
fi

# Test API endpoints
echo -e "${YELLOW}Testing API endpoints...${NC}"
if curl -s http://localhost:8001/api/v1/dashboard/metrics | grep -q "overall_compliance"; then
    echo -e "${GREEN}✓ API endpoints working${NC}"
else
    echo -e "${RED}✗ API endpoints not working${NC}"
    exit 1
fi

echo ""
echo -e "${GREEN}=========================================="
echo "  ✓ Docker setup is working!"
echo "==========================================${NC}"
echo ""
echo "Access the application at:"
echo "  Frontend: http://localhost:3000"
echo "  Backend API: http://localhost:8001"
echo "  API Docs: http://localhost:8001/docs"
echo ""
echo "To stop: docker-compose down"
echo "To view logs: docker-compose logs -f"