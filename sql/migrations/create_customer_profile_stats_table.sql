-- Migration: Create Customer Profile Stats Table
-- Description: Cache aggregated statistics for customer profiles to optimize performance
-- Date: 2026-02-17
-- Phase: Customer Public Profile - Phase 1.2
-- Note: avg_rating is NOT included as customers table already has average_rating column

CREATE TABLE IF NOT EXISTS customer_profile_stats (
    customer_id BIGINT PRIMARY KEY,
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
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Cached customer profile statistics for performance optimization';

-- Note: For customer ratings, use customers.average_rating column
-- The customers table already has: average_rating, total_rating_points, total_review_count

-- Verification query
SELECT 
    TABLE_NAME,
    TABLE_ROWS,
    CREATE_TIME,
    TABLE_COMMENT
FROM INFORMATION_SCHEMA.TABLES
WHERE TABLE_SCHEMA = DATABASE()
  AND TABLE_NAME = 'customer_profile_stats';

-- Show table structure
DESCRIBE customer_profile_stats;
