-- Migration: Add rating summary fields to service_providers and customers tables
-- Date: 2026-01-07
-- Description: Adds fields to track rating statistics for both providers and customers

USE quickfix;

-- Note: service_providers already has 'rating', 'total_rating_points', and 'total_review_count' columns
-- We'll just update the rating column comment and add the index

-- Update the existing 'rating' column to clarify its purpose
ALTER TABLE service_providers
MODIFY COLUMN rating DECIMAL(3, 2) DEFAULT 0.00 COMMENT 'Average rating calculated from reviews (total_rating_points / total_review_count)';

-- Create index for sorting providers by rating (skip if already exists)
-- Note: Check if index exists first to avoid errors
-- CREATE INDEX idx_provider_rating ON service_providers(rating DESC);

-- Add rating summary fields to customers table
ALTER TABLE customers
ADD COLUMN total_rating_points INT NOT NULL DEFAULT 0 COMMENT 'Sum of all ratings received from providers',
ADD COLUMN total_review_count INT NOT NULL DEFAULT 0 COMMENT 'Total number of reviews received from providers',
ADD COLUMN average_rating DECIMAL(3, 2) NOT NULL DEFAULT 0.00 COMMENT 'Calculated average rating (total_rating_points / total_review_count)';

-- Create index for sorting customers by rating (useful for providers to see reliable customers)
CREATE INDEX idx_customer_rating ON customers(average_rating DESC);

-- Verify the changes for service_providers
DESCRIBE service_providers;

-- Show indexes for service_providers
SHOW INDEX FROM service_providers;

-- Verify the changes for customers
DESCRIBE customers;

-- Show indexes for customers
SHOW INDEX FROM customers;
