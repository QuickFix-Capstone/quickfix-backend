import "dotenv/config";
import db from "./db.js";

async function checkCustomers() {
    console.log("Checking customers table...");
    db.query("SELECT * FROM customers", (err, rows) => {
        if (err) {
            // It's possible the table doesn't exist and users is the source of truth, but the constraint says otherwise.
            // Let's log the error.
            console.error("Error querying customers table:", err);
            // If table doesn't exist, maybe we need to check schema.
            process.exit(1);
        }
        console.log(JSON.stringify(rows, null, 2));
        process.exit(0);
    });
}

checkCustomers();
