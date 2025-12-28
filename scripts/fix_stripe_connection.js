import "dotenv/config";
import Stripe from "stripe";
import db from "../db.js";
import fs from "fs";

const stripe = new Stripe(process.env.STRIPE_SECRET_KEY);

async function fixStripeConnection() {
    console.log("🔍 Finding provider without Stripe Account...");

    // 1. Find a provider who is missing stripe_account_id
    db.query("SELECT * FROM service_providers WHERE stripe_account_id IS NULL OR stripe_account_id = '' LIMIT 1", async (err, rows) => {
        if (err) {
            console.error("❌ DB API Error:", err);
            process.exit(1);
        }

        if (rows.length === 0) {
            console.log("✅ All providers already have Stripe accounts linked! Nothing to do.");
            checkProviders();
            return;
        }

        const provider = rows[0];
        console.log(`🚀 Found Provider ID: ${provider.provider_id} (${provider.email || "No Email"}). Creating Stripe Account...`);

        try {
            // 2. Create a Stripe 'express' account (Test Mode)
            const account = await stripe.accounts.create({
                type: "express",
                email: provider.email || `provider_${provider.provider_id}@example.com`,
                capabilities: {
                    card_payments: { requested: true },
                    transfers: { requested: true },
                },
            });

            console.log(`✨ Created Stripe Account: ${account.id}`);

            // 3. Update DB
            db.query(
                "UPDATE service_providers SET stripe_account_id=?, stripe_onboarding_complete=1 WHERE provider_id=?",
                [account.id, provider.provider_id],
                (updateErr) => {
                    if (updateErr) {
                        console.error("❌ Error updating DB:", updateErr);
                        process.exit(1);
                    }
                    console.log(`🎉 Successfully linked Provider ${provider.provider_id} to Account ${account.id}`);
                    process.exit(0);
                }
            );

        } catch (stripeErr) {
            console.error("❌ Stripe API Error:", stripeErr.message);
            fs.writeFileSync('error.txt', stripeErr.message);
            process.exit(1);
        }
    });
}

function checkProviders() {
    db.query("SELECT provider_id, stripe_account_id FROM service_providers", (err, rows) => {
        if (!err) console.table(rows);
        process.exit(0);
    });
}

fixStripeConnection();
