-- Migration: Create separate review tables for customer-provider relationships
-- Date: 2026-01-19
-- Description: Creates two separate tables for bidirectional reviews:
--   1. customer_provider_reviews - reviews written BY customers ABOUT providers
--   2. provider_customer_reviews - reviews written BY providers ABOUT customers

USE quickfix;

-- Drop the old unified reviews table if it exists
DROP TABLE IF EXISTS reviews;

-- ============================================================================
-- Table 1: customer_provider_reviews
-- Reviews written BY customers ABOUT service providers
-- ============================================================================
CREATE TABLE customer_provider_reviews (
    review_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    job_id BIGINT NOT NULL,

    -- Reviewer (customer who wrote the review)
    customer_id BIGINT NOT NULL,

    -- Reviewee (provider being reviewed)
    provider_id BIGINT NOT NULL,

    -- Review content
    rating INT NOT NULL,
    comment TEXT NOT NULL,

    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    -- Foreign key constraints
    CONSTRAINT fk_cp_review_job FOREIGN KEY (job_id)
        REFERENCES jobs(job_id) ON DELETE CASCADE,
    CONSTRAINT fk_cp_review_customer FOREIGN KEY (customer_id)
        REFERENCES customers(customer_id) ON DELETE CASCADE,
    CONSTRAINT fk_cp_review_provider FOREIGN KEY (provider_id)
        REFERENCES service_providers(provider_id) ON DELETE CASCADE,

    -- Unique constraint: one review per customer per job
    CONSTRAINT unique_customer_job_review UNIQUE (job_id, customer_id),

    -- Check constraints
    CONSTRAINT chk_cp_rating_range CHECK (rating >= 1 AND rating <= 5),
    CONSTRAINT chk_cp_comment_length CHECK (CHAR_LENGTH(comment) >= 10 AND CHAR_LENGTH(comment) <= 1000),

    -- Indexes for performance
    INDEX idx_cp_job_id (job_id),
    INDEX idx_cp_customer_id (customer_id),
    INDEX idx_cp_provider_id (provider_id),
    INDEX idx_cp_provider_created (provider_id, created_at DESC),
    INDEX idx_cp_created_at (created_at)

) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================================
-- Table 2: provider_customer_reviews
-- Reviews written BY service providers ABOUT customers
-- ============================================================================
CREATE TABLE provider_customer_reviews (
    review_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    job_id BIGINT NOT NULL,

    -- Reviewer (provider who wrote the review)
    provider_id BIGINT NOT NULL,

    -- Reviewee (customer being reviewed)
    customer_id BIGINT NOT NULL,

    -- Review content
    rating INT NOT NULL,
    comment TEXT NOT NULL,

    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    -- Foreign key constraints
    CONSTRAINT fk_pc_review_job FOREIGN KEY (job_id)
        REFERENCES jobs(job_id) ON DELETE CASCADE,
    CONSTRAINT fk_pc_review_provider FOREIGN KEY (provider_id)
        REFERENCES service_providers(provider_id) ON DELETE CASCADE,
    CONSTRAINT fk_pc_review_customer FOREIGN KEY (customer_id)
        REFERENCES customers(customer_id) ON DELETE CASCADE,

    -- Unique constraint: one review per provider per job
    CONSTRAINT unique_provider_job_review UNIQUE (job_id, provider_id),

    -- Check constraints
    CONSTRAINT chk_pc_rating_range CHECK (rating >= 1 AND rating <= 5),
    CONSTRAINT chk_pc_comment_length CHECK (CHAR_LENGTH(comment) >= 10 AND CHAR_LENGTH(comment) <= 1000),

    -- Indexes for performance
    INDEX idx_pc_job_id (job_id),
    INDEX idx_pc_provider_id (provider_id),
    INDEX idx_pc_customer_id (customer_id),
    INDEX idx_pc_customer_created (customer_id, created_at DESC),
    INDEX idx_pc_created_at (created_at)

) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================================
-- Verification
-- ============================================================================

-- Verify tables were created
DESCRIBE customer_provider_reviews;
DESCRIBE provider_customer_reviews;

-- Show indexes
SHOW INDEX FROM customer_provider_reviews;
SHOW INDEX FROM provider_customer_reviews;
