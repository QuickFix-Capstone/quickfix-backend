# Customer Public Profile - Backend Implementation Plan

**Feature**: Provider View of Customer Public Profile  
**Backend Stack**: AWS API Gateway + Lambda + MySQL (RDS)  
**Updated**: February 14, 2026

---

## Overview

This document outlines the complete backend implementation for allowing service providers to view customer public profiles, including reviews, ratings, and activity summaries while maintaining privacy and security.

---

## Phase 1: Database Schema Updates

### 1.1 Add Customer Profile Fields

```sql
ALTER TABLE customers
ADD COLUMN display_name VARCHAR(100) NULL COMMENT 'Public display name',
ADD COLUMN avatar_url VARCHAR(500) NULL COMMENT 'Profile picture URL',
ADD COLUMN profile_visibility ENUM('public', 'restricted', 'private') 
    NOT NULL DEFAULT 'restricted' 
    COMMENT 'Who can view profile: public=all providers, restricted=interacted only, private=hidden';
```

### 1.2 Create Customer Profile Stats Table

For performance optimization, cache aggregated statistics:

```sql
CREATE TABLE customer_profile_stats (
    customer_id BIGINT PRIMARY KEY,
    avg_rating DECIMAL(3,2) NULL COMMENT 'Average rating from provider reviews',
    review_count INT NOT NULL DEFAULT 0,
    jobs_posted_6mo INT NOT NULL DEFAULT 0,
    jobs_completed INT NOT NULL DEFAULT 0,
    jobs_cancelled INT NOT NULL DEFAULT 0,
    completion_rate DECIMAL(5,2) NULL COMMENT 'Percentage of completed jobs',
    cancellation_rate DECIMAL(5,2) NULL COMMENT 'Percentage of cancelled jobs',
    avg_response_time_minutes INT NULL COMMENT 'Average message response time',
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    CONSTRAINT fk_stats_customer 
        FOREIGN KEY (customer_id) REFERENCES customers(customer_id) ON DELETE CASCADE,
    
    INDEX idx_last_updated (last_updated)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

### 1.3 Add Review Visibility Flag

```sql
ALTER TABLE reviews
ADD COLUMN is_visible BOOLEAN NOT NULL DEFAULT TRUE COMMENT 'Whether review is publicly visible',
ADD INDEX idx_customer_visible (customer_id, is_visible);
```

### 1.4 Create Provider-Customer Interaction Tracking

Track when providers interact with customers to enforce "restricted" privacy:

```sql
CREATE TABLE provider_customer_interactions (
    interaction_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    provider_id BIGINT NOT NULL,
    customer_id BIGINT NOT NULL,
    interaction_type ENUM('job_view', 'job_application', 'booking', 'message', 'job_completed') NOT NULL,
    job_id BIGINT NULL,
    booking_id BIGINT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT fk_interaction_provider 
        FOREIGN KEY (provider_id) REFERENCES service_providers(provider_id) ON DELETE CASCADE,
    CONSTRAINT fk_interaction_customer 
        FOREIGN KEY (customer_id) REFERENCES customers(customer_id) ON DELETE CASCADE,
    
    INDEX idx_provider_customer (provider_id, customer_id),
    INDEX idx_customer (customer_id),
    UNIQUE KEY unique_interaction (provider_id, customer_id, interaction_type, job_id, booking_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

---

## Phase 2: Lambda Functions

### 2.1 Authorization Helper Function

**File**: `lambda/helpers/customerProfileAuth.js`

```javascript
const mysql = require('mysql2/promise');

/**
 * Check if provider can view customer profile based on privacy settings
 * @param {number} providerId - Provider's ID from Cognito
 * @param {number} customerId - Customer ID to check access for
 * @param {Connection} connection - MySQL connection
 * @returns {Object} { allowed: boolean, reason: string }
 */
async function canProviderViewCustomer(providerId, customerId, connection) {
    try {
        // 1. Check customer privacy settings
        const [customer] = await connection.query(
            'SELECT profile_visibility FROM customers WHERE customer_id = ?',
            [customerId]
        );
        
        if (!customer.length) {
            return { allowed: false, reason: 'Customer not found' };
        }
        
        const visibility = customer[0].profile_visibility;
        
        // If public, allow all authenticated providers
        if (visibility === 'public') {
            return { allowed: true };
        }
        
        // If private, deny
        if (visibility === 'private') {
            return { allowed: false, reason: 'Profile is private' };
        }
        
        // If restricted, check for interactions
        const [interactions] = await connection.query(
            `SELECT COUNT(*) as count FROM provider_customer_interactions 
             WHERE provider_id = ? AND customer_id = ?`,
            [providerId, customerId]
        );
        
        return { 
            allowed: interactions[0].count > 0,
            reason: interactions[0].count === 0 ? 'No prior interaction with this customer' : null
        };
    } catch (error) {
        console.error('Authorization check error:', error);
        return { allowed: false, reason: 'Authorization check failed' };
    }
}

module.exports = { canProviderViewCustomer };
```

### 2.2 Stats Calculation Function

**File**: `lambda/helpers/calculateCustomerStats.js`

```javascript
/**
 * Calculate customer profile statistics
 * @param {number} customerId - Customer ID
 * @param {Connection} connection - MySQL connection
 * @returns {Object} Stats object
 */
async function calculateCustomerStats(customerId, connection) {
    try {
        const [stats] = await connection.query(`
            SELECT 
                -- Review stats
                COALESCE(AVG(r.rating), 0) as avg_rating,
                COUNT(DISTINCT r.review_id) as review_count,
                
                -- Job stats (last 6 months)
                COUNT(DISTINCT CASE 
                    WHEN j.created_at >= DATE_SUB(NOW(), INTERVAL 6 MONTH) 
                    THEN j.job_id 
                END) as jobs_posted_6mo,
                
                COUNT(DISTINCT CASE 
                    WHEN j.status = 'completed' 
                    THEN j.job_id 
                END) as jobs_completed,
                
                COUNT(DISTINCT CASE 
                    WHEN j.status = 'cancelled' 
                    THEN j.job_id 
                END) as jobs_cancelled,
                
                -- Calculate rates
                CASE 
                    WHEN COUNT(DISTINCT j.job_id) > 0 
                    THEN (COUNT(DISTINCT CASE WHEN j.status = 'completed' THEN j.job_id END) * 100.0 / COUNT(DISTINCT j.job_id))
                    ELSE NULL 
                END as completion_rate,
                
                CASE 
                    WHEN COUNT(DISTINCT j.job_id) > 0 
                    THEN (COUNT(DISTINCT CASE WHEN j.status = 'cancelled' THEN j.job_id END) * 100.0 / COUNT(DISTINCT j.job_id))
                    ELSE NULL 
                END as cancellation_rate
                
            FROM customers c
            LEFT JOIN reviews r ON c.customer_id = r.customer_id AND r.is_visible = TRUE
            LEFT JOIN jobs j ON c.customer_id = j.customer_id
            WHERE c.customer_id = ?
            GROUP BY c.customer_id
        `, [customerId]);
        
        return stats[0] || null;
    } catch (error) {
        console.error('Stats calculation error:', error);
        return null;
    }
}

/**
 * Upsert customer stats into cache table
 */
async function upsertStats(customerId, stats, connection) {
    if (!stats) return;
    
    await connection.query(`
        INSERT INTO customer_profile_stats 
        (customer_id, avg_rating, review_count, jobs_posted_6mo, jobs_completed, 
         jobs_cancelled, completion_rate, cancellation_rate)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ON DUPLICATE KEY UPDATE
            avg_rating = VALUES(avg_rating),
            review_count = VALUES(review_count),
            jobs_posted_6mo = VALUES(jobs_posted_6mo),
            jobs_completed = VALUES(jobs_completed),
            jobs_cancelled = VALUES(jobs_cancelled),
            completion_rate = VALUES(completion_rate),
            cancellation_rate = VALUES(cancellation_rate),
            last_updated = CURRENT_TIMESTAMP
    `, [
        customerId,
        stats.avg_rating,
        stats.review_count,
        stats.jobs_posted_6mo,
        stats.jobs_completed,
        stats.jobs_cancelled,
        stats.completion_rate,
        stats.cancellation_rate
    ]);
}

/**
 * Check if stats are stale (older than 1 hour)
 */
function isStale(lastUpdated) {
    const oneHourAgo = new Date(Date.now() - 60 * 60 * 1000);
    return new Date(lastUpdated) < oneHourAgo;
}

module.exports = { calculateCustomerStats, upsertStats, isStale };
```

### 2.3 Main Profile Endpoint Lambda

**File**: `lambda/getCustomerProfile.js`  
**Route**: `GET /provider/customers/{customer_id}/profile`

```javascript
const mysql = require('mysql2/promise');
const { canProviderViewCustomer } = require('./helpers/customerProfileAuth');
const { calculateCustomerStats, upsertStats, isStale } = require('./helpers/calculateCustomerStats');

exports.handler = async (event) => {
    let connection;
    
    try {
        const customerId = event.pathParameters.customer_id;
        const providerId = event.requestContext.authorizer.claims.sub; // From Cognito JWT
        
        // Create DB connection
        connection = await mysql.createConnection({
            host: process.env.DB_HOST,
            user: process.env.DB_USER,
            password: process.env.DB_PASSWORD,
            database: process.env.DB_NAME
        });
        
        // 1. Authorization check
        const authCheck = await canProviderViewCustomer(providerId, customerId, connection);
        if (!authCheck.allowed) {
            return {
                statusCode: 403,
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ 
                    message: authCheck.reason || 'Access denied to this customer profile' 
                })
            };
        }
        
        // 2. Get customer basic info
        const [customer] = await connection.query(`
            SELECT 
                customer_id,
                display_name,
                CONCAT(first_name, ' ', SUBSTRING(last_name, 1, 1), '.') as fallback_name,
                avatar_url,
                created_at,
                profile_visibility
            FROM customers 
            WHERE customer_id = ?
        `, [customerId]);
        
        if (!customer.length) {
            return { 
                statusCode: 404, 
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message: 'Customer not found' }) 
            };
        }
        
        // 3. Get or calculate stats
        let [stats] = await connection.query(
            'SELECT * FROM customer_profile_stats WHERE customer_id = ?',
            [customerId]
        );
        
        // If stats don't exist or are stale (>1 hour), recalculate
        if (!stats.length || isStale(stats[0].last_updated)) {
            const freshStats = await calculateCustomerStats(customerId, connection);
            await upsertStats(customerId, freshStats, connection);
            stats = [freshStats];
        }
        
        // 4. Get recent reviews (limited to 5)
        const [reviews] = await connection.query(`
            SELECT 
                r.review_id,
                r.rating,
                r.comment,
                r.created_at,
                j.category as job_category,
                DATE_FORMAT(r.created_at, '%M %Y') as review_date
            FROM reviews r
            LEFT JOIN jobs j ON r.job_id = j.job_id
            WHERE r.customer_id = ? AND r.is_visible = TRUE
            ORDER BY r.created_at DESC
            LIMIT 5
        `, [customerId]);
        
        // 5. Get job category distribution
        const [categories] = await connection.query(`
            SELECT 
                category,
                COUNT(*) as count
            FROM jobs
            WHERE customer_id = ? AND category IS NOT NULL
            GROUP BY category
            ORDER BY count DESC
            LIMIT 5
        `, [customerId]);
        
        // 6. Generate badges
        const badges = generateBadges(stats[0], customer[0]);
        
        return {
            statusCode: 200,
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                customer: {
                    customer_id: customer[0].customer_id,
                    display_name: customer[0].display_name || customer[0].fallback_name,
                    avatar_url: customer[0].avatar_url,
                    member_since: customer[0].created_at,
                    is_new: isNewCustomer(customer[0].created_at)
                },
                stats: stats[0] || {},
                recent_reviews: reviews,
                job_categories: categories,
                badges
            })
        };
        
    } catch (error) {
        console.error('Error fetching customer profile:', error);
        return {
            statusCode: 500,
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message: 'Internal server error' })
        };
    } finally {
        if (connection) await connection.end();
    }
};

function isNewCustomer(createdAt) {
    const threeMonthsAgo = new Date(Date.now() - 90 * 24 * 60 * 60 * 1000);
    return new Date(createdAt) > threeMonthsAgo;
}

function generateBadges(stats, customer) {
    const badges = [];
    
    if (isNewCustomer(customer.created_at)) {
        badges.push({ type: 'new_customer', label: 'New Customer' });
    }
    
    if (stats && stats.jobs_posted_6mo >= 10) {
        badges.push({ type: 'frequent_poster', label: 'Frequent Poster' });
    }
    
    if (stats && stats.completion_rate >= 90) {
        badges.push({ type: 'reliable', label: 'Reliable' });
    }
    
    if (stats && stats.avg_rating >= 4.5) {
        badges.push({ type: 'highly_rated', label: 'Highly Rated' });
    }
    
    return badges;
}
```

### 2.4 Reviews Pagination Endpoint

**File**: `lambda/getCustomerReviews.js`  
**Route**: `GET /provider/customers/{customer_id}/reviews`

```javascript
const mysql = require('mysql2/promise');
const { canProviderViewCustomer } = require('./helpers/customerProfileAuth');

exports.handler = async (event) => {
    let connection;
    
    try {
        const customerId = event.pathParameters.customer_id;
        const providerId = event.requestContext.authorizer.claims.sub;
        const limit = parseInt(event.queryStringParameters?.limit || '10');
        const cursor = event.queryStringParameters?.cursor; // review_id for pagination
        const sort = event.queryStringParameters?.sort || 'recent'; // recent, highest, lowest
        
        // Create DB connection
        connection = await mysql.createConnection({
            host: process.env.DB_HOST,
            user: process.env.DB_USER,
            password: process.env.DB_PASSWORD,
            database: process.env.DB_NAME
        });
        
        // Authorization check
        const authCheck = await canProviderViewCustomer(providerId, customerId, connection);
        if (!authCheck.allowed) {
            return { 
                statusCode: 403, 
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message: 'Access denied' }) 
            };
        }
        
        // Build query based on sort
        let orderBy = 'r.created_at DESC';
        if (sort === 'highest') orderBy = 'r.rating DESC, r.created_at DESC';
        if (sort === 'lowest') orderBy = 'r.rating ASC, r.created_at DESC';
        
        const cursorCondition = cursor ? `AND r.review_id < ?` : '';
        const params = cursor ? [customerId, cursor, limit + 1] : [customerId, limit + 1];
        
        const [reviews] = await connection.query(`
            SELECT 
                r.review_id,
                r.rating,
                r.comment,
                r.created_at,
                j.category as job_category,
                sp.business_name as provider_name,
                DATE_FORMAT(r.created_at, '%M %d, %Y') as formatted_date
            FROM reviews r
            LEFT JOIN jobs j ON r.job_id = j.job_id
            LEFT JOIN service_providers sp ON r.provider_id = sp.provider_id
            WHERE r.customer_id = ? AND r.is_visible = TRUE ${cursorCondition}
            ORDER BY ${orderBy}
            LIMIT ?
        `, params);
        
        const hasMore = reviews.length > limit;
        const items = hasMore ? reviews.slice(0, -1) : reviews;
        const nextCursor = hasMore ? items[items.length - 1].review_id : null;
        
        return {
            statusCode: 200,
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                reviews: items,
                pagination: {
                    has_more: hasMore,
                    next_cursor: nextCursor,
                    limit
                }
            })
        };
        
    } catch (error) {
        console.error('Error fetching customer reviews:', error);
        return {
            statusCode: 500,
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message: 'Internal server error' })
        };
    } finally {
        if (connection) await connection.end();
    }
};
```

### 2.5 Track Interaction Lambda

**File**: `lambda/helpers/trackProviderInteraction.js`

```javascript
/**
 * Track provider-customer interaction for access control
 * Called when provider views job, applies, messages customer, etc.
 */
async function trackInteraction(providerId, customerId, interactionType, jobId = null, bookingId = null, connection) {
    try {
        await connection.query(`
            INSERT INTO provider_customer_interactions 
            (provider_id, customer_id, interaction_type, job_id, booking_id)
            VALUES (?, ?, ?, ?, ?)
            ON DUPLICATE KEY UPDATE created_at = CURRENT_TIMESTAMP
        `, [providerId, customerId, interactionType, jobId, bookingId]);
        
        console.log(`Tracked interaction: ${interactionType} between provider ${providerId} and customer ${customerId}`);
    } catch (error) {
        console.error('Error tracking interaction:', error);
        // Don't throw - tracking failures shouldn't break main functionality
    }
}

module.exports = { trackInteraction };
```

**Integration Points**: Update existing lambdas to call `trackInteraction`:
- Job view endpoint → `trackInteraction(providerId, customerId, 'job_view', jobId)`
- Job application endpoint → `trackInteraction(providerId, customerId, 'job_application', jobId)`
- Messaging endpoint → `trackInteraction(providerId, customerId, 'message')`
- Job completion → `trackInteraction(providerId, customerId, 'job_completed', jobId)`

---

## Phase 3: API Gateway Configuration

### 3.1 Add New Routes

**API Gateway Resource Configuration**:

```yaml
Resources:
  /provider/customers/{customer_id}/profile:
    GET:
      Integration: Lambda (getCustomerProfile)
      Authorization: Cognito User Pool (provider group)
      Request Parameters:
        - customer_id (path, required)
      CORS: Enabled
      Response Models:
        200: CustomerProfileResponse
        403: ErrorResponse
        404: ErrorResponse
        500: ErrorResponse

  /provider/customers/{customer_id}/reviews:
    GET:
      Integration: Lambda (getCustomerReviews)
      Authorization: Cognito User Pool (provider group)
      Request Parameters:
        - customer_id (path, required)
        - limit (query, optional, default: 10)
        - cursor (query, optional)
        - sort (query, optional, enum: [recent, highest, lowest])
      CORS: Enabled
      Response Models:
        200: CustomerReviewsResponse
        403: ErrorResponse
        500: ErrorResponse
```

### 3.2 Response Models

**CustomerProfileResponse**:
```json
{
  "customer": {
    "customer_id": 123,
    "display_name": "John D.",
    "avatar_url": "https://...",
    "member_since": "2025-01-15T10:30:00Z",
    "is_new": false
  },
  "stats": {
    "avg_rating": 4.7,
    "review_count": 23,
    "jobs_posted_6mo": 7,
    "jobs_completed": 15,
    "jobs_cancelled": 2,
    "completion_rate": 88.24,
    "cancellation_rate": 11.76
  },
  "recent_reviews": [
    {
      "review_id": 456,
      "rating": 5,
      "comment": "Great customer, clear requirements",
      "job_category": "Plumbing",
      "review_date": "January 2026"
    }
  ],
  "job_categories": [
    { "category": "Plumbing", "count": 5 },
    { "category": "Electrical", "count": 3 }
  ],
  "badges": [
    { "type": "reliable", "label": "Reliable" },
    { "type": "frequent_poster", "label": "Frequent Poster" }
  ]
}
```

---

## Phase 4: Background Jobs

### 4.1 Stats Refresh Lambda (Scheduled)

**File**: `lambda/refreshCustomerStats.js`  
**Trigger**: CloudWatch Events (every hour)

```javascript
const mysql = require('mysql2/promise');
const { calculateCustomerStats, upsertStats } = require('./helpers/calculateCustomerStats');

exports.handler = async (event) => {
    let connection;
    
    try {
        connection = await mysql.createConnection({
            host: process.env.DB_HOST,
            user: process.env.DB_USER,
            password: process.env.DB_PASSWORD,
            database: process.env.DB_NAME
        });
        
        // Find customers with stale stats (>1 hour old)
        const [staleCustomers] = await connection.query(`
            SELECT customer_id 
            FROM customer_profile_stats 
            WHERE last_updated < DATE_SUB(NOW(), INTERVAL 1 HOUR)
            LIMIT 100
        `);
        
        console.log(`Refreshing stats for ${staleCustomers.length} customers`);
        
        for (const customer of staleCustomers) {
            const stats = await calculateCustomerStats(customer.customer_id, connection);
            await upsertStats(customer.customer_id, stats, connection);
        }
        
        return {
            statusCode: 200,
            body: JSON.stringify({ 
                message: `Refreshed stats for ${staleCustomers.length} customers` 
            })
        };
        
    } catch (error) {
        console.error('Error refreshing stats:', error);
        return {
            statusCode: 500,
            body: JSON.stringify({ message: 'Error refreshing stats' })
        };
    } finally {
        if (connection) await connection.end();
    }
};
```

**CloudWatch Event Rule**:
```json
{
  "schedule": "rate(1 hour)",
  "target": "refreshCustomerStats Lambda"
}
```

---

## Phase 5: Testing & Validation

### 5.1 Unit Tests

**Test File**: `tests/customerProfileAuth.test.js`

```javascript
const { canProviderViewCustomer } = require('../lambda/helpers/customerProfileAuth');

describe('Customer Profile Authorization', () => {
    test('should allow access for public profiles', async () => {
        // Mock connection with public customer
        const result = await canProviderViewCustomer(1, 2, mockConnection);
        expect(result.allowed).toBe(true);
    });
    
    test('should deny access for private profiles', async () => {
        const result = await canProviderViewCustomer(1, 3, mockConnection);
        expect(result.allowed).toBe(false);
        expect(result.reason).toBe('Profile is private');
    });
    
    test('should allow restricted access with prior interaction', async () => {
        const result = await canProviderViewCustomer(1, 4, mockConnection);
        expect(result.allowed).toBe(true);
    });
    
    test('should deny restricted access without interaction', async () => {
        const result = await canProviderViewCustomer(1, 5, mockConnection);
        expect(result.allowed).toBe(false);
    });
});
```

### 5.2 Integration Tests

Test end-to-end profile retrieval with various scenarios:
- Authorized provider viewing public profile
- Unauthorized provider attempting access
- Profile with no reviews
- Profile with many reviews (pagination)
- Stats calculation accuracy

### 5.3 Security Tests

- SQL injection attempts in customer_id parameter
- JWT token validation
- Rate limiting (prevent profile scraping)
- CORS configuration
- Sensitive data leakage (addresses, phone numbers)

---

## Implementation Timeline

### Week 1: Database + Core Logic
- [ ] Execute database schema updates (Phase 1)
- [ ] Create authorization helper (2.1)
- [ ] Create stats calculation helper (2.2)
- [ ] Write unit tests for helpers

### Week 2: API Endpoints
- [ ] Implement getCustomerProfile lambda (2.3)
- [ ] Implement getCustomerReviews lambda (2.4)
- [ ] Configure API Gateway routes (Phase 3)
- [ ] Test endpoints in staging

### Week 3: Integration + Optimization
- [ ] Implement interaction tracking (2.5)
- [ ] Update existing lambdas to track interactions
- [ ] Create stats refresh background job (4.1)
- [ ] Performance testing and optimization

### Week 4: Testing + Deployment
- [ ] Complete all unit tests (5.1)
- [ ] Complete integration tests (5.2)
- [ ] Security audit (5.3)
- [ ] Staging deployment
- [ ] Production rollout with monitoring

---

## Key Considerations

### Privacy & Security
- Always validate authorization before returning data
- Never expose: full addresses, phone numbers, email, payment info
- Implement rate limiting to prevent profile scraping
- Log all access attempts for audit trail

### Performance
- Use `customer_profile_stats` table to avoid expensive aggregations on every request
- Implement cursor-based pagination for reviews (not offset-based)
- Add database indexes on frequently queried columns
- Consider caching frequently accessed profiles (Redis/ElastiCache)

### Scalability
- Stats refresh runs hourly, not on every request
- Interaction tracking uses INSERT...ON DUPLICATE KEY to avoid duplicates
- Pagination prevents large result sets
- Connection pooling for Lambda (reuse connections)

### Monitoring
Add CloudWatch metrics for:
- Profile view count (by customer_id)
- Authorization failures (403 responses)
- Stats calculation duration
- API latency (p50, p95, p99)
- Error rates

### Future Enhancements
- Customer response time tracking (requires message timestamps)
- Provider can "favorite" customers
- Customer can see who viewed their profile
- Dispute/report mechanism for reviews
- Profile completeness score

---

## Environment Variables

Required for all Lambda functions:

```bash
DB_HOST=quickfix-db.xxxxx.us-east-2.rds.amazonaws.com
DB_USER=quickfix_app
DB_PASSWORD=<secure-password>
DB_NAME=quickfix
AWS_REGION=us-east-2
```

---

## Rollback Plan

If issues arise in production:

1. **Immediate**: Disable new API routes in API Gateway
2. **Database**: Schema changes are additive (no data loss)
3. **Rollback**: Revert Lambda function versions to previous stable version
4. **Monitoring**: Check CloudWatch logs for error patterns

---

## Success Metrics

Track these KPIs post-launch:

- Profile view rate (% of providers viewing customer profiles)
- Authorization success rate (should be >95%)
- API response time (<500ms p95)
- Stats accuracy (manual validation sample)
- User feedback (provider satisfaction with feature)

---

## Contact & Support

For questions or issues during implementation:
- Backend Team Lead: [contact]
- Database Admin: [contact]
- DevOps: [contact]

---

**Document Version**: 1.0  
**Last Updated**: February 14, 2026  
**Status**: Ready for Implementation
