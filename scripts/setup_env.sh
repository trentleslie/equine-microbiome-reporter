#!/bin/bash
# Auto-detect environment and set up appropriate configuration

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}=== Equine Microbiome Reporter Environment Setup ===${NC}"
echo

# Check if we're on the actual HippoVet machine
if [ -d "/mnt/c/Users/hippovet/epi2melabs/data/PlusPFP-8" ]; then
    echo -e "${GREEN}✓ HippoVet environment detected${NC}"
    ENV_TYPE="hippovet"
    DB_PATH="/mnt/c/Users/hippovet/epi2melabs/data/PlusPFP-8"

# Check if we have the mock hippovet setup
elif [ -d "/mnt/c/Users/$USER/hippovet/epi2melabs/data/PlusPFP-8" ]; then
    echo -e "${GREEN}✓ Development environment with HippoVet mock setup detected${NC}"
    ENV_TYPE="development"
    DB_PATH="/mnt/c/Users/$USER/hippovet/epi2melabs/data/PlusPFP-8"

# Check if database is being downloaded
elif [ -f "/mnt/c/Users/$USER/hippovet/epi2melabs/data/PlusPFP-8.tar.gz" ]; then
    echo -e "${YELLOW}⚠ Database download in progress...${NC}"
    FILE_SIZE=$(stat -c%s "/mnt/c/Users/$USER/hippovet/epi2melabs/data/PlusPFP-8.tar.gz" 2>/dev/null)
    EXPECTED_SIZE=5516357619  # 5.1GB
    PERCENT=$((FILE_SIZE * 100 / EXPECTED_SIZE))
    echo -e "Progress: ${PERCENT}% complete"
    ENV_TYPE="downloading"

else
    echo -e "${YELLOW}⚠ No Kraken2 database found${NC}"
    ENV_TYPE="mock"
    USE_MOCK=true
fi

# Set up the appropriate .env file
if [ "$ENV_TYPE" = "hippovet" ]; then
    echo "Using HippoVet production configuration"
    cp .env.hippovet .env

elif [ "$ENV_TYPE" = "development" ]; then
    echo "Using development configuration with HippoVet paths"
    # Expand USER variable in the template
    sed "s/\${USER}/$USER/g" .env.development > .env

elif [ "$ENV_TYPE" = "downloading" ]; then
    echo "Using mock mode while database downloads"
    sed "s/\${USER}/$USER/g" .env.development > .env
    echo "USE_MOCK_KRAKEN=true" >> .env

else
    echo "Using mock mode (no database)"
    cp .env.example .env
    echo "USE_MOCK_KRAKEN=true" >> .env
fi

# Verify the setup
echo
echo -e "${BLUE}=== Configuration Summary ===${NC}"
if [ -f .env ]; then
    echo "Database path: $(grep KRAKEN2_DB_PATH .env | cut -d= -f2)"
    echo "Mock mode: $(grep USE_MOCK_KRAKEN .env | cut -d= -f2)"
    echo "Output dir: $(grep DEFAULT_OUTPUT_DIR .env | cut -d= -f2)"
    echo
    echo -e "${GREEN}✓ Environment configured successfully!${NC}"
else
    echo -e "${YELLOW}⚠ Failed to create .env file${NC}"
    exit 1
fi

# Check download status if applicable
if [ "$ENV_TYPE" = "downloading" ]; then
    echo
    echo -e "${YELLOW}Database is downloading in the background.${NC}"
    echo "Check progress with: tail -f /mnt/c/Users/$USER/hippovet/epi2melabs/data/download.log"
    echo "Once complete, run: cd /mnt/c/Users/$USER/hippovet/epi2melabs/data && tar -xzf PlusPFP-8.tar.gz"
fi