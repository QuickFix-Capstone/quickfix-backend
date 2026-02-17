-- Master Migration Script: Customer Public Profile - Phase 1
-- Description: Runs all Phase 1 database schema updates for customer public profile feature
-- Date: 2026-02-17
-- Author: Backend Team
-- 
-- This script executes all Phase 1 migrations in the correct order:
-- 1. Add customer profile fields (display_name, avatar_url, profile_visibility)
-- 2. Create customer_profile_stats table
-- 3. Add review visibility flag
-- 4. Create provider_customer_interactions table
--
-- IMPORTANT: Review each migration before running in production
-- BACKUP: Ensure database backup is taken before running

-- Set session variables for safety
SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0;
SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='TRADITIONAL,ALLOW_INVALID_DATES';

-- Start transaction (note: DDL statements auto-commit in MySQL, but we track progress)
SELECT 'Starting Customer Profile Phase 1 Migrations...' AS Status;
SELECT NOW() AS StartTime;

-- ============================================================================
-- Migration 1.1: Add Customer Profile Fields
-- ============================================================================
SELECT '1.1: Adding customer profile fields...' AS Status;

SOURCE sql/migrations/add_customer_profile_fields.sql;

SELECT '1.1: Customer profile fields added successfully' AS Status;

-- ============================================================================
-- Migration 1.2: Create Customer Profile Stats Table
-- ============================================================================
SELECT '1.2: Creating customer_profile_stats table...' AS Status;

SOURCE sql/migrations/create_customer_profile_stats_table.sql;

SELECT '1.2: customer_profile_stats table created successfully' AS Status;

-- ============================================================================
-- Migration 1.3: Add Review Visibility Flag
-- ============================================================================
SELECT '1.3: Adding review visibility flag...' AS Status;

SOURCE sql/migrations/add_review_visibility_flag.sql;

SELECT '1.3: Review visibility flag added successfully' AS Status;

-- ============================================================================
-- Migration 1.4: Create Provider-Customer Interactions Table
-- ============================================================================
SELECT '1.4: Creating provider_customer_interactions table...' AS Status;

SOURCE sql/migrations/create_provider_customer_interactions_table.sql;

SELECT '1.4: provider_customer_interactions table created successfully' AS Status;

-- ============================================================================
-- Final Verification
-- ============================================================================
SELECT 'Running final verification...' AS Status;

-- Verify all new columns exist
SELECT 
    'customers' AS table_name,
    COUNT(*) AS new_columns
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_SCHEMA = DATABASE()
  AND TABLE_NAME = 'customers'
  AND COLUMN_NAME IN ('display_name', 'profile_visibility');

-- Verify new tables exist
SELECT 
    TABLE_NAME,
    TABLE_ROWS,
    CREATE_TIME
FROM INFORMATION_SCHEMA.TABLES
WHERE TABLE_SCHEMA = DATABASE()
  AND TABLE_NAME IN ('customer_profile_stats', 'provider_customer_interactions')
ORDER BY TABLE_NAME;

-- Verify review visibility column
SELECT 
    'reviews' AS table_name,
    COUNT(*) AS new_columns
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_SCHEMA = DATABASE()
  AND TABLE_NAME = 'reviews'
  AND COLUMN_NAME = 'is_visible';

-- Restore session variables
SET SQL_MODE=@OLD_SQL_MODE;
SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS;

SELECT 'Phase 1 Migrations Completed Successfully!' AS Status;
SELECT NOW() AS EndTime;
