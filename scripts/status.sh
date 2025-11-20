#!/bin/bash

# IRIS Development Environment Status Check Script

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Get the project root directory
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
COMPOSE_FILE="$PROJECT_ROOT/docker/docker-compose.dev.yml"

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  IRIS Development Environment Status${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}✗ Docker is not running${NC}"
    exit 1
else
    echo -e "${GREEN}✓ Docker is running${NC}"
fi

echo ""

# Check service status
if [ -f "$COMPOSE_FILE" ]; then
    echo "Service Status:"
    docker compose -f "$COMPOSE_FILE" ps
else
    echo -e "${RED}✗ docker-compose.dev.yml not found${NC}"
    exit 1
fi

echo ""

# Check individual services
check_service() {
    local service=$1
    local port=$2

    if docker compose -f "$COMPOSE_FILE" ps | grep -q "$service.*Up"; then
        echo -e "${GREEN}✓${NC} $service is running"

        if [ -n "$port" ]; then
            if nc -z localhost $port 2>/dev/null; then
                echo -e "  Port $port is accessible"
            else
                echo -e "${YELLOW}  Warning: Port $port is not accessible${NC}"
            fi
        fi
    else
        echo -e "${RED}✗${NC} $service is not running"
    fi
}

echo "Detailed Status:"
check_service "oracle-iris-dev" 1524
check_service "iris-minio" 9000
check_service "iris-redis" 6379
check_service "iris-mlflow" 5000

echo ""
echo "Quick Access URLs:"
echo "  Oracle EM Express: https://localhost:5503/em"
echo "  MinIO Console:     http://localhost:9001"
echo "  MLflow UI:         http://localhost:5000"
