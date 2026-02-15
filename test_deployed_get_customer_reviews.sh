#!/bin/bash

# Test the deployed GET /customer/reviews endpoint
# This endpoint requires JWT authentication

API_URL="https://kfvf20j7j9.execute-api.us-east-2.amazonaws.com/prod/customer/reviews"

echo "=========================================="
echo "Testing GET /customer/reviews (Deployed)"
echo "=========================================="
echo ""
echo "API URL: $API_URL"
echo ""

# Check if JWT token file exists
if [ -f "/tmp/customer_jwt_token.txt" ]; then
    JWT_TOKEN=$(cat /tmp/customer_jwt_token.txt)
    echo "✅ Found JWT token"
else
    echo "⚠️  No JWT token found at /tmp/customer_jwt_token.txt"
    echo ""
    echo "To get a JWT token, run:"
    echo "  ./get_customer_token.sh"
    echo ""
    echo "Testing without authentication (will fail with 401)..."
    JWT_TOKEN=""
fi

echo ""
echo "=========================================="
echo "Test 1: GET reviews (default params)"
echo "=========================================="
if [ -n "$JWT_TOKEN" ]; then
    curl -X GET "$API_URL" \
      -H "Authorization: Bearer $JWT_TOKEN" \
      -H "Content-Type: application/json" \
      -w "\n\nHTTP Status: %{http_code}\n" \
      -s | jq '.'
else
    curl -X GET "$API_URL" \
      -H "Content-Type: application/json" \
      -w "\n\nHTTP Status: %{http_code}\n" \
      -s | jq '.'
fi

echo ""
echo "=========================================="
echo "Test 2: GET reviews with sorting"
echo "=========================================="
if [ -n "$JWT_TOKEN" ]; then
    curl -X GET "$API_URL?sort=highest_rating&limit=5" \
      -H "Authorization: Bearer $JWT_TOKEN" \
      -H "Content-Type: application/json" \
      -w "\n\nHTTP Status: %{http_code}\n" \
      -s | jq '.'
else
    echo "Skipped (no JWT token)"
fi

echo ""
echo "=========================================="
echo "Test 3: GET reviews with pagination"
echo "=========================================="
if [ -n "$JWT_TOKEN" ]; then
    curl -X GET "$API_URL?limit=1&offset=0" \
      -H "Authorization: Bearer $JWT_TOKEN" \
      -H "Content-Type: application/json" \
      -w "\n\nHTTP Status: %{http_code}\n" \
      -s | jq '.'
else
    echo "Skipped (no JWT token)"
fi

echo ""
echo "=========================================="
echo "✅ Testing complete!"
echo "=========================================="
