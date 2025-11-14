#!/bin/bash

#
# Load Testing Script for District Marketplace
#
# This script runs various load test scenarios and generates reports
#

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}District Marketplace Load Tests${NC}"
echo -e "${BLUE}========================================${NC}\n"

# Create results directory
RESULTS_DIR="load_tests/results"
mkdir -p "$RESULTS_DIR"

# Check if USE_MOCK_AI is set
if [ -z "$USE_MOCK_AI" ]; then
    echo -e "${YELLOW}Warning: USE_MOCK_AI not set. Using real AI (may be slow and costly)${NC}"
    echo -e "${YELLOW}Recommend: export USE_MOCK_AI=True${NC}\n"
else
    echo -e "${GREEN}Using Mock AI: $USE_MOCK_AI${NC}\n"
fi

# Test 1: Light Load (Warmup)
echo -e "${BLUE}Test 1: Light Load (10 users, 30 seconds)${NC}"
echo "Testing system warmup and basic functionality..."
locust -f load_tests/locustfile.py \
    --host=http://localhost:8000 \
    --users 10 \
    --spawn-rate 2 \
    --run-time 30s \
    --headless \
    --html="$RESULTS_DIR/light_load_report.html" \
    --csv="$RESULTS_DIR/light_load"

echo -e "${GREEN}✓ Light load test complete${NC}\n"
sleep 2

# Test 2: Medium Load (Concurrent Users)
echo -e "${BLUE}Test 2: Medium Load (50 users, 60 seconds)${NC}"
echo "Testing concurrent user handling..."
locust -f load_tests/locustfile.py \
    --host=http://localhost:8000 \
    --users 50 \
    --spawn-rate 5 \
    --run-time 60s \
    --headless \
    --html="$RESULTS_DIR/medium_load_report.html" \
    --csv="$RESULTS_DIR/medium_load"

echo -e "${GREEN}✓ Medium load test complete${NC}\n"
sleep 2

# Test 3: Heavy Load (Stress Test)
echo -e "${BLUE}Test 3: Heavy Load (100 users, 90 seconds)${NC}"
echo "Testing system under stress..."
locust -f load_tests/locustfile.py \
    --host=http://localhost:8000 \
    --users 100 \
    --spawn-rate 10 \
    --run-time 90s \
    --headless \
    --html="$RESULTS_DIR/heavy_load_report.html" \
    --csv="$RESULTS_DIR/heavy_load"

echo -e "${GREEN}✓ Heavy load test complete${NC}\n"
sleep 2

# Test 4: Spike Test (Rapid Increase)
echo -e "${BLUE}Test 4: Spike Test (0→200 users in 10s, hold 30s)${NC}"
echo "Testing rapid traffic spike handling..."
locust -f load_tests/locustfile.py \
    --host=http://localhost:8000 \
    --users 200 \
    --spawn-rate 20 \
    --run-time 40s \
    --headless \
    --html="$RESULTS_DIR/spike_test_report.html" \
    --csv="$RESULTS_DIR/spike_test"

echo -e "${GREEN}✓ Spike test complete${NC}\n"

# Test 5: Seller-Heavy Workload
echo -e "${BLUE}Test 5: Seller-Heavy (100 sellers listing products, 60s)${NC}"
echo "Testing product creation load..."
locust -f load_tests/locustfile.py \
    --host=http://localhost:8000 \
    --users 100 \
    --spawn-rate 10 \
    --run-time 60s \
    --headless \
    --html="$RESULTS_DIR/seller_load_report.html" \
    --csv="$RESULTS_DIR/seller_load" \
    --class-picker \
    SellerUser

echo -e "${GREEN}✓ Seller load test complete${NC}\n"

# Test 6: Buyer-Heavy Workload
echo -e "${BLUE}Test 6: Buyer-Heavy (100 buyers searching, 60s)${NC}"
echo "Testing search load..."
locust -f load_tests/locustfile.py \
    --host=http://localhost:8000 \
    --users 100 \
    --spawn-rate 10 \
    --run-time 60s \
    --headless \
    --html="$RESULTS_DIR/buyer_load_report.html" \
    --csv="$RESULTS_DIR/buyer_load" \
    --class-picker \
    BuyerUser

echo -e "${GREEN}✓ Buyer load test complete${NC}\n"

# Summary
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}All Load Tests Complete!${NC}"
echo -e "${BLUE}========================================${NC}\n"

echo -e "Reports generated in: ${GREEN}$RESULTS_DIR/${NC}"
echo -e "  - light_load_report.html"
echo -e "  - medium_load_report.html"
echo -e "  - heavy_load_report.html"
echo -e "  - spike_test_report.html"
echo -e "  - seller_load_report.html"
echo -e "  - buyer_load_report.html"

echo -e "\nCSV files also available for analysis:"
ls -lh "$RESULTS_DIR"/*.csv | awk '{print "  - " $9}'

echo -e "\n${GREEN}Done!${NC}\n"
