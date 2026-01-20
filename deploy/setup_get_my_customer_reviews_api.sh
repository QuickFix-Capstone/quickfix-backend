#!/usr/bin/env bash
# Setup API Gateway HTTP API v2 endpoint for get_my_customer_reviews Lambda

set -e

FUNC_NAME="get_my_customer_reviews"
AWS_REGION="us-east-2"
AWS_ACCOUNT_ID="008971679867"
API_ID="kfvf20j7j9"

echo "🔍 Checking API Gateway HTTP API..."

# Verify API exists
API_NAME=$(aws apigatewayv2 get-api \
  --api-id "${API_ID}" \
  --region "${AWS_REGION}" \
  --query 'Name' \
  --output text 2>/dev/null || echo "")

if [ -z "$API_NAME" ]; then
  echo "❌ API Gateway not found"
  exit 1
fi

echo "✅ Found API: ${API_NAME} (${API_ID})"

# Get or create integration
echo "🔗 Setting up Lambda integration..."

LAMBDA_ARN="arn:aws:lambda:${AWS_REGION}:${AWS_ACCOUNT_ID}:function:${FUNC_NAME}"

# Check if integration exists for this Lambda
INTEGRATION_ID=$(aws apigatewayv2 get-integrations \
  --api-id "${API_ID}" \
  --region "${AWS_REGION}" \
  --query "Items[?IntegrationUri=='${LAMBDA_ARN}'].IntegrationId" \
  --output text 2>/dev/null || echo "")

if [ -z "$INTEGRATION_ID" ]; then
  echo "📝 Creating new integration..."
  INTEGRATION_ID=$(aws apigatewayv2 create-integration \
    --api-id "${API_ID}" \
    --integration-type AWS_PROXY \
    --integration-uri "${LAMBDA_ARN}" \
    --payload-format-version "2.0" \
    --region "${AWS_REGION}" \
    --query 'IntegrationId' \
    --output text)
  echo "✅ Created integration: ${INTEGRATION_ID}"
else
  echo "✅ Found existing integration: ${INTEGRATION_ID}"
fi

# Get or create route for GET /customer/reviews
echo "📝 Setting up route GET /customer/reviews..."

ROUTE_ID=$(aws apigatewayv2 get-routes \
  --api-id "${API_ID}" \
  --region "${AWS_REGION}" \
  --query "Items[?RouteKey=='GET /customer/reviews'].RouteId" \
  --output text 2>/dev/null || echo "")

if [ -z "$ROUTE_ID" ]; then
  echo "📝 Creating new route..."
  ROUTE_ID=$(aws apigatewayv2 create-route \
    --api-id "${API_ID}" \
    --route-key "GET /customer/reviews" \
    --target "integrations/${INTEGRATION_ID}" \
    --authorization-type JWT \
    --region "${AWS_REGION}" \
    --query 'RouteId' \
    --output text)
  echo "✅ Created route: ${ROUTE_ID}"
else
  echo "📝 Updating existing route..."
  aws apigatewayv2 update-route \
    --api-id "${API_ID}" \
    --route-id "${ROUTE_ID}" \
    --target "integrations/${INTEGRATION_ID}" \
    --region "${AWS_REGION}" > /dev/null
  echo "✅ Updated route: ${ROUTE_ID}"
fi

# Add Lambda permission
echo "🔑 Adding Lambda invoke permission..."

aws lambda add-permission \
  --function-name "${FUNC_NAME}" \
  --statement-id "apigatewayv2-invoke-${FUNC_NAME}-$(date +%s)" \
  --action lambda:InvokeFunction \
  --principal apigateway.amazonaws.com \
  --source-arn "arn:aws:execute-api:${AWS_REGION}:${AWS_ACCOUNT_ID}:${API_ID}/*/*" \
  --region "${AWS_REGION}" 2>/dev/null || echo "⚠️  Permission may already exist"

# Deploy API
echo "🚀 Deploying API..."
aws apigatewayv2 create-deployment \
  --api-id "${API_ID}" \
  --stage-name prod \
  --description "Added GET /customer/reviews endpoint" \
  --region "${AWS_REGION}" > /dev/null

echo ""
echo "✅ API Gateway setup complete!"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📍 API Endpoint:"
echo "   GET https://${API_ID}.execute-api.${AWS_REGION}.amazonaws.com/prod/customer/reviews"
echo ""
echo "🔐 Authentication:"
echo "   Authorization: Bearer <JWT_TOKEN>"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
