#!/usr/bin/env bash
# Test the update_review API endpoint with JWT authentication

set -e

API_URL="https://kfvf20j7j9.execute-api.us-east-2.amazonaws.com/prod/reviews"
JWT_TOKEN_FILE="/tmp/jwt_token.txt"

# Check if JWT token exists
if [ ! -f "$JWT_TOKEN_FILE" ]; then
  echo "❌ JWT token not found. Please run: ./scripts/get_jwt_token.sh"
  exit 1
fi

JWT_TOKEN=$(cat "$JWT_TOKEN_FILE")

echo "🧪 Testing PUT /reviews/{review_id} endpoint"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Test 1: Update rating and comment
echo "📋 Test 1: Update review #5 (rating + comment)"
echo "─────────────────────────────────────────────────────────────"
curl -X PUT "${API_URL}/5" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${JWT_TOKEN}" \
  -d '{
    "rating": 3,
    "comment": "Testing API Gateway endpoint - updated rating to 3 stars via HTTP API"
  }' | python3 -m json.tool

echo ""
echo ""

# Test 2: Update comment only
echo "📋 Test 2: Update comment only"
echo "─────────────────────────────────────────────────────────────"
curl -X PUT "${API_URL}/5" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${JWT_TOKEN}" \
  -d '{
    "comment": "Updated via API Gateway: The service was good but took longer than expected."
  }' | python3 -m json.tool

echo ""
echo ""

# Test 3: Update both fields
echo "📋 Test 3: Update both rating and comment"
echo "─────────────────────────────────────────────────────────────"
curl -X PUT "${API_URL}/5" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${JWT_TOKEN}" \
  -d '{
    "rating": 4,
    "comment": "Final test: Actually the service was quite good. Professional plumber who fixed the issue."
  }' | python3 -m json.tool

echo ""
echo ""

# Test 4: Invalid rating (should fail)
echo "📋 Test 4: Invalid rating (should return 400)"
echo "─────────────────────────────────────────────────────────────"
curl -X PUT "${API_URL}/5" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${JWT_TOKEN}" \
  -d '{
    "rating": 6
  }' | python3 -m json.tool

echo ""
echo ""

# Test 5: Non-existent review (should fail)
echo "📋 Test 5: Non-existent review (should return 404)"
echo "─────────────────────────────────────────────────────────────"
curl -X PUT "${API_URL}/99999" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${JWT_TOKEN}" \
  -d '{
    "rating": 4
  }' | python3 -m json.tool

echo ""
echo ""

# Test 6: No authorization header (should fail)
echo "📋 Test 6: No JWT token (should return 401)"
echo "─────────────────────────────────────────────────────────────"
curl -X PUT "${API_URL}/5" \
  -H "Content-Type: application/json" \
  -d '{
    "rating": 4
  }' | python3 -m json.tool

echo ""
echo ""

# Restore original review
echo "📋 Restoring original review data..."
echo "─────────────────────────────────────────────────────────────"
curl -X PUT "${API_URL}/5" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${JWT_TOKEN}" \
  -d '{
    "rating": 5,
    "comment": "Excellent plumbing service! Very professional and fixed my leak quickly."
  }' | python3 -m json.tool

echo ""
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ API Gateway testing complete!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
