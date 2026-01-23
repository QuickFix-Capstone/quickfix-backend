-- Script to verify and add rating columns to service_providers and customers tables
-- Run this to fix the "Unknown column 'rating'" error

USE quickfix;

-- First, let's check what columns exist
SELECT 'Checking service_providers columns...' as status;
SHOW COLUMNS FROM service_providers LIKE '%rating%';

SELECT 'Checking customers columns...' as status;
SHOW COLUMNS FROM customers LIKE '%rating%';

-- Add rating columns to service_providers if they don't exist
-- Note: This uses IF NOT EXISTS equivalent for MySQL

-- Check if rating column exists, if not add it
SET @dbname = DATABASE();
SET @tablename = "service_providers";
SET @columnname = "rating";
SET @preparedStatement = (SELECT IF(
  (
    SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
    WHERE
      (table_name = @tablename)
      AND (table_schema = @dbname)
      AND (column_name = @columnname)
  ) > 0,
  "SELECT 'rating column already exists in service_providers' as status;",
  "ALTER TABLE service_providers ADD COLUMN rating DECIMAL(3, 2) DEFAULT 0.00 COMMENT 'Average rating calculated from reviews';"
));
PREPARE alterIfNotExists FROM @preparedStatement;
EXECUTE alterIfNotExists;
DEALLOCATE PREPARE alterIfNotExists;

-- Add total_rating_points to service_providers
SET @columnname = "total_rating_points";
SET @preparedStatement = (SELECT IF(
  (
    SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
    WHERE
      (table_name = @tablename)
      AND (table_schema = @dbname)
      AND (column_name = @columnname)
  ) > 0,
  "SELECT 'total_rating_points column already exists in service_providers' as status;",
  "ALTER TABLE service_providers ADD COLUMN total_rating_points INT DEFAULT 0 COMMENT 'Sum of all ratings received';"
));
PREPARE alterIfNotExists FROM @preparedStatement;
EXECUTE alterIfNotExists;
DEALLOCATE PREPARE alterIfNotExists;

-- Add total_review_count to service_providers
SET @columnname = "total_review_count";
SET @preparedStatement = (SELECT IF(
  (
    SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
    WHERE
      (table_name = @tablename)
      AND (table_schema = @dbname)
      AND (column_name = @columnname)
  ) > 0,
  "SELECT 'total_review_count column already exists in service_providers' as status;",
  "ALTER TABLE service_providers ADD COLUMN total_review_count INT DEFAULT 0 COMMENT 'Total number of reviews received';"
));
PREPARE alterIfNotExists FROM @preparedStatement;
EXECUTE alterIfNotExists;
DEALLOCATE PREPARE alterIfNotExists;

-- Now do the same for customers table
SET @tablename = "customers";

-- Add total_rating_points to customers
SET @columnname = "total_rating_points";
SET @preparedStatement = (SELECT IF(
  (
    SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
    WHERE
      (table_name = @tablename)
      AND (table_schema = @dbname)
      AND (column_name = @columnname)
  ) > 0,
  "SELECT 'total_rating_points column already exists in customers' as status;",
  "ALTER TABLE customers ADD COLUMN total_rating_points INT DEFAULT 0 COMMENT 'Sum of all ratings received from providers';"
));
PREPARE alterIfNotExists FROM @preparedStatement;
EXECUTE alterIfNotExists;
DEALLOCATE PREPARE alterIfNotExists;

-- Add total_review_count to customers
SET @columnname = "total_review_count";
SET @preparedStatement = (SELECT IF(
  (
    SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
    WHERE
      (table_name = @tablename)
      AND (table_schema = @dbname)
      AND (column_name = @columnname)
  ) > 0,
  "SELECT 'total_review_count column already exists in customers' as status;",
  "ALTER TABLE customers ADD COLUMN total_review_count INT DEFAULT 0 COMMENT 'Total number of reviews received from providers';"
));
PREPARE alterIfNotExists FROM @preparedStatement;
EXECUTE alterIfNotExists;
DEALLOCATE PREPARE alterIfNotExists;

-- Add average_rating to customers
SET @columnname = "average_rating";
SET @preparedStatement = (SELECT IF(
  (
    SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
    WHERE
      (table_name = @tablename)
      AND (table_schema = @dbname)
      AND (column_name = @columnname)
  ) > 0,
  "SELECT 'average_rating column already exists in customers' as status;",
  "ALTER TABLE customers ADD COLUMN average_rating DECIMAL(3, 2) DEFAULT 0.00 COMMENT 'Calculated average rating';"
));
PREPARE alterIfNotExists FROM @preparedStatement;
EXECUTE alterIfNotExists;
DEALLOCATE PREPARE alterIfNotExists;

-- Add indexes if they don't exist
-- Index for service_providers rating
SET @tablename = "service_providers";
SET @indexname = "idx_provider_rating";
SET @preparedStatement = (SELECT IF(
  (
    SELECT COUNT(*) FROM INFORMATION_SCHEMA.STATISTICS
    WHERE
      (table_name = @tablename)
      AND (table_schema = @dbname)
      AND (index_name = @indexname)
  ) > 0,
  "SELECT 'idx_provider_rating index already exists' as status;",
  "CREATE INDEX idx_provider_rating ON service_providers(rating DESC);"
));
PREPARE alterIfNotExists FROM @preparedStatement;
EXECUTE alterIfNotExists;
DEALLOCATE PREPARE alterIfNotExists;

-- Index for customers average_rating
SET @tablename = "customers";
SET @indexname = "idx_customer_rating";
SET @preparedStatement = (SELECT IF(
  (
    SELECT COUNT(*) FROM INFORMATION_SCHEMA.STATISTICS
    WHERE
      (table_name = @tablename)
      AND (table_schema = @dbname)
      AND (index_name = @indexname)
  ) > 0,
  "SELECT 'idx_customer_rating index already exists' as status;",
  "CREATE INDEX idx_customer_rating ON customers(average_rating DESC);"
));
PREPARE alterIfNotExists FROM @preparedStatement;
EXECUTE alterIfNotExists;
DEALLOCATE PREPARE alterIfNotExists;

-- Verify the final state
SELECT 'Final verification - service_providers columns:' as status;
SHOW COLUMNS FROM service_providers LIKE '%rating%';

SELECT 'Final verification - customers columns:' as status;
SHOW COLUMNS FROM customers LIKE '%rating%';

SELECT '✅ Migration complete! All rating columns added successfully.' as status;
