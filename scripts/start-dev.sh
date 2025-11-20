#!/bin/bash

# IRIS Development Environment Startup Script
# This script starts all development containers and services

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  IRIS Development Environment Startup${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Get the project root directory (parent of scripts directory)
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}Error: Docker is not running. Please start Docker and try again.${NC}"
    exit 1
fi

# Check if docker-compose file exists
COMPOSE_FILE="$PROJECT_ROOT/docker/docker-compose.dev.yml"
if [ ! -f "$COMPOSE_FILE" ]; then
    echo -e "${RED}Error: docker-compose.dev.yml not found at $COMPOSE_FILE${NC}"
    exit 1
fi

echo -e "${YELLOW}Starting IRIS development containers...${NC}"
docker compose -f "$COMPOSE_FILE" up -d

echo ""
echo -e "${YELLOW}Waiting for services to become healthy...${NC}"
echo ""

# Function to check service health
check_service_health() {
    local service=$1
    local max_wait=${2:-300}  # Default 5 minutes
    local elapsed=0

    while [ $elapsed -lt $max_wait ]; do
        if docker compose -f "$COMPOSE_FILE" ps | grep -q "$service.*healthy"; then
            echo -e "${GREEN}✓ $service is healthy${NC}"
            return 0
        elif docker compose -f "$COMPOSE_FILE" ps | grep -q "$service.*unhealthy"; then
            echo -e "${RED}✗ $service is unhealthy${NC}"
            return 1
        fi

        sleep 5
        elapsed=$((elapsed + 5))
        echo -n "."
    done

    echo -e "${RED}✗ $service health check timed out${NC}"
    return 1
}

# Wait for Oracle Database (takes longest)
echo -n "Waiting for Oracle Database (this may take 3-5 minutes on first start)..."
check_service_health "oracle-iris-dev" 600  # 10 minutes for Oracle

# Wait for other services
echo ""
echo -n "Waiting for MinIO..."
check_service_health "iris-minio" 60

echo ""
echo -n "Waiting for Redis..."
check_service_health "iris-redis" 30

echo ""
echo -n "Waiting for MLflow..."
# MLflow doesn't have health check in current config, just wait a bit
sleep 10
echo -e "${GREEN}✓ MLflow started${NC}"

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  All services are ready!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

echo "Service URLs:"
echo "  Oracle Database:"
echo "    Host: localhost"
echo "    Port: 1524"
echo "    Service: FREEPDB1"
echo "    SYS Password: IrisDev123!"
echo "    User: iris_user / IrisUser123!"
echo "    EM Express: https://localhost:5503/em"
echo ""
echo "  MinIO Console:"
echo "    URL: http://localhost:9001"
echo "    Username: iris-admin"
echo "    Password: IrisMinIO123!"
echo ""
echo "  MinIO S3 API:"
echo "    Endpoint: http://localhost:9000"
echo ""
echo "  Redis:"
echo "    Host: localhost"
echo "    Port: 6379"
echo ""
echo "  MLflow Tracking Server:"
echo "    URL: http://localhost:5000"
echo ""

echo -e "${YELLOW}Useful commands:${NC}"
echo "  View logs:        docker compose -f docker/docker-compose.dev.yml logs -f [service]"
echo "  Stop environment: ./scripts/stop-dev.sh"
echo "  Connect to Oracle: sqlplus iris_user/IrisUser123!@localhost:1524/FREEPDB1"
echo ""

echo -e "${GREEN}Development environment is ready! Happy coding!${NC}"
