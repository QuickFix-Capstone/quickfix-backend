#!/usr/bin/env bash
# Test get_customer_reviews endpoint with JWT authentication
# Usage: ./test_get_customer_reviews.sh [customer_id] [sort] [limit] [offset]

set -e

API_ENDPOINT="https://kfvf20j7j9.execute-api.us-east-2.amazonaws.com/prod/reviews/customer"

# Get JWT token
echo "🔐 Getting JWT token..."
JWT_TOKEN=$(cat /tmp/jwt_token.txt 2>/dev/null || echo "")

if [ -z "$JWT_TOKEN" ]; then
  echo "⚠️  No token found. Running get_jwt_token.sh first..."
  ./scripts/get_jwt_token.sh > /dev/null 2>&1
  JWT_TOKEN=$(cat /tmp/jwt_token.txt)
fi

echo "✅ Token loaded"
echo ""

# Parse arguments
CUSTOMER_ID="${1:-2}"
SORT="${2:-highest_rating}"
LIMIT="${3:-10}"
OFFSET="${4:-0}"

# Build query string
QUERY_STRING="?sort=${SORT}&limit=${LIMIT}&offset=${OFFSET}"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🧪 Testing GET /reviews/customer/{customer_id}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Customer ID: ${CUSTOMER_ID}"
echo "Sort:        ${SORT}"
echo "Limit:       ${LIMIT}"
echo "Offset:      ${OFFSET}"
echo "Endpoint:    ${API_ENDPOINT}/${CUSTOMER_ID}${QUERY_STRING}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Make the request
echo "📤 Sending request..."
RESPONSE=$(curl -s -w "\n%{http_code}" -X GET "${API_ENDPOINT}/${CUSTOMER_ID}${QUERY_STRING}" \
  -H "Authorization: Bearer ${JWT_TOKEN}" \
  -H "Content-Type: application/json")

# Parse response
HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
BODY=$(echo "$RESPONSE" | sed '$d')

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📥 Response"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "HTTP Status: ${HTTP_CODE}"
echo ""
echo "${BODY}" | jq '.' 2>/dev/null || echo "${BODY}"
echo ""

# Check status
if [ "$HTTP_CODE" = "200" ]; then
  echo "✅ Request successful!"
  
  # Extract summary info
  CUSTOMER_NAME=$(echo "${BODY}" | jq -r '.summary.customer_name' 2>/dev/null || echo "N/A")
  TOTAL_REVIEWS=$(echo "${BODY}" | jq -r '.summary.total_reviews' 2>/dev/null || echo "N/A")
  AVG_RATING=$(echo "${BODY}" | jq -r '.summary.average_rating' 2>/dev/null || echo "N/A")
  
  echo ""
  echo "📊 Summary:"
  echo "   Customer: ${CUSTOMER_NAME}"
  echo "   Total Reviews: ${TOTAL_REVIEWS}"
  echo "   Average Rating: ${AVG_RATING}⭐"
  
elif [ "$HTTP_CODE" = "401" ]; then
  echo "❌ Authentication failed - Token may be expired"
  echo "💡 Run: ./scripts/get_jwt_token.sh"
elif [ "$HTTP_CODE" = "404" ]; then
  echo "❌ Customer not found"
elif [ "$HTTP_CODE" = "400" ]; then
  echo "❌ Bad request - Check parameters"
else
  echo "⚠️  Request failed with status ${HTTP_CODE}"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "💡 Usage examples:"
echo "   ./scripts/test_get_customer_reviews.sh 2"
echo "   ./scripts/test_get_customer_reviews.sh 1 newest 20 0"
echo "   ./scripts/test_get_customer_reviews.sh 3 lowest_rating 5 0"
echo ""
echo "💡 Sort options: newest, oldest, highest_rating, lowest_rating"
echo ""
