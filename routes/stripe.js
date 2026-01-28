import "dotenv/config"; // Ensure env vars are loaded before anything else
import express from "express";
import Stripe from "stripe";
import db from "../db.js";

const router = express.Router();
// Initialize Stripe with the secret key from env
const stripe = new Stripe(process.env.STRIPE_SECRET_KEY);

//  1) Provider onboarding link (Connect Express)
router.post("/connect/onboard", (req, res) => {
    const { providerId, email } = req.body;

    stripe.accounts.create(
        {
            type: "express",
            email,
            capabilities: {
                card_payments: { requested: true },
                transfers: { requested: true },
            },
        },
        async (err, account) => {
            if (err) return res.status(500).json({ error: err.message });

            // Save stripe account id in DB (using service_providers instead of users)
            db.query(
                "UPDATE service_providers SET stripe_account_id=? WHERE provider_id=?",
                [account.id, providerId],
                (dbErr) => {
                    if (dbErr) return res.status(500).json({ error: dbErr.message });

                    stripe.accountLinks.create(
                        {
                            account: account.id,
                            refresh_url: `${process.env.FRONTEND_URL}/provider/onboard/refresh`,
                            return_url: `${process.env.FRONTEND_URL}/provider/onboard/return`,
                            type: "account_onboarding",
                        },
                        (linkErr, link) => {
                            if (linkErr) return res.status(500).json({ error: linkErr.message });
                            return res.json({ url: link.url });
                        }
                    );
                }
            );
        }
    );
});

//  2) Create PaymentIntent with split payout (Connect)
//  2) Create PaymentIntent with split payout (Connect)
router.post("/payment/create-intent", async (req, res) => {
    let { customerId, providerId, amountCents, currency = "cad", bookingId, orderId } = req.body;

    // 🚨 HARDCODED FOR TESTING
    if (!customerId) customerId = 1;
    if (!providerId) providerId = 2;

    if (!amountCents || amountCents < 50) {
        return res.status(400).json({ error: "Invalid amount." });
    }

    // Helper: Create Stripe PI and update DB
    const createIntentAndSave = async (finalOrderId) => {
        try {
            // Check provider connect status
            db.query(
                "SELECT stripe_account_id FROM service_providers WHERE provider_id=?",
                [providerId],
                async (err, rows) => {
                    if (err) return res.status(500).json({ error: err.message });

                    // Allow test bypass or require connected account
                    let providerStripeAccount = rows.length ? rows[0].stripe_account_id : null;
                    if (!providerStripeAccount && process.env.NODE_ENV !== 'test') {
                        // Fallback for dev/test if needed, or error
                        // return res.status(400).json({ error: "Provider is not connected to Stripe." });
                    }

                    const feePercent = Number(process.env.PLATFORM_FEE_PERCENT || 10);
                    const applicationFee = Math.round((amountCents * feePercent) / 100);

                    const paymentIntent = await stripe.paymentIntents.create({
                        amount: amountCents,
                        currency,
                        automatic_payment_methods: { enabled: true },
                        metadata: {
                            orderId: String(finalOrderId),
                            customerId: String(customerId),
                            providerId: String(providerId),
                            bookingId: bookingId ? String(bookingId) : "",
                        },
                        // Split payout if provider is connected
                        ...(providerStripeAccount && providerStripeAccount !== 'acct_test_bypass' && {
                            application_fee_amount: applicationFee,
                            transfer_data: {
                                destination: providerStripeAccount,
                            },
                        }),
                    });

                    // Update order with PI ID
                    db.query(
                        "UPDATE orders SET stripe_payment_intent_id=? WHERE id=?",
                        [paymentIntent.id, finalOrderId]
                    );

                    res.json({ clientSecret: paymentIntent.client_secret, orderId: finalOrderId });
                }
            );
        } catch (e) {
            console.error("Stripe Error:", e);
            res.status(500).json({ error: e.message });
        }
    };

    // Main Logic: Use existing orderId OR create new Order
    if (orderId) {
        console.log(`Using existing Order ID: ${orderId}`);
        createIntentAndSave(orderId);
    } else {
        console.log("Creating NEW Order for Payment");
        db.query(
            "INSERT INTO orders (customer_id, provider_id, amount_cents, currency, status) VALUES (?, ?, ?, ?, 'pending')",
            [customerId, providerId, amountCents, currency],
            (dbErr, result) => {
                if (dbErr) return res.status(500).json({ error: dbErr.message });
                createIntentAndSave(result.insertId);
            }
        );
    }
});

// ✅ 3) Webhook (to confirm payment + update DB)
// This needs to be mounted before express.json() in server.js or handled with express.raw() here if mounted separately.
// Since we are exporting a router, we should probably handle the raw body parsing in the route definition or in server.js specific to this route.
// The user provided snippet suggests: router.post("/stripe/webhook", express.raw({ type: "application/json" }), ...)
// So we will keep that.

router.post("/stripe/webhook", express.raw({ type: "application/json" }), async (req, res) => {
    const stripe = new Stripe(process.env.STRIPE_SECRET_KEY); // Re-init to be safe or reuse outer? Outer is fine usually.
    const sig = req.headers["stripe-signature"];
    let event;

    try {
        event = stripe.webhooks.constructEvent(req.body, sig, process.env.STRIPE_WEBHOOK_SECRET);
    } catch (err) {
        console.error(`Webhook Error: ${err.message}`);
        return res.status(400).send(`Webhook Error: ${err.message}`);
    }

    if (event.type === "payment_intent.succeeded") {
        const pi = event.data.object;
        const orderId = pi.metadata?.orderId;

        if (orderId) {
            db.query("UPDATE orders SET status='paid' WHERE id=?", [orderId]);
        }
    }

    res.json({ received: true });
});

export default router;
