USE quickfix;
USE quickfix;
CREATE TABLE customers (
    customer_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    phone VARCHAR(20) NULL,
    address VARCHAR(255) NULL,
    city VARCHAR(100) NULL,
    state VARCHAR(100) NULL,
    postal_code VARCHAR(20) NULL,
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