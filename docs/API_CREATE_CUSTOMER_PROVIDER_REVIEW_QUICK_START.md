# Customer Provider Review API - Quick Start

## TL;DR

```javascript
// POST https://kfvf20j7j9.execute-api.us-east-2.amazonaws.com/customer/reviews

const response = await fetch(
  'https://kfvf20j7j9.execute-api.us-east-2.amazonaws.com/customer/reviews',
  {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${customerJwtToken}`
    },
    body: JSON.stringify({
      job_id: 1079,  // OR booking_id (not both)
      provider_id: 'SP-xxx',
      rating: 5,  // 1-5
      comment: 'Great service!'  // 10-1000 chars
    })
  }
);

const data = await response.json();
// Returns: { message: "...", review: { review_id, ... } }
```

---

## Request

| Field | Type | Required | Rules |
|-------|------|----------|-------|
| `job_id` | number | Yes* | Completed job |
| `booking_id` | number | Yes* | Completed booking |
| `provider_id` | string | Yes | Must match assigned provider |
| `rating` | number | Yes | 1-5 |
| `comment` | string | Yes | 10-1000 characters |

*Either `job_id` OR `booking_id` required (not both)

---

## Response Codes

| Code | Meaning |
|------|---------|
| 201 | ✅ Review created |
| 400 | ❌ Invalid input |
| 401 | ❌ Not authenticated |
| 403 | ❌ Not your job |
| 404 | ❌ Job not found |
| 409 | ❌ Already reviewed |
| 500 | ❌ Server error |

---

## Common Errors

```javascript
// Duplicate review
{ "message": "You have already submitted a review for this job or booking" }

// Invalid rating
{ "message": "rating must be between 1 and 5" }

// Comment too short
{ "message": "comment must be at least 10 characters" }

// Missing fields
{ "message": "Missing required fields: provider_id, comment" }

// Wrong provider
{ "message": "Provider ID does not match the assigned provider for this job" }

// Not completed
{ "message": "Job must be completed before submitting a review" }
```

---

## Validation Checklist

Before calling the API:

- [ ] User is authenticated (have JWT token)
- [ ] Job/booking status is "completed"
- [ ] Have either `job_id` OR `booking_id` (not both)
- [ ] `provider_id` matches the assigned provider
- [ ] Rating is 1, 2, 3, 4, or 5
- [ ] Comment is 10-1000 characters
- [ ] User hasn't already reviewed this job/booking

---

## React Hook Example

```typescript
import { useState } from 'react';

export const useCreateReview = () => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const createReview = async (
    reviewData: {
      job_id?: number;
      booking_id?: number;
      provider_id: string;
      rating: number;
      comment: string;
    },
    jwtToken: string
  ) => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch(
        'https://kfvf20j7j9.execute-api.us-east-2.amazonaws.com/customer/reviews',
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
        throw new Error(data.message);
      }

      return data.review;
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to create review';
      setError(message);
      throw err;
    } finally {
      setLoading(false);
    }
  };

  return { createReview, loading, error };
};

// Usage in component
function ReviewForm({ jobId, providerId, jwtToken }) {
  const { createReview, loading, error } = useCreateReview();
  const [rating, setRating] = useState(5);
  const [comment, setComment] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const review = await createReview(
        { job_id: jobId, provider_id: providerId, rating, comment },
        jwtToken
      );
      console.log('Review created:', review);
      // Handle success
    } catch (err) {
      // Error is already set in the hook
    }
  };

  return (
    <form onSubmit={handleSubmit}>
      {/* Form fields */}
      {error && <div className="error">{error}</div>}
      <button disabled={loading}>
        {loading ? 'Submitting...' : 'Submit Review'}
      </button>
    </form>
  );
}
```

---

## Testing with cURL

```bash
# Set your token
export TOKEN="your-jwt-token-here"

# Create a review
curl -X POST \
  https://kfvf20j7j9.execute-api.us-east-2.amazonaws.com/customer/reviews \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "job_id": 1079,
    "provider_id": "SP-2f2664c0-7488-429c-9ad2-5d2c10787ead",
    "rating": 5,
    "comment": "Excellent service! Very professional."
  }'
```

---

## Need More Details?

See the full documentation: `API_CREATE_CUSTOMER_PROVIDER_REVIEW.md`
