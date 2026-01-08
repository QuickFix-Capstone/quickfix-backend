#!/usr/bin/env bash
# Setup API Gateway endpoint for get_review_by_id Lambda with JWT authorizer

set -e

FUNC_NAME="get_review_by_id"
AWS_REGION="us-east-2"
AWS_ACCOUNT_ID="008971679867"
API_NAME="QuickFixAPI"

# Cognito User Pool details
COGNITO_USER_POOL_ID="us-east-2_45z5OMePi"
COGNITO_APP_CLIENT_ID="p2u5qdegml3hp60n6ohu52n2b"

echo "🔍 Finding or creating API Gateway..."

# Check if API Gateway exists
API_ID=$(aws apigateway get-rest-apis \
  --region "${AWS_REGION}" \
  --query "items[?name=='${API_NAME}'].id" \
  --output text)

if [ -z "$API_ID" ]; then
  echo "📝 Creating new API Gateway: ${API_NAME}..."
  API_ID=$(aws apigateway create-rest-api \
    --name "${API_NAME}" \
    --description "QuickFix Service Platform API" \
    --region "${AWS_REGION}" \
    --endpoint-configuration types=REGIONAL \
    --query 'id' \
    --output text)
  echo "✅ Created API Gateway with ID: ${API_ID}"
else
  echo "✅ Found existing API Gateway with ID: ${API_ID}"
fi

# Get root resource ID
ROOT_RESOURCE_ID=$(aws apigateway get-resources \
  --rest-api-id "${API_ID}" \
  --region "${AWS_REGION}" \
  --query 'items[?path==`/`].id' \
  --output text)

echo "📍 Root resource ID: ${ROOT_RESOURCE_ID}"

# Check if /review resource exists, if not create it
REVIEW_RESOURCE_ID=$(aws apigateway get-resources \
  --rest-api-id "${API_ID}" \
  --region "${AWS_REGION}" \
  --query "items[?path=='/review'].id" \
  --output text)

if [ -z "$REVIEW_RESOURCE_ID" ]; then
  echo "📝 Creating /review resource..."
  REVIEW_RESOURCE_ID=$(aws apigateway create-resource \
    --rest-api-id "${API_ID}" \
    --parent-id "${ROOT_RESOURCE_ID}" \
    --path-part "review" \
    --region "${AWS_REGION}" \
    --query 'id' \
    --output text)
  echo "✅ Created /review resource with ID: ${REVIEW_RESOURCE_ID}"
else
  echo "✅ Found existing /review resource with ID: ${REVIEW_RESOURCE_ID}"
fi

# Check if /review/{review_id} resource exists, if not create it
REVIEW_ID_RESOURCE_ID=$(aws apigateway get-resources \
  --rest-api-id "${API_ID}" \
  --region "${AWS_REGION}" \
  --query "items[?path=='/review/{review_id}'].id" \
  --output text)

if [ -z "$REVIEW_ID_RESOURCE_ID" ]; then
  echo "📝 Creating /review/{review_id} resource..."
  REVIEW_ID_RESOURCE_ID=$(aws apigateway create-resource \
    --rest-api-id "${API_ID}" \
    --parent-id "${REVIEW_RESOURCE_ID}" \
    --path-part "{review_id}" \
    --region "${AWS_REGION}" \
    --query 'id' \
    --output text)
  echo "✅ Created /review/{review_id} resource with ID: ${REVIEW_ID_RESOURCE_ID}"
else
  echo "✅ Found existing /review/{review_id} resource with ID: ${REVIEW_ID_RESOURCE_ID}"
fi

# Create or find JWT authorizer
echo "🔐 Setting up JWT Authorizer..."

AUTHORIZER_ID=$(aws apigateway get-authorizers \
  --rest-api-id "${API_ID}" \
  --region "${AWS_REGION}" \
  --query "items[?name=='CognitoAuthorizer'].id" \
  --output text)

if [ -z "$AUTHORIZER_ID" ]; then
  echo "📝 Creating Cognito JWT Authorizer..."

  # Note: Update the COGNITO_USER_POOL_ID and COGNITO_APP_CLIENT_ID above
  if [ "$COGNITO_USER_POOL_ID" = "YOUR_USER_POOL_ID" ]; then
    echo "⚠️  WARNING: Please update COGNITO_USER_POOL_ID in this script"
    echo "⚠️  Skipping authorizer creation for now"
    AUTHORIZER_ID=""
  else
    AUTHORIZER_ID=$(aws apigateway create-authorizer \
      --rest-api-id "${API_ID}" \
      --name "CognitoAuthorizer" \
      --type COGNITO_USER_POOLS \
      --provider-arns "arn:aws:cognito-idp:${AWS_REGION}:${AWS_ACCOUNT_ID}:userpool/${COGNITO_USER_POOL_ID}" \
      --identity-source "method.request.header.Authorization" \
      --region "${AWS_REGION}" \
      --query 'id' \
      --output text)
    echo "✅ Created Authorizer with ID: ${AUTHORIZER_ID}"
  fi
else
  echo "✅ Found existing Authorizer with ID: ${AUTHORIZER_ID}"
fi

# Create GET method on /review/{review_id}
echo "📝 Creating GET method on /review/{review_id}..."

# Delete existing method if it exists
aws apigateway delete-method \
  --rest-api-id "${API_ID}" \
  --resource-id "${REVIEW_ID_RESOURCE_ID}" \
  --http-method GET \
  --region "${AWS_REGION}" 2>/dev/null || true

# Create GET method with JWT authorization
aws apigateway put-method \
  --rest-api-id "${API_ID}" \
  --resource-id "${REVIEW_ID_RESOURCE_ID}" \
  --http-method GET \
  --authorization-type COGNITO_USER_POOLS \
  --authorizer-id "${AUTHORIZER_ID}" \
  --request-parameters "method.request.header.Authorization=true,method.request.path.review_id=true" \
  --region "${AWS_REGION}"

echo "✅ Created GET method"

# Set up Lambda integration
echo "🔗 Setting up Lambda integration..."

LAMBDA_ARN="arn:aws:lambda:${AWS_REGION}:${AWS_ACCOUNT_ID}:function:${FUNC_NAME}"

aws apigateway put-integration \
  --rest-api-id "${API_ID}" \
  --resource-id "${REVIEW_ID_RESOURCE_ID}" \
  --http-method GET \
  --type AWS_PROXY \
  --integration-http-method POST \
  --uri "arn:aws:apigateway:${AWS_REGION}:lambda:path/2015-03-31/functions/${LAMBDA_ARN}/invocations" \
  --region "${AWS_REGION}"

echo "✅ Lambda integration configured"

# Add Lambda permission for API Gateway to invoke the function
echo "🔑 Adding Lambda invoke permission for API Gateway..."

aws lambda add-permission \
  --function-name "${FUNC_NAME}" \
  --statement-id "apigateway-invoke-${FUNC_NAME}-$(date +%s)" \
  --action lambda:InvokeFunction \
  --principal apigateway.amazonaws.com \
  --source-arn "arn:aws:execute-api:${AWS_REGION}:${AWS_ACCOUNT_ID}:${API_ID}/*/*" \
  --region "${AWS_REGION}" 2>/dev/null || echo "⚠️  Permission may already exist"

echo "✅ Lambda permission added"

# Enable CORS for OPTIONS method
echo "🌐 Setting up CORS..."

# Delete existing OPTIONS method if it exists
aws apigateway delete-method \
  --rest-api-id "${API_ID}" \
  --resource-id "${REVIEW_ID_RESOURCE_ID}" \
  --http-method OPTIONS \
  --region "${AWS_REGION}" 2>/dev/null || true

# Create OPTIONS method
aws apigateway put-method \
  --rest-api-id "${API_ID}" \
  --resource-id "${REVIEW_ID_RESOURCE_ID}" \
  --http-method OPTIONS \
  --authorization-type NONE \
  --region "${AWS_REGION}"

# Set up method response for OPTIONS (must be created BEFORE integration response)
aws apigateway put-method-response \
  --rest-api-id "${API_ID}" \
  --resource-id "${REVIEW_ID_RESOURCE_ID}" \
  --http-method OPTIONS \
  --status-code 200 \
  --response-parameters '{
    "method.response.header.Access-Control-Allow-Headers": true,
    "method.response.header.Access-Control-Allow-Methods": true,
    "method.response.header.Access-Control-Allow-Origin": true
  }' \
  --region "${AWS_REGION}"

# Set up mock integration for OPTIONS
aws apigateway put-integration \
  --rest-api-id "${API_ID}" \
  --resource-id "${REVIEW_ID_RESOURCE_ID}" \
  --http-method OPTIONS \
  --type MOCK \
  --request-templates '{"application/json": "{\"statusCode\": 200}"}' \
  --region "${AWS_REGION}"

# Set up integration response for OPTIONS (must be created AFTER method response)
aws apigateway put-integration-response \
  --rest-api-id "${API_ID}" \
  --resource-id "${REVIEW_ID_RESOURCE_ID}" \
  --http-method OPTIONS \
  --status-code 200 \
  --response-parameters '{
    "method.response.header.Access-Control-Allow-Headers": "'\''Content-Type,Authorization'\''",
    "method.response.header.Access-Control-Allow-Methods": "'\''GET,OPTIONS'\''",
    "method.response.header.Access-Control-Allow-Origin": "'\''*'\''"
  }' \
  --region "${AWS_REGION}"

echo "✅ CORS configured"

# Deploy API
echo "🚀 Deploying API to 'prod' stage..."

aws apigateway create-deployment \
  --rest-api-id "${API_ID}" \
  --stage-name prod \
  --stage-description "Production stage" \
  --description "Deployment for get_review_by_id endpoint" \
  --region "${AWS_REGION}"

echo ""
echo "✅ API Gateway setup complete!"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📍 API Endpoint:"
echo "   GET https://${API_ID}.execute-api.${AWS_REGION}.amazonaws.com/prod/review/{review_id}"
echo ""
echo "🔐 Authentication:"
echo "   Authorization: Bearer <JWT_TOKEN>"
echo ""
echo "📝 Example cURL request:"
echo "   curl -X GET \\"
echo "     https://${API_ID}.execute-api.${AWS_REGION}.amazonaws.com/prod/review/1 \\"
echo "     -H 'Content-Type: application/json' \\"
echo "     -H 'Authorization: Bearer YOUR_JWT_TOKEN'"
echo ""
echo "💡 This endpoint can be used by both customers and service providers"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
