# Deployment Summary: GET /customer/reviews

## Deployment Date
2026-02-15 04:24:40 UTC

## What Was Deployed

### Lambda Function
- **Name:** `get_customer_reviews_to_providers`
- **Purpose:** Returns reviews written BY customers about providers
- **Runtime:** Python 3.11
- **Handler:** `handler.handler`
- **Memory:** 256 MB
- **Timeout:** 30 seconds

### Changes Made
1. **Fixed Database Collation Issue**
   - Updated JOIN clause to use `CAST(r.provider_id AS CHAR) = CAST(sp.provider_id AS CHAR)`
   - Added `charset='utf8mb4'` to database connection
   - Resolves: `Illegal mix of collations` error

2. **Files Modified:**
   - `lambda/reviews/get_customer_reviews_to_providers/handler.py`
   - `src/db/rds_main.py`

## API Endpoint

### Production URL
```
https://kfvf20j7j9.execute-api.us-east-2.amazonaws.com/prod/customer/reviews
```

### Authentication
- **Type:** JWT Bearer Token
- **Authorizer ID:** z8zn33
- **Required:** Yes

### Query Parameters
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `sort` | string | `newest` | Sort order: `newest`, `oldest`, `highest_rating`, `lowest_rating` |
| `limit` | integer | `10` | Results per page (1-100) |
| `offset` | integer | `0` | Pagination offset |

## Testing

### Local Testing
```bash
# Run local tests
source venv/bin/activate
PYTHONPATH=. python test_get_customer_reviews.py
```

### Production Testing
```bash
# Get JWT token first
./get_customer_token.sh

# Run production tests
./test_deployed_get_customer_reviews.sh
```

### Manual cURL Test
```bash
# Get reviews for authenticated customer
curl -X GET \
  'https://kfvf20j7j9.execute-api.us-east-2.amazonaws.com/prod/customer/reviews?sort=newest&limit=10' \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json"
```

## Response Example

```json
{
  "reviews": [
    {
      "review_id": 42,
      "job_id": 1086,
      "provider_id": "SP-2f2664c0-7488-429c-9ad2-5d2c10787ead",
      "provider_name": "VerdantLine Landscaping Updtaed",
      "provider_rating": 4.0,
      "rating": 5,
      "comment": "This is test for review",
      "created_at": "2026-02-15T01:02:59",
      "updated_at": "2026-02-15T01:02:59"
    }
  ],
  "pagination": {
    "limit": 10,
    "offset": 0,
    "total_count": 1,
    "has_more": false,
    "next_offset": null
  },
  "customer": {
    "customer_id": 13,
    "name": "Test Yang",
    "total_reviews_written": 1
  }
}
```

## Deployment Commands Used

```bash
# 1. Deploy Lambda function
cd deploy
bash deploy_get_customer_reviews_to_providers.sh

# 2. Create API Gateway deployment
aws apigatewayv2 create-deployment \
  --api-id kfvf20j7j9 \
  --stage-name prod \
  --description "Redeployed get_customer_reviews_to_providers with collation fix" \
  --region us-east-2
```

## Verification

### Lambda Function Status
```bash
aws lambda get-function \
  --function-name get_customer_reviews_to_providers \
  --region us-east-2
```

### API Gateway Route
```bash
aws apigatewayv2 get-routes \
  --api-id kfvf20j7j9 \
  --region us-east-2 \
  --query "Items[?RouteKey=='GET /customer/reviews']"
```

## Rollback Plan

If issues occur, rollback using:

```bash
# 1. Revert code changes in git
git checkout HEAD~1 lambda/reviews/get_customer_reviews_to_providers/handler.py
git checkout HEAD~1 src/db/rds_main.py

# 2. Redeploy previous version
cd deploy
bash deploy_get_customer_reviews_to_providers.sh

# 3. Create new deployment
aws apigatewayv2 create-deployment \
  --api-id kfvf20j7j9 \
  --stage-name prod \
  --description "Rollback get_customer_reviews_to_providers" \
  --region us-east-2
```

## Monitoring

### CloudWatch Logs
```bash
# View recent logs
aws logs tail /aws/lambda/get_customer_reviews_to_providers --follow --region us-east-2
```

### Metrics to Monitor
- Invocation count
- Error rate
- Duration
- Throttles

## Status

✅ **Deployment Successful**
- Lambda function updated
- API Gateway deployed to prod
- All tests passing
- Ready for production use
