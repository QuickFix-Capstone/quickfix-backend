# Internal API Guide: update_ratings

## Overview

The `update_ratings` Lambda function is now exposed as an **internal API endpoint** with **IAM authentication**. This means:

- ✅ **Secure**: Requires AWS credentials (not publicly accessible)
- ✅ **Internal-only**: Designed for service-to-service communication
- ✅ **Flexible**: Can be called via Lambda SDK or HTTP with SigV4 signing
- ❌ **Not public**: Returns 403 Forbidden without AWS credentials
- ❌ **No JWT**: User JWT tokens won't work (requires IAM credentials)

---

## API Endpoint

```
POST https://kfvf20j7j9.execute-api.us-east-2.amazonaws.com/prod/internal/update-ratings
```

**Authentication**: AWS_IAM (requires AWS Signature Version 4)

---

## When to Use This API

### Use Case 1: Lambda-to-Lambda Invocation (Recommended)
When you need to update ratings from another Lambda function.

**Advantages:**
- Simplest implementation
- Automatic authentication via execution role
- No SigV4 signing required
- Faster than HTTP

### Use Case 2: HTTP with IAM Authentication
When you need to call from:
- Backend services with AWS credentials
- Admin tools
- Monitoring/testing scripts
- Applications running on EC2/ECS with IAM roles

---

## Method 1: Lambda-to-Lambda (Recommended)

### Asynchronous (Fire-and-Forget)

Use this when you don't need to wait for the result.

```python
import boto3
import json

lambda_client = boto3.client('lambda', region_name='us-east-2')

# After creating a review, trigger rating update
lambda_client.invoke(
    FunctionName='update_ratings',
    InvocationType='Event',  # Async - returns immediately
    Payload=json.dumps({
        'reviewee_id': 'google-oauth2|103949366066974158596',  # string for provider
        'reviewee_type': 'provider'
    })
)

# Or for customer
lambda_client.invoke(
    FunctionName='update_ratings',
    InvocationType='Event',
    Payload=json.dumps({
        'reviewee_id': 1,  # integer for customer
        'reviewee_type': 'customer'
    })
)
```

**Best for:**
- `create_review` Lambda - update ratings after creating review
- `delete_review` Lambda - update ratings after deleting review
- Background jobs

### Synchronous (Wait for Result)

Use this when you need the updated rating information immediately.

```python
import boto3
import json

lambda_client = boto3.client('lambda', region_name='us-east-2')

response = lambda_client.invoke(
    FunctionName='update_ratings',
    InvocationType='RequestResponse',  # Sync - waits for result
    Payload=json.dumps({
        'reviewee_id': 5,
        'reviewee_type': 'provider'
    })
)

# Parse the response
result = json.loads(response['Payload'].read())
print(result)
# {
#   "statusCode": 200,
#   "body": "{\"message\": \"Rating updated successfully\", ...}"
# }

# Parse the body
body = json.loads(result['body'])
rating_info = body['rating_info']
print(f"Average rating: {rating_info['average_rating']}")
print(f"Total reviews: {rating_info['total_review_count']}")
```

**Best for:**
- When you need immediate confirmation
- When the calling function needs updated rating data
- Admin operations

---

## Method 2: HTTP with IAM Authentication

### Python with requests-aws4auth

```python
import requests
from requests_aws4auth import AWS4Auth
import boto3
import json

# Get AWS credentials
credentials = boto3.Session().get_credentials()

# Create SigV4 auth
auth = AWS4Auth(
    credentials.access_key,
    credentials.secret_key,
    'us-east-2',
    'execute-api',
    session_token=credentials.token
)

# Make authenticated request
response = requests.post(
    'https://kfvf20j7j9.execute-api.us-east-2.amazonaws.com/prod/internal/update-ratings',
    auth=auth,
    json={
        'reviewee_id': 'provider-id-123',
        'reviewee_type': 'provider'
    }
)

if response.status_code == 200:
    result = response.json()
    print(f"Success: {result['message']}")
    print(f"Average rating: {result['rating_info']['average_rating']}")
else:
    print(f"Error {response.status_code}: {response.text}")
```

**Requirements:**
```bash
pip install requests requests-aws4auth boto3
```

### JavaScript/Node.js with AWS SDK

```javascript
const AWS = require('aws-sdk');
const https = require('https');

// Using aws4 library for signing
const aws4 = require('aws4');

const options = {
  hostname: 'kfvf20j7j9.execute-api.us-east-2.amazonaws.com',
  path: '/prod/internal/update-ratings',
  method: 'POST',
  service: 'execute-api',
  region: 'us-east-2',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    reviewee_id: 1,
    reviewee_type: 'customer'
  })
};

// Sign the request
aws4.sign(options, AWS.config.credentials);

// Make the request
const req = https.request(options, (res) => {
  let data = '';
  res.on('data', (chunk) => data += chunk);
  res.on('end', () => {
    console.log('Response:', JSON.parse(data));
  });
});

req.write(options.body);
req.end();
```

**Requirements:**
```bash
npm install aws-sdk aws4
```

### AWS CLI

```bash
# Using awscurl (tool for signing AWS requests)
pip install awscurl

awscurl \
  --service execute-api \
  --region us-east-2 \
  -X POST \
  -H 'Content-Type: application/json' \
  -d '{"reviewee_id": 1, "reviewee_type": "provider"}' \
  https://kfvf20j7j9.execute-api.us-east-2.amazonaws.com/prod/internal/update-ratings
```

---

## Request Format

### Endpoint
```
POST /internal/update-ratings
```

### Headers
```
Content-Type: application/json
Authorization: AWS4-HMAC-SHA256 Credential=... (automatically added by SigV4)
```

### Request Body

```json
{
  "reviewee_id": "string or integer",
  "reviewee_type": "provider" | "customer"
}
```

**Fields:**
- `reviewee_id` (required):
  - For providers: string (e.g., Cognito sub like `"google-oauth2|123..."`)
  - For customers: integer (e.g., `1`, `5`, `100`)
- `reviewee_type` (required): Either `"provider"` or `"customer"`

---

## Response Format

### Success (200 OK)

```json
{
  "message": "Rating updated successfully",
  "rating_info": {
    "reviewee_type": "provider",
    "reviewee_id": "google-oauth2|103949366066974158596",
    "average_rating": 4.75,
    "total_rating_points": 19,
    "total_review_count": 4
  }
}
```

### Error Responses

#### 400 Bad Request - Missing Field
```json
{
  "message": "Missing required field: reviewee_id"
}
```

#### 400 Bad Request - Invalid Type
```json
{
  "message": "reviewee_type must be 'customer' or 'provider'"
}
```

#### 400 Bad Request - Invalid Customer ID
```json
{
  "message": "customer_id must be a valid integer"
}
```

#### 403 Forbidden - No Authentication
```json
{
  "message": "Forbidden"
}
```

This means:
- Missing AWS credentials
- Invalid AWS signature
- Expired credentials
- IAM user/role lacks permissions

#### 500 Internal Server Error
```json
{
  "message": "Database connection failed"
}
```

or

```json
{
  "message": "Internal server error while updating rating"
}
```

---

## IAM Permissions Required

To call this API, the IAM user/role needs:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": "execute-api:Invoke",
      "Resource": "arn:aws:execute-api:us-east-2:008971679867:kfvf20j7j9/prod/POST/internal/update-ratings"
    }
  ]
}
```

**For Lambda functions:**
Lambda execution roles automatically have permission to call API Gateway endpoints in the same AWS account.

---

## Integration Example: create_review Lambda

Here's how to integrate with the `create_review` Lambda:

```python
# In lambda/reviews/create_review/handler.py

import boto3
import json

def handler(event, context):
    # ... existing code to create review ...

    # After successfully creating the review (after line 167)
    review_id = cur.lastrowid
    conn.commit()

    # ✅ NEW: Trigger rating update asynchronously
    try:
        lambda_client = boto3.client('lambda', region_name='us-east-2')
        lambda_client.invoke(
            FunctionName='update_ratings',
            InvocationType='Event',  # Async - don't wait
            Payload=json.dumps({
                'reviewee_id': data['reviewee_id'],
                'reviewee_type': data['reviewee_type']
            })
        )
        print(f"✅ Triggered rating update for {data['reviewee_type']} {data['reviewee_id']}")
    except Exception as e:
        # Don't fail the review creation if rating update fails
        print(f"⚠️  Failed to trigger rating update: {e}")

    # ... continue with existing response ...
    return _response(201, {
        "message": "Review created successfully",
        "review_id": review_id
    })
```

**Important:**
- Use `InvocationType='Event'` for async (recommended)
- Wrap in try/except to prevent rating update failures from breaking review creation
- Log the invocation for debugging

---

## Security Considerations

### ✅ What This API Prevents

1. **Public Access**: Cannot be called from browser/frontend
2. **Unauthorized Users**: Requires valid AWS credentials
3. **JWT Bypass**: User authentication tokens don't work
4. **Rate Limiting**: AWS API Gateway provides built-in protection

### ⚠️ What This API Allows

1. **Any AWS IAM User/Role**: Anyone with AWS credentials in your account can call it
2. **Cross-Service Access**: Other Lambda functions can call it automatically
3. **Account-Wide Access**: Not restricted to specific services

### 🔒 Best Practices

1. **Use Lambda-to-Lambda for internal calls** (simpler, more secure)
2. **Only expose via HTTP when necessary** (for services outside Lambda)
3. **Monitor CloudWatch Logs** for suspicious activity
4. **Use least-privilege IAM roles** for services calling this API
5. **Consider VPC restrictions** if you need tighter control

---

## Testing

### Test Script
Run the provided test script:

```bash
cd lambda/reviews/update_ratings
python3 test_iam_api.py
```

This will:
1. Test with proper IAM authentication (should succeed)
2. Test without authentication (should fail with 403)
3. Test with invalid input (should fail with 400)

### Manual Testing with AWS CLI

```bash
# Install awscurl if not already installed
pip install awscurl

# Test provider rating update
awscurl \
  --service execute-api \
  --region us-east-2 \
  -X POST \
  -H 'Content-Type: application/json' \
  -d '{"reviewee_id": "google-oauth2|103949366066974158596", "reviewee_type": "provider"}' \
  https://kfvf20j7j9.execute-api.us-east-2.amazonaws.com/prod/internal/update-ratings

# Test customer rating update
awscurl \
  --service execute-api \
  --region us-east-2 \
  -X POST \
  -H 'Content-Type: application/json' \
  -d '{"reviewee_id": 1, "reviewee_type": "customer"}' \
  https://kfvf20j7j9.execute-api.us-east-2.amazonaws.com/prod/internal/update-ratings
```

---

## Monitoring

### CloudWatch Logs

View Lambda execution logs:
```bash
aws logs tail /aws/lambda/update_ratings --follow --region us-east-2
```

### API Gateway Metrics

Monitor API calls in CloudWatch:
- Go to AWS Console → CloudWatch → API Gateway
- View metrics for API: `kfvf20j7j9`
- Check: Request count, latency, 4xx/5xx errors

### Check Last API Call

```bash
aws logs tail /aws/lambda/update_ratings --since 5m --region us-east-2
```

---

## Comparison: Direct Lambda vs HTTP API

| Feature | Lambda-to-Lambda | HTTP with IAM |
|---------|-----------------|---------------|
| **Setup Complexity** | Simple | Complex (SigV4) |
| **Performance** | Faster | Slower (HTTP) |
| **Cost** | Lower | Higher |
| **Authentication** | Automatic | Manual signing |
| **Best For** | Internal services | External tools |
| **Debugging** | CloudWatch only | API Gateway + CloudWatch |

**Recommendation**: Use Lambda-to-Lambda for 95% of cases. Only use HTTP when calling from outside Lambda (EC2, containers, local tools).

---

## Troubleshooting

### Error: 403 Forbidden

**Cause**: Missing or invalid AWS credentials

**Solutions:**
1. Configure AWS credentials: `aws configure`
2. Check IAM permissions: User needs `execute-api:Invoke` permission
3. Verify credentials: `aws sts get-caller-identity`
4. Check credential expiration (especially for assumed roles)

### Error: Signature Mismatch

**Cause**: Incorrect SigV4 signing

**Solutions:**
1. Ensure you're using the correct region: `us-east-2`
2. Verify service name: `execute-api`
3. Check system clock (SigV4 is time-sensitive)
4. Use libraries like `requests-aws4auth` instead of manual signing

### Error: Connection Timeout

**Cause**: Network/VPC issues

**Solutions:**
1. Check Lambda is in correct VPC (if using VPC)
2. Verify security group rules
3. Check NAT gateway configuration
4. Test connectivity: `curl https://kfvf20j7j9.execute-api.us-east-2.amazonaws.com/`

### Lambda Not Updating Ratings

**Cause**: Integration not set up in create_review

**Solutions:**
1. Add boto3 invocation to `create_review` handler
2. Verify Lambda execution role has `lambda:InvokeFunction` permission
3. Check CloudWatch logs for errors
4. Test update_ratings manually first

---

## Next Steps

1. **Integrate with create_review**: Add async invocation after review creation
2. **Monitor Usage**: Watch CloudWatch metrics for errors
3. **Add to delete_review**: Call this API when reviews are deleted
4. **Add to update_review**: Call this API when review ratings change
5. **Document for Team**: Share this guide with backend developers

---

## Summary

✅ **Deployed**: Internal API with IAM authentication
✅ **Tested**: Verified IAM auth works, rejects unauthenticated requests
✅ **Secure**: Not publicly accessible
✅ **Documented**: Complete usage guide and examples
✅ **Ready**: For integration with other Lambda functions

**Endpoint**: `POST https://kfvf20j7j9.execute-api.us-east-2.amazonaws.com/prod/internal/update-ratings`
**Auth**: AWS_IAM (SigV4)
**Purpose**: Internal service-to-service rating updates

---

**Created**: 2026-01-11
**Author**: Claude Code
**Version**: 1.0
