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
    provider_id VARCHAR(40) NOT NULL,
    cognito_sub VARCHAR(64) NOT NULL UNIQUE,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(150) NOT NULL,
    address_line VARCHAR(150),
    city VARCHAR(100),
    province VARCHAR(50),
    postal_code VARCHAR(20),
    bio TEXT,
    rating FLOAT DEFAULT 0.0,
    certification_url VARCHAR(512),
    verification_status VARCHAR(20) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at DATETIME NOT NULL,
    PRIMARY KEY (provider_id),
    UNIQUE KEY uq_service_provider_email (email)
);
CREATE TABLE service_offerings (
    service_offering_id VARCHAR(40) NOT NULL,
    provider_id VARCHAR(40) NOT NULL,
    title VARCHAR(150) NOT NULL,
    description TEXT NOT NULL,
    category VARCHAR(50) NOT NULL,
    price DECIMAL(10, 2) NOT NULL,
    pricing_type VARCHAR(30) NOT NULL,
    rating DECIMAL(3, 2) DEFAULT 0.00,
    main_image_url VARCHAR(512),
    is_active BOOLEAN DEFAULT TRUE,
    created_at DATETIME NOT NULL,
    PRIMARY KEY (service_offering_id),
    CONSTRAINT fk_service_offering_provider FOREIGN KEY (provider_id) REFERENCES service_providers(provider_id) ON DELETE CASCADE
);
ALTER TABLE service_providers
ADD COLUMN cognito_sub VARCHAR(64) NOT NULL UNIQUE
AFTER provider_id;
ALTER TABLE service_providers
ADD COLUMN phone_number VARCHAR(20)
AFTER email;
CREATE TABLE admins (
    admin_id VARCHAR(40) NOT NULL,
    cognito_sub VARCHAR(64) NOT NULL UNIQUE,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(150) NOT NULL UNIQUE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at DATETIME NOT NULL,
    updated_at DATETIME,
    PRIMARY KEY (admin_id)
);
INSERT INTO admins (
        admin_id,
        cognito_sub,
        name,
        email,
        is_active,
        created_at,
        updated_at
    )
VALUES (
        'admin_id:varchar',
        'cognito_sub:varchar',
        'name:varchar',
        'email:varchar',
        'is_active:tinyint',
        'created_at:datetime',
        'updated_at:datetime'
    );