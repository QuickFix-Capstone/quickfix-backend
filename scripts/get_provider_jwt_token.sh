#!/usr/bin/env bash
# Quick script to get JWT token for SERVICE PROVIDER from AWS Cognito
# Usage: ./get_provider_jwt_token.sh

set -e

# Cognito Configuration
USER_POOL_ID="us-east-2_45z5OMePi"
CLIENT_ID="p2u5qdegml3hp60n6ohu52n2b"
REGION="us-east-2"

# Service Provider Credentials
EMAIL="ajaypersaud04@gmail.com"
PASSWORD="Ajay@2003"

echo "🔐 Getting JWT token for SERVICE PROVIDER from AWS Cognito..."
echo ""

# Authenticate and get tokens
RESPONSE=$(aws cognito-idp initiate-auth \
  --auth-flow USER_PASSWORD_AUTH \
  --client-id "${CLIENT_ID}" \
  --auth-parameters USERNAME="${EMAIL}",PASSWORD="${PASSWORD}" \
  --region "${REGION}" 2>&1)

# Check if authentication was successful
if echo "$RESPONSE" | grep -q "AuthenticationResult"; then
  # Extract tokens
  ID_TOKEN=$(echo "$RESPONSE" | jq -r '.AuthenticationResult.IdToken')
  ACCESS_TOKEN=$(echo "$RESPONSE" | jq -r '.AuthenticationResult.AccessToken')
  REFRESH_TOKEN=$(echo "$RESPONSE" | jq -r '.AuthenticationResult.RefreshToken')
  EXPIRES_IN=$(echo "$RESPONSE" | jq -r '.AuthenticationResult.ExpiresIn')
  
  echo "✅ Authentication successful!"
  echo ""
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  echo "📋 SERVICE PROVIDER ID TOKEN (use this for API calls):"
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  echo "${ID_TOKEN}"
  echo ""
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  echo "⏰ Token expires in: ${EXPIRES_IN} seconds (~$((EXPIRES_IN / 60)) minutes)"
  echo ""
  echo "💡 Export as environment variable:"
  echo "   export PROVIDER_JWT_TOKEN=\"${ID_TOKEN}\""
  echo ""
  echo "💡 Use in curl commands:"
  echo "   curl -H \"Authorization: Bearer \${PROVIDER_JWT_TOKEN}\" ..."
  echo ""
  
  # Save to file for easy access
  echo "${ID_TOKEN}" > /tmp/provider_jwt_token.txt
  echo "💾 Token saved to: /tmp/provider_jwt_token.txt"
  echo ""
  echo "💡 Load token from file:"
  echo "   export PROVIDER_JWT_TOKEN=\$(cat /tmp/provider_jwt_token.txt)"
  echo ""
  
  # Decode and show user info
  echo "👤 Provider Info:"
  echo "   Email: ${EMAIL}"
  PROVIDER_SUB=$(echo "${ID_TOKEN}" | cut -d'.' -f2 | base64 -d 2>/dev/null | python3 -c "import sys, json; print(json.load(sys.stdin).get('sub', 'N/A'))" 2>/dev/null || echo "N/A")
  echo "   Cognito Sub: ${PROVIDER_SUB}"
  echo ""
  
else
  echo "❌ Authentication failed!"
  echo ""
  echo "Error details:"
  echo "$RESPONSE"
  exit 1
fi
