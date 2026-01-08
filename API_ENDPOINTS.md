# QuickFix API Endpoints

## Base URL
```
https://bpielc3fzh.execute-api.us-east-2.amazonaws.com/prod
```

## Authentication
All endpoints require JWT authentication via AWS Cognito.

**Header:**
```
Authorization: Bearer <JWT_TOKEN>
```

**Cognito Details:**
- User Pool ID: `us-east-2_45z5OMePi`
- App Client ID: `p2u5qdegml3hp60n6ohu52n2b`
- Region: `us-east-2`

---

## Reviews Endpoints

### Create Review

Create a new review for a completed job.

**Endpoint:** `POST /reviews`

**Authentication:** Required (JWT)

**Request Body:**
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

**Field Validations:**
- `job_id`: Must exist and be in "completed" status
- `reviewer_type`: Must be "customer" or "provider"
- `reviewee_type`: Must be "customer" or "provider"
- `rating`: Integer between 1-5 (inclusive)
- `comment`: String between 10-1000 characters
- Cannot review yourself
- Cannot submit duplicate reviews for the same job

**Success Response (201 Created):**
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
    "created_at": "2026-01-08T02:52:15"
  }
}
```

**Error Responses:**

| Status Code | Description | Example Response |
|-------------|-------------|------------------|
| 400 | Invalid input / validation failed | `{"message": "rating must be between 1 and 5"}` |
| 401 | Unauthorized (missing or invalid JWT) | `{"message": "Unauthorized"}` |
| 404 | Job not found | `{"message": "Job not found"}` |
| 409 | Duplicate review | `{"message": "You have already submitted a review for this job"}` |
| 500 | Internal server error | `{"message": "Internal server error while creating review"}` |

**cURL Example:**
```bash
curl -X POST \
  https://bpielc3fzh.execute-api.us-east-2.amazonaws.com/prod/reviews \
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

**JavaScript Fetch Example:**
```javascript
const createReview = async (reviewData, jwtToken) => {
  const response = await fetch(
    'https://bpielc3fzh.execute-api.us-east-2.amazonaws.com/prod/reviews',
    {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${jwtToken}`
      },
      body: JSON.stringify(reviewData)
    }
  );

  const data = await response.json();

  if (!response.ok) {
    throw new Error(data.message || 'Failed to create review');
  }

  return data;
};

// Usage
const review = {
  job_id: 123,
  reviewer_id: 1,
  reviewer_type: "customer",
  reviewee_id: 5,
  reviewee_type: "provider",
  rating: 5,
  comment: "Excellent service! Very professional."
};

createReview(review, userJwtToken)
  .then(result => console.log('Review created:', result))
  .catch(error => console.error('Error:', error));
```

---

## CORS Configuration

All endpoints support CORS with the following headers:
- `Access-Control-Allow-Origin: *`
- `Access-Control-Allow-Headers: Content-Type, Authorization`
- `Access-Control-Allow-Methods: POST, OPTIONS`

---

## Rate Limiting

API Gateway may apply rate limiting. Contact your administrator for current limits.

---

## Support

For issues or questions:
- Check Lambda logs: `/aws/lambda/create_review`
- Review deployment documentation: `deploy/DEPLOY_CREATE_REVIEW.md`
