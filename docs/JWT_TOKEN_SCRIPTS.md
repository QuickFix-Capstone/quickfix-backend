# JWT Token Scripts - Quick Reference

## Available Scripts

### 1. Customer JWT Token
```bash
./scripts/get_jwt_token.sh
```
- **Email:** ykphrfly@gmail.com
- **Password:** Yang@860101
- **Token saved to:** `/tmp/jwt_token.txt`
- **Use for:** Customer endpoints, general testing

### 2. Service Provider JWT Token
```bash
./scripts/get_provider_jwt_token.sh
```
- **Email:** ajaypersaud04@gmail.com
- **Password:** Ajay@2003
- **Cognito Sub:** 515b5500-f0c1-7031-70ee-1ef9e9413a79
- **Cognito Groups:** ServiceProvider
- **Token saved to:** `/tmp/provider_jwt_token.txt`
- **Use for:** Provider-specific endpoints, provider testing

---

## Usage Examples

### Get Customer Token
```bash
# Get fresh customer token
./scripts/get_jwt_token.sh

# Use in curl
curl -H "Authorization: Bearer $(cat /tmp/jwt_token.txt)" \
  https://kfvf20j7j9.execute-api.us-east-2.amazonaws.com/prod/reviews/provider/SP-001
```

### Get Provider Token
```bash
# Get fresh provider token
./scripts/get_provider_jwt_token.sh

# Use in curl
curl -H "Authorization: Bearer $(cat /tmp/provider_jwt_token.txt)" \
  https://kfvf20j7j9.execute-api.us-east-2.amazonaws.com/prod/reviews/customer/1
```

### Export as Environment Variables
```bash
# Customer token
export JWT_TOKEN=$(cat /tmp/jwt_token.txt)

# Provider token
export PROVIDER_JWT_TOKEN=$(cat /tmp/provider_jwt_token.txt)

# Use in commands
curl -H "Authorization: Bearer $JWT_TOKEN" ...
curl -H "Authorization: Bearer $PROVIDER_JWT_TOKEN" ...
```

---

## Token Details

### Token Expiration
- **Lifetime:** 60 minutes (3600 seconds)
- **Refresh:** Run the script again to get a new token

### Token Contents
Both tokens include:
- `sub`: Cognito user ID
- `email`: User email address
- `cognito:groups`: User groups (Customer or ServiceProvider)
- `iss`: Cognito issuer
- `aud`: App client ID
- `exp`: Expiration timestamp

### Decode Token (for debugging)
```bash
# Decode the JWT payload
cat /tmp/jwt_token.txt | cut -d'.' -f2 | base64 -d | jq '.'
```

---

## Quick Testing

### Test Provider Reviews Endpoint
```bash
# Get customer token and test
./scripts/get_jwt_token.sh > /dev/null 2>&1
./scripts/test_get_provider_reviews.sh SP-001
```

### Test Customer Reviews Endpoint (when deployed)
```bash
# Get provider token and test
./scripts/get_provider_jwt_token.sh > /dev/null 2>&1
curl -X GET \
  "https://kfvf20j7j9.execute-api.us-east-2.amazonaws.com/prod/reviews/customer/2" \
  -H "Authorization: Bearer $(cat /tmp/provider_jwt_token.txt)" | jq '.'
```

---

## Troubleshooting

### Token Expired
**Error:** `{"message": "Unauthorized"}`

**Solution:** Get a fresh token
```bash
./scripts/get_jwt_token.sh  # or get_provider_jwt_token.sh
```

### Wrong Token Type
**Issue:** Using customer token for provider endpoint or vice versa

**Solution:** Use the correct token for the user type:
- Customer endpoints → Customer token
- Provider endpoints → Provider token
- General review endpoints → Either token works

---

## Notes

- Tokens are stored in `/tmp/` and will be deleted on system restart
- Both scripts use the same Cognito User Pool and App Client
- The provider token includes `cognito:groups: ["ServiceProvider"]`
- The customer token doesn't have groups (or has `["Customer"]`)
