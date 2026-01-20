#!/usr/bin/env bash
# Update API Gateway routes to separate customer and provider review endpoints

set -e

API_ID="kfvf20j7j9"
AWS_REGION="us-east-2"

echo "🔍 Current routes for reviews..."
aws apigatewayv2 get-routes \
  --api-id "${API_ID}" \
  --region "${AWS_REGION}" \
  --query 'Items[?contains(RouteKey, `review`)].{RouteKey: RouteKey, RouteId: RouteId}' \
  --output table

echo ""
echo "📝 Step 1: Update POST /reviews to POST /customer/reviews"

# Get the current POST /reviews route
ROUTE_ID=$(aws apigatewayv2 get-routes \
  --api-id "${API_ID}" \
  --region "${AWS_REGION}" \
  --query "Items[?RouteKey=='POST /reviews'].RouteId" \
  --output text)

if [ -n "$ROUTE_ID" ]; then
  echo "Found route ID: ${ROUTE_ID}"
  echo "Updating route key to POST /customer/reviews..."
  
  aws apigatewayv2 update-route \
    --api-id "${API_ID}" \
    --route-id "${ROUTE_ID}" \
    --route-key "POST /customer/reviews" \
    --region "${AWS_REGION}"
  
  echo "✅ Updated route to POST /customer/reviews"
else
  echo "❌ POST /reviews route not found"
fi

echo ""
echo "✅ Route update complete!"
echo ""
echo "Updated routes:"
aws apigatewayv2 get-routes \
  --api-id "${API_ID}" \
  --region "${AWS_REGION}" \
  --query 'Items[?contains(RouteKey, `review`)].{RouteKey: RouteKey, RouteId: RouteId}' \
  --output table
