#!/usr/bin/env bash
# Setup API Gateway route for PUT /reviews/{review_id}

set -e

API_ID="kfvf20j7j9"
AWS_REGION="us-east-2"
LAMBDA_ARN="arn:aws:lambda:us-east-2:008971679867:function:update_review"
AUTHORIZER_ID="z8zn33"  # QuickFixCustomerAuth JWT authorizer

echo "🚀 Setting up API Gateway route for update_review..."
echo ""
echo "API ID: ${API_ID}"
echo "Lambda: update_review"
echo "Route: PUT /reviews/{review_id}"
echo "Auth: JWT (Authorizer ${AUTHORIZER_ID})"
echo ""

# Step 1: Create integration
echo "📝 Creating Lambda integration..."
INTEGRATION_ID=$(aws apigatewayv2 create-integration \
  --api-id "${API_ID}" \
  --integration-type AWS_PROXY \
  --integration-uri "${LAMBDA_ARN}" \
  --payload-format-version "2.0" \
  --region "${AWS_REGION}" \
  --query 'IntegrationId' \
  --output text)

echo "✅ Integration created: ${INTEGRATION_ID}"

# Step 2: Create route with JWT authorization
echo "📝 Creating route: PUT /reviews/{review_id}..."
ROUTE_ID=$(aws apigatewayv2 create-route \
  --api-id "${API_ID}" \
  --route-key "PUT /reviews/{review_id}" \
  --target "integrations/${INTEGRATION_ID}" \
  --authorization-type JWT \
  --authorizer-id "${AUTHORIZER_ID}" \
  --region "${AWS_REGION}" \
  --query 'RouteId' \
  --output text)

echo "✅ Route created: ${ROUTE_ID}"

# Step 3: Grant API Gateway permission to invoke Lambda
echo "📝 Granting API Gateway permission to invoke Lambda..."
aws lambda add-permission \
  --function-name update_review \
  --statement-id apigateway-update-review-$(date +%s) \
  --action lambda:InvokeFunction \
  --principal apigateway.amazonaws.com \
  --source-arn "arn:aws:execute-api:${AWS_REGION}:008971679867:${API_ID}/*/*/reviews/*" \
  --region "${AWS_REGION}" 2>/dev/null || echo "Permission may already exist"

# Step 4: Deploy to prod stage
echo "📝 Deploying to prod stage..."
aws apigatewayv2 create-deployment \
  --api-id "${API_ID}" \
  --stage-name prod \
  --region "${AWS_REGION}" > /dev/null

echo ""
echo "✅ API Gateway setup complete!"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📋 Endpoint Details"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Endpoint URL:"
echo "  PUT https://${API_ID}.execute-api.${AWS_REGION}.amazonaws.com/prod/reviews/{review_id}"
echo ""
echo "Authorization: JWT (required)"
echo "  Header: Authorization: Bearer <JWT_TOKEN>"
echo ""
echo "Integration: ${INTEGRATION_ID}"
echo "Route: ${ROUTE_ID}"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
