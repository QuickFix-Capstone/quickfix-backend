#!/usr/bin/env bash
# Test update_ratings endpoint with JWT authentication
# Usage: ./test_update_ratings.sh [provider|customer] [id]

set -e

API_ENDPOINT="https://kfvf20j7j9.execute-api.us-east-2.amazonaws.com/prod/internal/update-ratings"

# Get JWT token
echo "🔐 Getting JWT token..."
JWT_TOKEN=$(cat /tmp/jwt_token.txt 2>/dev/null || echo "")

if [ -z "$JWT_TOKEN" ]; then
  echo "⚠️  No token found. Running get_jwt_token.sh first..."
  ./scripts/get_jwt_token.sh
  JWT_TOKEN=$(cat /tmp/jwt_token.txt)
fi

echo "✅ Token loaded"
echo ""

# Parse arguments
REVIEWEE_TYPE="${1:-provider}"
REVIEWEE_ID="${2}"

# Auto-detect ID if not provided
if [ -z "$REVIEWEE_ID" ]; then
  if [ "$REVIEWEE_TYPE" = "provider" ]; then
    REVIEWEE_ID="google-oauth2|103949366066974158596"
    echo "ℹ️  Using default provider ID: ${REVIEWEE_ID}"
  else
    REVIEWEE_ID="1"
    echo "ℹ️  Using default customer ID: ${REVIEWEE_ID}"
  fi
fi

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🧪 Testing update_ratings endpoint"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Reviewee Type: ${REVIEWEE_TYPE}"
echo "Reviewee ID:   ${REVIEWEE_ID}"
echo "Endpoint:      ${API_ENDPOINT}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Make the request
echo "📤 Sending request..."
RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "${API_ENDPOINT}" \
  -H "Authorization: Bearer ${JWT_TOKEN}" \
  -H "Content-Type: application/json" \
  -d "{
    \"reviewee_id\": \"${REVIEWEE_ID}\",
    \"reviewee_type\": \"${REVIEWEE_TYPE}\"
  }")

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
  echo "✅ Rating updated successfully!"
elif [ "$HTTP_CODE" = "401" ]; then
  echo "❌ Authentication failed - Token may be expired"
  echo "💡 Run: ./scripts/get_jwt_token.sh"
elif [ "$HTTP_CODE" = "403" ]; then
  echo "❌ Forbidden - Check JWT authorizer configuration"
else
  echo "⚠️  Request failed with status ${HTTP_CODE}"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "💡 Usage examples:"
echo "   ./scripts/test_update_ratings.sh provider google-oauth2|103949366066974158596"
echo "   ./scripts/test_update_ratings.sh customer 1"
echo ""
