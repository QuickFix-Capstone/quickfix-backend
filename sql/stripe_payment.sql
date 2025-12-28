USE quickfix;

-- Add Stripe related columns to service_providers (mapped from users)
ALTER TABLE service_providers
  ADD COLUMN stripe_account_id VARCHAR(255) NULL,
  ADD COLUMN stripe_onboarding_complete TINYINT(1) DEFAULT 0;

-- Create orders table
CREATE TABLE orders (
  id INT AUTO_INCREMENT PRIMARY KEY,
  customer_id BIGINT NOT NULL,
  provider_id BIGINT NOT NULL,
  amount_cents INT NOT NULL,
  currency VARCHAR(10) DEFAULT 'cad',
  status VARCHAR(50) DEFAULT 'pending',
  stripe_payment_intent_id VARCHAR(255),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (customer_id) REFERENCES customers(customer_id),
  FOREIGN KEY (provider_id) REFERENCES service_providers(provider_id)
);
