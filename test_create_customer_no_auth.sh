#!/bin/bash
# Simple test without requiring a real JWT token
# Tests the Lambda function with a mock event

set -e

echo "=========================================="
echo "Testing create_customer (No Auth Test)"
echo "=========================================="
echo ""

# Generate unique email
TIMESTAMP=$(date +%s)
TEST_EMAIL="test-noauth-${TIMESTAMP}@example.com"

echo "📧 Test email: $TEST_EMAIL"
echo "⚠️  Note: This test won't include JWT, so group assignment will be skipped"
echo ""

# Create test payload without Authorization header
TEST_PAYLOAD=$(cat <<EOF
{
  "body": "{\"first_name\":\"NoAuth\",\"last_name\":\"Test\",\"email\":\"$TEST_EMAIL\",\"phone\":\"416-555-0000\",\"address\":\"123 Test St\",\"city\":\"Toronto\",\"state\":\"ON\",\"postal_code\":\"M5H 1J9\"}"
}
EOF
)

echo "🚀 Invoking Lambda function..."
echo ""

aws lambda invoke \
  --function-name create_customer \
  --region us-east-2 \
  --cli-binary-format raw-in-base64-out \
  --payload "$TEST_PAYLOAD" \
  response_noauth.json

echo ""
echo "📄 Response:"
cat response_noauth.json | jq .
echo ""

echo "📊 Checking CloudWatch logs..."
echo ""
aws logs tail /aws/lambda/create_customer --since 1m --region us-east-2 | tail -20

echo ""
echo "=========================================="
echo "✅ Test Complete!"
echo ""
echo "Expected behavior:"
echo "  - Customer created successfully (201)"
echo "  - Log shows: '⚠️ Could not extract email from JWT, skipping group assignment'"
echo "  - User NOT added to Cognito group (no JWT provided)"
echo "=========================================="
