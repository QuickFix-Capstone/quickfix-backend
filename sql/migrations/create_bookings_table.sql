-- Migration: Create bookings table
-- Date: 2026-01-01
-- Description: Creates the bookings table to manage customer service bookings
USE quickfix;
-- Create bookings table
CREATE TABLE bookings (
    booking_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    customer_id BIGINT NOT NULL,
    provider_id VARCHAR(40) NOT NULL,
    -- Must match service_providers.provider_id type
    -- Service details
    service_category VARCHAR(100) NOT NULL,
    service_description TEXT NOT NULL,
    -- Scheduling
    scheduled_date DATE NOT NULL,
    scheduled_time TIME NOT NULL,
    -- Status tracking
    status ENUM(
        'pending',
        'confirmed',
        'in_progress',
        'completed',
        'cancelled'
    ) NOT NULL DEFAULT 'pending',
    -- Service location (where the service will be performed)
    service_address VARCHAR(255) NOT NULL,
    service_city VARCHAR(100) NOT NULL,
    service_state VARCHAR(100) NOT NULL,
    service_postal_code VARCHAR(20) NOT NULL,
    -- Pricing
    estimated_price DECIMAL(10, 2) NULL,
    final_price DECIMAL(10, 2) NULL,
    -- Additional information
    notes TEXT NULL,
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    completed_at TIMESTAMP NULL,
    -- Foreign key constraints
    CONSTRAINT fk_booking_customer FOREIGN KEY (customer_id) REFERENCES customers(customer_id) ON DELETE CASCADE,
    CONSTRAINT fk_booking_provider FOREIGN KEY (provider_id) REFERENCES service_providers(provider_id) ON DELETE CASCADE,
    -- Indexes for performance
    INDEX idx_customer_id (customer_id),
    INDEX idx_provider_id (provider_id),
    INDEX idx_status (status),
    INDEX idx_scheduled_date (scheduled_date),
    INDEX idx_created_at (created_at)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci;
-- Verify the table was created
DESCRIBE bookings;
-- Show indexes
SHOW INDEX
FROM bookings;