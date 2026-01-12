#!/usr/bin/env bash
# Fix JWT authorization for update_ratings endpoint
# This script ensures the JWT authorizer is properly configured

set -e

API_ID="kfvf20j7j9"
AWS_REGION="us-east-2"
AUTHORIZER_ID="z8zn33"

echo "🔧 Fixing JWT authorization for update_ratings endpoint..."
echo ""

# Get the route ID
ROUTE_ID=$(aws apigatewayv2 get-routes \
  --api-id "${API_ID}" \
  --region "${AWS_REGION}" \
  --query "Items[?RouteKey=='POST /internal/update-ratings'].RouteId" \
  --output text)

if [ -z "$ROUTE_ID" ]; then
  echo "❌ Route not found: POST /internal/update-ratings"
  exit 1
fi

echo "✅ Found route: ${ROUTE_ID}"
echo ""

# Update the route to ensure JWT authorization is properly set
echo "🔄 Updating route with JWT authorization..."
aws apigatewayv2 update-route \
  --api-id "${API_ID}" \
  --route-id "${ROUTE_ID}" \
  --authorization-type JWT \
  --authorizer-id "${AUTHORIZER_ID}" \
  --region "${AWS_REGION}" > /dev/null

echo "✅ Route updated with JWT authorizer"
echo ""

# Deploy to prod stage
echo "🚀 Deploying changes to prod stage..."
aws apigatewayv2 create-deployment \
  --api-id "${API_ID}" \
  --stage-name prod \
  --region "${AWS_REGION}" > /dev/null

echo "✅ Deployment complete"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ JWT authorization fixed!"
echo ""
echo "Test the endpoint with:"
echo "  ./scripts/test_update_ratings.sh provider"
echo ""
