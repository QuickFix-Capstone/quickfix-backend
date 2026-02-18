# Phase 1 Adjustment - Remove Duplicate avg_rating Column

**Date**: February 17, 2026  
**Status**: ✅ Completed

---

## Issue Identified

The `customer_profile_stats` table was created with an `avg_rating` column, but the `customers` table already has rating-related columns:
- `average_rating` DECIMAL(3,2)
- `total_rating_points` INT
- `total_review_count` INT

This created unnecessary data duplication.

---

## Solution

Removed `avg_rating` from `customer_profile_stats` table to avoid duplication.

### Changes Made

**Database:**
- Dropped `customer_profile_stats.avg_rating` column
- Table now has 9 columns instead of 10

**Documentation:**
- Updated `CUSTOMER_PROFILE_BACKEND_IMPLEMENTATION.md`
- Updated SQL migration files
- Updated helper functions to use `customers.average_rating`

**Code Changes:**
- `calculateCustomerStats()` now reads from `customers.average_rating`
- `upsertStats()` no longer includes avg_rating
- `getCustomerProfile` lambda merges rating from customers table

---

## Final customer_profile_stats Structure

```sql
CREATE TABLE customer_profile_stats (
    customer_id BIGINT PRIMARY KEY,
    -- avg_rating removed (use customers.average_rating instead)
    review_count INT NOT NULL DEFAULT 0,
    jobs_posted_6mo INT NOT NULL DEFAULT 0,
    jobs_completed INT NOT NULL DEFAULT 0,
    jobs_cancelled INT NOT NULL DEFAULT 0,
    completion_rate DECIMAL(5,2) NULL,
    cancellation_rate DECIMAL(5,2) NULL,
    avg_response_time_minutes INT NULL,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);
```

---

## Usage in Queries

**Before (incorrect):**
```javascript
const [stats] = await connection.query(
    'SELECT avg_rating FROM customer_profile_stats WHERE customer_id = ?',
    [customerId]
);
```

**After (correct):**
```javascript
// Get stats from cache table
const [stats] = await connection.query(
    'SELECT * FROM customer_profile_stats WHERE customer_id = ?',
    [customerId]
);

// Get rating from customers table
const [customer] = await connection.query(
    'SELECT average_rating FROM customers WHERE customer_id = ?',
    [customerId]
);

// Merge them
const fullStats = {
    ...stats[0],
    avg_rating: customer[0].average_rating
};
```

---

## Benefits

1. **No Data Duplication**: Single source of truth for customer ratings
2. **Consistency**: Rating updates in customers table are immediately reflected
3. **Simpler Maintenance**: No need to sync two columns
4. **Existing Infrastructure**: Leverages already-maintained rating columns

---

## Migration Files

- `sql/migrations/adjust_customer_profile_stats_remove_avg_rating.sql`
- `run_adjust_customer_profile_stats.py` (executed successfully)

---

## Verification

```sql
-- Verify avg_rating is removed
DESCRIBE customer_profile_stats;

-- Verify customers table has rating columns
SELECT COLUMN_NAME, COLUMN_TYPE 
FROM INFORMATION_SCHEMA.COLUMNS 
WHERE TABLE_NAME = 'customers' 
  AND COLUMN_NAME IN ('average_rating', 'total_rating_points', 'total_review_count');
```

---

**Status**: Adjustment complete and tested ✅
