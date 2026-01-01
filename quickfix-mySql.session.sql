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