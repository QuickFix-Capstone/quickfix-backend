import "dotenv/config";
import db from "../db.js";

async function createTestCustomer() {
    console.log("Creating test customer...");

    const customer = {
        first_name: "Test",
        last_name: "User",
        email: "test_customer_stripe@example.com"
    };

    db.query(
        "INSERT INTO customers (first_name, last_name, email) VALUES (?, ?, ?)",
        [customer.first_name, customer.last_name, customer.email],
        (err, result) => {
            if (err) {
                // If duplicate entry, just find the ID
                if (err.code === 'ER_DUP_ENTRY') {
                    console.log("Customer already exists. Fetching ID...");
                    db.query("SELECT customer_id FROM customers WHERE email = ?", [customer.email], (err2, rows) => {
                        if (err2) {
                            console.error(err2);
                            process.exit(1);
                        }
                        console.log("CUSTOMER_ID:", rows[0].customer_id);
                        process.exit(0);
                    });
                } else {
                    console.error("Error creating customer:", err);
                    process.exit(1);
                }
                return;
            }
            console.log("Created new customer.");
            console.log("CUSTOMER_ID:", result.insertId);
            process.exit(0);
        }
    );
}

createTestCustomer();
