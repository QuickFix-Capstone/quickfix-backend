import "dotenv/config";
import db from "./db.js";

async function checkUsers() {
    console.log("Checking users table...");
    db.query("SELECT * FROM users", (err, rows) => {
        if (err) {
            console.error("Error querying DB:", err);
            process.exit(1);
        }
        console.log(JSON.stringify(rows, null, 2));
        process.exit(0);
    });
}

checkUsers();
