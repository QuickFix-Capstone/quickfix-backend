-- Migration: Create Provider-Customer Interactions Table
-- Description: Track interactions between providers and customers for access control
-- Date: 2026-02-17
-- Phase: Customer Public Profile - Phase 1.4
-- Note: provider_id is VARCHAR(40) to match service_providers table (Cognito UUID)

CREATE TABLE IF NOT EXISTS provider_customer_interactions (
    interaction_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    provider_id VARCHAR(40) NOT NULL COMMENT 'Cognito provider UUID',
    customer_id BIGINT NOT NULL,
    interaction_type ENUM('job_view', 'job_application', 'booking', 'message', 'job_completed') NOT NULL,
    job_id BIGINT NULL,
    booking_id BIGINT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT fk_interaction_provider 
        FOREIGN KEY (provider_id) REFERENCES service_providers(provider_id) ON DELETE CASCADE,
    CONSTRAINT fk_interaction_customer 
        FOREIGN KEY (customer_id) REFERENCES customers(customer_id) ON DELETE CASCADE,
    
    INDEX idx_provider_customer (provider_id, customer_id),
    INDEX idx_customer (customer_id),
    INDEX idx_interaction_type (interaction_type),
    INDEX idx_created_at (created_at),
    
    UNIQUE KEY unique_interaction (provider_id, customer_id, interaction_type, job_id, booking_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Tracks provider-customer interactions for profile access control';

-- Verification query
SELECT 
    TABLE_NAME,
    TABLE_ROWS,
    CREATE_TIME,
    TABLE_COMMENT
FROM INFORMATION_SCHEMA.TABLES
WHERE TABLE_SCHEMA = DATABASE()
  AND TABLE_NAME = 'provider_customer_interactions';

-- Show table structure
DESCRIBE provider_customer_interactions;

-- Show indexes
SHOW INDEX FROM provider_customer_interactions;
