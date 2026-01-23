-- Migration: Create reviews table
-- Date: 2026-01-07
-- Description: Creates the reviews table for bidirectional reviews (customers ↔ providers) after job completion

USE quickfix;

-- Create reviews table
CREATE TABLE reviews (
    review_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    job_id BIGINT NOT NULL,

    -- Reviewer information (who wrote the review)
    reviewer_id BIGINT NOT NULL,
    reviewer_type ENUM('customer', 'provider') NOT NULL,

    -- Reviewee information (who is being reviewed)
    reviewee_id BIGINT NOT NULL,
    reviewee_type ENUM('customer', 'provider') NOT NULL,

    -- Review content
    rating INT NOT NULL,
    comment TEXT NOT NULL,

    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    -- Foreign key constraints
    CONSTRAINT fk_review_job FOREIGN KEY (job_id)
        REFERENCES jobs(job_id) ON DELETE CASCADE,

    -- Unique constraint: one review per reviewer per job
    -- This prevents a customer from reviewing the same job twice
    -- and prevents a provider from reviewing the same job twice
    CONSTRAINT unique_reviewer_job UNIQUE (job_id, reviewer_id, reviewer_type),

    -- Check constraints
    CONSTRAINT chk_rating_range CHECK (rating >= 1 AND rating <= 5),
    CONSTRAINT chk_comment_length CHECK (CHAR_LENGTH(comment) >= 10 AND CHAR_LENGTH(comment) <= 1000),

    -- Prevent self-reviews (reviewer and reviewee cannot be the same)
    CONSTRAINT chk_no_self_review CHECK (
        NOT (reviewer_id = reviewee_id AND reviewer_type = reviewee_type)
    ),

    -- Indexes for performance
    INDEX idx_job_id (job_id),
    INDEX idx_reviewer (reviewer_id, reviewer_type),
    INDEX idx_reviewee_created (reviewee_id, reviewee_type, created_at DESC),
    INDEX idx_created_at (created_at)

) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Verify the table was created
DESCRIBE reviews;

-- Show indexes
SHOW INDEX FROM reviews;
