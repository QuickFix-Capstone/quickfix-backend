#!/usr/bin/env bash
# Quick script to get JWT token from AWS Cognito
# Usage: ./get_jwt_token.sh

set -e

# Cognito Configuration
USER_POOL_ID="us-east-2_45z5OMePi"
CLIENT_ID="p2u5qdegml3hp60n6ohu52n2b"
REGION="us-east-2"

# User Credentials
EMAIL="ykphrfly@gmail.com"
PASSWORD="Yang@860101"

echo "🔐 Getting JWT token from AWS Cognito..."
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
  echo "📋 ID TOKEN (use this for API calls):"
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  echo "${ID_TOKEN}"
  echo ""
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  echo "⏰ Token expires in: ${EXPIRES_IN} seconds (~$((EXPIRES_IN / 60)) minutes)"
  echo ""
  echo "💡 Export as environment variable:"
  echo "   export JWT_TOKEN=\"${ID_TOKEN}\""
  echo ""
  echo "💡 Use in curl commands:"
  echo "   curl -H \"Authorization: Bearer \${JWT_TOKEN}\" ..."
  echo ""
  
  # Save to file for easy access
  echo "${ID_TOKEN}" > /tmp/jwt_token.txt
  echo "💾 Token saved to: /tmp/jwt_token.txt"
  echo ""
  echo "💡 Load token from file:"
  echo "   export JWT_TOKEN=\$(cat /tmp/jwt_token.txt)"
  echo ""
  
else
  echo "❌ Authentication failed!"
  echo ""
  echo "Error details:"
  echo "$RESPONSE"
  exit 1
fi
