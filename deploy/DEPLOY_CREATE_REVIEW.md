# Deploy create_review Lambda Function

This guide covers deploying the `create_review` Lambda function with API Gateway and JWT authentication.

## Prerequisites

- AWS CLI configured with appropriate credentials
- Access to AWS Account: `008971679867`
- Region: `us-east-2`
- IAM Role: `create_customer-role-qch33m23` (already exists)
- Python 3.11
- Cognito User Pool configured (for JWT authentication)

## Environment Variables

The Lambda function requires these environment variables (automatically set by the deployment script):

```bash
MYSQL_HOST=quickfix-mysql.cno624c2aarh.us-east-2.rds.amazonaws.com
MYSQL_USER=admin
MYSQL_PASSWORD=QuickFix123!
MYSQL_DB=quickfix
MYSQL_PORT=3306
```

## Deployment Steps

### Step 1: Create the Lambda Function

```bash
cd deploy
./create_review_lambda.sh
```

This script will:
- ✅ Create the Lambda function in AWS
- ✅ Set environment variables
- ✅ Configure timeout (30 seconds) and memory (256 MB)
- ✅ Deploy the initial code

### Step 2: Setup API Gateway (Optional - if not done manually)

**Before running this script, update the Cognito details:**

Edit `setup_create_review_api.sh` and update:
```bash
COGNITO_USER_POOL_ID="YOUR_USER_POOL_ID"    # e.g., us-east-2_xxxxxxxxx
COGNITO_APP_CLIENT_ID="YOUR_APP_CLIENT_ID"
```

Then run:
```bash
./setup_create_review_api.sh
```

This script will:
- ✅ Find or create `QuickFixAPI` REST API
- ✅ Create `/reviews` resource
- ✅ Setup POST method with JWT authorizer
- ✅ Configure CORS (OPTIONS method)
- ✅ Connect Lambda function
- ✅ Deploy to `prod` stage

### Step 3: Redeploy Code (for updates)

After making code changes:

```bash
./deploy_create_review.sh
```

## API Endpoint

After deployment, your endpoint will be:

```
POST https://{API_ID}.execute-api.us-east-2.amazonaws.com/prod/reviews
```

## Authentication

The endpoint requires a valid JWT token from Cognito:

```bash
Authorization: Bearer <JWT_TOKEN>
```

## Request Format

```json
{
  "job_id": 123,
  "reviewer_id": 1,
  "reviewer_type": "customer",
  "reviewee_id": 5,
  "reviewee_type": "provider",
  "rating": 5,
  "comment": "Excellent service! Very professional and completed the job on time."
}
```

### Field Validations

- `job_id`: Must exist and be in "completed" status
- `reviewer_type`: Must be "customer" or "provider"
- `reviewee_type`: Must be "customer" or "provider"
- `rating`: Integer between 1-5 (inclusive)
- `comment`: String between 10-1000 characters
- Cannot review yourself
- Cannot review the same job twice

## Response Codes

| Code | Description |
|------|-------------|
| 201  | Review created successfully |
| 400  | Invalid input data (validation failed) |
| 401  | Unauthorized (missing or invalid JWT) |
| 404  | Job not found |
| 409  | Conflict (duplicate review) |
| 500  | Internal server error |

## Success Response Example

```json
{
  "message": "Review created successfully",
  "review": {
    "review_id": 42,
    "job_id": 123,
    "reviewer_id": 1,
    "reviewer_type": "customer",
    "reviewee_id": 5,
    "reviewee_type": "provider",
    "rating": 5,
    "comment": "Excellent service! Very professional and completed the job on time.",
    "created_at": "2026-01-08T02:41:55"
  }
}
```

## Error Response Example

```json
{
  "message": "rating must be between 1 and 5"
}
```

## Testing

### Local Testing

Test the Lambda function locally:

```bash
cd ..  # Go to project root
python test_create_review.py
```

### Test with cURL

```bash
curl -X POST \
  https://{API_ID}.execute-api.us-east-2.amazonaws.com/prod/reviews \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer YOUR_JWT_TOKEN' \
  -d '{
    "job_id": 1,
    "reviewer_id": 1,
    "reviewer_type": "customer",
    "reviewee_id": 5,
    "reviewee_type": "provider",
    "rating": 5,
    "comment": "Excellent service! Very professional and completed the job on time. Would definitely hire again."
  }'
```

## Troubleshooting

### Lambda Function Not Found

```bash
aws lambda list-functions --region us-east-2 | grep create_review
```

If not found, run `./create_review_lambda.sh`

### API Gateway Not Configured

```bash
aws apigateway get-rest-apis --region us-east-2 --query 'items[*].[name,id]'
```

### Check Lambda Logs

```bash
aws logs tail /aws/lambda/create_review --follow --region us-east-2
```

### Update Environment Variables

```bash
aws lambda update-function-configuration \
  --function-name create_review \
  --environment Variables={MYSQL_HOST=your-host,MYSQL_USER=admin,...} \
  --region us-east-2
```

## Architecture

```
Client (Frontend)
    ↓ POST /reviews
    ↓ (JWT Token)
API Gateway
    ↓ (Validates JWT with Cognito)
    ↓ (Invokes Lambda)
create_review Lambda
    ↓ (Validates data)
    ↓ (Inserts into DB)
RDS MySQL (quickfix database)
```

## Files

- `lambda/reviews/create_review/handler.py` - Lambda function code
- `deploy/create_review_lambda.sh` - Create Lambda function
- `deploy/deploy_create_review.sh` - Deploy/update Lambda code
- `deploy/setup_create_review_api.sh` - Setup API Gateway
- `test_create_review.py` - Local test script

## Next Steps

After successful deployment:

1. ✅ Update frontend to call the new API endpoint
2. ✅ Add transaction logic to update provider/customer ratings
3. ✅ Implement additional review endpoints (get, list, etc.)
