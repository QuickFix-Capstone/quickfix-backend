# Review System Implementation Plan

**Project:** QuickFix Backend
**Document Created:** 2026-01-08
**Last Updated:** 2026-01-11
**Current Branch:** kunpeng/lambda-db-setup
**Completion Status:** 50% (Phase 1 Complete + 2 core endpoints implemented)

---

## Executive Summary

The QuickFix review system has a solid foundation with database schema, two core endpoints (CREATE and GET by ID), and deployment infrastructure. However, **60% of the functionality remains unimplemented**, including critical features like rating aggregation, review listing endpoints, and frontend integration documentation.

### What's Working ✅
- Database schema with reviews table and rating summary fields
- POST /reviews - Create review endpoint
- GET /reviews/{review_id} - Get single review endpoint
- **POST /internal/update-ratings - Rating aggregation Lambda (internal API)**
- Deployment scripts and API Gateway configuration

### What's Missing ❌
- **CRITICAL:** List reviews endpoints (can't display review history)
- **CRITICAL:** Frontend integration guide
- **IMPORTANT:** Update/delete review endpoints
- **OPTIONAL:** Notifications, moderation, image attachments

---

## Implementation Task List

### Phase 1: CRITICAL - Rating Aggregation System ✅ COMPLETE

**Priority:** P0 - Blocking for production
**Status:** ✅ Complete (2026-01-11)
**Implementation:** Internal HTTP API with IAM authentication
**Estimated Tasks:** 3
**Dependencies:** None

#### Tasks:

1. ✅ **Implement rating update Lambda function** - COMPLETE
   - **File:** `lambda/reviews/update_ratings/handler.py`
   - **Description:** Create a Lambda function that calculates and updates rating aggregates
   - **Status:** Deployed as internal HTTP API at `POST /internal/update-ratings`
   - **Logic:**
     ```python
     # For providers:
     rating = total_rating_points / total_review_count
     # For customers:
     average_rating = total_rating_points / total_review_count
     ```
   - **Inputs:** reviewee_id, reviewee_type (customer/provider)
   - **Database Updates:**
     - `service_providers.rating`
     - `service_providers.total_rating_points`
     - `service_providers.total_review_count`
     - `customers.average_rating`
     - `customers.total_rating_points`
     - `customers.total_review_count`

2. ✅ **Integrate rating updates into create_review Lambda** - COMPLETE
   - **File:** `lambda/reviews/create_review/handler.py`
   - **Implementation:** Internal HTTP API with IAM authentication
   - **Endpoint:** `POST /internal/update-ratings` (AWS_IAM auth)
   - **Approach:** Lambda-to-Lambda invocation or HTTP call with SigV4 signing
   - **Note:** Can be called asynchronously after review creation

3. ✅ **Test rating aggregation logic** - COMPLETE
   - **Test Cases:**
     - Single review (rating should equal review rating)
     - Multiple reviews (verify average calculation)
     - Mixed ratings (1 star + 5 star = 3.0 average)
     - Edge case: First review for new provider
   - **Validation:**
     - Verify `total_rating_points` increments correctly
     - Verify `total_review_count` increments correctly
     - Verify calculated rating matches expected average
   - **Status:** Tested and deployed

---

### Phase 2: CRITICAL - List Reviews Endpoints 🔴 **← NEXT PRIORITY**

**Priority:** P0 - Blocking for production
**Status:** ⏳ Not Started
**Estimated Tasks:** 7
**Dependencies:** None

#### Tasks:

4. **Implement GET /reviews/provider/{provider_id} endpoint**
   - **File:** `lambda/reviews/get_provider_reviews/handler.py`
   - **Functionality:**
     - Retrieve all reviews where `reviewee_id = provider_id` AND `reviewee_type = 'provider'`
     - Order by `created_at DESC` (newest first)
     - Include reviewer information (name, profile)
     - Support sorting options (newest, oldest, highest rating, lowest rating)
   - **Response Format:**
     ```json
     {
       "reviews": [
         {
           "review_id": 123,
           "job_id": 456,
           "reviewer_name": "John Doe",
           "reviewer_type": "customer",
           "rating": 5,
           "comment": "Excellent service!",
           "created_at": "2026-01-08T10:30:00Z"
         }
       ],
       "total_count": 42,
       "average_rating": 4.7
     }
     ```

5. **Add pagination support to provider reviews endpoint**
   - **Query Parameters:**
     - `limit` (default: 10, max: 100)
     - `offset` (default: 0)
     - `cursor` (alternative: use cursor-based pagination)
   - **Response Headers:**
     - `X-Total-Count`: Total number of reviews
     - `X-Has-More`: Boolean indicating more results exist
   - **Response Format:**
     ```json
     {
       "reviews": [...],
       "pagination": {
         "limit": 10,
         "offset": 0,
         "total_count": 42,
         "has_more": true,
         "next_offset": 10
       }
     }
     ```

6. **Implement GET /reviews/customer/{customer_id} endpoint**
   - **File:** `lambda/reviews/get_customer_reviews/handler.py`
   - **Functionality:** Same as provider reviews but for customers
   - **Query:** `reviewee_id = customer_id` AND `reviewee_type = 'customer'`

7. **Add pagination support to customer reviews endpoint**
   - Same pagination logic as task #5

8. **Implement GET /reviews/job/{job_id} endpoint**
   - **File:** `lambda/reviews/get_job_reviews/handler.py`
   - **Functionality:**
     - Retrieve all reviews for a specific job
     - Typically 0-2 reviews (customer reviews provider, provider reviews customer)
     - No pagination needed (small result set)
   - **Use Case:** Display mutual reviews on job completion page

9. **Create deployment scripts for list reviews Lambda functions**
   - **Files:**
     - `deploy/create_get_provider_reviews_lambda.sh`
     - `deploy/deploy_get_provider_reviews.sh`
     - `deploy/create_get_customer_reviews_lambda.sh`
     - `deploy/deploy_get_customer_reviews.sh`
     - `deploy/create_get_job_reviews_lambda.sh`
     - `deploy/deploy_get_job_reviews.sh`
   - **Reference:** Use existing `deploy/create_get_review_by_id_lambda.sh` as template

10. **Set up API Gateway routes for all list reviews endpoints**
    - **Files:**
      - `deploy/setup_get_provider_reviews_api.sh`
      - `deploy/setup_get_customer_reviews_api.sh`
      - `deploy/setup_get_job_reviews_api.sh`
    - **Endpoints:**
      - `GET /prod/reviews/provider/{provider_id}`
      - `GET /prod/reviews/customer/{customer_id}`
      - `GET /prod/reviews/job/{job_id}`
    - **Configuration:**
      - JWT authorization (reuse existing authorizer)
      - CORS enabled
      - Lambda proxy integration
      - HTTP API v2 (APIGatewayV2)

---

### Phase 3: IMPORTANT - Update Review Functionality 🟡

**Priority:** P1 - Important for UX
**Estimated Tasks:** 5
**Dependencies:** Phase 1 (rating aggregation)

#### Tasks:

11. **Implement PUT /reviews/{review_id} endpoint**
    - **File:** `lambda/reviews/update_review/handler.py`
    - **Functionality:**
      - Update `rating` and/or `comment` fields
      - Update `updated_at` timestamp
      - Validate new rating (1-5) and comment length (10-1000 chars)
    - **Request Body:**
      ```json
      {
        "rating": 4,
        "comment": "Updated: Service was good but could be better"
      }
      ```
    - **Validation:**
      - Review must exist (404 if not found)
      - User must be the original reviewer (403 if unauthorized)
      - Rating and comment must meet same constraints as creation

12. **Add ownership verification to ensure only review author can update**
    - **Implementation:**
      - Extract `user_id` from JWT token (Cognito claims)
      - Query review: `SELECT reviewer_id, reviewer_type FROM reviews WHERE review_id = ?`
      - Verify: `reviewer_id == user_id` AND `reviewer_type` matches user type
    - **Error Response (403):**
      ```json
      {
        "error": "Forbidden",
        "message": "You can only update your own reviews"
      }
      ```

13. **Trigger rating recalculation when review is updated with new rating**
    - **Logic:**
      - Check if `rating` field changed (old_rating != new_rating)
      - If changed:
        - Calculate delta: `delta = new_rating - old_rating`
        - Update `total_rating_points += delta`
        - Recalculate average: `rating = total_rating_points / total_review_count`
      - If only comment changed, skip rating recalculation
    - **Options:**
      - Call update_ratings Lambda (from Phase 1)
      - Embed logic directly in update handler

14. **Create deployment scripts for update review Lambda function**
    - **Files:**
      - `deploy/create_update_review_lambda.sh`
      - `deploy/deploy_update_review.sh`
    - **Configuration:**
      - Same IAM role as create_review
      - Same VPC configuration
      - Same environment variables (DB credentials)

15. **Set up API Gateway route for PUT /reviews/{review_id}**
    - **File:** `deploy/setup_update_review_api.sh`
    - **Endpoint:** `PUT /prod/reviews/{review_id}`
    - **Configuration:**
      - JWT authorization required
      - CORS enabled
      - Lambda proxy integration

---

### Phase 4: IMPORTANT - Delete Review Functionality 🟡

**Priority:** P1 - Important for UX
**Estimated Tasks:** 5
**Dependencies:** Phase 1 (rating aggregation)

#### Tasks:

16. **Implement DELETE /reviews/{review_id} endpoint**
    - **File:** `lambda/reviews/delete_review/handler.py`
    - **Functionality:**
      - Hard delete from database: `DELETE FROM reviews WHERE review_id = ?`
      - Alternative: Soft delete with `deleted_at` timestamp (requires schema change)
    - **Response:**
      ```json
      {
        "message": "Review deleted successfully",
        "review_id": 123
      }
      ```
    - **Considerations:**
      - Should deletion be permanent or reversible?
      - Should deleted reviews be hidden or marked as deleted?

17. **Add ownership verification to ensure only review author can delete**
    - **Implementation:** Same logic as task #12
    - **Error Response (403):**
      ```json
      {
        "error": "Forbidden",
        "message": "You can only delete your own reviews"
      }
      ```

18. **Implement rating recalculation logic when review is deleted**
    - **Logic:**
      - Before deletion, capture `rating` value
      - Update reviewee's totals:
        - `total_rating_points -= deleted_review_rating`
        - `total_review_count -= 1`
      - Recalculate average:
        - If `total_review_count == 0`: `rating = 0.00`
        - Else: `rating = total_rating_points / total_review_count`
    - **Edge Case:** Last review deleted → rating becomes 0.00

19. **Create deployment scripts for delete review Lambda function**
    - **Files:**
      - `deploy/create_delete_review_lambda.sh`
      - `deploy/deploy_delete_review.sh`

20. **Set up API Gateway route for DELETE /reviews/{review_id}**
    - **File:** `deploy/setup_delete_review_api.sh`
    - **Endpoint:** `DELETE /prod/reviews/{review_id}`
    - **Configuration:**
      - JWT authorization required
      - CORS enabled

---

### Phase 5: CRITICAL - Frontend Integration Documentation 🔴

**Priority:** P0 - Blocking for frontend development
**Estimated Tasks:** 5
**Dependencies:** Phases 1-4 (all endpoints implemented)

#### Tasks:

21. **Create comprehensive frontend integration guide for review APIs**
    - **File:** `docs/FRONTEND_REVIEW_API.md`
    - **Reference:** Use `docs/FRONTEND_MESSAGING_API.md` as template
    - **Sections:**
      - API Overview
      - Authentication (JWT token usage)
      - Error Handling
      - Rate Limiting
      - Code Examples (React/JavaScript)

22. **Add JavaScript/React code examples for creating reviews**
    - **Example:**
      ```javascript
      // Create a review after job completion
      const createReview = async (jobId, rating, comment) => {
        const response = await fetch(
          'https://API_ID.execute-api.REGION.amazonaws.com/prod/reviews',
          {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              'Authorization': `Bearer ${jwtToken}`
            },
            body: JSON.stringify({
              job_id: jobId,
              rating: rating,
              comment: comment
            })
          }
        );

        if (!response.ok) {
          const error = await response.json();
          throw new Error(error.message);
        }

        return await response.json();
      };
      ```

23. **Add JavaScript/React code examples for displaying provider reviews**
    - **Example:**
      ```javascript
      // Fetch and display provider reviews with pagination
      const ProviderReviews = ({ providerId }) => {
        const [reviews, setReviews] = useState([]);
        const [loading, setLoading] = useState(true);

        useEffect(() => {
          const fetchReviews = async () => {
            const response = await fetch(
              `https://API_ID.execute-api.REGION.amazonaws.com/prod/reviews/provider/${providerId}?limit=10&offset=0`,
              {
                headers: {
                  'Authorization': `Bearer ${jwtToken}`
                }
              }
            );
            const data = await response.json();
            setReviews(data.reviews);
            setLoading(false);
          };

          fetchReviews();
        }, [providerId]);

        return (
          <div>
            {reviews.map(review => (
              <ReviewCard key={review.review_id} review={review} />
            ))}
          </div>
        );
      };
      ```

24. **Add JavaScript/React code examples for updating/deleting reviews**
    - **Example:**
      ```javascript
      // Update a review
      const updateReview = async (reviewId, newRating, newComment) => {
        const response = await fetch(
          `https://API_ID.execute-api.REGION.amazonaws.com/prod/reviews/${reviewId}`,
          {
            method: 'PUT',
            headers: {
              'Content-Type': 'application/json',
              'Authorization': `Bearer ${jwtToken}`
            },
            body: JSON.stringify({
              rating: newRating,
              comment: newComment
            })
          }
        );
        return await response.json();
      };

      // Delete a review
      const deleteReview = async (reviewId) => {
        const response = await fetch(
          `https://API_ID.execute-api.REGION.amazonaws.com/prod/reviews/${reviewId}`,
          {
            method: 'DELETE',
            headers: {
              'Authorization': `Bearer ${jwtToken}`
            }
          }
        );
        return await response.json();
      };
      ```

25. **Document error handling and edge cases for frontend developers**
    - **Error Codes:**
      - `400` - Invalid request (missing fields, invalid rating/comment)
      - `401` - Unauthorized (missing/invalid JWT token)
      - `403` - Forbidden (trying to update/delete someone else's review)
      - `404` - Not found (review/job doesn't exist)
      - `409` - Conflict (duplicate review for same job)
      - `500` - Server error
    - **Edge Cases:**
      - Job not completed → Cannot create review
      - Trying to review yourself → Prevented by database constraint
      - Duplicate review → Show error message
      - Network timeout → Retry logic
    - **Best Practices:**
      - Always validate rating (1-5) before API call
      - Always validate comment length (10-1000 chars) before API call
      - Show loading states during API calls
      - Display user-friendly error messages

---

### Phase 6: Quality Assurance & Testing 🟡

**Priority:** P1 - Important for reliability
**Estimated Tasks:** 3
**Dependencies:** Phases 1-4

#### Tasks:

26. **Add foreign key constraints validation for reviewer_id and reviewee_id**
    - **Current Issue:** Database has no FK constraints to verify user/provider IDs exist
    - **Options:**
      - **Option A:** Add FK constraints in database schema
        ```sql
        ALTER TABLE reviews
        ADD CONSTRAINT fk_reviewer_customer
        FOREIGN KEY (reviewer_id) REFERENCES customers(customer_id);

        ALTER TABLE reviews
        ADD CONSTRAINT fk_reviewer_provider
        FOREIGN KEY (reviewer_id) REFERENCES service_providers(provider_id);
        ```
      - **Option B:** Add validation in Lambda handlers
        ```python
        # Verify reviewer exists
        if reviewer_type == 'customer':
            cursor.execute("SELECT 1 FROM customers WHERE customer_id = %s", (reviewer_id,))
        else:
            cursor.execute("SELECT 1 FROM service_providers WHERE provider_id = %s", (reviewer_id,))

        if not cursor.fetchone():
            return error_response(400, "Invalid reviewer ID")
        ```
    - **Recommendation:** Option B (Lambda validation) to avoid complex multi-table FK constraints

27. **Create comprehensive integration tests for all review endpoints**
    - **File:** `tests/integration/test_review_endpoints.py`
    - **Test Cases:**
      - **Create Review:**
        - ✓ Valid review creation
        - ✓ Duplicate review rejection
        - ✓ Self-review prevention
        - ✓ Invalid job_id rejection
        - ✓ Job not completed rejection
        - ✓ Invalid rating (0, 6, -1)
        - ✓ Invalid comment length (too short, too long)
      - **Get Review:**
        - ✓ Valid review retrieval
        - ✓ Non-existent review (404)
        - ✓ Invalid review_id format
      - **List Reviews:**
        - ✓ List provider reviews (empty, single, multiple)
        - ✓ Pagination (first page, middle page, last page)
        - ✓ Sorting (newest, oldest, highest rating, lowest rating)
        - ✓ Non-existent provider (empty result)
      - **Update Review:**
        - ✓ Valid update (rating only, comment only, both)
        - ✓ Unauthorized update (different user)
        - ✓ Non-existent review (404)
        - ✓ Invalid new rating/comment
      - **Delete Review:**
        - ✓ Valid deletion
        - ✓ Unauthorized deletion (different user)
        - ✓ Non-existent review (404)
        - ✓ Rating recalculation after deletion
    - **Tools:**
      - `pytest` for test framework
      - `boto3` for Lambda invocation
      - `requests` for API Gateway testing

28. **Test rating aggregation with edge cases**
    - **Test Cases:**
      - Single review: `rating = review_rating`
      - Two reviews: `rating = (r1 + r2) / 2`
      - Many reviews: Verify average calculation
      - All 5-star reviews: `rating = 5.00`
      - All 1-star reviews: `rating = 1.00`
      - Mixed reviews: Verify decimal precision (e.g., 4.67)
      - Update review: Verify rating recalculates correctly
      - Delete review: Verify rating recalculates correctly
      - Delete last review: `rating = 0.00`, `total_review_count = 0`
    - **Validation:**
      - Query database directly to verify values
      - Compare calculated rating with expected value
      - Check for rounding errors (use DECIMAL, not FLOAT)

---

### Phase 7: OPTIONAL - Enhanced Features 🟢

**Priority:** P2 - Nice to have
**Estimated Tasks:** 3
**Dependencies:** Phases 1-6

#### Tasks:

29. **Integrate notification system to alert users when they receive reviews**
    - **Implementation:**
      - After successful review creation, trigger notification
      - Use existing messaging/notification system (if available)
      - Notification content:
        - "You received a new 5-star review from John Doe!"
        - Include link to view review
    - **Files:**
      - Modify `lambda/reviews/create_review/handler.py`
      - Call notification Lambda or SNS topic
    - **Channels:**
      - In-app notification
      - Email (optional)
      - Push notification (optional)

30. **Add review flagging/moderation features for inappropriate content**
    - **Database Schema Change:**
      ```sql
      ALTER TABLE reviews
      ADD COLUMN flagged BOOLEAN DEFAULT FALSE,
      ADD COLUMN flag_reason VARCHAR(500),
      ADD COLUMN flagged_at TIMESTAMP,
      ADD COLUMN flagged_by INT,
      ADD COLUMN moderation_status ENUM('pending', 'approved', 'rejected') DEFAULT 'approved';
      ```
    - **New Endpoints:**
      - `POST /reviews/{review_id}/flag` - Flag inappropriate review
      - `GET /reviews/flagged` - List flagged reviews (admin only)
      - `PUT /reviews/{review_id}/moderate` - Approve/reject review (admin only)
    - **Use Cases:**
      - Offensive language
      - Spam
      - False information
      - Personal attacks

31. **Implement review image attachment support with S3 integration**
    - **Database Schema Change:**
      ```sql
      CREATE TABLE review_images (
        image_id INT AUTO_INCREMENT PRIMARY KEY,
        review_id INT NOT NULL,
        s3_key VARCHAR(500) NOT NULL,
        s3_bucket VARCHAR(255) NOT NULL,
        image_url VARCHAR(1000) NOT NULL,
        uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (review_id) REFERENCES reviews(review_id) ON DELETE CASCADE
      );
      ```
    - **Implementation:**
      - Generate pre-signed S3 upload URLs
      - Allow 1-5 images per review
      - Max image size: 5MB
      - Supported formats: JPG, PNG, WEBP
      - Thumbnail generation (optional)
    - **New Endpoints:**
      - `POST /reviews/{review_id}/images/upload-url` - Get pre-signed upload URL
      - `GET /reviews/{review_id}/images` - List review images
      - `DELETE /reviews/{review_id}/images/{image_id}` - Delete image
    - **Security:**
      - Verify file type (magic bytes, not just extension)
      - Scan for malware (AWS CloudWatch, third-party service)
      - Rate limit uploads

---

### Phase 8: Finalization 🟡

**Priority:** P1 - Required before production
**Estimated Tasks:** 2
**Dependencies:** All previous phases

#### Tasks:

32. **Update API documentation with all new endpoints and examples**
    - **File:** `API_ENDPOINTS.md`
    - **Add Sections:**
      - List Provider Reviews (GET /reviews/provider/{provider_id})
      - List Customer Reviews (GET /reviews/customer/{customer_id})
      - List Job Reviews (GET /reviews/job/{job_id})
      - Update Review (PUT /reviews/{review_id})
      - Delete Review (DELETE /reviews/{review_id})
    - **Include:**
      - Endpoint description
      - Authentication requirements
      - Request parameters
      - Request body (if applicable)
      - Response format (success and error)
      - cURL examples
      - JavaScript fetch examples

33. **Commit and push all review system changes to repository**
    - **Git Workflow:**
      ```bash
      # Commit current uncommitted changes first
      git add deploy/setup_get_review_by_id_api.sh
      git commit -m "refactor: migrate GET review by ID to HTTP API v2"

      # After implementing all features, create feature commits
      git add lambda/reviews/update_ratings/
      git commit -m "feat: add rating aggregation Lambda function"

      git add lambda/reviews/get_provider_reviews/
      git commit -m "feat: add GET provider reviews endpoint with pagination"

      # ... (continue for each major feature)

      # Push to remote
      git push origin kunpeng/lambda-db-setup

      # Create pull request to master
      gh pr create --title "feat: Complete review system implementation" \
        --body "Implements remaining review system features including rating aggregation, list endpoints, update/delete functionality, and frontend documentation"
      ```
    - **Commit Message Convention:**
      - `feat:` - New features
      - `fix:` - Bug fixes
      - `refactor:` - Code refactoring
      - `docs:` - Documentation updates
      - `test:` - Test additions/updates

---

## Implementation Timeline Estimate

### Critical Path (Minimum Viable Product)
**Phases 1, 2, 5** - Core functionality + Documentation
- **Total Tasks:** 15 tasks
- **Blocking Issues:** None (can start immediately)

### Full Feature Set (Production Ready)
**Phases 1-6, 8** - All core features + testing + deployment
- **Total Tasks:** 28 tasks
- **Blocking Issues:** Phase 3-4 depend on Phase 1 completion

### Complete System (All Enhancements)
**All Phases 1-8** - Including optional features
- **Total Tasks:** 33 tasks
- **Blocking Issues:** Phase 7 depends on all previous phases

---

## Technical Decisions & Trade-offs

### Decision 1: Rating Calculation Approach
**Options:**
1. **Embedded Logic** - Calculate ratings directly in create_review Lambda
2. **Separate Lambda** - Dedicated update_ratings Lambda called asynchronously
3. **Database Triggers** - MySQL stored procedures auto-update ratings

**Recommendation:** Separate Lambda (Option 2)
- **Pros:** Reusable for update/delete endpoints, separation of concerns, easier testing
- **Cons:** Additional Lambda function, slightly more complex architecture
- **Trade-off:** Complexity vs. maintainability → Choose maintainability

### Decision 2: Pagination Strategy
**Options:**
1. **Offset-based** - `?limit=10&offset=20` (skip N records)
2. **Cursor-based** - `?limit=10&cursor=abc123` (keyset pagination)

**Recommendation:** Offset-based (Option 1) for initial implementation
- **Pros:** Simple to implement, familiar to developers, works with SQL `LIMIT/OFFSET`
- **Cons:** Performance degrades with large offsets, inconsistent results if data changes
- **Future Enhancement:** Add cursor-based pagination for better performance at scale

### Decision 3: Delete Behavior
**Options:**
1. **Hard Delete** - Permanently remove from database
2. **Soft Delete** - Mark as deleted with `deleted_at` timestamp

**Recommendation:** Hard Delete (Option 1) for initial implementation
- **Pros:** Simpler, no schema changes, truly removes data
- **Cons:** Irreversible, no audit trail
- **Future Enhancement:** Implement soft delete with admin restore functionality

### Decision 4: Foreign Key Validation
**Options:**
1. **Database FK Constraints** - Enforce at database level
2. **Lambda Validation** - Verify in application code

**Recommendation:** Lambda Validation (Option 2)
- **Pros:** Avoids complex multi-table FK constraints (reviewer can be customer OR provider)
- **Cons:** Validation logic in multiple places, potential for bugs
- **Trade-off:** Database integrity vs. schema complexity → Choose Lambda validation

---

## API Endpoint Summary (After Completion)

| Method | Endpoint | Status | Description |
|--------|----------|--------|-------------|
| POST | `/reviews` | ✅ Implemented | Create a new review |
| GET | `/reviews/{review_id}` | ✅ Implemented | Get review by ID |
| GET | `/reviews/provider/{provider_id}` | ❌ Missing | List all provider reviews (paginated) |
| GET | `/reviews/customer/{customer_id}` | ❌ Missing | List all customer reviews (paginated) |
| GET | `/reviews/job/{job_id}` | ❌ Missing | List all job reviews |
| PUT | `/reviews/{review_id}` | ❌ Missing | Update existing review |
| DELETE | `/reviews/{review_id}` | ❌ Missing | Delete review |
| POST | `/reviews/{review_id}/flag` | 🟢 Optional | Flag inappropriate review |
| GET | `/reviews/flagged` | 🟢 Optional | List flagged reviews (admin) |
| POST | `/reviews/{review_id}/images/upload-url` | 🟢 Optional | Get pre-signed S3 upload URL |

**Legend:**
- ✅ Implemented and deployed
- ❌ Not implemented (required)
- 🟢 Optional enhancement (future)

---

## Database Schema Changes Required

### Current Schema (Implemented)
- ✅ `reviews` table with all core fields
- ✅ `service_providers.rating` fields
- ✅ `customers.average_rating` fields
- ✅ Proper indexes and constraints

### Optional Schema Changes (Phase 7)
- ❌ `reviews.flagged` fields (moderation)
- ❌ `review_images` table (image attachments)
- ❌ `reviews.deleted_at` field (soft delete)

---

## Testing Checklist

### Unit Tests
- [ ] Rating calculation logic (average, edge cases)
- [ ] Input validation (rating range, comment length)
- [ ] Ownership verification (update/delete permissions)

### Integration Tests
- [ ] Create review → Rating updates correctly
- [ ] Update review → Rating recalculates
- [ ] Delete review → Rating recalculates
- [ ] Pagination → Correct results at various offsets
- [ ] Duplicate review → Rejected with 409
- [ ] Self-review → Rejected with 400

### End-to-End Tests
- [ ] Complete user flow: Job completion → Create review → Provider sees new rating
- [ ] Update flow: Create review → Update rating → Verify average changed
- [ ] Delete flow: Create review → Delete review → Verify rating recalculated

### Performance Tests
- [ ] List reviews with 1000+ reviews (pagination performance)
- [ ] Concurrent review creation (race condition testing)
- [ ] Rating calculation with 10,000+ reviews

---

## Deployment Checklist

### Before Deployment
- [ ] All Lambda functions tested locally
- [ ] Environment variables configured (DB credentials, API endpoints)
- [ ] IAM roles and policies configured
- [ ] VPC configuration verified (database access)
- [ ] API Gateway authorizers configured
- [ ] CORS settings configured

### Deployment Steps
1. [ ] Deploy rating aggregation Lambda
2. [ ] Deploy list reviews Lambdas (provider, customer, job)
3. [ ] Deploy update review Lambda
4. [ ] Deploy delete review Lambda
5. [ ] Configure API Gateway routes
6. [ ] Test each endpoint with cURL/Postman
7. [ ] Update API documentation
8. [ ] Notify frontend team of new endpoints

### Post-Deployment Validation
- [ ] Verify all endpoints return 200/201 for valid requests
- [ ] Verify error responses (400, 401, 403, 404, 409, 500)
- [ ] Check CloudWatch logs for errors
- [ ] Monitor Lambda execution times
- [ ] Verify database connections (no connection leaks)

---

## Dependencies & Prerequisites

### Required AWS Resources
- ✅ RDS MySQL database (existing)
- ✅ Lambda execution role with RDS access (existing)
- ✅ VPC configuration (existing)
- ✅ API Gateway (existing)
- ✅ Cognito user pool for JWT auth (existing)
- ❌ S3 bucket (only for Phase 7 - image attachments)
- ❌ SNS topic (only for Phase 7 - notifications)

### Required Python Packages
- ✅ `pymysql` (database connector)
- ✅ `boto3` (AWS SDK)
- ❌ `Pillow` (only for image processing in Phase 7)

### Required Tools
- ✅ AWS CLI (configured)
- ✅ `jq` (JSON processing in bash scripts)
- ✅ Git

---

## Risk Assessment

### High Risk
- **Rating Aggregation Bugs** - Incorrect calculations could display wrong provider ratings
  - **Mitigation:** Comprehensive unit tests, manual verification with known data
- **Concurrent Update Race Conditions** - Two users updating same review simultaneously
  - **Mitigation:** Database-level unique constraints, optimistic locking

### Medium Risk
- **Pagination Performance** - Large offset pagination slow on big datasets
  - **Mitigation:** Implement cursor-based pagination in future, add database indexes
- **Ownership Verification Bypass** - Security flaw allowing unauthorized updates/deletes
  - **Mitigation:** Thorough security testing, penetration testing

### Low Risk
- **Documentation Outdated** - API docs not matching implementation
  - **Mitigation:** Update docs in same commit as code changes
- **Frontend Integration Issues** - Frontend team misusing APIs
  - **Mitigation:** Comprehensive frontend guide with working examples

---

## Success Criteria

### Phase 1 Success Criteria
- ✅ Create review → Provider rating updates automatically
- ✅ Rating calculation accurate to 2 decimal places
- ✅ Zero manual intervention required for rating updates

### Phase 2 Success Criteria
- ✅ Can list all reviews for any provider/customer
- ✅ Pagination works correctly (no duplicate/missing results)
- ✅ API response time < 500ms for 100 reviews

### Phase 5 Success Criteria
- ✅ Frontend developer can integrate without asking questions
- ✅ All code examples work copy-paste
- ✅ Error handling documented for all edge cases

### Overall Success Criteria
- ✅ All 7 core endpoints implemented and deployed
- ✅ All integration tests passing
- ✅ Frontend documentation complete
- ✅ Zero critical bugs in production
- ✅ API response time < 1 second (p95)

---

## Contact & Questions

For questions about this implementation plan, contact:
- **Project Lead:** [Name]
- **Backend Team:** [Names]
- **Frontend Team:** [Names]

---

## Document History

| Date | Version | Author | Changes |
|------|---------|--------|---------|
| 2026-01-08 | 1.0 | Claude Code | Initial implementation plan created |

---

## References

- [Database Schema](../sql/migrations/create_reviews_table.sql)
- [Existing Create Review Lambda](../lambda/reviews/create_review/handler.py)
- [Existing Get Review Lambda](../lambda/reviews/get_review_by_id/handler.py)
- [API Documentation](../API_ENDPOINTS.md)
- [Deployment Guide](../deploy/DEPLOY_CREATE_REVIEW.md)
