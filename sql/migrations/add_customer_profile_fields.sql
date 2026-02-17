-- Migration: Add Customer Profile Fields
-- Description: Add display_name, avatar_url (if not exists), and profile_visibility to customers table
-- Date: 2026-02-17
-- Phase: Customer Public Profile - Phase 1.1

-- Add display_name column
ALTER TABLE customers
ADD COLUMN IF NOT EXISTS display_name VARCHAR(100) NULL 
COMMENT 'Public display name';

-- Add avatar_url column (check if it exists first, as it may have been added in a previous migration)
-- Note: This column may already exist from add_avatar_url_to_customers.sql
ALTER TABLE customers
ADD COLUMN IF NOT EXISTS avatar_url VARCHAR(500) NULL 
COMMENT 'Profile picture URL';

-- Add profile_visibility column
ALTER TABLE customers
ADD COLUMN IF NOT EXISTS profile_visibility ENUM('public', 'restricted', 'private') 
NOT NULL DEFAULT 'restricted' 
COMMENT 'Who can view profile: public=all providers, restricted=interacted only, private=hidden';

-- Add index for profile_visibility queries
ALTER TABLE customers
ADD INDEX IF NOT EXISTS idx_profile_visibility (profile_visibility);

-- Verification query
SELECT 
    COLUMN_NAME, 
    COLUMN_TYPE, 
    IS_NULLABLE, 
    COLUMN_DEFAULT, 
    COLUMN_COMMENT
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_SCHEMA = DATABASE()
  AND TABLE_NAME = 'customers'
  AND COLUMN_NAME IN ('display_name', 'avatar_url', 'profile_visibility')
ORDER BY ORDINAL_POSITION;
