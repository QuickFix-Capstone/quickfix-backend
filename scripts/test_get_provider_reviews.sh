#!/usr/bin/env bash
# Test get_provider_reviews endpoint
# Usage: ./test_get_provider_reviews.sh [provider_id] [sort] [limit] [offset]

set -e

API_ENDPOINT="https://kfvf20j7j9.execute-api.us-east-2.amazonaws.com/prod/reviews/provider"

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
PROVIDER_ID="${1:-SP-001}"
SORT="${2:-highest_rating}"
LIMIT="${3:-10}"
OFFSET="${4:-0}"

# Build query string
QUERY_STRING="?sort=${SORT}&limit=${LIMIT}&offset=${OFFSET}"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🧪 Testing GET /reviews/provider/{provider_id}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Provider ID: ${PROVIDER_ID}"
echo "Sort:        ${SORT}"
echo "Limit:       ${LIMIT}"
echo "Offset:      ${OFFSET}"
echo "Endpoint:    ${API_ENDPOINT}/${PROVIDER_ID}${QUERY_STRING}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Make the request
echo "📤 Sending request..."
RESPONSE=$(curl -s -w "\n%{http_code}" -X GET "${API_ENDPOINT}/${PROVIDER_ID}${QUERY_STRING}" \
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
  TOTAL_REVIEWS=$(echo "${BODY}" | jq -r '.summary.total_reviews' 2>/dev/null || echo "N/A")
  AVG_RATING=$(echo "${BODY}" | jq -r '.summary.average_rating' 2>/dev/null || echo "N/A")
  
  echo ""
  echo "📊 Summary:"
  echo "   Total Reviews: ${TOTAL_REVIEWS}"
  echo "   Average Rating: ${AVG_RATING}"
  
elif [ "$HTTP_CODE" = "401" ]; then
  echo "❌ Authentication failed - Token may be expired"
  echo "💡 Run: ./scripts/get_jwt_token.sh"
elif [ "$HTTP_CODE" = "404" ]; then
  echo "❌ Provider not found"
elif [ "$HTTP_CODE" = "400" ]; then
  echo "❌ Bad request - Check parameters"
else
  echo "⚠️  Request failed with status ${HTTP_CODE}"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "💡 Usage examples:"
echo "   ./scripts/test_get_provider_reviews.sh SP-001"
echo "   ./scripts/test_get_provider_reviews.sh SP-001 newest 20 0"
echo "   ./scripts/test_get_provider_reviews.sh SP-002 lowest_rating 5 0"
echo ""
echo "💡 Sort options: newest, oldest, highest_rating, lowest_rating"
echo ""
