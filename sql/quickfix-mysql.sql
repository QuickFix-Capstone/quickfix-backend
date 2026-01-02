USE quickfix;
USE quickfix;
CREATE TABLE customers (
    customer_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    email VARCHAR(255) NOT NULL,
    phone VARCHAR(20) NULL,
    address VARCHAR(255) NULL,
    city VARCHAR(100) NULL,
    state VARCHAR(100) NULL,
    postal_code VARCHAR(20) NULL,
    cognito_sub VARCHAR(255) NULL UNIQUE,
    avatar_url VARCHAR(512) NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE service_providers (
    provider_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    email VARCHAR(255) NOT NULL,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    phone VARCHAR(20) NULL,
    business_name VARCHAR(255) NULL,
    bio TEXT NULL,
    category VARCHAR(100) NOT NULL,
    -- plumber, electrician, tutor, etc.
    rating DECIMAL(3, 2) DEFAULT 0.00,
    -- avg rating like 4.75
    city VARCHAR(100) NULL,
    state VARCHAR(100) NULL,
    postal_code VARCHAR(20) NULL,
    is_verified BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);
CREATE TABLE provider_certifications (
    cert_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    provider_id BIGINT NOT NULL,
    cert_url VARCHAR(512) NOT NULL,
    cert_type VARCHAR(100) NULL,
    -- e.g., “plumbing license”, “insurance”
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (provider_id) REFERENCES service_providers(provider_id)
);
ALTER TABLE provider_certifications
ADD CONSTRAINT fk_provider_certifications_provider FOREIGN KEY (provider_id) REFERENCES service_providers(provider_id) ON DELETE CASCADE;
SHOW CREATE TABLE provider_certifications;
ALTER TABLE provider_certifications DROP FOREIGN KEY provider_certifications_ibfk_1;
DELETE t1
FROM service_providers t1
    INNER JOIN service_providers t2
WHERE t1.provider_id > t2.provider_id
    AND t1.email = t2.email;
ALTER TABLE service_providers
ADD CONSTRAINT uq_service_providers_email UNIQUE (email);
ALTER TABLE customers
ADD COLUMN avatar_url VARCHAR(512) NULL COMMENT 'S3 URL for customer profile avatar';
DESCRIBE customers;
-- Bookings table
CREATE TABLE bookings (
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
describe service_providers;