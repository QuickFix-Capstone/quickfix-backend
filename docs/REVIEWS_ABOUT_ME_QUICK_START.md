# Quick Start: Reviews About Me Feature

## Overview
This guide will help you quickly deploy and test the "Reviews About Me" feature, which allows customers to see reviews that providers have written about them.

---

## Prerequisites

- AWS CLI configured with proper credentials
- Database access to QuickFix RDS instance
- Customer JWT token for testing

---

## Step 1: Deploy Lambda Function

```bash
# Deploy the Lambda function
./deploy/create_get_customer_reviews_about_me_lambda.sh
```

This will:
- Create the Lambda function `get_customer_reviews_about_me`
- Configure environment variables
- Set up proper IAM role and permissions

---

## Step 2: Configure API Gateway

### Option A: Using AWS Console

1. Go to API Gateway console
2. Select your API (QuickFix API)
3. Navigate to `/customer` resource
4. Create new child resource:
   - Resource Name: `reviews-about-me`
   - Resource Path: `/reviews-about-me`
5. Create GET method:
   - Integration type: Lambda Function
   - Lambda Function: `get_customer_reviews_about_me`
   - Use Lambda Proxy integration: ✓
6. Method Request settings:
   - Authorization: Cognito User Pool Authorizer
   - API Key Required: No
7. Enable CORS
8. Deploy to `prod` stage

### Option B: Using AWS CLI

```bash
# Get API ID
API_ID="kfvf20j7j9"
REGION="us-east-2"

# Get parent resource ID for /customer
PARENT_ID=$(aws apigateway get-resources \
  --rest-api-id $API_ID \
  --region $REGION \
  --query "items[?path=='/customer'].id" \
  --output text)

# Create reviews-about-me resource
RESOURCE_ID=$(aws apigateway create-resource \
  --rest-api-id $API_ID \
  --parent-id $PARENT_ID \
  --path-part "reviews-about-me" \
  --region $REGION \
  --query 'id' \
  --output text)

# Create GET method
aws apigateway put-method \
  --rest-api-id $API_ID \
  --resource-id $RESOURCE_ID \
  --http-method GET \
  --authorization-type COGNITO_USER_POOLS \
  --authorizer-id YOUR_AUTHORIZER_ID \
  --region $REGION

# Set up Lambda integration
LAMBDA_ARN="arn:aws:lambda:us-east-2:730335490415:function:get_customer_reviews_about_me"

aws apigateway put-integration \
  --rest-api-id $API_ID \
  --resource-id $RESOURCE_ID \
  --http-method GET \
  --type AWS_PROXY \
  --integration-http-method POST \
  --uri "arn:aws:apigateway:$REGION:lambda:path/2015-03-31/functions/$LAMBDA_ARN/invocations" \
  --region $REGION

# Deploy to prod
aws apigateway create-deployment \
  --rest-api-id $API_ID \
  --stage-name prod \
  --region $REGION
```

---

## Step 3: Add Test Data (Optional)

If you don't have provider reviews about customers yet:

```bash
# Connect to MySQL
mysql -h quickfix-db.c3gy8vvwpwqo.us-east-2.rds.amazonaws.com \
  -u admin -p quickfix

# Run the test data script
source sql/test_data/add_provider_customer_reviews.sql
```

Or manually insert test data:

```sql
INSERT INTO provider_customer_reviews (job_id, provider_id, customer_id, rating, comment)
VALUES 
    (1, 1, 1, 5, 'Excellent customer! Very clear communication and respectful.'),
    (2, 2, 1, 4, 'Good customer, prompt payment and reasonable expectations.');
```

---

## Step 4: Test the Endpoint

### Using the Test Script

```bash
# Run all tests
./test_reviews_about_me.sh
```

### Manual Testing

```bash
# Get customer token
TOKEN=$(./get_customer_token.sh)

# Test basic request
curl -X GET \
  'https://kfvf20j7j9.execute-api.us-east-2.amazonaws.com/prod/customer/reviews-about-me' \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" | jq '.'

# Test with parameters
curl -X GET \
  'https://kfvf20j7j9.execute-api.us-east-2.amazonaws.com/prod/customer/reviews-about-me?limit=5&sort=highest_rating' \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" | jq '.'
```

---

## Step 5: Verify Results

### Expected Response (with data)

```json
{
  "reviews": [
    {
      "review_id": 1,
      "job_id": 123,
      "booking_id": null,
      "provider_id": 456,
      "provider_name": "John's Plumbing",
      "provider_rating": 4.8,
      "service_title": "Fix leaking pipe",
      "rating": 5,
      "comment": "Excellent customer! Very clear communication.",
      "created_at": "2024-01-15T10:30:00",
      "updated_at": "2024-01-15T10:30:00"
    }
  ],
  "pagination": {
    "limit": 20,
    "offset": 0,
    "total_count": 1,
    "has_more": false,
    "next_offset": null
  },
  "customer": {
    "customer_id": 1,
    "name": "Jane Doe",
    "total_reviews_received": 1
  }
}
```

### Expected Response (empty state)

```json
{
  "reviews": [],
  "pagination": {
    "limit": 20,
    "offset": 0,
    "total_count": 0,
    "has_more": false,
    "next_offset": null
  },
  "customer": {
    "customer_id": 1,
    "name": "Jane Doe",
    "total_reviews_received": 0
  }
}
```

---

## Troubleshooting

### Issue: 401 Unauthorized

**Solution:** Check that your JWT token is valid and not expired

```bash
# Get a fresh token
TOKEN=$(./get_customer_token.sh)
```

### Issue: 500 Internal Server Error

**Solution:** Check CloudWatch logs

```bash
aws logs tail /aws/lambda/get_customer_reviews_about_me --follow --region us-east-2
```

### Issue: Empty reviews array

**Possible causes:**
1. No providers have reviewed this customer yet
2. Customer ID mismatch
3. Database connection issue

**Solution:** Add test data or check database

```bash
# Check if reviews exist
mysql -h quickfix-db.c3gy8vvwpwqo.us-east-2.rds.amazonaws.com \
  -u admin -p quickfix \
  -e "SELECT * FROM provider_customer_reviews LIMIT 5;"
```

### Issue: API Gateway 403 Forbidden

**Solution:** Verify Cognito authorizer is configured correctly

```bash
# List authorizers
aws apigateway get-authorizers \
  --rest-api-id kfvf20j7j9 \
  --region us-east-2
```

---

## API Endpoints Summary

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/customer/reviews-about-me` | GET | Get reviews providers wrote about me |
| `/customer/reviews` | GET | Get reviews I wrote about providers |
| `/customer/review` | POST | Create a review about a provider |

---

## Next Steps

1. ✅ Deploy Lambda function
2. ✅ Configure API Gateway
3. ✅ Test endpoint
4. 🔄 Integrate with frontend
5. 🔄 Add provider review submission endpoint (optional)

---

## Related Documentation

- [Full API Documentation](./API_CUSTOMER_REVIEWS_ABOUT_ME.md)
- [Customer Provider Reviews API](./API_CREATE_CUSTOMER_PROVIDER_REVIEW.md)
- [Frontend Integration Guide](./FRONTEND_GET_CUSTOMER_REVIEWS_GUIDE.md)

---

## Support

For issues or questions:
1. Check CloudWatch logs
2. Verify database connectivity
3. Test with curl before frontend integration
4. Review API Gateway configuration
