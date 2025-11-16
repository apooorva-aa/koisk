#!/bin/bash
# Quick start script for PostgreSQL + pgvector RAG setup

set -e

echo "======================================================================"
echo "Kiosk PostgreSQL + pgvector Quick Start"
echo "======================================================================"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Navigate to project root
cd "$(dirname "$0")/.."
PROJECT_ROOT=$(pwd)

echo -e "\n${YELLOW}Step 1: Starting PostgreSQL with pgvector...${NC}"
docker compose -f docker-compose.dev.yml up -d postgres

echo -e "\n${YELLOW}Waiting for PostgreSQL to be healthy...${NC}"
sleep 5

# Check if healthy
if docker compose -f docker-compose.dev.yml ps postgres | grep -q "healthy"; then
    echo -e "${GREEN}✓ PostgreSQL is running and healthy${NC}"
else
    echo -e "${RED}✗ PostgreSQL failed to start${NC}"
    docker compose -f docker-compose.dev.yml logs postgres
    exit 1
fi

echo -e "\n${YELLOW}Step 2: Running integration test...${NC}"
if python tests/test_knowledge_base_integration.py; then
    echo -e "${GREEN}✓ Integration test passed${NC}"
else
    echo -e "${RED}✗ Integration test failed${NC}"
    exit 1
fi

echo -e "\n${YELLOW}Step 3: Running scraper to ingest IIITM data...${NC}"
echo -e "${YELLOW}This may take 5-10 minutes depending on network speed...${NC}"
cd src
if python -m services.scrape_knowledge_base; then
    echo -e "${GREEN}✓ Scraper completed successfully${NC}"
else
    echo -e "${RED}✗ Scraper failed${NC}"
    exit 1
fi

cd "$PROJECT_ROOT"

echo -e "\n${YELLOW}Step 4: Verifying ingested data...${NC}"
# Use docker exec to run psql inside the container
DOCUMENT_COUNT=$(docker compose -f docker-compose.dev.yml exec -T postgres \
    psql -U postgres -d kiosk_db -t -c "SELECT COUNT(*) FROM knowledge_documents;")

echo -e "${GREEN}✓ Total documents in database: ${DOCUMENT_COUNT}${NC}"

echo -e "\n${YELLOW}Step 5: Viewing sample documents...${NC}"
docker compose -f docker-compose.dev.yml exec -T postgres \
    psql -U postgres -d kiosk_db -c "
        SELECT 
            metadata->>'title' AS title,
            metadata->>'category' AS category,
            LEFT(content, 100) AS content_preview,
            created_at
        FROM knowledge_documents
        ORDER BY created_at DESC
        LIMIT 5;
    "

echo -e "\n======================================================================"
echo -e "${GREEN}✓ Setup completed successfully!${NC}"
echo -e "======================================================================"
echo ""
echo "Next steps:"
echo "  - View all documents: docker compose -f docker-compose.dev.yml exec postgres psql -U postgres -d kiosk_db"
echo "  - View logs: docker compose -f docker-compose.dev.yml logs -f postgres"
echo "  - Stop: docker compose -f docker-compose.dev.yml down"
echo "  - Stop and remove data: docker compose -f docker-compose.dev.yml down -v"
echo ""
