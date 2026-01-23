USE quickfix;
-- TABLE: customers
-- (Commented out assuming these are already run)
/*
 ALTER TABLE customers
 ADD CONSTRAINT uq_customers_email UNIQUE (email);
 
 -- 2) Add cognito_sub column (Option 2)
 ALTER TABLE customers
 ADD COLUMN cognito_sub VARCHAR(255) NULL;
 
 -- (optional but recommended) Make cognito_sub unique when present
 ALTER TABLE customers
 ADD CONSTRAINT uq_customers_cognito_sub UNIQUE (cognito_sub);
 */
SELECT *
FROM customers;
-- FIX: Set cognito_sub as unique and remove email unique constraint
-- 1. Remove unique constraint from email
-- Note: MySQL usually names the index after the column if not specified.
ALTER TABLE customers DROP INDEX email;
-- 2. Add cognito_sub column if it doesn't exist
-- If the column already exists, comment out the next line to avoid errors.
ALTER TABLE customers
ADD COLUMN cognito_sub VARCHAR(255) NULL;
-- 3. Make cognito_sub unique
ALTER TABLE customers
ADD CONSTRAINT uq_customers_cognito_sub UNIQUE (cognito_sub);
-- 4. Delete the extra email column (Verify name first: e.g., 'Email' or 'email_1')
-- If you have a column named 'Email' (capital E) and 'email', here is how to drop one:
-- ALTER TABLE customers DROP COLUMN Email;
-- TABLE: service_providers
-- 3) Remove duplicate emails from service_providers (Keep oldest/smallest ID)
-- (Run this if you haven't already cleaned up duplicates)
/*
 DELETE t1
 FROM service_providers t1
 INNER JOIN service_providers t2
 WHERE t1.provider_id > t2.provider_id
 AND t1.email = t2.email;
 */
-- 4) Add UNIQUE constraint to service_providers email
-- (Comment out if already exists)
/*
 ALTER TABLE service_providers
 ADD CONSTRAINT uq_service_providers_email UNIQUE (email);
 */
-- 5) Add cognito_sub to service_providers (THIS IS NEW)
-- If this fails with "Duplicate column", comment it out.
ALTER TABLE service_providers
ADD COLUMN cognito_sub VARCHAR(255) NULL;
ALTER TABLE service_providers
ADD CONSTRAINT uq_service_providers_cognito_sub UNIQUE (cognito_sub);
DESCRIBE customers;
ALTER TABLE customers DROP INDEX email;
SHOW INDEX
FROM customers;
ALTER TABLE customers DROP INDEX uq_customers_email;
SHOW INDEX
FROM customers;
TRUNCATE TABLE customers;
-- ============================================
-- Migration: Create bookings table
-- Date: 2026-01-01
-- ============================================
CREATE TABLE IF NOT EXISTS bookings (
    booking_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    customer_id BIGINT NOT NULL,
    provider_id VARCHAR(40) NOT NULL,
    -- Changed to match service_providers.provider_id type
    service_category VARCHAR(100) NOT NULL,
    service_description TEXT NOT NULL,
    scheduled_date DATE NOT NULL,
    scheduled_time TIME NOT NULL,
    status ENUM(
        'pending',
        'confirmed',
        'in_progress',
        'completed',
        'cancelled'
    ) NOT NULL DEFAULT 'pending',
    service_address VARCHAR(255) NOT NULL,
    service_city VARCHAR(100) NOT NULL,
    service_state VARCHAR(100) NOT NULL,
    service_postal_code VARCHAR(20) NOT NULL,
    estimated_price DECIMAL(10, 2) NULL,
    final_price DECIMAL(10, 2) NULL,
    notes TEXT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    completed_at TIMESTAMP NULL,
    CONSTRAINT fk_booking_customer FOREIGN KEY (customer_id) REFERENCES customers(customer_id) ON DELETE CASCADE,
    CONSTRAINT fk_booking_provider FOREIGN KEY (provider_id) REFERENCES service_providers(provider_id) ON DELETE CASCADE,
    INDEX idx_customer_id (customer_id),
    INDEX idx_provider_id (provider_id),
    INDEX idx_status (status),
    INDEX idx_scheduled_date (scheduled_date)
);
-- Verify the table
DESCRIBE bookings;
-- ============================================
-- Migration: Create jobs and job_applications tables
-- Date: 2026-01-02
-- ============================================
-- Jobs table
CREATE TABLE IF NOT EXISTS jobs (
    job_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    customer_id BIGINT NOT NULL,
    title VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,
    category VARCHAR(100) NULL,
    location_address VARCHAR(500) NOT NULL,
    location_city VARCHAR(100) NULL,
    location_state VARCHAR(50) NULL,
    location_zip VARCHAR(20) NULL,
    preferred_date DATE NULL,
    preferred_time TIME NULL,
    budget_min DECIMAL(10, 2) NULL,
    budget_max DECIMAL(10, 2) NULL,
    status ENUM(
        'open',
        'assigned',
        'in_progress',
        'completed',
        'cancelled'
    ) NOT NULL DEFAULT 'open',
    assigned_provider_id VARCHAR(40) NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_job_customer FOREIGN KEY (customer_id) REFERENCES customers(customer_id) ON DELETE CASCADE,
    INDEX idx_customer_id (customer_id),
    INDEX idx_status (status),
    INDEX idx_category (category)
);
-- Job applications table
CREATE TABLE IF NOT EXISTS job_applications (
    application_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    job_id BIGINT NOT NULL,
    provider_id VARCHAR(40) NOT NULL,
    proposed_price DECIMAL(10, 2) NULL,
    message TEXT NULL,
    status ENUM('pending', 'accepted', 'rejected') NOT NULL DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_application_job FOREIGN KEY (job_id) REFERENCES jobs(job_id) ON DELETE CASCADE,
    UNIQUE KEY unique_application (job_id, provider_id),
    INDEX idx_job_id (job_id),
    INDEX idx_provider_id (provider_id)
);
-- Verify tables
DESCRIBE jobs;
DESCRIBE job_applications;
DESCRIBE orders;
SELECT 
    TABLE_NAME,
    COLUMN_NAME,
    CONSTRAINT_NAME,
    REFERENCED_TABLE_NAME,
    REFERENCED_COLUMN_NAME
FROM
    INFORMATION_SCHEMA.KEY_COLUMN_USAGE
WHERE
    TABLE_SCHEMA = 'quickfix'
    AND TABLE_NAME = 'orders'
    AND REFERENCED_TABLE_NAME IS NOT NULL;