-- Migration: Add booking_id to review tables
-- Date: 2026-01-21
-- Description: Support reviews for both jobs and bookings

USE quickfix;

-- Add booking_id to customer_provider_reviews
ALTER TABLE customer_provider_reviews
ADD COLUMN booking_id BIGINT NULL AFTER job_id,
ADD CONSTRAINT fk_cp_review_booking FOREIGN KEY (booking_id)
    REFERENCES bookings(booking_id) ON DELETE CASCADE,
ADD INDEX idx_cp_booking_id (booking_id);

-- Add booking_id to provider_customer_reviews
ALTER TABLE provider_customer_reviews
ADD COLUMN booking_id BIGINT NULL AFTER job_id,
ADD CONSTRAINT fk_pc_review_booking FOREIGN KEY (booking_id)
    REFERENCES bookings(booking_id) ON DELETE CASCADE,
ADD INDEX idx_pc_booking_id (booking_id);

-- Add constraint: must have either job_id OR booking_id (not both, not neither)
-- Note: MySQL doesn't support CHECK constraints well in older versions
-- We'll enforce this in application logic

-- Verify changes
DESCRIBE customer_provider_reviews;
DESCRIBE provider_customer_reviews;
