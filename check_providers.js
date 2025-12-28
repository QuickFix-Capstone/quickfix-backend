import "dotenv/config";
import db from "./db.js";

async function checkProviders() {
    db.query("SELECT provider_id FROM service_providers LIMIT 1", (err, rows) => {
        if (err) {
            console.error(err);
            process.exit(1);
        }
        if (rows.length > 0) {
            console.log("PROVIDER_ID:", rows[0].provider_id);
        } else {
            console.log("No providers found");
        }
        process.exit(0);
    });
}

checkProviders();
