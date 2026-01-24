-- ============================================================================
-- PRE-MIGRATION VALIDATION SCRIPT
-- Purpose: Check if data is compatible with schema changes
-- Run this BEFORE executing the migration
-- ============================================================================
USE quickfix;
-- ============================================================================
-- CHECK 1: Verify service_providers.provider_id is BIGINT
-- ============================================================================
SELECT 'Checking service_providers.provider_id type...' AS 'Step 1';
SELECT COLUMN_NAME,
    DATA_TYPE,
    COLUMN_TYPE
FROM information_schema.COLUMNS
WHERE TABLE_SCHEMA = 'quickfix'
    AND TABLE_NAME = 'service_providers'
    AND COLUMN_NAME = 'provider_id';
-- ============================================================================
-- CHECK 2: Check existing provider_id values in bookings
-- ============================================================================
SELECT 'Checking bookings.provider_id values...' AS 'Step 2';
-- Check if bookings table exists and has data
SELECT COUNT(*) AS total_bookings
FROM bookings;
-- Check data type
SELECT COLUMN_NAME,
    DATA_TYPE,
    COLUMN_TYPE
FROM information_schema.COLUMNS
WHERE TABLE_SCHEMA = 'quickfix'
    AND TABLE_NAME = 'bookings'
    AND COLUMN_NAME = 'provider_id';
-- Sample existing values
SELECT DISTINCT provider_id
FROM bookings
LIMIT 10;
-- Check if any non-numeric values exist (will fail conversion)
SELECT provider_id,
    CASE
        WHEN provider_id REGEXP '^[0-9]+$' THEN 'OK - Numeric'
        ELSE 'ERROR - Non-numeric'
    END AS conversion_status
FROM bookings
WHERE provider_id NOT REGEXP '^[0-9]+$'
LIMIT 10;
-- ============================================================================
-- CHECK 3: Check existing assigned_provider_id values in jobs
-- ============================================================================
SELECT 'Checking jobs.assigned_provider_id values...' AS 'Step 3';
-- Check if jobs table exists and has data
SELECT COUNT(*) AS total_jobs
FROM jobs;
-- Check data type
SELECT COLUMN_NAME,
    DATA_TYPE,
    COLUMN_TYPE
FROM information_schema.COLUMNS
WHERE TABLE_SCHEMA = 'quickfix'
    AND TABLE_NAME = 'jobs'
    AND COLUMN_NAME = 'assigned_provider_id';
-- Sample existing values
SELECT DISTINCT assigned_provider_id
FROM jobs
WHERE assigned_provider_id IS NOT NULL
LIMIT 10;
-- Check if any non-numeric values exist
SELECT assigned_provider_id,
    CASE
        WHEN assigned_provider_id REGEXP '^[0-9]+$' THEN 'OK - Numeric'
        ELSE 'ERROR - Non-numeric'
    END AS conversion_status
FROM jobs
WHERE assigned_provider_id IS NOT NULL
    AND assigned_provider_id NOT REGEXP '^[0-9]+$'
LIMIT 10;
-- ============================================================================
-- CHECK 4: Check existing provider_id values in job_applications
-- ============================================================================
SELECT 'Checking job_applications.provider_id values...' AS 'Step 4';
-- Check if job_applications table exists and has data
SELECT COUNT(*) AS total_applications
FROM job_applications;
-- Check data type
SELECT COLUMN_NAME,
    DATA_TYPE,
    COLUMN_TYPE
FROM information_schema.COLUMNS
WHERE TABLE_SCHEMA = 'quickfix'
    AND TABLE_NAME = 'job_applications'
    AND COLUMN_NAME = 'provider_id';
-- Sample existing values
SELECT DISTINCT provider_id
FROM job_applications
LIMIT 10;
-- Check if any non-numeric values exist
SELECT provider_id,
    CASE
        WHEN provider_id REGEXP '^[0-9]+$' THEN 'OK - Numeric'
        ELSE 'ERROR - Non-numeric'
    END AS conversion_status
FROM job_applications
WHERE provider_id NOT REGEXP '^[0-9]+$'
LIMIT 10;
-- ============================================================================
-- CHECK 5: Verify foreign key references
-- ============================================================================
SELECT 'Checking current foreign key constraints...' AS 'Step 5';
SELECT TABLE_NAME,
    CONSTRAINT_NAME,
    REFERENCED_TABLE_NAME,
    REFERENCED_COLUMN_NAME
FROM information_schema.KEY_COLUMN_USAGE
WHERE TABLE_SCHEMA = 'quickfix'
    AND TABLE_NAME IN ('bookings', 'jobs', 'job_applications')
    AND REFERENCED_TABLE_NAME IS NOT NULL;
-- ============================================================================
-- CHECK 6: Check for orphaned records
-- ============================================================================
SELECT 'Checking for orphaned records...' AS 'Step 6';
-- Bookings with invalid provider_id
SELECT 'Bookings with invalid provider_id' AS issue,
    COUNT(*) AS count
FROM bookings b
    LEFT JOIN service_providers sp ON b.provider_id = sp.provider_id
WHERE sp.provider_id IS NULL;
-- Jobs with invalid assigned_provider_id
SELECT 'Jobs with invalid assigned_provider_id' AS issue,
    COUNT(*) AS count
FROM jobs j
    LEFT JOIN service_providers sp ON j.assigned_provider_id = sp.provider_id
WHERE j.assigned_provider_id IS NOT NULL
    AND sp.provider_id IS NULL;
-- Job applications with invalid provider_id
SELECT 'Job applications with invalid provider_id' AS issue,
    COUNT(*) AS count
FROM job_applications ja
    LEFT JOIN service_providers sp ON ja.provider_id = sp.provider_id
WHERE sp.provider_id IS NULL;
-- ============================================================================
-- CHECK 7: Check if new columns already exist
-- ============================================================================
SELECT 'Checking if new columns already exist...' AS 'Step 7';
SELECT TABLE_NAME,
    COLUMN_NAME
FROM information_schema.COLUMNS
WHERE TABLE_SCHEMA = 'quickfix'
    AND (
        (
            TABLE_NAME = 'bookings'
            AND COLUMN_NAME IN (
                'confirmation_token',
                'confirmation_token_expires_at',
                'confirmed_at',
                'job_id'
            )
        )
        OR (
            TABLE_NAME = 'jobs'
            AND COLUMN_NAME IN ('booking_id', 'final_price', 'completed_at')
        )
        OR (
            TABLE_NAME = 'job_applications'
            AND COLUMN_NAME IN ('updated_at', 'responded_at')
        )
    )
ORDER BY TABLE_NAME,
    COLUMN_NAME;
-- ============================================================================
-- SUMMARY
-- ============================================================================
SELECT '
========================================
PRE-MIGRATION VALIDATION COMPLETE
========================================

Review the results above:

✅ SAFE TO PROCEED if:
   - All provider_id values are numeric
   - No orphaned records found
   - service_providers.provider_id is BIGINT
   - New columns do not already exist

⚠️  CAUTION if:
   - Non-numeric provider_id values found
   - Orphaned records exist
   - Some new columns already exist

❌ DO NOT PROCEED if:
   - service_providers.provider_id is not BIGINT
   - Critical data integrity issues found

Next Steps:
1. Review all checks above
2. Fix any data issues found
3. Run the migration script if all checks pass
4. Backup database before migration!

========================================
' AS 'Validation Summary';