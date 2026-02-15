# Reviews About Me - Deployment Checklist

## Pre-Deployment Checklist

### ✅ Code Implementation
- [x] Lambda handler created (`lambda/reviews/get_customer_reviews_about_me/handler.py`)
- [x] Deployment script created (`deploy/create_get_customer_reviews_about_me_lambda.sh`)
- [x] Test script created (`test_reviews_about_me.sh`)
- [x] Scripts made executable

### ✅ Database
- [x] Table `provider_customer_reviews` exists (created in previous migration)
- [x] Index `idx_pc_customer_created` exists for performance
- [x] Foreign key constraints configured
- [x] Test data script created (`sql/test_data/add_provider_customer_reviews.sql`)

### ✅ Documentation
- [x] Full API documentation (`docs/API_CUSTOMER_REVIEWS_ABOUT_ME.md`)
- [x] Quick start guide (`docs/REVIEWS_ABOUT_ME_QUICK_START.md`)
- [x] Comparison guide (`docs/CUSTOMER_REVIEWS_COMPARISON.md`)
- [x] Deployment summary (`DEPLOYMENT_SUMMARY_reviews_about_me.md`)

---

## Deployment Steps

### Step 1: Deploy Lambda Function
```bash
./deploy/create_get_customer_reviews_about_me_lambda.sh
```

**Verify:**
- [ ] Lambda function created successfully
- [ ] Environment variables set correctly
- [ ] IAM role attached
- [ ] Function appears in AWS Console

**Check with:**
```bash
aws lambda get-function \
  --function-name get_customer_reviews_about_me \
  --region us-east-2
```

---

### Step 2: Configure API Gateway

#### Option A: AWS Console
- [ ] Navigate to API Gateway console
- [ ] Select QuickFix API
- [ ] Find `/customer` resource
- [ ] Create child resource `reviews-about-me`
- [ ] Add GET method
- [ ] Configure Lambda integration
- [ ] Set integration type to Lambda Proxy
- [ ] Select function: `get_customer_reviews_about_me`
- [ ] Configure Cognito authorizer
- [ ] Enable CORS
- [ ] Deploy to `prod` stage

#### Option B: AWS CLI
```bash
# Get API ID and parent resource ID
API_ID="kfvf20j7j9"
REGION="us-east-2"

# Create resource
aws apigateway create-resource \
  --rest-api-id $API_ID \
  --parent-id <PARENT_RESOURCE_ID> \
  --path-part "reviews-about-me" \
  --region $REGION

# Add GET method (see docs for full commands)
```

**Verify:**
- [ ] Endpoint appears in API Gateway
- [ ] Method has Cognito authorization
- [ ] Lambda integration configured
- [ ] CORS enabled
- [ ] Deployed to prod stage

---

### Step 3: Test the Endpoint

#### Quick Test
```bash
# Get token
TOKEN=$(./get_customer_token.sh)

# Test endpoint
curl -X GET \
  'https://kfvf20j7j9.execute-api.us-east-2.amazonaws.com/prod/customer/reviews-about-me' \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json"
```

**Expected result:**
- [ ] Status code: 200
- [ ] Response has `reviews` array
- [ ] Response has `pagination` object
- [ ] Response has `customer` object

#### Comprehensive Tests
```bash
./test_reviews_about_me.sh
```

**Verify all tests pass:**
- [ ] Test 1: Default pagination
- [ ] Test 2: Custom limit
- [ ] Test 3: Sort by highest rating
- [ ] Test 4: Sort by oldest
- [ ] Test 5: Pagination with offset

---

### Step 4: Add Test Data (Optional)

If no reviews exist yet:

```bash
# Connect to database
mysql -h quickfix-db.c3gy8vvwpwqo.us-east-2.rds.amazonaws.com \
  -u admin -p quickfix

# Run test data script
source sql/test_data/add_provider_customer_reviews.sql
```

**Verify:**
- [ ] Test reviews inserted
- [ ] Reviews appear in query results
- [ ] Foreign key relationships valid

---

### Step 5: Monitor and Verify

#### CloudWatch Logs
```bash
# View logs
aws logs tail /aws/lambda/get_customer_reviews_about_me --follow --region us-east-2
```

**Check for:**
- [ ] No error messages
- [ ] Successful invocations
- [ ] Reasonable execution times (< 200ms)

#### CloudWatch Metrics
- [ ] Invocations > 0
- [ ] Errors = 0
- [ ] Duration < 200ms average
- [ ] No throttles

---

## Post-Deployment Verification

### Functional Tests

#### Test 1: Empty State
```bash
# Test with customer who has no reviews
TOKEN=$(./get_customer_token.sh)
curl -X GET \
  'https://kfvf20j7j9.execute-api.us-east-2.amazonaws.com/prod/customer/reviews-about-me' \
  -H "Authorization: Bearer $TOKEN" | jq '.pagination.total_count'
```
- [ ] Returns 0 for customers with no reviews
- [ ] Returns empty array
- [ ] No errors

#### Test 2: With Data
```bash
# Test with customer who has reviews
curl -X GET \
  'https://kfvf20j7j9.execute-api.us-east-2.amazonaws.com/prod/customer/reviews-about-me' \
  -H "Authorization: Bearer $TOKEN" | jq '.reviews[0]'
```
- [ ] Returns review objects
- [ ] All fields present
- [ ] Provider information included
- [ ] Dates formatted correctly

#### Test 3: Pagination
```bash
# Test pagination
curl -X GET \
  'https://kfvf20j7j9.execute-api.us-east-2.amazonaws.com/prod/customer/reviews-about-me?limit=5&offset=0' \
  -H "Authorization: Bearer $TOKEN" | jq '.pagination'
```
- [ ] Respects limit parameter
- [ ] Respects offset parameter
- [ ] `has_more` calculated correctly
- [ ] `next_offset` provided when applicable

#### Test 4: Sorting
```bash
# Test sorting
curl -X GET \
  'https://kfvf20j7j9.execute-api.us-east-2.amazonaws.com/prod/customer/reviews-about-me?sort=highest_rating' \
  -H "Authorization: Bearer $TOKEN" | jq '.reviews[].rating'
```
- [ ] Newest sort works
- [ ] Oldest sort works
- [ ] Highest rating sort works
- [ ] Lowest rating sort works

#### Test 5: Error Handling
```bash
# Test invalid parameters
curl -X GET \
  'https://kfvf20j7j9.execute-api.us-east-2.amazonaws.com/prod/customer/reviews-about-me?limit=999' \
  -H "Authorization: Bearer $TOKEN"
```
- [ ] Returns 400 for invalid limit
- [ ] Returns 400 for invalid sort
- [ ] Returns 401 for missing token
- [ ] Error messages are clear

---

## Performance Verification

### Database Query Performance
```sql
-- Test query performance
EXPLAIN SELECT 
    r.review_id,
    r.job_id,
    r.booking_id,
    r.provider_id,
    r.rating,
    r.comment,
    r.created_at,
    r.updated_at,
    sp.business_name as provider_name,
    sp.average_rating as provider_rating,
    COALESCE(b.service_description, j.title) as service_title
FROM provider_customer_reviews r
LEFT JOIN service_providers sp ON r.provider_id = sp.provider_id
LEFT JOIN bookings b ON r.booking_id = b.booking_id
LEFT JOIN jobs j ON r.job_id = j.job_id
WHERE r.customer_id = 1
ORDER BY r.created_at DESC
LIMIT 20 OFFSET 0;
```

**Verify:**
- [ ] Uses index `idx_pc_customer_created`
- [ ] No full table scans
- [ ] Query time < 50ms

### Lambda Performance
- [ ] Cold start < 1000ms
- [ ] Warm execution < 200ms
- [ ] Memory usage < 128MB
- [ ] No timeouts

---

## Security Verification

### Authentication
- [ ] Requires valid JWT token
- [ ] Rejects requests without token (401)
- [ ] Rejects expired tokens (401)

### Authorization
- [ ] Customer can only see their own reviews
- [ ] Cannot access other customers' reviews
- [ ] Customer ID extracted from JWT, not query params

### Input Validation
- [ ] Validates limit (1-100)
- [ ] Validates offset (≥0)
- [ ] Validates sort options
- [ ] Sanitizes all inputs

### SQL Injection Protection
- [ ] Uses parameterized queries
- [ ] No string concatenation in SQL
- [ ] All user inputs escaped

---

## Frontend Integration Checklist

### API Client Updates
- [ ] Add endpoint to API client
- [ ] Add TypeScript types/interfaces
- [ ] Add error handling
- [ ] Add loading states

### UI Components
- [ ] Create ReviewsAboutMe component
- [ ] Add to customer profile/dashboard
- [ ] Implement pagination controls
- [ ] Add sort dropdown
- [ ] Show empty state message

### Testing
- [ ] Unit tests for API calls
- [ ] Integration tests for component
- [ ] E2E tests for user flow
- [ ] Test error scenarios

---

## Documentation Checklist

### For Developers
- [x] API documentation complete
- [x] Code comments added
- [x] Deployment guide written
- [x] Test scripts documented

### For Users
- [ ] User guide created (if needed)
- [ ] FAQ updated
- [ ] Help text in UI
- [ ] Tooltips added

---

## Rollback Plan

If issues occur:

### Rollback Lambda
```bash
# List versions
aws lambda list-versions-by-function \
  --function-name get_customer_reviews_about_me \
  --region us-east-2

# Rollback to previous version
aws lambda update-alias \
  --function-name get_customer_reviews_about_me \
  --name prod \
  --function-version <PREVIOUS_VERSION> \
  --region us-east-2
```

### Rollback API Gateway
```bash
# List deployments
aws apigateway get-deployments \
  --rest-api-id kfvf20j7j9 \
  --region us-east-2

# Rollback to previous deployment
aws apigateway create-deployment \
  --rest-api-id kfvf20j7j9 \
  --stage-name prod \
  --description "Rollback" \
  --region us-east-2
```

### Remove Endpoint
- [ ] Delete API Gateway method
- [ ] Delete Lambda function
- [ ] Update frontend to hide feature

---

## Success Criteria

The deployment is successful when:

- [x] Lambda function deployed without errors
- [ ] API Gateway endpoint configured correctly
- [ ] All tests pass
- [ ] No errors in CloudWatch logs
- [ ] Response times < 200ms
- [ ] Frontend can fetch and display reviews
- [ ] Empty state handled gracefully
- [ ] Pagination works correctly
- [ ] Sorting works correctly
- [ ] Error handling works as expected

---

## Next Steps After Deployment

1. **Monitor for 24 hours**
   - Check CloudWatch logs regularly
   - Monitor error rates
   - Track response times

2. **Gather feedback**
   - Test with real users
   - Collect UI/UX feedback
   - Identify edge cases

3. **Optimize if needed**
   - Add caching if response times high
   - Adjust pagination defaults
   - Add additional indexes if needed

4. **Future enhancements**
   - Add filtering by rating
   - Add search functionality
   - Add review statistics
   - Add export functionality

---

## Support Contacts

- **Backend Issues:** Check CloudWatch logs
- **Database Issues:** Check RDS metrics
- **API Gateway Issues:** Check API Gateway logs
- **Frontend Issues:** Check browser console

---

## Completion Sign-off

- [ ] All deployment steps completed
- [ ] All tests passing
- [ ] Documentation updated
- [ ] Team notified
- [ ] Monitoring configured
- [ ] Ready for production use

**Deployed by:** _________________  
**Date:** _________________  
**Version:** 1.0.0
