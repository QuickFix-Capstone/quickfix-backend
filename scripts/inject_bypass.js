import "dotenv/config";
import db from "../db.js";

async function injectBypass() {
    console.log("💉 Injecting bypass ID...");
    db.query(
        "UPDATE service_providers SET stripe_account_id='acct_test_bypass' WHERE stripe_account_id IS NULL OR stripe_account_id = ''",
        (err, result) => {
            if (err) {
                console.error("❌ Error:", err);
                process.exit(1);
            }
            console.log(`✅ Updated ${result.changedRows} providers with bypass ID.`);
            process.exit(0);
        }
    );
}

injectBypass();
