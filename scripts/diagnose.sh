#!/bin/bash

# Autonomous DevOps Agent - Diagnostic Script
# This script helps diagnose common setup issues

echo " Autonomous DevOps Agent - System Diagnostics"
echo "================================================"
echo ""

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check Docker
echo "1. Checking Docker..."
if command -v docker &> /dev/null; then
    docker_version=$(docker --version)
    echo -e "${GREEN}${NC} Docker installed: $docker_version"
    
    # Check if Docker daemon is running
    if docker info &> /dev/null; then
        echo -e "${GREEN}${NC} Docker daemon is running"
    else
        echo -e "${RED}${NC} Docker daemon is not running. Please start Docker Desktop."
        echo "   On macOS/Windows: Open Docker Desktop app"
        echo "   On Linux: sudo systemctl start docker"
    fi
else
    echo -e "${RED}${NC} Docker not found. Please install Docker Desktop:"
    echo "   https://www.docker.com/products/docker-desktop"
fi
echo ""

# Check Docker Compose
echo "2. Checking Docker Compose..."
if command -v docker-compose &> /dev/null; then
    compose_version=$(docker-compose --version)
    echo -e "${GREEN}${NC} Docker Compose installed: $compose_version"
else
    echo -e "${RED}${NC} Docker Compose not found. It should come with Docker Desktop."
fi
echo ""

# Check .env file
echo "3. Checking Environment Configuration..."
if [ -f ".env" ]; then
    echo -e "${GREEN}${NC} .env file exists"
    
    # Check for GEMINI_API_KEY
    if grep -q "GEMINI_API_KEY=" .env; then
        api_key_value=$(grep "GEMINI_API_KEY=" .env | cut -d '=' -f2)
        if [ -z "$api_key_value" ] || [ "$api_key_value" = "your_api_key_here" ]; then
            echo -e "${RED}${NC} GEMINI_API_KEY is not set in .env file"
            echo "   Please add your API key from https://makersuite.google.com/app/apikey"
        else
            echo -e "${GREEN}${NC} GEMINI_API_KEY is configured"
        fi
    else
        echo -e "${RED}${NC} GEMINI_API_KEY not found in .env file"
    fi
else
    echo -e "${YELLOW}${NC} .env file not found. Creating from template..."
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo -e "${GREEN}${NC} Created .env from .env.example"
        echo -e "${YELLOW}${NC} Please edit .env and add your GEMINI_API_KEY"
    else
        echo -e "${RED}${NC} .env.example not found. Cannot create .env file."
    fi
fi
echo ""

# Check port availability
echo "4. Checking Port Availability..."
check_port() {
    local port=$1
    local service=$2
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        echo -e "${YELLOW}${NC} Port $port is in use (needed for $service)"
        echo "   Run: lsof -i :$port to see what's using it"
        return 1
    else
        echo -e "${GREEN}${NC} Port $port is available ($service)"
        return 0
    fi
}

ports_ok=true
check_port 8000 "API" || ports_ok=false
check_port 8501 "UI" || ports_ok=false
check_port 6379 "Redis" || ports_ok=false
check_port 5555 "Flower" || ports_ok=false

if ! $ports_ok; then
    echo ""
    echo -e "${YELLOW}${NC} Some ports are in use. You can either:"
    echo "   1. Stop the conflicting services"
    echo "   2. Change ports in your .env file"
fi
echo ""

# Check if services are running
echo "5. Checking Docker Services..."
if docker-compose ps 2>/dev/null | grep -q "Up"; then
    echo -e "${GREEN}${NC} Docker Compose services are running"
    echo ""
    echo "Running services:"
    docker-compose ps --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}"
else
    echo -e "${YELLOW}${NC} No Docker Compose services are running"
    echo "   Run: docker-compose up -d to start all services"
fi
echo ""

# Check connectivity
echo "6. Testing Service Connectivity..."
if docker-compose ps 2>/dev/null | grep -q "api.*Up"; then
    # Test API health endpoint
    if curl -s http://localhost:8000/ > /dev/null 2>&1; then
        echo -e "${GREEN}${NC} API is accessible at http://localhost:8000"
        
        # Check API health
        health=$(curl -s http://localhost:8000/ | grep -o '"status":"[^"]*"' | cut -d'"' -f4)
        if [ "$health" = "healthy" ]; then
            echo -e "${GREEN}${NC} API health check: healthy"
        else
            echo -e "${YELLOW}${NC} API health check: $health"
        fi
    else
        echo -e "${RED}${NC} Cannot connect to API at http://localhost:8000"
    fi
    
    # Test UI
    if curl -s http://localhost:8501/ > /dev/null 2>&1; then
        echo -e "${GREEN}${NC} UI is accessible at http://localhost:8501"
    else
        echo -e "${YELLOW}${NC} Cannot connect to UI at http://localhost:8501"
    fi
else
    echo -e "${YELLOW}${NC} Services not running. Skipping connectivity tests."
fi
echo ""

# Summary
echo "================================================"
echo " Diagnostic Summary"
echo "================================================"

all_good=true

if ! command -v docker &> /dev/null || ! docker info &> /dev/null; then
    all_good=false
    echo -e "${RED}${NC} Docker needs to be installed and running"
fi

if [ ! -f ".env" ] || ! grep -q "GEMINI_API_KEY=.+" .env; then
    all_good=false
    echo -e "${RED}${NC} Environment configuration needs attention"
fi

if ! docker-compose ps 2>/dev/null | grep -q "Up"; then
    all_good=false
    echo -e "${YELLOW}${NC} Services need to be started with: docker-compose up -d"
fi

if $all_good; then
    echo -e "${GREEN} Everything looks good!${NC}"
    echo ""
    echo "You can access:"
    echo "  • UI: http://localhost:8501"
    echo "  • API Docs: http://localhost:8000/docs"
    echo "  • Flower: http://localhost:5555"
else
    echo ""
    echo "Please fix the issues above and run this script again."
fi

echo ""
echo "For more help, see the README.md file or open an issue on GitHub."
