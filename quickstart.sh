#!/bin/bash

# Autonomous DevOps Agent - Quick Start Script

echo "Autonomous DevOps Agent - Quick Start"
echo "========================================"
echo ""

# Check for Docker
if ! command -v docker &> /dev/null; then
    echo "[ERROR] Docker is not installed. Please install Docker first."
    echo "Visit: https://docs.docker.com/get-docker/"
    exit 1
fi

# Check for Docker Compose
if ! command -v docker-compose &> /dev/null; then
    echo "[ERROR] Docker Compose is not installed. Please install Docker Compose first."
    echo "Visit: https://docs.docker.com/compose/install/"
    exit 1
fi

echo "[OK] Docker and Docker Compose are installed"
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "Creating .env file from template..."
    cp .env.example .env
    echo ""
    echo "[WARNING] Please edit .env file and add your OpenAI API key"
    echo "   Run: nano .env"
    echo "   Or open .env in your favorite editor"
    echo ""
    read -p "Press Enter when you've added your API key..."
fi

# Check if OpenAI API key is set
if grep -q "your_openai_api_key_here" .env; then
    echo "[ERROR] OpenAI API key not configured in .env file"
    echo "Please edit .env and add your actual API key"
    exit 1
fi

echo "[OK] Configuration file ready"
echo ""

# Build and start services
echo "Building Docker images..."
docker-compose build

echo ""
echo "Starting services..."
docker-compose up -d

# Wait for services to be ready
echo ""
echo "Waiting for services to start..."
sleep 10

# Check service health
echo ""
echo "Checking service health..."
docker-compose ps

# Test API endpoint
echo ""
echo "Testing API endpoint..."
if curl -s http://localhost:8000/ > /dev/null; then
    echo "[OK] API is running at http://localhost:8000"
else
    echo "[WARNING] API might still be starting up. Please wait a moment."
fi

echo ""
echo "========================================"
echo "Setup complete!"
echo ""
echo "Access points:"
echo "   • API:        http://localhost:8000"
echo "   • API Docs:   http://localhost:8000/docs"
echo "   • Flower:     http://localhost:5555"
echo ""
echo "Useful commands:"
echo "   • View logs:      docker-compose logs -f"
echo "   • Stop services:  docker-compose down"
echo "   • Restart:        docker-compose restart"
echo ""
echo "Try your first bug fix:"
echo 'curl -X POST "http://localhost:8000/api/v1/fix_bug" \'
echo '  -H "Content-Type: application/json" \'
echo '  -d '"'"'{"repository_url": "https://github.com/test/repo",'
echo '       "branch": "main",'
echo '       "issue_description": "Function returns wrong value",'
echo '       "language": "python"}'"'"'
echo ""
echo "Happy bug fixing!"
