-- ============================================================================
-- Simple Migration: Booking Confirmation Workflow
-- Date: 2026-01-23
-- Description: Add confirmation workflow fields to bookings and jobs tables
-- ============================================================================
USE quickfix;
-- ============================================================================
-- STEP 1: Add Booking Confirmation Workflow Fields
-- ============================================================================
-- Add confirmation token field
ALTER TABLE bookings
ADD COLUMN confirmation_token VARCHAR(64) NULL COMMENT 'SHA-256 hash token for email confirmation';
-- Add token expiration field
ALTER TABLE bookings
ADD COLUMN confirmation_token_expires_at TIMESTAMP NULL COMMENT 'Token expiration timestamp (7 days from creation)';
-- Add confirmed timestamp
ALTER TABLE bookings
ADD COLUMN confirmed_at TIMESTAMP NULL COMMENT 'Timestamp when provider confirmed the booking';
-- Add job reference
ALTER TABLE bookings
ADD COLUMN job_id BIGINT NULL COMMENT 'Reference to job created after confirmation';
-- Add index for confirmation token
ALTER TABLE bookings
ADD INDEX idx_confirmation_token (confirmation_token);
-- ============================================================================
-- STEP 2: Update Booking Status Enum
-- ============================================================================
ALTER TABLE bookings
MODIFY COLUMN status ENUM(
        'pending_confirmation',
        'pending',
        'confirmed',
        'in_progress',
        'completed',
        'cancelled'
    ) NOT NULL DEFAULT 'pending_confirmation' COMMENT 'Booking lifecycle status';
-- ============================================================================
-- STEP 3: Add Job-Booking Relationship Fields
-- ============================================================================
-- Add booking reference to jobs
ALTER TABLE jobs
ADD COLUMN booking_id BIGINT NULL COMMENT 'Reference to booking if job was created from confirmed booking';
-- Add final price field
ALTER TABLE jobs
ADD COLUMN final_price DECIMAL(10, 2) NULL COMMENT 'Actual final price charged for the job';
-- Add completed timestamp
ALTER TABLE jobs
ADD COLUMN completed_at TIMESTAMP NULL COMMENT 'Timestamp when job was completed';
-- Add index for booking_id
ALTER TABLE jobs
ADD INDEX idx_booking_id (booking_id);
-- ============================================================================
-- STEP 4: Add Foreign Key Constraints
-- ============================================================================
-- Link booking to job
ALTER TABLE bookings
ADD CONSTRAINT fk_booking_job FOREIGN KEY (job_id) REFERENCES jobs(job_id) ON DELETE
SET NULL;
-- Link job to booking
ALTER TABLE jobs
ADD CONSTRAINT fk_job_booking FOREIGN KEY (booking_id) REFERENCES bookings(booking_id) ON DELETE
SET NULL;
-- ============================================================================
-- Verification
-- ============================================================================
SELECT '=== Migration Completed Successfully ===' AS Status;
SELECT 'Bookings table now has confirmation workflow fields' AS Note;
SELECT 'Jobs table now has booking relationship fields' AS Note;
-- Show updated bookings structure
SELECT 'Bookings Table Structure:' AS '';
DESCRIBE bookings;
-- Show updated jobs structure  
SELECT 'Jobs Table Structure:' AS '';
DESCRIBE jobs;