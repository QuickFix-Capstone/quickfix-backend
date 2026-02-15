# Customer Reviews: Endpoint Comparison

## Overview

QuickFix has two customer review endpoints that serve different purposes. This document clarifies the difference between them.

---

## Endpoint Comparison

| Feature | `/customer/reviews` | `/customer/reviews-about-me` |
|---------|---------------------|------------------------------|
| **Purpose** | Reviews I wrote | Reviews written about me |
| **Reviewer** | Customer (me) | Service Provider |
| **Reviewee** | Service Provider | Customer (me) |
| **Use Case** | "My review history" | "My reputation" |
| **Table** | `customer_provider_reviews` | `provider_customer_reviews` |
| **Direction** | Customer → Provider | Provider → Customer |

---

## Visual Representation

```
┌─────────────────────────────────────────────────────────────┐
│                    Customer Reviews System                   │
└─────────────────────────────────────────────────────────────┘

GET /customer/reviews
┌──────────┐                    ┌──────────┐
│ Customer │ ──── reviews ────> │ Provider │
│   (Me)   │                    │          │
└──────────┘                    └──────────┘
"I reviewed this provider"


GET /customer/reviews-about-me
┌──────────┐                    ┌──────────┐
│ Customer │ <──── reviews ──── │ Provider │
│   (Me)   │                    │          │
└──────────┘                    └──────────┘
"This provider reviewed me"
```

---

## Detailed Comparison

### GET /customer/reviews

**What it shows:** Reviews that I (the customer) have written about service providers

**Example scenario:**
- I hired John's Plumbing to fix my sink
- After the job, I wrote a 5-star review about John
- This review appears in `/customer/reviews`

**Response example:**
```json
{
  "reviews": [
    {
      "review_id": 1,
      "provider_name": "John's Plumbing",
      "rating": 5,
      "comment": "Excellent service! Fixed my sink quickly.",
      "created_at": "2024-01-15T10:30:00"
    }
  ],
  "customer": {
    "total_reviews_written": 1
  }
}
```

**Use cases:**
- View my review history
- Edit/delete my past reviews
- See which providers I've reviewed
- Track my feedback to providers

---

### GET /customer/reviews-about-me

**What it shows:** Reviews that service providers have written about me (the customer)

**Example scenario:**
- I hired John's Plumbing to fix my sink
- After the job, John wrote a review about me as a customer
- This review appears in `/customer/reviews-about-me`

**Response example:**
```json
{
  "reviews": [
    {
      "review_id": 1,
      "provider_name": "John's Plumbing",
      "rating": 5,
      "comment": "Great customer! Clear communication and prompt payment.",
      "created_at": "2024-01-15T11:00:00"
    }
  ],
  "customer": {
    "total_reviews_received": 1
  }
}
```

**Use cases:**
- View my reputation as a customer
- See feedback from providers
- Understand how providers perceive me
- Build trust with future providers

---

## Database Schema

### customer_provider_reviews
**Used by:** `/customer/reviews`

```sql
CREATE TABLE customer_provider_reviews (
    review_id BIGINT PRIMARY KEY,
    customer_id BIGINT NOT NULL,  -- Reviewer (me)
    provider_id BIGINT NOT NULL,  -- Reviewee (them)
    rating INT NOT NULL,
    comment TEXT NOT NULL,
    ...
);
```

### provider_customer_reviews
**Used by:** `/customer/reviews-about-me`

```sql
CREATE TABLE provider_customer_reviews (
    review_id BIGINT PRIMARY KEY,
    provider_id BIGINT NOT NULL,  -- Reviewer (them)
    customer_id BIGINT NOT NULL,  -- Reviewee (me)
    rating INT NOT NULL,
    comment TEXT NOT NULL,
    ...
);
```

---

## Query Parameters

Both endpoints support the same query parameters:

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `limit` | integer | 20 | Results per page (1-100) |
| `offset` | integer | 0 | Pagination offset |
| `sort` | string | "newest" | Sort order |

**Sort options:**
- `newest` - Most recent first
- `oldest` - Oldest first
- `highest_rating` - Highest rated first
- `lowest_rating` - Lowest rated first

---

## Frontend Integration

### Separate Tabs/Sections

```javascript
// Tab 1: Reviews I Wrote
const MyReviews = () => {
  const [reviews, setReviews] = useState([]);
  
  useEffect(() => {
    fetch('/customer/reviews', {
      headers: { 'Authorization': `Bearer ${token}` }
    })
    .then(res => res.json())
    .then(data => setReviews(data.reviews));
  }, []);
  
  return (
    <div>
      <h2>Reviews I Wrote</h2>
      {reviews.map(review => (
        <ReviewCard 
          key={review.review_id}
          providerName={review.provider_name}
          rating={review.rating}
          comment={review.comment}
          canEdit={true}  // I can edit my own reviews
        />
      ))}
    </div>
  );
};

// Tab 2: Reviews About Me
const ReviewsAboutMe = () => {
  const [reviews, setReviews] = useState([]);
  
  useEffect(() => {
    fetch('/customer/reviews-about-me', {
      headers: { 'Authorization': `Bearer ${token}` }
    })
    .then(res => res.json())
    .then(data => setReviews(data.reviews));
  }, []);
  
  return (
    <div>
      <h2>Reviews About Me</h2>
      {reviews.map(review => (
        <ReviewCard 
          key={review.review_id}
          providerName={review.provider_name}
          rating={review.rating}
          comment={review.comment}
          canEdit={false}  // I cannot edit reviews about me
        />
      ))}
    </div>
  );
};
```

---

## Common Questions

### Q: Can I edit reviews about me?
**A:** No. Reviews about you are written by providers and can only be edited by them.

### Q: Can I delete reviews about me?
**A:** No. However, you may be able to report inappropriate reviews (future feature).

### Q: Can providers see my reviews about them?
**A:** Yes. Provider reviews are public and visible to the provider.

### Q: Can I see reviews about other customers?
**A:** No. You can only see reviews about yourself for privacy reasons.

### Q: What if I have no reviews?
**A:** Both endpoints return an empty array with `total_count: 0`. This is normal for new users.

---

## Testing Both Endpoints

```bash
# Get customer token
TOKEN=$(./get_customer_token.sh)

# Test reviews I wrote
curl -X GET \
  'https://kfvf20j7j9.execute-api.us-east-2.amazonaws.com/prod/customer/reviews' \
  -H "Authorization: Bearer $TOKEN" | jq '.customer.total_reviews_written'

# Test reviews about me
curl -X GET \
  'https://kfvf20j7j9.execute-api.us-east-2.amazonaws.com/prod/customer/reviews-about-me' \
  -H "Authorization: Bearer $TOKEN" | jq '.customer.total_reviews_received'
```

---

## Summary

| Aspect | `/customer/reviews` | `/customer/reviews-about-me` |
|--------|---------------------|------------------------------|
| **I am the...** | Reviewer | Reviewee |
| **Shows reviews by...** | Me | Providers |
| **Shows reviews about...** | Providers | Me |
| **I can edit...** | ✅ Yes | ❌ No |
| **I can delete...** | ✅ Yes | ❌ No |
| **Purpose** | My feedback history | My reputation |

---

## Related Documentation

- [GET /customer/reviews API](./FRONTEND_GET_CUSTOMER_REVIEWS_GUIDE.md)
- [GET /customer/reviews-about-me API](./API_CUSTOMER_REVIEWS_ABOUT_ME.md)
- [POST /customer/review API](./API_CREATE_CUSTOMER_PROVIDER_REVIEW.md)
