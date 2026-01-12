#!/usr/bin/env bash
# Setup API Gateway endpoint for get_customer_reviews Lambda WITHOUT JWT authorizer
# User will configure JWT manually later

set -e

FUNC_NAME="get_customer_reviews"
AWS_REGION="us-east-2"
AWS_ACCOUNT_ID="008971679867"
API_ID="kfvf20j7j9"  # Existing HTTP API Gateway ID

echo "🔍 Using existing API Gateway: ${API_ID}"
echo "⚠️  Note: JWT authorization NOT configured - you'll set this up manually"

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

# Step 2: Create route WITHOUT authorization
echo "📝 Creating route: GET /reviews/customer/{customer_id} (NO JWT)..."

ROUTE_ID=$(aws apigatewayv2 create-route \
  --api-id "${API_ID}" \
  --route-key "GET /reviews/customer/{customer_id}" \
  --authorization-type NONE \
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
    --query "Items[?RouteKey=='GET /reviews/customer/{customer_id}'].RouteId" \
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
  --source-arn "arn:aws:execute-api:${AWS_REGION}:${AWS_ACCOUNT_ID}:${API_ID}/*/*/reviews/customer/*" \
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
echo "✅ API Gateway setup complete (WITHOUT JWT)!"
echo ""
echo "📍 API Endpoint:"
echo "   GET https://${API_ID}.execute-api.${AWS_REGION}.amazonaws.com/prod/reviews/customer/{customer_id}"
echo ""
echo "⚠️  IMPORTANT: JWT Authorization NOT configured"
echo "   You need to manually add JWT authorizer to this route"
echo ""
echo "📝 To add JWT authorization manually:"
echo "   1. Go to API Gateway console"
echo "   2. Select route: GET /reviews/customer/{customer_id}"
echo "   3. Route ID: ${ROUTE_ID}"
echo "   4. Set Authorization: JWT"
echo "   5. Select Authorizer: QuickFixCustomerAuth (z8zn33)"
echo "   6. Deploy to prod stage"
echo ""
echo "📝 Or use AWS CLI:"
echo "   aws apigatewayv2 update-route \\"
echo "     --api-id ${API_ID} \\"
echo "     --route-id ${ROUTE_ID} \\"
echo "     --authorization-type JWT \\"
echo "     --authorizer-id z8zn33 \\"
echo "     --region ${AWS_REGION}"
echo ""
echo "   aws apigatewayv2 create-deployment \\"
echo "     --api-id ${API_ID} \\"
echo "     --stage-name prod \\"
echo "     --region ${AWS_REGION}"
echo ""
echo "📝 Test without auth (for now):"
echo "   curl -X GET \\"
echo "     'https://${API_ID}.execute-api.${AWS_REGION}.amazonaws.com/prod/reviews/customer/2'"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
