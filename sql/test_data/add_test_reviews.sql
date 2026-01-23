-- Add test reviews and update provider ratings
-- This script creates sample reviews to test the get_provider_reviews endpoint
-- First, let's check if we have customers
SELECT customer_id,
    name
FROM customers
LIMIT 5;
-- Insert some test reviews for SP-001 (Carter Plumbing)
INSERT INTO reviews (
        job_id,
        reviewer_id,
        reviewer_type,
        reviewee_id,
        reviewee_type,
        rating,
        comment
    )
VALUES (
        1,
        1,
        'customer',
        'SP-001',
        'provider',
        5,
        'Excellent plumbing service! Very professional and fixed my leak quickly.'
    ),
    (
        2,
        2,
        'customer',
        'SP-001',
        'provider',
        4,
        'Good work, arrived on time. Would recommend.'
    ),
    (
        3,
        3,
        'customer',
        'SP-001',
        'provider',
        5,
        'Outstanding service! Carter Plumbing is the best in town.'
    );
-- Insert test reviews for SP-002 (Rogers Electrical)
INSERT INTO reviews (
        job_id,
        reviewer_id,
        reviewer_type,
        reviewee_id,
        reviewee_type,
        rating,
        comment
    )
VALUES (
        4,
        1,
        'customer',
        'SP-002',
        'provider',
        3,
        'Service was okay, but took longer than expected.'
    ),
    (
        5,
        4,
        'customer',
        'SP-002',
        'provider',
        5,
        'Great electrician! Fixed my wiring issues perfectly.'
    );
-- Insert test reviews for SP-003 (Chen HVAC Services)
INSERT INTO reviews (
        job_id,
        reviewer_id,
        reviewer_type,
        reviewee_id,
        reviewee_type,
        rating,
        comment
    )
VALUES (
        6,
        2,
        'customer',
        'SP-003',
        'provider',
        5,
        'Amazing HVAC service! My AC is working perfectly now.'
    ),
    (
        7,
        3,
        'customer',
        'SP-003',
        'provider',
        4,
        'Very knowledgeable and friendly. Good pricing too.'
    ),
    (
        8,
        5,
        'customer',
        'SP-003',
        'provider',
        5,
        'Chen HVAC is fantastic! Highly recommend for any heating/cooling needs.'
    );
-- Now update the provider ratings manually (or you can call the update_ratings Lambda)
-- For SP-001: 3 reviews, ratings: 5, 4, 5 = total 14 points, avg 4.67
UPDATE service_providers
SET total_rating_points = 14,
    total_review_count = 3,
    average_rating = 4.67
WHERE provider_id = 'SP-001';
-- For SP-002: 2 reviews, ratings: 3, 5 = total 8 points, avg 4.00
UPDATE service_providers
SET total_rating_points = 8,
    total_review_count = 2,
    average_rating = 4.00
WHERE provider_id = 'SP-002';
-- For SP-003: 3 reviews, ratings: 5, 4, 5 = total 14 points, avg 4.67
UPDATE service_providers
SET total_rating_points = 14,
    total_review_count = 3,
    average_rating = 4.67
WHERE provider_id = 'SP-003';
-- Verify the data
SELECT provider_id,
    business_name,
    average_rating,
    total_review_count
FROM service_providers
WHERE provider_id IN ('SP-001', 'SP-002', 'SP-003');
-- Check the reviews
SELECT r.review_id,
    r.reviewee_id,
    r.rating,
    r.comment,
    c.name as reviewer_name
FROM reviews r
    LEFT JOIN customers c ON r.reviewer_id = c.customer_id
WHERE r.reviewee_type = 'provider'
    AND r.reviewee_id IN ('SP-001', 'SP-002', 'SP-003')
ORDER BY r.reviewee_id,
    r.created_at DESC;