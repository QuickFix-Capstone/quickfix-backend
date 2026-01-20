# create_review Lambda Function

Creates a new review for a completed job. Supports bidirectional reviews (customer ↔ provider).

## Function Details

- **Runtime**: Python 3.11
- **Handler**: `handler.handler`
- **Timeout**: 30 seconds
- **Memory**: 256 MB
- **Region**: us-east-2

## Input

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

## Validations

✅ **Required Fields**
- job_id, reviewer_id, reviewer_type, reviewee_id, reviewee_type, rating, comment

✅ **Business Rules**
- Job must exist and be in "completed" status
- Rating must be between 1-5
- Comment must be 10-1000 characters
- Cannot review yourself
- Cannot submit duplicate reviews

✅ **Type Validations**
- reviewer_type: "customer" or "provider"
- reviewee_type: "customer" or "provider"

## Response Codes

| Code | Description |
|------|-------------|
| 201  | Review created successfully |
| 400  | Invalid input / validation failed |
| 404  | Job not found |
| 409  | Duplicate review (already reviewed this job) |
| 500  | Internal server error |

## Local Testing

```bash
# From project root
python test_create_review.py
```

## Deployment

See [../../deploy/DEPLOY_CREATE_REVIEW.md](../../deploy/DEPLOY_CREATE_REVIEW.md) for deployment instructions.

## Database Schema

Inserts into the `reviews` table:

```sql
CREATE TABLE reviews (
    review_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    job_id BIGINT NOT NULL,
    reviewer_id BIGINT NOT NULL,
    reviewer_type ENUM('customer', 'provider') NOT NULL,
    reviewee_id BIGINT NOT NULL,
    reviewee_type ENUM('customer', 'provider') NOT NULL,
    rating INT NOT NULL,
    comment TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);
```

## Future Enhancements

- [ ] Update provider/customer rating statistics after review creation
- [ ] Send notification to reviewee
- [ ] Add review moderation/flagging
- [ ] Support review images/attachments
