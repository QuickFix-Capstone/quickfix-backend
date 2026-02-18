-- Migration: Adjust customer_profile_stats table - Remove avg_rating column
-- Description: Remove avg_rating from customer_profile_stats since customers table already has average_rating
-- Date: 2026-02-17
-- Phase: Customer Public Profile - Phase 1 Adjustment

-- Drop avg_rating column from customer_profile_stats
-- The customers table already has average_rating, total_rating_points, and total_review_count
-- We'll use those existing columns instead of duplicating the data

ALTER TABLE customer_profile_stats
DROP COLUMN IF EXISTS avg_rating;

-- Verification query
SELECT 
    COLUMN_NAME, 
    COLUMN_TYPE, 
    IS_NULLABLE, 
    COLUMN_DEFAULT, 
    COLUMN_COMMENT
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_SCHEMA = DATABASE()
  AND TABLE_NAME = 'customer_profile_stats'
ORDER BY ORDINAL_POSITION;

-- Verify customers table still has average_rating
SELECT 
    COLUMN_NAME, 
    COLUMN_TYPE, 
    COLUMN_COMMENT
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_SCHEMA = DATABASE()
  AND TABLE_NAME = 'customers'
  AND COLUMN_NAME IN ('average_rating', 'total_rating_points', 'total_review_count');
