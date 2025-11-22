#!/bin/bash

# Autonomous DevOps Agent - Quick Start Script
# This script automates the setup process for new developers

echo " Autonomous DevOps Agent - Quick Start"
echo "========================================"
echo ""
echo "This script will:" 
echo "  1. Check prerequisites"
echo "  2. Set up configuration"
echo "  3. Start all services"
echo "  4. Verify everything works"
echo ""

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo " Checking prerequisites..."

# Check for Docker
if ! command -v docker &> /dev/null; then
    echo -e "${RED} Docker is not installed${NC}"
    echo "   Please install Docker Desktop: https://docs.docker.com/get-docker/"
    exit 1
fi

# Check if Docker daemon is running
if ! docker info &> /dev/null; then
    echo -e "${RED} Docker daemon is not running${NC}"
    echo "   Please start Docker Desktop"
    exit 1
fi

# Check for Docker Compose
if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED} Docker Compose is not installed${NC}"
    echo "   It should come with Docker Desktop"
    exit 1
fi

echo -e "${GREEN} Docker and Docker Compose are ready${NC}"
echo ""

echo " Setting up configuration..."

# Check if .env exists
if [ ! -f .env ]; then
    echo "Creating .env file from template..."
    cp .env.example .env
    echo -e "${GREEN} Created .env file${NC}"
    echo ""
    echo -e "${YELLOW}️  IMPORTANT: You need to add your Gemini API key${NC}"
    echo "   1. Get your free API key: https://makersuite.google.com/app/apikey"
    echo "   2. Open .env file in your editor"
    echo "   3. Replace 'your_api_key_here' with your actual key"
    echo ""
    read -p "Press Enter when you've added your API key..."
fi

# Check if Gemini API key is set
if grep -q "GEMINI_API_KEY=your_api_key_here" .env || grep -q "GEMINI_API_KEY=$" .env || ! grep -q "GEMINI_API_KEY=." .env; then
    echo -e "${RED} Gemini API key not configured${NC}"
    echo ""
    echo "Please:"
    echo "  1. Get your free key at: https://makersuite.google.com/app/apikey"
    echo "  2. Edit .env file"
    echo "  3. Set GEMINI_API_KEY=your_actual_key"
    echo ""
    exit 1
fi

echo -e "${GREEN} Configuration ready${NC}"
echo ""

# Stop any existing services to avoid conflicts
echo " Cleaning up any existing services..."
docker-compose down 2>/dev/null

echo ""
echo "️  Building Docker images (this may take a few minutes)..."
docker-compose build

echo ""
echo " Starting services..."
docker-compose up -d

# Wait for services to be ready
echo ""
echo "⏳ Waiting for services to start (30 seconds)..."
for i in {1..30}; do
    echo -n "."
    sleep 1
done
echo ""

# Check service health
echo ""
echo " Checking service health..."
services_healthy=true
if docker-compose ps | grep -q "Exit"; then
    services_healthy=false
    echo -e "${RED} Some services failed to start${NC}"
    docker-compose ps
    echo ""
    echo "Check logs with: docker-compose logs"
else
    echo -e "${GREEN} All services are running${NC}"
    docker-compose ps --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}"
fi

# Test endpoints
echo ""
echo " Testing service endpoints..."

# Test API
if curl -s http://localhost:8000/ > /dev/null 2>&1; then
    echo -e "${GREEN} API is accessible${NC}"
    api_health=$(curl -s http://localhost:8000/ | grep -o '"status":"[^"]*"' | cut -d'"' -f4)
    if [ "$api_health" = "healthy" ]; then
        echo -e "${GREEN}   Health: $api_health${NC}"
    else
        echo -e "${YELLOW}   Health: $api_health${NC}"
    fi
else
    echo -e "${YELLOW}️  API is still starting up. Try again in a moment.${NC}"
fi

# Test UI
if curl -s http://localhost:8501/ > /dev/null 2>&1; then
    echo -e "${GREEN} UI is accessible${NC}"
else
    echo -e "${YELLOW}️  UI is still starting up. Try again in a moment.${NC}"
fi

echo ""
echo "========================================"
if $services_healthy; then
    echo -e "${GREEN} Setup complete!${NC}"
else
    echo -e "${YELLOW}️  Setup completed with warnings${NC}"
fi
echo ""
echo " Access your services:"
echo ""
echo "    UI (Recommended):  http://localhost:8501"
echo "    API:               http://localhost:8000"
echo "    API Docs:          http://localhost:8000/docs"
echo "    Monitoring:        http://localhost:5555"
echo ""
echo "========================================"
echo ""
echo " Quick Start:"
echo "   1. Open the UI: http://localhost:8501"
echo "   2. Click 'Submit Bug Fix'"
echo "   3. Enter a repository URL and bug description"
echo "   4. Watch the AI fix your bug!"
echo ""
echo " Useful commands:"
echo "   • View logs:         docker-compose logs -f"
echo "   • Stop services:     docker-compose down"
echo "   • Restart services:  docker-compose restart"
echo "   • Check health:      ./scripts/diagnose.sh"
echo ""
echo "Need help? Check the README.md or run ./scripts/diagnose.sh"
echo ""
echo -e "${GREEN}Happy bug fixing! →${NC}"
