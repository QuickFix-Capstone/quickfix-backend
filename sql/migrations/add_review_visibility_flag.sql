-- Migration: Add Review Visibility Flag
-- Description: Add is_visible column to provider_customer_reviews table for public profile display control
-- Date: 2026-02-17
-- Phase: Customer Public Profile - Phase 1.3
-- Note: This applies to provider_customer_reviews (reviews ABOUT customers, shown on customer profiles)

-- Add is_visible column to provider_customer_reviews table
ALTER TABLE provider_customer_reviews
ADD COLUMN is_visible BOOLEAN NOT NULL DEFAULT TRUE 
COMMENT 'Whether review is publicly visible on customer profile';

-- Add composite index for efficient customer profile queries
ALTER TABLE provider_customer_reviews
ADD INDEX idx_customer_visible (customer_id, is_visible);

-- Verification query
SELECT 
    COLUMN_NAME, 
    COLUMN_TYPE, 
    IS_NULLABLE, 
    COLUMN_DEFAULT, 
    COLUMN_COMMENT
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_SCHEMA = DATABASE()
  AND TABLE_NAME = 'provider_customer_reviews'
  AND COLUMN_NAME = 'is_visible';

-- Show indexes on provider_customer_reviews table
SHOW INDEX FROM provider_customer_reviews WHERE Key_name = 'idx_customer_visible';
