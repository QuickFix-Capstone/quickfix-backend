-- Migration: Add avatar_url column to customers table
-- Date: 2026-01-01
-- Description: Adds avatar_url field to store S3 URLs for customer profile pictures
USE quickfix;
-- Add avatar_url column to customers table
ALTER TABLE customers
ADD COLUMN avatar_url VARCHAR(512) NULL COMMENT 'S3 URL for customer profile avatar';
-- Verify the change
DESCRIBE customers;