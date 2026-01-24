-- ============================================================================
-- CORRECTED MIGRATION: Update Schema for Booking Confirmation Workflow
-- Date: 2026-01-23
-- Description: Fixes service_providers.provider_id to VARCHAR and adds 
--              confirmation workflow support
-- Fixed: Removed IF EXISTS from DROP FOREIGN KEY (not supported in MySQL 5.7)
-- ============================================================================
USE quickfix;
-- ============================================================================
-- STEP 1: Drop Foreign Key Constraints (before modifying columns)
-- ============================================================================
-- Note: Using procedure to handle non-existent constraints gracefully
DELIMITER $$ DROP PROCEDURE IF EXISTS drop_fk_if_exists $$ CREATE PROCEDURE drop_fk_if_exists(
    IN tableName VARCHAR(64),
    IN constraintName VARCHAR(64)
) BEGIN
DECLARE CONTINUE HANDLER FOR SQLEXCEPTION BEGIN
END;
SET @sql = CONCAT(
        'ALTER TABLE ',
        tableName,
        ' DROP FOREIGN KEY ',
        constraintName
    );
PREPARE stmt
FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;
END $$ DELIMITER;
-- Drop existing foreign keys
CALL drop_fk_if_exists('bookings', 'fk_booking_provider');
CALL drop_fk_if_exists('jobs', 'fk_job_assigned_provider');
CALL drop_fk_if_exists('job_applications', 'fk_application_provider');
CALL drop_fk_if_exists(
    'service_offerings',
    'fk_service_offering_provider'
);
CALL drop_fk_if_exists(
    'provider_certifications',
    'fk_provider_certifications_provider'
);
DROP PROCEDURE IF EXISTS drop_fk_if_exists;
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
-- Create procedure to add columns if they don't exist
DELIMITER $$ DROP PROCEDURE IF EXISTS add_column_if_not_exists $$ CREATE PROCEDURE add_column_if_not_exists(
    IN tableName VARCHAR(64),
    IN columnName VARCHAR(64),
    IN columnDefinition VARCHAR(255)
) BEGIN
DECLARE CONTINUE HANDLER FOR SQLEXCEPTION BEGIN
END;
SET @sql = CONCAT(
        'ALTER TABLE ',
        tableName,
        ' ADD COLUMN ',
        columnName,
        ' ',
        columnDefinition
    );
PREPARE stmt
FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;
END $$ DELIMITER;
-- Add confirmation workflow columns
CALL add_column_if_not_exists(
    'bookings',
    'confirmation_token',
    'VARCHAR(64) NULL COMMENT "SHA-256 hash token for email confirmation"'
);
CALL add_column_if_not_exists(
    'bookings',
    'confirmation_token_expires_at',
    'TIMESTAMP NULL COMMENT "Token expiration timestamp (7 days from creation)"'
);
CALL add_column_if_not_exists(
    'bookings',
    'confirmed_at',
    'TIMESTAMP NULL COMMENT "Timestamp when provider confirmed the booking"'
);
CALL add_column_if_not_exists(
    'bookings',
    'job_id',
    'BIGINT NULL COMMENT "Reference to job created after confirmation"'
);
DROP PROCEDURE IF EXISTS add_column_if_not_exists;
-- Add index for confirmation token
DELIMITER $$ DROP PROCEDURE IF EXISTS add_index_if_not_exists $$ CREATE PROCEDURE add_index_if_not_exists(
    IN tableName VARCHAR(64),
    IN indexName VARCHAR(64),
    IN columnName VARCHAR(64)
) BEGIN
DECLARE CONTINUE HANDLER FOR SQLEXCEPTION BEGIN
END;
SET @sql = CONCAT(
        'ALTER TABLE ',
        tableName,
        ' ADD INDEX ',
        indexName,
        ' (',
        columnName,
        ')'
    );
PREPARE stmt
FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;
END $$ DELIMITER;
CALL add_index_if_not_exists(
    'bookings',
    'idx_confirmation_token',
    'confirmation_token'
);
DROP PROCEDURE IF EXISTS add_index_if_not_exists;
-- ============================================================================
-- STEP 6: Add Job-Booking Relationship Fields
-- ============================================================================
DELIMITER $$ DROP PROCEDURE IF EXISTS add_column_if_not_exists $$ CREATE PROCEDURE add_column_if_not_exists(
    IN tableName VARCHAR(64),
    IN columnName VARCHAR(64),
    IN columnDefinition VARCHAR(255)
) BEGIN
DECLARE CONTINUE HANDLER FOR SQLEXCEPTION BEGIN
END;
SET @sql = CONCAT(
        'ALTER TABLE ',
        tableName,
        ' ADD COLUMN ',
        columnName,
        ' ',
        columnDefinition
    );
PREPARE stmt
FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;
END $$ DELIMITER;
CALL add_column_if_not_exists(
    'jobs',
    'booking_id',
    'BIGINT NULL COMMENT "Reference to booking if job was created from confirmed booking"'
);
CALL add_column_if_not_exists(
    'jobs',
    'final_price',
    'DECIMAL(10, 2) NULL COMMENT "Actual final price charged for the job"'
);
CALL add_column_if_not_exists(
    'jobs',
    'completed_at',
    'TIMESTAMP NULL COMMENT "Timestamp when job was completed"'
);
DROP PROCEDURE IF EXISTS add_column_if_not_exists;
-- Add index for booking_id
DELIMITER $$ DROP PROCEDURE IF EXISTS add_index_if_not_exists $$ CREATE PROCEDURE add_index_if_not_exists(
    IN tableName VARCHAR(64),
    IN indexName VARCHAR(64),
    IN columnName VARCHAR(64)
) BEGIN
DECLARE CONTINUE HANDLER FOR SQLEXCEPTION BEGIN
END;
SET @sql = CONCAT(
        'ALTER TABLE ',
        tableName,
        ' ADD INDEX ',
        indexName,
        ' (',
        columnName,
        ')'
    );
PREPARE stmt
FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;
END $$ DELIMITER;
CALL add_index_if_not_exists('jobs', 'idx_booking_id', 'booking_id');
DROP PROCEDURE IF EXISTS add_index_if_not_exists;
-- ============================================================================
-- STEP 7: Add Cross-Reference Foreign Keys
-- ============================================================================
DELIMITER $$ DROP PROCEDURE IF EXISTS add_fk_if_not_exists $$ CREATE PROCEDURE add_fk_if_not_exists(
    IN tableName VARCHAR(64),
    IN constraintName VARCHAR(64),
    IN fkDefinition VARCHAR(255)
) BEGIN
DECLARE CONTINUE HANDLER FOR SQLEXCEPTION BEGIN
END;
SET @sql = CONCAT(
        'ALTER TABLE ',
        tableName,
        ' ADD CONSTRAINT ',
        constraintName,
        ' ',
        fkDefinition
    );
PREPARE stmt
FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;
END $$ DELIMITER;
CALL add_fk_if_not_exists(
    'bookings',
    'fk_booking_job',
    'FOREIGN KEY (job_id) REFERENCES jobs(job_id) ON DELETE SET NULL'
);
CALL add_fk_if_not_exists(
    'jobs',
    'fk_job_booking',
    'FOREIGN KEY (booking_id) REFERENCES bookings(booking_id) ON DELETE SET NULL'
);
DROP PROCEDURE IF EXISTS add_fk_if_not_exists;
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
DELIMITER $$ DROP PROCEDURE IF EXISTS add_column_if_not_exists $$ CREATE PROCEDURE add_column_if_not_exists(
    IN tableName VARCHAR(64),
    IN columnName VARCHAR(64),
    IN columnDefinition VARCHAR(255)
) BEGIN
DECLARE CONTINUE HANDLER FOR SQLEXCEPTION BEGIN
END;
SET @sql = CONCAT(
        'ALTER TABLE ',
        tableName,
        ' ADD COLUMN ',
        columnName,
        ' ',
        columnDefinition
    );
PREPARE stmt
FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;
END $$ DELIMITER;
CALL add_column_if_not_exists(
    'job_applications',
    'updated_at',
    'TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT "Last update timestamp"'
);
CALL add_column_if_not_exists(
    'job_applications',
    'responded_at',
    'TIMESTAMP NULL COMMENT "Timestamp when application was accepted/rejected"'
);
DROP PROCEDURE IF EXISTS add_column_if_not_exists;
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
SELECT 'Booking confirmation workflow fields added' AS 'Note';