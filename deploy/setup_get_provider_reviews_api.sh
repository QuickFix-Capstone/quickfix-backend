#!/usr/bin/env bash
# Setup API Gateway endpoint for get_provider_reviews Lambda with JWT authorizer
# Uses HTTP API (API Gateway v2) - same as existing QuickFixAPI

set -e

FUNC_NAME="get_provider_reviews"
AWS_REGION="us-east-2"
AWS_ACCOUNT_ID="008971679867"
API_ID="kfvf20j7j9"  # Existing HTTP API Gateway ID
AUTHORIZER_ID="z8zn33"  # Existing JWT authorizer for customers/general use

echo "🔍 Using existing API Gateway: ${API_ID}"

# Step 1: Create Lambda integration
echo "🔗 Creating Lambda integration..."

LAMBDA_ARN="arn:aws:lambda:${AWS_REGION}:${AWS_ACCOUNT_ID}:function:${FUNC_NAME}"

INTEGRATION_ID=$(aws apigatewayv2 create-integration \
  --api-id "${API_ID}" \
  --integration-type AWS_PROXY \
  --integration-uri "${LAMBDA_ARN}" \
  --payload-format-version 2.0 \
  --region "${AWS_REGION}" \
  --query 'IntegrationId' \
  --output text)

echo "✅ Created integration: ${INTEGRATION_ID}"

# Step 2: Create route
echo "📝 Creating route: GET /reviews/provider/{provider_id}..."

ROUTE_ID=$(aws apigatewayv2 create-route \
  --api-id "${API_ID}" \
  --route-key "GET /reviews/provider/{provider_id}" \
  --authorization-type JWT \
  --authorizer-id "${AUTHORIZER_ID}" \
  --target "integrations/${INTEGRATION_ID}" \
  --region "${AWS_REGION}" \
  --query 'RouteId' \
  --output text 2>/dev/null || echo "")

if [ -z "$ROUTE_ID" ]; then
  echo "⚠️  Route may already exist, trying to update..."
  
  # Get existing route ID
  ROUTE_ID=$(aws apigatewayv2 get-routes \
    --api-id "${API_ID}" \
    --region "${AWS_REGION}" \
    --query "Items[?RouteKey=='GET /reviews/provider/{provider_id}'].RouteId" \
    --output text)
  
  if [ -n "$ROUTE_ID" ]; then
    # Update existing route
    aws apigatewayv2 update-route \
      --api-id "${API_ID}" \
      --route-id "${ROUTE_ID}" \
      --target "integrations/${INTEGRATION_ID}" \
      --region "${AWS_REGION}"
    echo "✅ Updated existing route: ${ROUTE_ID}"
  fi
else
  echo "✅ Created route: ${ROUTE_ID}"
fi

# Step 3: Add Lambda permission
echo "🔑 Adding Lambda invoke permission..."

aws lambda add-permission \
  --function-name "${FUNC_NAME}" \
  --statement-id "apigatewayv2-invoke-$(date +%s)" \
  --action lambda:InvokeFunction \
  --principal apigateway.amazonaws.com \
  --source-arn "arn:aws:execute-api:${AWS_REGION}:${AWS_ACCOUNT_ID}:${API_ID}/*/*/reviews/provider/*" \
  --region "${AWS_REGION}" 2>/dev/null || echo "⚠️  Permission may already exist"

echo "✅ Lambda permission added"

# Step 4: Deploy to prod stage
echo "🚀 Deploying to prod stage..."

aws apigatewayv2 create-deployment \
  --api-id "${API_ID}" \
  --stage-name prod \
  --region "${AWS_REGION}" > /dev/null

echo "✅ Deployment complete"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ API Gateway setup complete!"
echo ""
echo "📍 API Endpoint:"
echo "   GET https://${API_ID}.execute-api.${AWS_REGION}.amazonaws.com/prod/reviews/provider/{provider_id}"
echo ""
echo "🔐 Authentication:"
echo "   Authorization: Bearer <JWT_TOKEN>"
echo ""
echo "📝 Example cURL requests:"
echo ""
echo "   # Get reviews for SP-001 (default: newest, limit 10)"
echo "   curl -X GET \\"
echo "     'https://${API_ID}.execute-api.${AWS_REGION}.amazonaws.com/prod/reviews/provider/SP-001' \\"
echo "     -H 'Authorization: Bearer YOUR_JWT_TOKEN'"
echo ""
echo "   # Get reviews sorted by highest rating with pagination"
echo "   curl -X GET \\"
echo "     'https://${API_ID}.execute-api.${AWS_REGION}.amazonaws.com/prod/reviews/provider/SP-001?sort=highest_rating&limit=20&offset=0' \\"
echo "     -H 'Authorization: Bearer YOUR_JWT_TOKEN'"
echo ""
echo "💡 Query Parameters:"
echo "   - sort: newest (default), oldest, highest_rating, lowest_rating"
echo "   - limit: 1-100 (default: 10)"
echo "   - offset: pagination offset (default: 0)"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
