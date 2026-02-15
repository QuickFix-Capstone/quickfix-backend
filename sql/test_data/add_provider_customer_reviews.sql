-- Add test reviews from providers about customers
-- This script creates sample reviews to test the get_customer_reviews_about_me endpoint

USE quickfix;

-- First, let's check if we have providers and customers
SELECT 'Checking providers...' as status;
SELECT provider_id, business_name FROM service_providers LIMIT 5;

SELECT 'Checking customers...' as status;
SELECT customer_id, first_name, last_name, email FROM customers LIMIT 5;

SELECT 'Checking jobs...' as status;
SELECT job_id, customer_id, title FROM jobs LIMIT 5;

-- Insert sample provider reviews about customers
-- Make sure to use existing provider_id, customer_id, and job_id from your database

-- Example: Provider reviews customer after completing a job
INSERT INTO provider_customer_reviews (job_id, provider_id, customer_id, rating, comment)
VALUES 
    -- Adjust these IDs based on your actual data
    (1, 1, 1, 5, 'Excellent customer! Very clear communication and respectful. Would work with again.'),
    (2, 2, 1, 4, 'Good customer, prompt payment and reasonable expectations. Minor delays in response.'),
    (3, 1, 2, 5, 'Outstanding customer! Professional, courteous, and provided clear instructions.'),
    (4, 3, 1, 3, 'Average experience. Customer changed requirements multiple times during the job.'),
    (5, 2, 2, 5, 'Perfect customer! Friendly, understanding, and very appreciative of the work done.')
ON DUPLICATE KEY UPDATE 
    rating = VALUES(rating),
    comment = VALUES(comment),
    updated_at = CURRENT_TIMESTAMP;

-- Verify the inserted reviews
SELECT 'Verifying inserted reviews...' as status;
SELECT 
    r.review_id,
    r.job_id,
    r.provider_id,
    sp.business_name as provider_name,
    r.customer_id,
    CONCAT(c.first_name, ' ', c.last_name) as customer_name,
    r.rating,
    r.comment,
    r.created_at
FROM provider_customer_reviews r
LEFT JOIN service_providers sp ON r.provider_id = sp.provider_id
LEFT JOIN customers c ON r.customer_id = c.customer_id
ORDER BY r.created_at DESC
LIMIT 10;

-- Show summary by customer
SELECT 'Summary by customer...' as status;
SELECT 
    c.customer_id,
    CONCAT(c.first_name, ' ', c.last_name) as customer_name,
    COUNT(r.review_id) as total_reviews,
    AVG(r.rating) as average_rating,
    MIN(r.rating) as lowest_rating,
    MAX(r.rating) as highest_rating
FROM customers c
LEFT JOIN provider_customer_reviews r ON c.customer_id = r.customer_id
GROUP BY c.customer_id, c.first_name, c.last_name
HAVING total_reviews > 0
ORDER BY total_reviews DESC;
