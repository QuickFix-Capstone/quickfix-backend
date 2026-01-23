-- Test Data for Job Applications Feature
-- Run this to create sample applications for testing
USE quickfix;
-- Insert test applications for job_id = 1
-- Note: Make sure you have valid provider_ids in your service_providers table
-- Example: Insert applications (replace provider_ids with actual ones from your database)
INSERT INTO job_applications (
        job_id,
        provider_id,
        proposed_price,
        message,
        status
    )
VALUES (
        1,
        'your-provider-id-1',
        100.00,
        'I have 10 years of experience with plumbing. Can start immediately!',
        'pending'
    ),
    (
        1,
        'your-provider-id-2',
        120.00,
        'Licensed plumber with excellent reviews. Available this week.',
        'pending'
    ),
    (
        1,
        'your-provider-id-3',
        95.00,
        'Best price guaranteed! 5 star rated service.',
        'pending'
    ) ON DUPLICATE KEY
UPDATE proposed_price =
VALUES(proposed_price),
    message =
VALUES(message);
-- Verify the data
SELECT ja.application_id,
    ja.job_id,
    ja.provider_id,
    ja.proposed_price,
    ja.message,
    ja.status,
    ja.created_at,
    sp.name,
    sp.business_name,
    sp.rating
FROM job_applications ja
    JOIN service_providers sp ON ja.provider_id = sp.provider_id
WHERE ja.job_id = 1
ORDER BY ja.created_at DESC;