USE quickfix;
-- Insert Customers
INSERT INTO customers (
        first_name,
        last_name,
        email,
        phone,
        address,
        city,
        state,
        postal_code
    )
VALUES (
        'John',
        'Doe',
        'john.doe@example.com',
        '555-0101',
        '123 Maple St',
        'Springfield',
        'IL',
        '62704'
    ),
    (
        'Jane',
        'Smith',
        'jane.smith@example.com',
        '555-0102',
        '456 Oak Ave',
        'Springfield',
        'IL',
        '62704'
    );
-- Insert Service Providers
INSERT INTO service_providers (
        email,
        first_name,
        last_name,
        phone,
        business_name,
        bio,
        category,
        rating,
        city,
        state,
        postal_code,
        is_verified
    )
VALUES (
        'bob.plumber@example.com',
        'Bob',
        'Builder',
        '555-0201',
        'Bob''s Plumbing',
        'Expert plumbing services for 20 years.',
        'Plumber',
        4.8,
        'Springfield',
        'IL',
        '62704',
        TRUE
    ),
    (
        'alice.electric@example.com',
        'Alice',
        'Wire',
        '555-0202',
        'Alice Electric',
        'Licensed electrician for residential and commercial.',
        'Electrician',
        4.9,
        'Springfield',
        'IL',
        '62704',
        TRUE
    );
-- Insert Service Offerings
-- Assumes provider_ids are 1 and 2 based on insertion order. 
-- In a real script, we might verify IDs, but for a fresh seed, this usually works if tables are empty or we use specific IDs.
-- However, since auto_increment is used, it's safer to not hardcode IDs if we were doing this programmatically, 
-- but for a simple manual seed script, we'll assume these are the first records or user will adjust.
INSERT INTO service_offerings (
        provider_id,
        title,
        description,
        category,
        price,
        city,
        state,
        postal_code
    )
VALUES (
        (
            SELECT provider_id
            FROM service_providers
            WHERE email = 'bob.plumber@example.com'
            LIMIT 1
        ), 'Leaky Faucet Fix', 'Fixing kitchen or bathroom faucets', 'Plumbing', 80.00, 'Springfield', 'IL', '62704'
    ), (
        (
            SELECT provider_id
            FROM service_providers
            WHERE email = 'alice.electric@example.com'
            LIMIT 1
        ), 'Outlet Installation', 'Installing new electrical outlets', 'Electrical', 120.00, 'Springfield', 'IL', '62704'
    );
-- Insert Provider Certifications
INSERT INTO provider_certifications (provider_id, cert_url, cert_type)
VALUES (
        (
            SELECT provider_id
            FROM service_providers
            WHERE email = 'bob.plumber@example.com'
            LIMIT 1
        ), 'https://example.com/certs/plumbing_license.pdf', 'Plumbing License'
    );