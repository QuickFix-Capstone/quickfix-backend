#!/bin/bash

# Test script for GET /customer/reviews-about-me endpoint

set -e

echo "=================================================="
echo "Testing GET /customer/reviews-about-me"
echo "=================================================="

# Get customer JWT token
echo "🔑 Getting customer JWT token..."
./get_customer_token.sh > /dev/null
if [ -f "/tmp/customer_jwt_token.txt" ]; then
    TOKEN=$(cat /tmp/customer_jwt_token.txt)
else
    echo "❌ Failed to get customer token file: /tmp/customer_jwt_token.txt"
    exit 1
fi

echo "✅ Token obtained"
echo ""

# API endpoint
API_URL="https://kfvf20j7j9.execute-api.us-east-2.amazonaws.com/prod/customer/reviews-about-me"

# Test 1: Get all reviews about me (default pagination)
echo "=================================================="
echo "Test 1: Get all reviews about me (default)"
echo "=================================================="
RESPONSE=$(curl -s -X GET "$API_URL" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -w "\n%{http_code}")
BODY=$(echo "$RESPONSE" | sed '$d')
STATUS=$(echo "$RESPONSE" | tail -n1)
echo "$BODY" | jq '.' 2>/dev/null || echo "$BODY"
echo ""
echo "HTTP Status: $STATUS"

echo ""
echo ""

# Test 2: Get reviews with custom limit
echo "=================================================="
echo "Test 2: Get reviews with limit=5"
echo "=================================================="
RESPONSE=$(curl -s -X GET "${API_URL}?limit=5" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -w "\n%{http_code}")
BODY=$(echo "$RESPONSE" | sed '$d')
STATUS=$(echo "$RESPONSE" | tail -n1)
echo "$BODY" | jq '.' 2>/dev/null || echo "$BODY"
echo ""
echo "HTTP Status: $STATUS"

echo ""
echo ""

# Test 3: Get reviews sorted by highest rating
echo "=================================================="
echo "Test 3: Get reviews sorted by highest rating"
echo "=================================================="
RESPONSE=$(curl -s -X GET "${API_URL}?sort=highest_rating&limit=10" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -w "\n%{http_code}")
BODY=$(echo "$RESPONSE" | sed '$d')
STATUS=$(echo "$RESPONSE" | tail -n1)
echo "$BODY" | jq '.' 2>/dev/null || echo "$BODY"
echo ""
echo "HTTP Status: $STATUS"

echo ""
echo ""

# Test 4: Get reviews sorted by oldest
echo "=================================================="
echo "Test 4: Get reviews sorted by oldest"
echo "=================================================="
RESPONSE=$(curl -s -X GET "${API_URL}?sort=oldest&limit=10" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -w "\n%{http_code}")
BODY=$(echo "$RESPONSE" | sed '$d')
STATUS=$(echo "$RESPONSE" | tail -n1)
echo "$BODY" | jq '.' 2>/dev/null || echo "$BODY"
echo ""
echo "HTTP Status: $STATUS"

echo ""
echo ""

# Test 5: Test pagination
echo "=================================================="
echo "Test 5: Test pagination (offset=5, limit=3)"
echo "=================================================="
RESPONSE=$(curl -s -X GET "${API_URL}?offset=5&limit=3" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -w "\n%{http_code}")
BODY=$(echo "$RESPONSE" | sed '$d')
STATUS=$(echo "$RESPONSE" | tail -n1)
echo "$BODY" | jq '.' 2>/dev/null || echo "$BODY"
echo ""
echo "HTTP Status: $STATUS"

echo ""
echo "=================================================="
echo "✅ All tests completed!"
echo "=================================================="
