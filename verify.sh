#!/bin/bash

echo "Verifying Docker Compose Setup..."
echo "================================="
echo ""

# Test if docker-compose.yml exists
if [ ! -f "docker-compose.yml" ]; then
    echo "❌ docker-compose.yml not found"
    exit 1
fi

# Test if Dockerfile.backend exists
if [ ! -f "Dockerfile.backend" ]; then
    echo "❌ Dockerfile.backend not found"
    exit 1
fi

# Test if frontend/Dockerfile exists
if [ ! -f "frontend/Dockerfile" ]; then
    echo "❌ frontend/Dockerfile not found"
    exit 1
fi

# Test if main_simple.py exists
if [ ! -f "src/api/main_simple.py" ]; then
    echo "❌ src/api/main_simple.py not found"
    exit 1
fi

echo "✅ All required files exist"
echo ""
echo "To start the application, run:"
echo ""
echo "  docker-compose build"
echo "  docker-compose up -d"
echo ""
echo "Then check:"
echo "  curl http://localhost:8001/health"
echo ""