USE quickfix;
ALTER TABLE customers
ADD CONSTRAINT uq_customers_email UNIQUE (email);
-- 2) Add cognito_sub column (Option 2)
ALTER TABLE customers
ADD COLUMN cognito_sub VARCHAR(255) NULL;
-- (optional but recommended) Make cognito_sub unique when present
ALTER TABLE customers
ADD CONSTRAINT uq_customers_cognito_sub UNIQUE (cognito_sub);
SELECT *
FROM customers;
-- 3) Remove duplicate emails from service_providers (Keep oldest/smallest ID)
DELETE t1
FROM service_providers t1
    INNER JOIN service_providers t2
WHERE t1.provider_id > t2.provider_id
    AND t1.email = t2.email;
-- 4) Add UNIQUE constraint to service_providers email
ALTER TABLE service_providers
ADD CONSTRAINT uq_service_providers_email UNIQUE (email);