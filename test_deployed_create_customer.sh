#!/bin/bash
# Test script for create_customer Lambda with Cognito group assignment
# This script tests the deployed Lambda function with a mock customer registration

set -e

echo "=========================================="
echo "Testing create_customer Lambda Function"
echo "=========================================="
echo ""

# Get a fresh customer token (you'll need to authenticate first)
echo "📝 Step 1: Get a customer JWT token"
echo "Run this command to get a token:"
echo "  ./get_customer_token.sh"
echo ""
echo "Or manually login and get token from browser localStorage"
echo ""

# Read token from user
read -p "Paste your JWT token here: " JWT_TOKEN

if [ -z "$JWT_TOKEN" ]; then
    echo "❌ No token provided. Exiting."
    exit 1
fi

# Generate unique email for testing
TIMESTAMP=$(date +%s)
TEST_EMAIL="test-customer-${TIMESTAMP}@example.com"

echo ""
echo "📧 Test email: $TEST_EMAIL"
echo ""

# Create test payload
TEST_PAYLOAD=$(cat <<EOF
{
  "first_name": "Test",
  "last_name": "Customer",
  "email": "$TEST_EMAIL",
  "phone": "416-555-${TIMESTAMP:(-4)}",
  "address": "123 Test Street",
  "city": "Toronto",
  "state": "ON",
  "postal_code": "M5H 1J9"
}
EOF
)

echo "🚀 Step 2: Invoking Lambda function..."
echo ""

# Invoke Lambda with Authorization header
aws lambda invoke \
  --function-name create_customer \
  --region us-east-2 \
  --cli-binary-format raw-in-base64-out \
  --payload "{
    \"headers\": {
      \"Authorization\": \"Bearer $JWT_TOKEN\"
    },
    \"body\": $(echo "$TEST_PAYLOAD" | jq -c .)
  }" \
  response.json

echo ""
echo "📄 Response:"
cat response.json | jq .
echo ""

# Check CloudWatch logs
echo "📊 Step 3: Checking CloudWatch logs..."
echo ""
aws logs tail /aws/lambda/create_customer --since 1m --region us-east-2 | grep -E "(Successfully added|Failed to add|Could not extract)" || echo "No Cognito group assignment logs found yet"

echo ""
echo "=========================================="
echo "✅ Test Complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Check AWS Console → Cognito → Users → Find: $TEST_EMAIL"
echo "2. Verify user is in 'customer' group"
echo "3. Check full logs: aws logs tail /aws/lambda/create_customer --follow --region us-east-2"
echo ""
