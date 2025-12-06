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
FROM customers