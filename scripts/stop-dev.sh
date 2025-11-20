#!/bin/bash

# IRIS Development Environment Shutdown Script
# This script stops all development containers

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}========================================${NC}"
echo -e "${YELLOW}  IRIS Development Environment Shutdown${NC}"
echo -e "${YELLOW}========================================${NC}"
echo ""

# Get the project root directory (parent of scripts directory)
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

COMPOSE_FILE="$PROJECT_ROOT/docker/docker-compose.dev.yml"

if [ ! -f "$COMPOSE_FILE" ]; then
    echo -e "${RED}Error: docker-compose.dev.yml not found at $COMPOSE_FILE${NC}"
    exit 1
fi

# Check if user wants to remove volumes
REMOVE_VOLUMES=false
if [ "$1" == "--volumes" ] || [ "$1" == "-v" ]; then
    echo -e "${RED}WARNING: This will remove all volumes and DELETE all data!${NC}"
    read -p "Are you sure you want to remove volumes? (yes/no): " confirm
    if [ "$confirm" == "yes" ]; then
        REMOVE_VOLUMES=true
    else
        echo "Volumes will be preserved."
    fi
fi

echo -e "${YELLOW}Stopping IRIS development containers...${NC}"

if [ "$REMOVE_VOLUMES" == true ]; then
    docker compose -f "$COMPOSE_FILE" down -v
    echo -e "${GREEN}✓ Containers stopped and volumes removed${NC}"
else
    docker compose -f "$COMPOSE_FILE" down
    echo -e "${GREEN}✓ Containers stopped (volumes preserved)${NC}"
fi

echo ""
echo -e "${GREEN}Development environment shut down successfully!${NC}"
echo ""

if [ "$REMOVE_VOLUMES" == false ]; then
    echo -e "${YELLOW}Note: Data volumes were preserved. To remove all data, run:${NC}"
    echo "  ./scripts/stop-dev.sh --volumes"
fi
