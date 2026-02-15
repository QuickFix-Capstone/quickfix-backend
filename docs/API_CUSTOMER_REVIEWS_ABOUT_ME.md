# API Documentation: Customer Reviews About Me

## Overview
This endpoint allows customers to view reviews that service providers have written about them. This is the "Reviews About Me" feature where customers can see their reputation from the provider's perspective.

---

## Endpoint

### GET /prod/customer/reviews-about-me

**Purpose:** Retrieve all reviews that service providers have written about the authenticated customer.

**Authentication:** Required (JWT Bearer token from Cognito)

**Base URL:** `https://kfvf20j7j9.execute-api.us-east-2.amazonaws.com/prod`

---

## Query Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `limit` | integer | No | 20 | Maximum number of reviews to return (1-100) |
| `offset` | integer | No | 0 | Pagination offset for results |
| `sort` | string | No | "newest" | Sort order: `newest`, `oldest`, `highest_rating`, `lowest_rating` |

---

## Request Example

```bash
# Get all reviews about me (default pagination)
curl -X GET \
  'https://kfvf20j7j9.execute-api.us-east-2.amazonaws.com/prod/customer/reviews-about-me' \
  -H 'Authorization: Bearer YOUR_JWT_TOKEN' \
  -H 'Content-Type: application/json'

# Get reviews with custom limit and sort
curl -X GET \
  'https://kfvf20j7j9.execute-api.us-east-2.amazonaws.com/prod/customer/reviews-about-me?limit=10&sort=highest_rating' \
  -H 'Authorization: Bearer YOUR_JWT_TOKEN' \
  -H 'Content-Type: application/json'

# Get reviews with pagination
curl -X GET \
  'https://kfvf20j7j9.execute-api.us-east-2.amazonaws.com/prod/customer/reviews-about-me?limit=5&offset=10' \
  -H 'Authorization: Bearer YOUR_JWT_TOKEN' \
  -H 'Content-Type: application/json'
```

---

## Response Format

### Success Response (200 OK)

```json
{
  "reviews": [
    {
      "review_id": 1,
      "job_id": 123,
      "booking_id": null,
      "provider_id": 456,
      "provider_name": "John's Plumbing Services",
      "provider_rating": 4.8,
      "service_title": "Fix leaking pipe",
      "rating": 5,
      "comment": "Excellent customer! Very clear communication and respectful. Would work with again.",
      "created_at": "2024-01-15T10:30:00",
      "updated_at": "2024-01-15T10:30:00"
    },
    {
      "review_id": 2,
      "job_id": 124,
      "booking_id": null,
      "provider_id": 789,
      "provider_name": "ABC Electrical",
      "provider_rating": 4.5,
      "service_title": "Install ceiling fan",
      "rating": 4,
      "comment": "Good customer, prompt payment and reasonable expectations. Minor delays in response.",
      "created_at": "2024-01-14T14:20:00",
      "updated_at": "2024-01-14T14:20:00"
    }
  ],
  "pagination": {
    "limit": 20,
    "offset": 0,
    "total_count": 2,
    "has_more": false,
    "next_offset": null
  },
  "customer": {
    "customer_id": 1,
    "name": "Jane Doe",
    "total_reviews_received": 2
  }
}
```

### Empty State Response (200 OK)

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

### Error Responses

#### 400 Bad Request
```json
{
  "message": "Invalid query parameters: limit must be between 1 and 100"
}
```

#### 401 Unauthorized
```json
{
  "message": "Unauthorized - missing email in JWT token"
}
```

#### 403 Forbidden
```json
{
  "message": "Customer not found for this email"
}
```

#### 500 Internal Server Error
```json
{
  "message": "Internal server error while retrieving reviews"
}
```

---

## Response Fields

### Review Object

| Field | Type | Description |
|-------|------|-------------|
| `review_id` | integer | Unique identifier for the review |
| `job_id` | integer/null | ID of the job this review is for |
| `booking_id` | integer/null | ID of the booking this review is for |
| `provider_id` | integer | ID of the provider who wrote the review |
| `provider_name` | string | Business name of the provider |
| `provider_rating` | float | Average rating of the provider (0.0-5.0) |
| `service_title` | string | Title/description of the service |
| `rating` | integer | Rating given by provider (1-5) |
| `comment` | string | Review comment text |
| `created_at` | string (ISO 8601) | When the review was created |
| `updated_at` | string (ISO 8601) | When the review was last updated |

### Pagination Object

| Field | Type | Description |
|-------|------|-------------|
| `limit` | integer | Number of results per page |
| `offset` | integer | Current pagination offset |
| `total_count` | integer | Total number of reviews available |
| `has_more` | boolean | Whether more results are available |
| `next_offset` | integer/null | Offset for next page (null if no more) |

### Customer Object

| Field | Type | Description |
|-------|------|-------------|
| `customer_id` | integer | Customer's unique identifier |
| `name` | string | Customer's full name |
| `total_reviews_received` | integer | Total reviews received from providers |

---

## Sort Options

| Value | Description |
|-------|-------------|
| `newest` | Most recent reviews first (default) |
| `oldest` | Oldest reviews first |
| `highest_rating` | Highest rated reviews first, then by date |
| `lowest_rating` | Lowest rated reviews first, then by date |

---

## Database Schema

### Table: provider_customer_reviews

```sql
CREATE TABLE provider_customer_reviews (
    review_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    job_id BIGINT NOT NULL,
    booking_id BIGINT NULL,
    provider_id BIGINT NOT NULL,
    customer_id BIGINT NOT NULL,
    rating INT NOT NULL,
    comment TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    CONSTRAINT fk_pc_review_job FOREIGN KEY (job_id)
        REFERENCES jobs(job_id) ON DELETE CASCADE,
    CONSTRAINT fk_pc_review_booking FOREIGN KEY (booking_id)
        REFERENCES bookings(booking_id) ON DELETE CASCADE,
    CONSTRAINT fk_pc_review_provider FOREIGN KEY (provider_id)
        REFERENCES service_providers(provider_id) ON DELETE CASCADE,
    CONSTRAINT fk_pc_review_customer FOREIGN KEY (customer_id)
        REFERENCES customers(customer_id) ON DELETE CASCADE,
    
    CONSTRAINT unique_provider_job_review UNIQUE (job_id, provider_id),
    CONSTRAINT chk_pc_rating_range CHECK (rating >= 1 AND rating <= 5),
    CONSTRAINT chk_pc_comment_length CHECK (CHAR_LENGTH(comment) >= 10 AND CHAR_LENGTH(comment) <= 1000),
    
    INDEX idx_pc_customer_created (customer_id, created_at DESC)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

---

## Testing

### Using the Test Script

```bash
# Make the test script executable
chmod +x test_reviews_about_me.sh

# Run the tests
./test_reviews_about_me.sh
```

### Manual Testing

```bash
# Get customer token
TOKEN=$(./get_customer_token.sh)

# Test the endpoint
curl -X GET \
  'https://kfvf20j7j9.execute-api.us-east-2.amazonaws.com/prod/customer/reviews-about-me?limit=10' \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" | jq '.'
```

---

## Related Endpoints

- **GET /customer/reviews** - Get reviews written BY the customer about providers
- **POST /customer/review** - Create a review about a provider
- **GET /provider/reviews** - Get reviews about a provider
- **POST /provider/review-customer** - Provider creates a review about a customer (future)

---

## Implementation Notes

1. **Authentication**: Uses Cognito JWT token to identify the customer
2. **Authorization**: Customers can only see reviews about themselves
3. **Performance**: Indexed on `customer_id` and `created_at` for fast queries
4. **Pagination**: Supports offset-based pagination for large result sets
5. **Sorting**: Multiple sort options for different use cases
6. **Data Integrity**: Foreign key constraints ensure data consistency

---

## Frontend Integration

### React Example

```javascript
const fetchReviewsAboutMe = async (limit = 20, offset = 0, sort = 'newest') => {
  const token = await getAuthToken(); // Your auth function
  
  const response = await fetch(
    `https://kfvf20j7j9.execute-api.us-east-2.amazonaws.com/prod/customer/reviews-about-me?limit=${limit}&offset=${offset}&sort=${sort}`,
    {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
    }
  );
  
  if (!response.ok) {
    throw new Error('Failed to fetch reviews');
  }
  
  return await response.json();
};

// Usage
const { reviews, pagination, customer } = await fetchReviewsAboutMe(10, 0, 'highest_rating');
```

---

## Deployment

### Deploy Lambda Function

```bash
# Make deployment script executable
chmod +x deploy/create_get_customer_reviews_about_me_lambda.sh

# Deploy the Lambda function
./deploy/create_get_customer_reviews_about_me_lambda.sh
```

### Configure API Gateway

1. Go to API Gateway console
2. Select your API
3. Create new resource: `/customer/reviews-about-me`
4. Add GET method
5. Set integration type: Lambda Function
6. Select function: `get_customer_reviews_about_me`
7. Enable CORS
8. Add Cognito authorizer
9. Deploy to `prod` stage

---

## Monitoring

### CloudWatch Metrics

- **Invocations**: Number of times the function is called
- **Duration**: Execution time per invocation
- **Errors**: Failed invocations
- **Throttles**: Rate-limited requests

### CloudWatch Logs

Log group: `/aws/lambda/get_customer_reviews_about_me`

---

## Future Enhancements

1. Add filtering by rating range
2. Add search functionality for review comments
3. Add date range filtering
4. Support for review responses/replies
5. Add review statistics (average rating, distribution)
6. Export reviews to PDF/CSV
