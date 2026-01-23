# Update Ratings Lambda Function

## Overview

This Lambda function recalculates and updates the aggregated rating for service providers and customers based on all reviews they have received. It is designed to be called internally by other Lambda functions (like `create_review`, `update_review`, `delete_review`) whenever review data changes.

## Purpose

When reviews are created, updated, or deleted, the rating aggregates need to be recalculated:
- **Service Providers:** Updates `service_providers.rating`, `total_rating_points`, `total_review_count`
- **Customers:** Updates `customers.average_rating`, `total_rating_points`, `total_review_count`

## Input

The function accepts a JSON payload with two required fields:

```json
{
  "reviewee_id": 5,
  "reviewee_type": "provider"
}
```

### Parameters

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `reviewee_id` | integer | Yes | The ID of the provider or customer whose rating should be updated |
| `reviewee_type` | string | Yes | Either `"provider"` or `"customer"` |

## Output

### Success Response (200)

```json
{
  "message": "Rating updated successfully",
  "rating_info": {
    "reviewee_type": "provider",
    "reviewee_id": 5,
    "rating": 4.75,
    "total_rating_points": 19,
    "total_review_count": 4
  }
}
```

### Error Responses

| Status Code | Description |
|-------------|-------------|
| 400 | Invalid input (missing fields, invalid type, invalid ID) |
| 500 | Database connection failed or internal error |

## How It Works

### For Providers

1. Queries all reviews where `reviewee_id = {provider_id}` AND `reviewee_type = 'provider'`
2. Calculates:
   - `total_review_count` = COUNT of reviews
   - `total_rating_points` = SUM of all ratings
   - `rating` = total_rating_points / total_review_count (or 0.00 if no reviews)
3. Updates `service_providers` table with calculated values

### For Customers

1. Queries all reviews where `reviewee_id = {customer_id}` AND `reviewee_type = 'customer'`
2. Calculates:
   - `total_review_count` = COUNT of reviews
   - `total_rating_points` = SUM of all ratings
   - `average_rating` = total_rating_points / total_review_count (or 0.00 if no reviews)
3. Updates `customers` table with calculated values

## Usage Examples

### Invocation from Another Lambda (Asynchronous)

```python
import boto3
import json

lambda_client = boto3.client('lambda')

# Invoke update_ratings Lambda after creating a review
payload = {
    "reviewee_id": 5,
    "reviewee_type": "provider"
}

lambda_client.invoke(
    FunctionName='update_ratings',
    InvocationType='Event',  # Asynchronous invocation
    Payload=json.dumps(payload)
)
```

### Invocation from Another Lambda (Synchronous)

```python
import boto3
import json

lambda_client = boto3.client('lambda')

# Invoke update_ratings Lambda and wait for response
payload = {
    "reviewee_id": 5,
    "reviewee_type": "provider"
}

response = lambda_client.invoke(
    FunctionName='update_ratings',
    InvocationType='RequestResponse',  # Synchronous invocation
    Payload=json.dumps(payload)
)

result = json.loads(response['Payload'].read())
print(result)  # {"statusCode": 200, "body": "..."}
```

### Direct Testing (API Gateway - Optional)

If you choose to expose this as an API endpoint:

```bash
curl -X POST https://API_ID.execute-api.REGION.amazonaws.com/prod/ratings/update \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -d '{
    "reviewee_id": 5,
    "reviewee_type": "provider"
  }'
```

### Local Testing

```bash
cd lambda/reviews/update_ratings
python handler.py
```

This will run the test scenarios defined in `if __name__ == "__main__"` block.

## Integration with Other Lambda Functions

This function is designed to be called from:

### 1. `create_review` Lambda
After successfully creating a review, invoke `update_ratings` to update the reviewee's rating:

```python
# In create_review/handler.py, after line 167 (conn.commit())

import boto3
lambda_client = boto3.client('lambda')

# Invoke update_ratings asynchronously
lambda_client.invoke(
    FunctionName='update_ratings',
    InvocationType='Event',
    Payload=json.dumps({
        "reviewee_id": data["reviewee_id"],
        "reviewee_type": data["reviewee_type"]
    })
)
```

### 2. `update_review` Lambda (Future)
When a review's rating changes, recalculate the reviewee's rating:

```python
# After updating review in database
lambda_client.invoke(
    FunctionName='update_ratings',
    InvocationType='Event',
    Payload=json.dumps({
        "reviewee_id": reviewee_id,
        "reviewee_type": reviewee_type
    })
)
```

### 3. `delete_review` Lambda (Future)
When a review is deleted, recalculate the reviewee's rating:

```python
# After deleting review from database
lambda_client.invoke(
    FunctionName='update_ratings',
    InvocationType='Event',
    Payload=json.dumps({
        "reviewee_id": reviewee_id,
        "reviewee_type": reviewee_type
    })
)
```

## Edge Cases Handled

1. **No reviews exist:** Rating set to 0.00, counts set to 0
2. **Single review:** Rating equals that review's rating
3. **Multiple reviews:** Calculates accurate average with 2 decimal precision
4. **All reviews deleted:** Rating reverts to 0.00

## Database Schema Requirements

### service_providers Table

```sql
ALTER TABLE service_providers
ADD COLUMN rating DECIMAL(3,2) DEFAULT 0.00,
ADD COLUMN total_rating_points INT DEFAULT 0,
ADD COLUMN total_review_count INT DEFAULT 0;
```

### customers Table

```sql
ALTER TABLE customers
ADD COLUMN average_rating DECIMAL(3,2) DEFAULT 0.00,
ADD COLUMN total_rating_points INT DEFAULT 0,
ADD COLUMN total_review_count INT DEFAULT 0;
```

## Environment Variables

This Lambda function uses the same database connection configuration as other review Lambdas:

- Database connection configured via `src.db.rds_main.get_connection()`
- Environment variables should be set during deployment (see deployment scripts)

## Error Handling

- **Database connection failures:** Returns 500 error
- **Invalid input:** Returns 400 error with descriptive message
- **SQL errors:** Transaction rollback + 500 error
- **All errors logged to CloudWatch** for debugging

## Performance Considerations

- **Query efficiency:** Uses indexed columns (`reviewee_id`, `reviewee_type`)
- **Aggregation:** Single query with COUNT and SUM (efficient)
- **Transaction safety:** Uses commits and rollbacks appropriately
- **Execution time:** Typically < 500ms for providers with < 1000 reviews

## Testing Checklist

- [ ] Provider with 0 reviews → rating = 0.00
- [ ] Provider with 1 review (5 stars) → rating = 5.00
- [ ] Provider with multiple reviews → accurate average (e.g., [5,4,5,4] = 4.50)
- [ ] Customer rating updates work identically
- [ ] Invalid reviewee_type rejected with 400
- [ ] Invalid reviewee_id rejected with 400
- [ ] Missing fields rejected with 400
- [ ] Database connection failure handled gracefully

## Deployment

See deployment scripts:
- `deploy/create_update_ratings_lambda.sh` - Create Lambda function
- `deploy/deploy_update_ratings.sh` - Update Lambda code

The Lambda function does **NOT** require an API Gateway route by default, as it's designed for internal Lambda-to-Lambda invocation.

## Monitoring

Monitor this function via CloudWatch:
- **Invocation count:** Should match number of review creates/updates/deletes
- **Error rate:** Should be near 0%
- **Duration:** Should be < 500ms
- **Logs:** Check for database errors or invalid inputs

## Future Enhancements

1. **Batch updates:** Update multiple ratings in a single invocation
2. **Caching:** Cache rating calculations for high-volume providers
3. **Weighted ratings:** Apply recency weighting (newer reviews count more)
4. **Validation:** Verify provider/customer exists before updating
