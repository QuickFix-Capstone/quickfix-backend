
import pool from '../db.js';

const createCustomers = `
CREATE TABLE IF NOT EXISTS customers (
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
`;

const createProviders = `
CREATE TABLE IF NOT EXISTS service_providers (
    provider_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    email VARCHAR(255) NOT NULL,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    phone VARCHAR(20) NULL,
    business_name VARCHAR(255) NULL,
    bio TEXT NULL,
    category VARCHAR(100) NOT NULL,
    rating DECIMAL(3, 2) DEFAULT 0.00,
    city VARCHAR(100) NULL,
    state VARCHAR(100) NULL,
    postal_code VARCHAR(20) NULL,
    is_verified BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE(email)
);
`;

const alterProviders1 = `
ALTER TABLE service_providers
ADD COLUMN stripe_account_id VARCHAR(255) NULL;
`;

const alterProviders2 = `
ALTER TABLE service_providers
ADD COLUMN stripe_onboarding_complete TINYINT(1) DEFAULT 0;
`;

const createOrders = `
CREATE TABLE IF NOT EXISTS orders (
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
`;

const runQuery = (sql, description) => {
    return new Promise((resolve, reject) => {
        pool.query(sql, (err, res) => {
            if (err) {
                // Ignore "Column already exists" (1060) or "Duplicate column name"
                if (err.code === 'ER_DUP_FIELDNAME') {
                    console.log(`✓ ${description} (already exists)`);
                    resolve();
                } else {
                    console.error(`✗ ${description}: ${err.message}`);
                    resolve(); // Continue anyway
                }
            } else {
                console.log(`✓ ${description}`);
                resolve(res);
            }
        });
    });
};

const run = async () => {
    console.log("Starting DB Fix...");
    try {
        await runQuery(createCustomers, "Create customers table");
        await runQuery(createProviders, "Create service_providers table");
        await runQuery(alterProviders1, "Add stripe_account_id column");
        await runQuery(alterProviders2, "Add stripe_onboarding_complete column");
        await runQuery(createOrders, "Create orders table");

        // Seed a provider if none exists (for testing)
        // Provider ID 2 is used in the frontend test
        // Let's create dummy provider 2
        const seedProvider = `
        INSERT IGNORE INTO service_providers (provider_id, email, first_name, last_name, category)
        VALUES (2, 'provider@example.com', 'John', 'Doe', 'Plumbing');
        `;
        await runQuery(seedProvider, "Seed dummy provider (id=2)");

        console.log("DB Fix Completed.");
    } catch (e) {
        console.error("Script error:", e);
    } finally {
        pool.end();
    }
};

run();
