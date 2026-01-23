# API Route Suggestions for get_provider_reviews

## Lambda Function Details
- **Function Name:** `get_provider_reviews`
- **ARN:** `arn:aws:lambda:us-east-2:008971679867:function:get_provider_reviews`
- **Status:** ✅ Deployed and Active

---

## Recommended API Routes

### Option 1: RESTful Style (RECOMMENDED) ⭐

```
GET /reviews/provider/{provider_id}
```

**Why this is best:**
- ✅ RESTful and intuitive
- ✅ Consistent with existing `GET /reviews/{review_id}` pattern
- ✅ Clear resource hierarchy: reviews → provider → specific provider
- ✅ Easy to understand: "Get reviews for this provider"

**Example URLs:**
```
GET /reviews/provider/SP-001
GET /reviews/provider/SP-001?sort=highest_rating&limit=20
GET /reviews/provider/google-oauth2|123456789?sort=newest&offset=10
```

**Authorization:** JWT (customers and providers can view reviews)

---

### Option 2: Query Parameter Style

```
GET /reviews?reviewee_type=provider&reviewee_id={provider_id}
```

**Pros:**
- More flexible for filtering
- Could reuse same endpoint for customers

**Cons:**
- ❌ Less intuitive
- ❌ Longer URLs
- ❌ Not as RESTful

---

### Option 3: Provider-Centric Route

```
GET /providers/{provider_id}/reviews
```

**Pros:**
- Provider-centric perspective
- Matches pattern like `/users/{id}/posts`

**Cons:**
- ❌ Inconsistent with your existing `/reviews/*` pattern
- ❌ Would require different route structure

---

## My Strong Recommendation: Option 1

```
GET /prod/reviews/provider/{provider_id}
```

### Query Parameters:
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `sort` | string | `newest` | Sort order: `newest`, `oldest`, `highest_rating`, `lowest_rating` |
| `limit` | integer | `10` | Results per page (1-100) |
| `offset` | integer | `0` | Pagination offset |

### Response Format:
```json
{
  "reviews": [
    {
      "review_id": 123,
      "job_id": 456,
      "reviewer_id": 1,
      "reviewer_name": "John Doe",
      "reviewer_type": "customer",
      "rating": 5,
      "comment": "Excellent service!",
      "created_at": "2026-01-12T04:39:34"
    }
  ],
  "pagination": {
    "limit": 10,
    "offset": 0,
    "total_count": 42,
    "has_more": true,
    "next_offset": 10
  },
  "summary": {
    "average_rating": 4.67,
    "total_reviews": 42
  }
}
```

---

## Complete Review System Routes

Here's how all your review endpoints would look together:

| Method | Route | Description | Auth |
|--------|-------|-------------|------|
| POST | `/reviews` | Create a review | JWT |
| GET | `/reviews/{review_id}` | Get single review | JWT |
| GET | `/reviews/provider/{provider_id}` | List provider reviews | JWT |
| GET | `/reviews/customer/{customer_id}` | List customer reviews | JWT |
| GET | `/reviews/job/{job_id}` | List job reviews | JWT |
| PUT | `/reviews/{review_id}` | Update review | JWT |
| DELETE | `/reviews/{review_id}` | Delete review | JWT |
| POST | `/internal/update-ratings` | Update ratings (internal) | JWT/IAM |

**Consistency:** All review-related endpoints start with `/reviews/`

---

## Setup Command (When Ready)

When you're ready to set up the API Gateway route, you can use:

```bash
./deploy/setup_get_provider_reviews_api.sh
```

This script should:
1. Create Lambda integration
2. Create route: `GET /reviews/provider/{provider_id}`
3. Attach JWT authorizer (ID: `z8zn33`)
4. Add Lambda invoke permission
5. Deploy to `prod` stage

---

## Testing After Setup

```bash
# Get JWT token
./scripts/get_jwt_token.sh

# Test the endpoint
curl -X GET \
  "https://kfvf20j7j9.execute-api.us-east-2.amazonaws.com/prod/reviews/provider/SP-001?sort=highest_rating&limit=10" \
  -H "Authorization: Bearer $(cat /tmp/jwt_token.txt)"
```

---

## Next Steps

1. ✅ Lambda deployed
2. ⏳ Create API Gateway route setup script
3. ⏳ Test endpoint with JWT
4. ⏳ Document in API_ENDPOINTS.md
5. ⏳ Update implementation plan

Would you like me to create the `setup_get_provider_reviews_api.sh` script for you?
