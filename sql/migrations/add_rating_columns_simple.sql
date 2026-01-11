-- Simple script to add rating columns to service_providers and customers tables
-- Run this to fix the "Unknown column 'rating'" error

USE quickfix;

-- Add rating columns to service_providers
ALTER TABLE service_providers
ADD COLUMN IF NOT EXISTS rating DECIMAL(3, 2) DEFAULT 0.00 COMMENT 'Average rating calculated from reviews',
ADD COLUMN IF NOT EXISTS total_rating_points INT DEFAULT 0 COMMENT 'Sum of all ratings received',
ADD COLUMN IF NOT EXISTS total_review_count INT DEFAULT 0 COMMENT 'Total number of reviews received';

-- Add rating columns to customers
ALTER TABLE customers
ADD COLUMN IF NOT EXISTS total_rating_points INT DEFAULT 0 COMMENT 'Sum of all ratings received from providers',
ADD COLUMN IF NOT EXISTS total_review_count INT DEFAULT 0 COMMENT 'Total number of reviews received from providers',
ADD COLUMN IF NOT EXISTS average_rating DECIMAL(3, 2) DEFAULT 0.00 COMMENT 'Calculated average rating';

-- Add indexes for performance
CREATE INDEX IF NOT EXISTS idx_provider_rating ON service_providers(rating DESC);
CREATE INDEX IF NOT EXISTS idx_customer_rating ON customers(average_rating DESC);

-- Verify columns were added
DESCRIBE service_providers;
DESCRIBE customers;

SELECT '✅ Rating columns added successfully!' as status;
