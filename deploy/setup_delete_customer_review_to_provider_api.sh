#!/usr/bin/env bash
set -e

FUNC_NAME="delete_customer_review_to_provider"
AWS_REGION="us-east-2"
AWS_ACCOUNT_ID="008971679867"
API_ID="kfvf20j7j9"
AUTHORIZER_ID="z8zn33"

echo "🔗 Setting up Lambda integration..."

LAMBDA_ARN="arn:aws:lambda:${AWS_REGION}:${AWS_ACCOUNT_ID}:function:${FUNC_NAME}"

# Check if integration exists
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

echo "📝 Checking for existing route DELETE /customer/reviews/{review_id}..."

# Check if route exists
ROUTE_ID=$(aws apigatewayv2 get-routes \
  --api-id "${API_ID}" \
  --region "${AWS_REGION}" \
  --query "Items[?RouteKey=='DELETE /customer/reviews/{review_id}'].RouteId" \
  --output text 2>/dev/null || echo "")

if [ -z "$ROUTE_ID" ]; then
  echo "📝 Creating new route..."
  ROUTE_ID=$(aws apigatewayv2 create-route \
    --api-id "${API_ID}" \
    --route-key "DELETE /customer/reviews/{review_id}" \
    --target "integrations/${INTEGRATION_ID}" \
    --authorization-type JWT \
    --authorizer-id "${AUTHORIZER_ID}" \
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

echo "🔑 Adding Lambda permission..."

aws lambda add-permission \
  --function-name "${FUNC_NAME}" \
  --statement-id "apigatewayv2-invoke-${FUNC_NAME}-$(date +%s)" \
  --action lambda:InvokeFunction \
  --principal apigateway.amazonaws.com \
  --source-arn "arn:aws:execute-api:${AWS_REGION}:${AWS_ACCOUNT_ID}:${API_ID}/*/*" \
  --region "${AWS_REGION}" 2>/dev/null || echo "⚠️  Permission may already exist"

echo "🚀 Deploying API..."

aws apigatewayv2 create-deployment \
  --api-id "${API_ID}" \
  --stage-name prod \
  --description "Added DELETE /customer/reviews/{review_id}" \
  --region "${AWS_REGION}" > /dev/null

echo "✅ API Gateway setup complete!"
echo ""
echo "DELETE https://${API_ID}.execute-api.${AWS_REGION}.amazonaws.com/prod/customer/reviews/{review_id}"
