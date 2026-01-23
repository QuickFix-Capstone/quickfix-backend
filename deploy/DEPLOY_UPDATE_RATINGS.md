# Deploy update_ratings Lambda Function

## Overview

This guide covers the deployment of the `update_ratings` Lambda function, which recalculates and updates aggregated ratings for service providers and customers after review changes.

## Prerequisites

- AWS CLI configured with appropriate credentials
- Python 3.11+ installed locally
- Access to AWS Lambda and IAM roles
- Network access to RDS database from Lambda (VPC configuration if needed)

## Deployment Steps

### Step 1: Create the Lambda Function

Run the creation script (first time only):

```bash
cd deploy
./create_update_ratings_lambda.sh
```

This script will:
1. Create the Lambda function in AWS
2. Configure environment variables (database credentials)
3. Automatically deploy the initial code via `deploy_update_ratings.sh`

**Expected Output:**
```
🚀 Creating Lambda function: update_ratings...
✅ Lambda function created successfully!
Now deploying the actual code...
✅ Deployed update_ratings
```

### Step 2: Update Lambda Code (Subsequent Deployments)

For code updates after the initial creation:

```bash
cd deploy
./deploy_update_ratings.sh
```

This script will:
1. Package the Lambda code with dependencies
2. Upload the deployment package to AWS
3. Update the Lambda function code

## Lambda Configuration

### Function Details

| Setting | Value |
|---------|-------|
| Function Name | `update_ratings` |
| Runtime | Python 3.11 |
| Handler | `handler.handler` |
| Timeout | 30 seconds |
| Memory | 256 MB |
| Region | us-east-2 |

### Environment Variables

The following environment variables are automatically configured:

| Variable | Description |
|----------|-------------|
| `MYSQL_HOST` | RDS MySQL hostname |
| `MYSQL_USER` | Database username |
| `MYSQL_PASSWORD` | Database password |
| `MYSQL_DB` | Database name (quickfix) |
| `MYSQL_PORT` | Database port (3306) |

### IAM Role

The Lambda uses the existing role:
```
arn:aws:iam::008971679867:role/service-role/create_customer-role-qch33m23
```

This role must have:
- ✅ Lambda execution permissions
- ✅ CloudWatch Logs write permissions
- ✅ VPC network access (if RDS is in VPC)
- ✅ RDS database access (security group configuration)

## Testing the Deployment

### Option 1: AWS CLI Test

Test with AWS CLI:

```bash
# Test updating provider rating
aws lambda invoke \
  --function-name update_ratings \
  --region us-east-2 \
  --payload '{"reviewee_id": 1, "reviewee_type": "provider"}' \
  response.json

cat response.json
```

### Option 2: Python boto3 Test

Run the provided test script:

```bash
cd lambda/reviews/update_ratings
python3 test_aws_invocation.py
```

This will:
- Get Lambda function info
- Test provider rating update
- Test customer rating update
- Test async invocation
- Test error handling

### Option 3: Local Testing

Test the handler locally (without AWS):

```bash
cd lambda/reviews/update_ratings
python3 handler.py
```

Or use the test script:

```bash
python3 test_update_ratings.py
```

## Monitoring

### CloudWatch Logs

View Lambda execution logs:

```bash
# Tail logs in real-time
aws logs tail /aws/lambda/update_ratings --follow --region us-east-2

# View recent logs
aws logs tail /aws/lambda/update_ratings --since 1h --region us-east-2
```

### Metrics to Monitor

Monitor these CloudWatch metrics:

| Metric | Expected Value | Alert If |
|--------|----------------|----------|
| Invocations | Matches review creates/updates/deletes | N/A |
| Errors | 0 | > 0% |
| Duration | < 500ms | > 1000ms |
| Throttles | 0 | > 0 |

### Common Logs

**Success:**
```
Rating updated successfully
```

**Database Connection Error:**
```
Database connection failed
```

**Invalid Input:**
```
reviewee_type must be 'customer' or 'provider'
```

## Integration with Other Lambdas

This Lambda is designed to be invoked by other Lambdas. It does **NOT** require an API Gateway route (internal use only).

### Asynchronous Invocation (Recommended)

```python
import boto3
import json

lambda_client = boto3.client('lambda')

# After creating/updating/deleting a review
lambda_client.invoke(
    FunctionName='update_ratings',
    InvocationType='Event',  # Async - fire and forget
    Payload=json.dumps({
        "reviewee_id": reviewee_id,
        "reviewee_type": reviewee_type  # "provider" or "customer"
    })
)
```

**Pros:**
- Non-blocking (doesn't slow down review creation)
- Automatic retry on failure
- Lower latency for review API

**Cons:**
- No immediate confirmation of success
- Slightly eventual consistency (rating updates after ~1-2 seconds)

### Synchronous Invocation

```python
response = lambda_client.invoke(
    FunctionName='update_ratings',
    InvocationType='RequestResponse',  # Sync - wait for response
    Payload=json.dumps({
        "reviewee_id": reviewee_id,
        "reviewee_type": reviewee_type
    })
)

result = json.loads(response['Payload'].read())
# Check result['statusCode'] for success
```

**Pros:**
- Immediate confirmation of success/failure
- Strong consistency (rating updated before API returns)

**Cons:**
- Blocks review creation API
- Higher latency
- Single point of failure

**Recommendation:** Use **async invocation** for production.

## Troubleshooting

### Issue: Lambda times out

**Cause:** Database connection slow or query takes too long

**Solution:**
- Check database is accessible from Lambda
- Verify security group rules allow Lambda → RDS traffic
- Check database performance (too many reviews?)
- Increase Lambda timeout if needed

### Issue: Database connection failed

**Cause:** Incorrect credentials or network configuration

**Solution:**
- Verify environment variables are correct
- Check Lambda is in same VPC as RDS (if RDS is in VPC)
- Verify security group allows inbound on port 3306
- Test database connection from Lambda's VPC

### Issue: Rating not updating

**Cause:** No reviews exist for the user, or wrong reviewee_id

**Solution:**
- Check database: `SELECT * FROM reviews WHERE reviewee_id = X AND reviewee_type = 'provider'`
- Verify reviewee_id is correct
- If no reviews exist, rating should be 0.00 (this is correct behavior)

### Issue: Permission denied

**Cause:** IAM role lacks necessary permissions

**Solution:**
- Ensure role has AWSLambdaVPCAccessExecutionRole (if using VPC)
- Add CloudWatch Logs permissions
- Verify database security group allows Lambda's security group

## Rolling Back

If deployment fails or introduces bugs:

```bash
# List function versions
aws lambda list-versions-by-function \
  --function-name update_ratings \
  --region us-east-2

# Revert to previous version
aws lambda update-function-code \
  --function-name update_ratings \
  --region us-east-2 \
  --s3-bucket YOUR_BACKUP_BUCKET \
  --s3-key previous-version.zip
```

**Better approach:** Keep previous `.build/update_ratings.zip` file:

```bash
# Backup before deploying
cp .build/update_ratings.zip .build/update_ratings.zip.backup

# Rollback if needed
aws lambda update-function-code \
  --function-name update_ratings \
  --zip-file fileb://.build/update_ratings.zip.backup \
  --region us-east-2
```

## Next Steps

After deploying `update_ratings`, you need to:

1. **Integrate with `create_review` Lambda**
   - Modify `lambda/reviews/create_review/handler.py`
   - Add Lambda invocation after review creation (line 167)
   - Redeploy `create_review` Lambda

2. **Test End-to-End Flow**
   - Create a review via `create_review` API
   - Wait 1-2 seconds (async invocation)
   - Check database to verify rating updated
   - Query provider/customer to see new rating

3. **Integrate with Future Endpoints**
   - `update_review` - Call update_ratings when rating changes
   - `delete_review` - Call update_ratings to recalculate

4. **Add Monitoring Alerts**
   - CloudWatch alarm for errors > 0%
   - CloudWatch alarm for duration > 1s
   - SNS notification on failures

## Deployment Checklist

Before deploying to production:

- [ ] Lambda function created successfully
- [ ] Code deployed and Lambda is "Active"
- [ ] Environment variables configured correctly
- [ ] Database credentials valid
- [ ] Network connectivity verified (Lambda → RDS)
- [ ] Security groups configured
- [ ] CloudWatch Logs accessible
- [ ] Test invocation successful (boto3 or AWS CLI)
- [ ] Provider rating update works
- [ ] Customer rating update works
- [ ] Error handling tested (invalid input)
- [ ] Integrated with `create_review` Lambda
- [ ] End-to-end test completed (create review → rating updates)

## Support

For issues or questions:
- Check CloudWatch Logs first: `/aws/lambda/update_ratings`
- Review database schema: `sql/migrations/add_rating_summary_to_users.sql`
- See README: `lambda/reviews/update_ratings/README.md`
- Review implementation plan: `docs/REVIEW_SYSTEM_IMPLEMENTATION_PLAN.md`

---

**Last Updated:** 2026-01-08
**Lambda ARN:** `arn:aws:lambda:us-east-2:008971679867:function:update_ratings`
