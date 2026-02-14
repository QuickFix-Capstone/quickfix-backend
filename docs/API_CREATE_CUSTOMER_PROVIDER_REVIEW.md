# Customer Provider Review API - Frontend Guide

## Overview

This API allows customers to submit reviews for service providers after completing a job or booking. Customers can rate providers on a scale of 1-5 and provide written feedback.

---

## Endpoint

```
POST /customer/reviews
```

**Base URL**: `https://kfvf20j7j9.execute-api.us-east-2.amazonaws.com`

**Full URL**: `https://kfvf20j7j9.execute-api.us-east-2.amazonaws.com/customer/reviews`

---

## Authentication

**Required**: Yes (Customer JWT Token)

Include the JWT token in the Authorization header:

```
Authorization: Bearer <CUSTOMER_JWT_TOKEN>
```

The customer ID is automatically extracted from the JWT token's email claim.

---

## Request

### Headers

```http
Content-Type: application/json
Authorization: Bearer <CUSTOMER_JWT_TOKEN>
```

### Request Body

```json
{
  "job_id": 1079,
  "provider_id": "SP-2f2664c0-7488-429c-9ad2-5d2c10787ead",
  "rating": 5,
  "comment": "Excellent service! Very professional and completed the job on time."
}
```

**OR** for booking-based reviews:

```json
{
  "booking_id": 456,
  "provider_id": "SP-2f2664c0-7488-429c-9ad2-5d2c10787ead",
  "rating": 5,
  "comment": "Excellent service! Very professional and completed the job on time."
}
```

### Field Specifications

| Field | Type | Required | Description | Validation |
|-------|------|----------|-------------|------------|
| `job_id` | number | Conditional* | The ID of the completed job | Must exist and be completed |
| `booking_id` | number | Conditional* | The ID of the completed booking | Must exist and be completed |
| `provider_id` | string | Yes | The ID of the provider being reviewed | Must match the assigned provider |
| `rating` | number | Yes | Rating from 1 to 5 | Integer between 1-5 (inclusive) |
| `comment` | string | Yes | Written review feedback | 10-1000 characters |

**\*Note**: You must provide either `job_id` OR `booking_id`, but not both.

---

## Response

### Success Response (201 Created)

```json
{
  "message": "Review created successfully",
  "review": {
    "review_id": 39,
    "job_id": 1079,
    "booking_id": null,
    "customer_id": 13,
    "provider_id": "SP-2f2664c0-7488-429c-9ad2-5d2c10787ead",
    "rating": 5,
    "comment": "Excellent service! Very professional and completed the job on time. Would definitely hire again.",
    "created_at": "2026-02-14T04:13:49"
  }
}
```

### Error Responses

| Status Code | Description | Example Response |
|-------------|-------------|------------------|
| 400 | Bad Request - Invalid input | `{"message": "rating must be between 1 and 5"}` |
| 400 | Bad Request - Missing fields | `{"message": "Missing required fields: provider_id, comment"}` |
| 400 | Bad Request - Both IDs provided | `{"message": "Cannot specify both job_id and booking_id"}` |
| 400 | Bad Request - Wrong provider | `{"message": "Provider ID does not match the assigned provider for this job"}` |
| 400 | Bad Request - Not completed | `{"message": "Job must be completed before submitting a review"}` |
| 401 | Unauthorized | `{"message": "Unauthorized - missing email in JWT token"}` |
| 403 | Forbidden - Not your job | `{"message": "You can only review jobs that you created"}` |
| 404 | Not Found | `{"message": "Job not found"}` |
| 409 | Conflict - Duplicate | `{"message": "You have already submitted a review for this job or booking"}` |
| 500 | Internal Server Error | `{"message": "Internal server error while creating review"}` |

---

## Frontend Implementation Examples

### React/TypeScript Example

```typescript
// types.ts
export interface CreateReviewRequest {
  job_id?: number;
  booking_id?: number;
  provider_id: string;
  rating: number;
  comment: string;
}

export interface Review {
  review_id: number;
  job_id: number | null;
  booking_id: number | null;
  customer_id: number;
  provider_id: string;
  rating: number;
  comment: string;
  created_at: string;
}

export interface CreateReviewResponse {
  message: string;
  review: Review;
}

export interface ErrorResponse {
  message: string;
}

// api/reviews.ts
const API_BASE_URL = 'https://kfvf20j7j9.execute-api.us-east-2.amazonaws.com';

export const createCustomerProviderReview = async (
  reviewData: CreateReviewRequest,
  jwtToken: string
): Promise<CreateReviewResponse> => {
  const response = await fetch(`${API_BASE_URL}/customer/reviews`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${jwtToken}`
    },
    body: JSON.stringify(reviewData)
  });

  const data = await response.json();

  if (!response.ok) {
    throw new Error(data.message || 'Failed to create review');
  }

  return data;
};

// components/ReviewForm.tsx
import React, { useState } from 'react';
import { createCustomerProviderReview } from '../api/reviews';

interface ReviewFormProps {
  jobId?: number;
  bookingId?: number;
  providerId: string;
  jwtToken: string;
  onSuccess: (review: Review) => void;
  onError: (error: string) => void;
}

export const ReviewForm: React.FC<ReviewFormProps> = ({
  jobId,
  bookingId,
  providerId,
  jwtToken,
  onSuccess,
  onError
}) => {
  const [rating, setRating] = useState<number>(5);
  const [comment, setComment] = useState<string>('');
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    // Validation
    if (comment.length < 10) {
      onError('Comment must be at least 10 characters');
      return;
    }
    
    if (comment.length > 1000) {
      onError('Comment must not exceed 1000 characters');
      return;
    }

    setIsSubmitting(true);

    try {
      const reviewData: CreateReviewRequest = {
        ...(jobId && { job_id: jobId }),
        ...(bookingId && { booking_id: bookingId }),
        provider_id: providerId,
        rating,
        comment
      };

      const response = await createCustomerProviderReview(reviewData, jwtToken);
      onSuccess(response.review);
    } catch (error) {
      onError(error instanceof Error ? error.message : 'Failed to submit review');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="review-form">
      <div className="form-group">
        <label htmlFor="rating">Rating</label>
        <div className="star-rating">
          {[1, 2, 3, 4, 5].map((star) => (
            <button
              key={star}
              type="button"
              onClick={() => setRating(star)}
              className={star <= rating ? 'star active' : 'star'}
              aria-label={`Rate ${star} stars`}
            >
              ★
            </button>
          ))}
        </div>
      </div>

      <div className="form-group">
        <label htmlFor="comment">Your Review</label>
        <textarea
          id="comment"
          value={comment}
          onChange={(e) => setComment(e.target.value)}
          placeholder="Share your experience with this provider (minimum 10 characters)"
          minLength={10}
          maxLength={1000}
          rows={5}
          required
        />
        <small>{comment.length}/1000 characters</small>
      </div>

      <button 
        type="submit" 
        disabled={isSubmitting || comment.length < 10}
      >
        {isSubmitting ? 'Submitting...' : 'Submit Review'}
      </button>
    </form>
  );
};
```

### Vue.js Example

```vue
<template>
  <form @submit.prevent="submitReview" class="review-form">
    <div class="form-group">
      <label>Rating</label>
      <div class="star-rating">
        <button
          v-for="star in 5"
          :key="star"
          type="button"
          @click="rating = star"
          :class="['star', { active: star <= rating }]"
        >
          ★
        </button>
      </div>
    </div>

    <div class="form-group">
      <label for="comment">Your Review</label>
      <textarea
        id="comment"
        v-model="comment"
        placeholder="Share your experience (minimum 10 characters)"
        :minlength="10"
        :maxlength="1000"
        rows="5"
        required
      />
      <small>{{ comment.length }}/1000 characters</small>
    </div>

    <button type="submit" :disabled="isSubmitting || comment.length < 10">
      {{ isSubmitting ? 'Submitting...' : 'Submit Review' }}
    </button>

    <div v-if="error" class="error-message">{{ error }}</div>
    <div v-if="success" class="success-message">Review submitted successfully!</div>
  </form>
</template>

<script setup lang="ts">
import { ref } from 'vue';

interface Props {
  jobId?: number;
  bookingId?: number;
  providerId: string;
  jwtToken: string;
}

const props = defineProps<Props>();
const emit = defineEmits(['success', 'error']);

const rating = ref(5);
const comment = ref('');
const isSubmitting = ref(false);
const error = ref('');
const success = ref(false);

const submitReview = async () => {
  error.value = '';
  success.value = false;

  if (comment.value.length < 10) {
    error.value = 'Comment must be at least 10 characters';
    return;
  }

  isSubmitting.value = true;

  try {
    const reviewData: any = {
      provider_id: props.providerId,
      rating: rating.value,
      comment: comment.value
    };

    if (props.jobId) reviewData.job_id = props.jobId;
    if (props.bookingId) reviewData.booking_id = props.bookingId;

    const response = await fetch(
      'https://kfvf20j7j9.execute-api.us-east-2.amazonaws.com/customer/reviews',
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${props.jwtToken}`
        },
        body: JSON.stringify(reviewData)
      }
    );

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.message || 'Failed to create review');
    }

    success.value = true;
    emit('success', data.review);
  } catch (err) {
    error.value = err instanceof Error ? err.message : 'Failed to submit review';
    emit('error', error.value);
  } finally {
    isSubmitting.value = false;
  }
};
</script>
```

### Plain JavaScript/Fetch Example

```javascript
// reviewService.js
const API_BASE_URL = 'https://kfvf20j7j9.execute-api.us-east-2.amazonaws.com';

/**
 * Create a customer review for a provider
 * @param {Object} reviewData - The review data
 * @param {number} [reviewData.job_id] - Job ID (required if booking_id not provided)
 * @param {number} [reviewData.booking_id] - Booking ID (required if job_id not provided)
 * @param {string} reviewData.provider_id - Provider ID
 * @param {number} reviewData.rating - Rating (1-5)
 * @param {string} reviewData.comment - Review comment (10-1000 chars)
 * @param {string} jwtToken - Customer JWT token
 * @returns {Promise<Object>} The created review
 */
async function createCustomerProviderReview(reviewData, jwtToken) {
  try {
    const response = await fetch(`${API_BASE_URL}/customer/reviews`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${jwtToken}`
      },
      body: JSON.stringify(reviewData)
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.message || `HTTP error! status: ${response.status}`);
    }

    return data;
  } catch (error) {
    console.error('Error creating review:', error);
    throw error;
  }
}

// Usage example
const reviewData = {
  job_id: 1079,
  provider_id: 'SP-2f2664c0-7488-429c-9ad2-5d2c10787ead',
  rating: 5,
  comment: 'Excellent service! Very professional and completed the job on time.'
};

const jwtToken = 'your-jwt-token-here';

createCustomerProviderReview(reviewData, jwtToken)
  .then(response => {
    console.log('Review created:', response.review);
    // Handle success (e.g., show success message, redirect)
  })
  .catch(error => {
    console.error('Failed to create review:', error.message);
    // Handle error (e.g., show error message to user)
  });
```

### Axios Example

```javascript
import axios from 'axios';

const API_BASE_URL = 'https://kfvf20j7j9.execute-api.us-east-2.amazonaws.com';

// Create axios instance with default config
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json'
  }
});

// Add request interceptor to include JWT token
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('customerJwtToken');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Create review function
export const createCustomerProviderReview = async (reviewData) => {
  try {
    const response = await apiClient.post('/customer/reviews', reviewData);
    return response.data;
  } catch (error) {
    if (error.response) {
      // Server responded with error
      throw new Error(error.response.data.message || 'Failed to create review');
    } else if (error.request) {
      // Request made but no response
      throw new Error('No response from server');
    } else {
      // Something else happened
      throw new Error('Failed to create review');
    }
  }
};

// Usage
createCustomerProviderReview({
  job_id: 1079,
  provider_id: 'SP-2f2664c0-7488-429c-9ad2-5d2c10787ead',
  rating: 5,
  comment: 'Excellent service!'
})
  .then(data => console.log('Success:', data))
  .catch(error => console.error('Error:', error.message));
```

---

## Validation Rules

### Client-Side Validation (Recommended)

Implement these validations before making the API call:

```javascript
function validateReviewData(reviewData) {
  const errors = [];

  // Check for job_id or booking_id
  if (!reviewData.job_id && !reviewData.booking_id) {
    errors.push('Either job_id or booking_id is required');
  }

  // Check for both IDs
  if (reviewData.job_id && reviewData.booking_id) {
    errors.push('Cannot specify both job_id and booking_id');
  }

  // Validate provider_id
  if (!reviewData.provider_id || reviewData.provider_id.trim() === '') {
    errors.push('Provider ID is required');
  }

  // Validate rating
  if (!reviewData.rating || reviewData.rating < 1 || reviewData.rating > 5) {
    errors.push('Rating must be between 1 and 5');
  }

  // Validate comment
  if (!reviewData.comment || reviewData.comment.trim().length < 10) {
    errors.push('Comment must be at least 10 characters');
  }

  if (reviewData.comment && reviewData.comment.length > 1000) {
    errors.push('Comment must not exceed 1000 characters');
  }

  return {
    isValid: errors.length === 0,
    errors
  };
}

// Usage
const validation = validateReviewData(reviewData);
if (!validation.isValid) {
  console.error('Validation errors:', validation.errors);
  // Show errors to user
} else {
  // Proceed with API call
}
```

---

## Error Handling Best Practices

```typescript
async function submitReviewWithErrorHandling(
  reviewData: CreateReviewRequest,
  jwtToken: string
) {
  try {
    const response = await createCustomerProviderReview(reviewData, jwtToken);
    
    // Success handling
    showSuccessMessage('Review submitted successfully!');
    return response.review;
    
  } catch (error) {
    // Parse error message
    const errorMessage = error instanceof Error ? error.message : 'Unknown error';
    
    // Handle specific error cases
    if (errorMessage.includes('already submitted')) {
      showErrorMessage('You have already reviewed this job');
    } else if (errorMessage.includes('must be completed')) {
      showErrorMessage('You can only review completed jobs');
    } else if (errorMessage.includes('rating must be')) {
      showErrorMessage('Please select a rating between 1 and 5');
    } else if (errorMessage.includes('at least 10 characters')) {
      showErrorMessage('Please write a more detailed review (minimum 10 characters)');
    } else if (errorMessage.includes('Unauthorized')) {
      showErrorMessage('Please log in to submit a review');
      // Redirect to login
    } else {
      showErrorMessage('Failed to submit review. Please try again.');
    }
    
    throw error;
  }
}
```

---

## Testing

### Test Scenarios

1. **Successful Review Creation**
   - Use a completed job/booking
   - Provide valid rating (1-5) and comment (10-1000 chars)
   - Expected: 201 status with review data

2. **Duplicate Review**
   - Try to review the same job/booking twice
   - Expected: 409 status with duplicate message

3. **Invalid Rating**
   - Provide rating outside 1-5 range
   - Expected: 400 status with validation error

4. **Short Comment**
   - Provide comment less than 10 characters
   - Expected: 400 status with validation error

5. **Missing Fields**
   - Omit required fields
   - Expected: 400 status with missing fields message

6. **Unauthorized Access**
   - Make request without JWT token
   - Expected: 401 status

7. **Wrong Provider**
   - Provide provider_id that doesn't match the job
   - Expected: 400 status with provider mismatch error

---

## Common Issues & Solutions

### Issue: "Unauthorized - missing email in JWT token"
**Solution**: Ensure you're using a valid customer JWT token with email claim.

### Issue: "You have already submitted a review for this job"
**Solution**: Check if the customer has already reviewed this job. Implement UI to show existing review instead of form.

### Issue: "Job must be completed before submitting a review"
**Solution**: Only show review form for jobs/bookings with status "completed".

### Issue: "Provider ID does not match the assigned provider"
**Solution**: Ensure you're passing the correct provider_id from the job/booking data.

### Issue: CORS errors
**Solution**: The API supports CORS. Ensure you're making requests from an allowed origin.

---

## Security Considerations

1. **Never expose JWT tokens** in client-side code or logs
2. **Store tokens securely** (e.g., httpOnly cookies or secure storage)
3. **Validate input** on the client side before sending to API
4. **Handle errors gracefully** without exposing sensitive information
5. **Implement rate limiting** on the frontend to prevent abuse

---

## Support

For issues or questions:
- Check Lambda logs: `/aws/lambda/create_customer_provider_review`
- Review test results: `TEST_RESULTS_create_customer_provider_review.md`
- Backend code: `lambda/reviews/create_customer_provider_review/handler.py`
