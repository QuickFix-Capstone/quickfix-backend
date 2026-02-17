-- Rollback Script: Customer Public Profile - Phase 1
-- Description: Rollback all Phase 1 database schema changes
-- Date: 2026-02-17
-- 
-- WARNING: This will remove all data from customer_profile_stats and provider_customer_interactions tables
-- IMPORTANT: Take a backup before running this rollback script
--
-- Run this script if you need to rollback Phase 1 migrations

-- Set session variables for safety
SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0;
SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='TRADITIONAL,ALLOW_INVALID_DATES';

SELECT 'Starting Customer Profile Phase 1 Rollback...' AS Status;
SELECT NOW() AS StartTime;

-- ============================================================================
-- Rollback 1.4: Drop Provider-Customer Interactions Table
-- ============================================================================
SELECT 'Rollback 1.4: Dropping provider_customer_interactions table...' AS Status;

DROP TABLE IF EXISTS provider_customer_interactions;

SELECT 'Rollback 1.4: provider_customer_interactions table dropped' AS Status;

-- ============================================================================
-- Rollback 1.3: Remove Review Visibility Flag
-- ============================================================================
SELECT 'Rollback 1.3: Removing review visibility flag...' AS Status;

-- Drop indexes first
ALTER TABLE reviews DROP INDEX IF EXISTS idx_customer_visible;
ALTER TABLE reviews DROP INDEX IF EXISTS idx_provider_visible;

-- Drop column
ALTER TABLE reviews DROP COLUMN IF EXISTS is_visible;

SELECT 'Rollback 1.3: Review visibility flag removed' AS Status;

-- ============================================================================
-- Rollback 1.2: Drop Customer Profile Stats Table
-- ============================================================================
SELECT 'Rollback 1.2: Dropping customer_profile_stats table...' AS Status;

DROP TABLE IF EXISTS customer_profile_stats;

SELECT 'Rollback 1.2: customer_profile_stats table dropped' AS Status;

-- ============================================================================
-- Rollback 1.1: Remove Customer Profile Fields
-- ============================================================================
SELECT 'Rollback 1.1: Removing customer profile fields...' AS Status;

-- Drop index
ALTER TABLE customers DROP INDEX IF EXISTS idx_profile_visibility;

-- Drop columns (keep avatar_url as it may be used elsewhere)
ALTER TABLE customers DROP COLUMN IF EXISTS profile_visibility;
ALTER TABLE customers DROP COLUMN IF EXISTS display_name;

SELECT 'Rollback 1.1: Customer profile fields removed' AS Status;

-- ============================================================================
-- Final Verification
-- ============================================================================
SELECT 'Running final verification...' AS Status;

-- Verify tables are dropped
SELECT 
    TABLE_NAME
FROM INFORMATION_SCHEMA.TABLES
WHERE TABLE_SCHEMA = DATABASE()
  AND TABLE_NAME IN ('customer_profile_stats', 'provider_customer_interactions');

-- Should return 0 rows if rollback successful

-- Verify columns are removed
SELECT 
    COLUMN_NAME
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_SCHEMA = DATABASE()
  AND TABLE_NAME = 'customers'
  AND COLUMN_NAME IN ('display_name', 'profile_visibility');

-- Should return 0 rows if rollback successful

SELECT 
    COLUMN_NAME
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_SCHEMA = DATABASE()
  AND TABLE_NAME = 'reviews'
  AND COLUMN_NAME = 'is_visible';

-- Should return 0 rows if rollback successful

-- Restore session variables
SET SQL_MODE=@OLD_SQL_MODE;
SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS;

SELECT 'Phase 1 Rollback Completed Successfully!' AS Status;
SELECT NOW() AS EndTime;
