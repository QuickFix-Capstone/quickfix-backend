-- ============================================================================
-- CORRECTED MIGRATION: Update Schema for Booking Confirmation Workflow
-- Date: 2026-01-23
-- Description: Fixes service_providers.provider_id to VARCHAR and adds 
--              confirmation workflow support
-- ============================================================================
USE quickfix;
-- ============================================================================
-- CRITICAL FIX: service_providers.provider_id should be VARCHAR, not BIGINT
-- ============================================================================
-- The code uses Cognito sub IDs (e.g., "google-oauth2|103949366066974158596")
-- which are strings, not integers. The schema incorrectly defines it as BIGINT.
-- ============================================================================
-- STEP 1: Drop Foreign Key Constraints (before modifying columns)
-- ============================================================================
ALTER TABLE bookings DROP FOREIGN KEY IF EXISTS fk_booking_provider;
ALTER TABLE jobs DROP FOREIGN KEY IF EXISTS fk_job_assigned_provider;
ALTER TABLE job_applications DROP FOREIGN KEY IF EXISTS fk_application_provider;
ALTER TABLE service_offerings DROP FOREIGN KEY IF EXISTS fk_service_offering_provider;
ALTER TABLE provider_certifications DROP FOREIGN KEY IF EXISTS fk_provider_certifications_provider;
-- ============================================================================
-- STEP 2: Fix service_providers.provider_id Type (BIGINT -> VARCHAR)
-- ============================================================================
-- Change provider_id from BIGINT AUTO_INCREMENT to VARCHAR(255)
-- Note: This will require manual data migration if you have existing numeric IDs
ALTER TABLE service_providers
MODIFY COLUMN provider_id VARCHAR(255) NOT NULL COMMENT 'Provider ID - Cognito sub or unique identifier';
-- Drop AUTO_INCREMENT and make it a regular primary key
ALTER TABLE service_providers DROP PRIMARY KEY,
    ADD PRIMARY KEY (provider_id);
-- ============================================================================
-- STEP 3: Update Related Tables to Use VARCHAR(255) for provider_id
-- ============================================================================
-- These tables already have VARCHAR(40), but should be VARCHAR(255) to match
-- Cognito sub length (can be longer than 40 characters)
ALTER TABLE bookings
MODIFY COLUMN provider_id VARCHAR(255) NOT NULL COMMENT 'Provider ID - matches service_providers.provider_id type';
ALTER TABLE jobs
MODIFY COLUMN assigned_provider_id VARCHAR(255) NULL COMMENT 'Assigned provider ID - matches service_providers.provider_id type';
ALTER TABLE job_applications
MODIFY COLUMN provider_id VARCHAR(255) NOT NULL COMMENT 'Provider ID - matches service_providers.provider_id type';
-- Update other related tables
ALTER TABLE service_offerings
MODIFY COLUMN provider_id VARCHAR(255) NOT NULL COMMENT 'Provider ID - matches service_providers.provider_id type';
ALTER TABLE provider_certifications
MODIFY COLUMN provider_id VARCHAR(255) NOT NULL COMMENT 'Provider ID - matches service_providers.provider_id type';
-- ============================================================================
-- STEP 4: Re-add Foreign Key Constraints with Correct Types
-- ============================================================================
ALTER TABLE bookings
ADD CONSTRAINT fk_booking_provider FOREIGN KEY (provider_id) REFERENCES service_providers(provider_id) ON DELETE CASCADE;
ALTER TABLE jobs
ADD CONSTRAINT fk_job_assigned_provider FOREIGN KEY (assigned_provider_id) REFERENCES service_providers(provider_id) ON DELETE
SET NULL;
ALTER TABLE job_applications
ADD CONSTRAINT fk_application_provider FOREIGN KEY (provider_id) REFERENCES service_providers(provider_id) ON DELETE CASCADE;
ALTER TABLE service_offerings
ADD CONSTRAINT fk_service_offering_provider FOREIGN KEY (provider_id) REFERENCES service_providers(provider_id) ON DELETE CASCADE;
ALTER TABLE provider_certifications
ADD CONSTRAINT fk_provider_certifications_provider FOREIGN KEY (provider_id) REFERENCES service_providers(provider_id) ON DELETE CASCADE;
-- ============================================================================
-- STEP 5: Add Booking Confirmation Workflow Fields
-- ============================================================================
ALTER TABLE bookings
ADD COLUMN IF NOT EXISTS confirmation_token VARCHAR(64) NULL COMMENT 'SHA-256 hash token for email confirmation',
    ADD COLUMN IF NOT EXISTS confirmation_token_expires_at TIMESTAMP NULL COMMENT 'Token expiration timestamp (7 days from creation)',
    ADD COLUMN IF NOT EXISTS confirmed_at TIMESTAMP NULL COMMENT 'Timestamp when provider confirmed the booking',
    ADD COLUMN IF NOT EXISTS job_id BIGINT NULL COMMENT 'Reference to job created after confirmation';
ALTER TABLE bookings
ADD INDEX IF NOT EXISTS idx_confirmation_token (confirmation_token);
-- ============================================================================
-- STEP 6: Add Job-Booking Relationship Fields
-- ============================================================================
ALTER TABLE jobs
ADD COLUMN IF NOT EXISTS booking_id BIGINT NULL COMMENT 'Reference to booking if job was created from confirmed booking',
    ADD COLUMN IF NOT EXISTS final_price DECIMAL(10, 2) NULL COMMENT 'Actual final price charged for the job',
    ADD COLUMN IF NOT EXISTS completed_at TIMESTAMP NULL COMMENT 'Timestamp when job was completed';
ALTER TABLE jobs
ADD INDEX IF NOT EXISTS idx_booking_id (booking_id);
-- ============================================================================
-- STEP 7: Add Cross-Reference Foreign Keys
-- ============================================================================
ALTER TABLE bookings
ADD CONSTRAINT fk_booking_job FOREIGN KEY (job_id) REFERENCES jobs(job_id) ON DELETE
SET NULL;
ALTER TABLE jobs
ADD CONSTRAINT fk_job_booking FOREIGN KEY (booking_id) REFERENCES bookings(booking_id) ON DELETE
SET NULL;
-- ============================================================================
-- STEP 8: Update Booking Status Enum
-- ============================================================================
ALTER TABLE bookings
MODIFY COLUMN status ENUM(
        'pending_confirmation',
        -- NEW: Waiting for provider email confirmation
        'pending',
        -- Provider confirmed, awaiting start
        'confirmed',
        -- Explicitly confirmed by both parties
        'in_progress',
        -- Service is being performed
        'completed',
        -- Service completed
        'cancelled' -- Booking cancelled
    ) NOT NULL DEFAULT 'pending_confirmation' COMMENT 'Booking lifecycle status';
-- ============================================================================
-- STEP 9: Add Timestamps to Job Applications
-- ============================================================================
ALTER TABLE job_applications
ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT 'Last update timestamp',
    ADD COLUMN IF NOT EXISTS responded_at TIMESTAMP NULL COMMENT 'Timestamp when application was accepted/rejected';
-- ============================================================================
-- STEP 10: Verification
-- ============================================================================
SELECT 'Service Providers Table Structure:' AS '';
DESCRIBE service_providers;
SELECT 'Bookings Table Structure:' AS '';
DESCRIBE bookings;
SELECT 'Jobs Table Structure:' AS '';
DESCRIBE jobs;
SELECT 'Job Applications Table Structure:' AS '';
DESCRIBE job_applications;
-- Verify all provider_id columns are VARCHAR(255)
SELECT 'Provider ID Column Types:' AS '';
SELECT TABLE_NAME,
    COLUMN_NAME,
    DATA_TYPE,
    COLUMN_TYPE
FROM information_schema.COLUMNS
WHERE TABLE_SCHEMA = 'quickfix'
    AND COLUMN_NAME LIKE '%provider_id%'
ORDER BY TABLE_NAME;
-- Verify foreign key constraints
SELECT 'Foreign Key Constraints:' AS '';
SELECT TABLE_NAME,
    CONSTRAINT_NAME,
    REFERENCED_TABLE_NAME,
    REFERENCED_COLUMN_NAME
FROM information_schema.KEY_COLUMN_USAGE
WHERE TABLE_SCHEMA = 'quickfix'
    AND REFERENCED_TABLE_NAME IS NOT NULL
ORDER BY TABLE_NAME,
    CONSTRAINT_NAME;
-- ============================================================================
-- MIGRATION COMPLETE
-- ============================================================================
SELECT 'Migration completed successfully!' AS 'Status';
SELECT 'provider_id is now VARCHAR(255) across all tables' AS 'Note';