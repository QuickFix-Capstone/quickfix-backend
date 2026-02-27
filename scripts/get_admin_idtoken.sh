#!/usr/bin/env bash
# Get a fresh Cognito ID token for admin analytics testing
# Usage: ./scripts/get_admin_idtoken.sh

set -euo pipefail

# Cognito configuration (override with env vars if needed)
CLIENT_ID="${COGNITO_CLIENT_ID:-p2u5qdegml3hp60n6ohu52n2b}"
REGION="${COGNITO_REGION:-us-east-2}"

# Admin user credentials (override with env vars if needed)
EMAIL="${ADMIN_EMAIL:-persaudskip173@gmail.com}"
PASSWORD="${ADMIN_PASSWORD:-Allow@AP2003}"

echo "Authenticating admin user with Cognito..."
echo "Email: ${EMAIL}"

RESPONSE="$(aws cognito-idp initiate-auth \
  --auth-flow USER_PASSWORD_AUTH \
  --client-id "${CLIENT_ID}" \
  --auth-parameters USERNAME="${EMAIL}",PASSWORD="${PASSWORD}" \
  --region "${REGION}" \
  --output json)"

ID_TOKEN="$(echo "${RESPONSE}" | jq -r '.AuthenticationResult.IdToken // empty')"
EXPIRES_IN="$(echo "${RESPONSE}" | jq -r '.AuthenticationResult.ExpiresIn // empty')"

if [[ -z "${ID_TOKEN}" ]]; then
  echo "Failed to get IdToken from Cognito response."
  echo "${RESPONSE}"
  exit 1
fi

echo "${ID_TOKEN}" > /tmp/admin_id_token.txt
echo "${RESPONSE}" > /tmp/admin_cognito_tokens.json

echo "Success. Fresh IdToken saved to /tmp/admin_id_token.txt"
echo "Full auth payload saved to /tmp/admin_cognito_tokens.json"
echo "Token expires in ${EXPIRES_IN} seconds."
echo "Export command:"
echo "  export ADMIN_ID_TOKEN=\$(cat /tmp/admin_id_token.txt)"
