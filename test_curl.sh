#!/bin/bash
# Sample cURL commands for testing the STEP API

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

API_URL="http://localhost:8000"

echo -e "${GREEN}STEP File Analysis API - Test Commands${NC}"
echo "========================================"
echo ""

# Check if STEP file is provided
if [ -z "$1" ]; then
    echo -e "${YELLOW}Usage: ./test_curl.sh <path_to_step_file>${NC}"
    echo ""
    echo "Example:"
    echo "  ./test_curl.sh sample.step"
    echo ""
    echo "Without a STEP file, only health check will run."
    echo ""
fi

# Health Check
echo -e "${GREEN}1. Health Check${NC}"
echo "curl $API_URL/health"
curl -s $API_URL/health | json_pp
echo ""
echo ""

if [ ! -z "$1" ]; then
    if [ ! -f "$1" ]; then
        echo -e "${RED}Error: File '$1' not found${NC}"
        exit 1
    fi
    
    STEP_FILE="$1"
    
    # Full Analysis
    echo -e "${GREEN}2. Full Analysis${NC}"
    echo "curl -X POST -F \"file=@$STEP_FILE\" $API_URL/analyze"
    curl -s -X POST -F "file=@$STEP_FILE" $API_URL/analyze | json_pp
    echo ""
    echo ""
    
    # Geometry Only
    echo -e "${GREEN}3. Geometry Analysis${NC}"
    echo "curl -X POST -F \"file=@$STEP_FILE\" $API_URL/analyze/geometry"
    curl -s -X POST -F "file=@$STEP_FILE" $API_URL/analyze/geometry | json_pp
    echo ""
    echo ""
    
    # Topology Only
    echo -e "${GREEN}4. Topology Analysis${NC}"
    echo "curl -X POST -F \"file=@$STEP_FILE\" $API_URL/analyze/topology"
    curl -s -X POST -F "file=@$STEP_FILE" $API_URL/analyze/topology | json_pp
    echo ""
    echo ""
    
    # Validation
    echo -e "${GREEN}5. File Validation${NC}"
    echo "curl -X POST -F \"file=@$STEP_FILE\" $API_URL/validate"
    curl -s -X POST -F "file=@$STEP_FILE" $API_URL/validate | json_pp
    echo ""
fi

echo -e "${GREEN}Testing complete!${NC}"
