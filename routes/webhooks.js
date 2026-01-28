import express from 'express';
import { handleLambdaRequest } from '../utils/lambda-runner.js';

const router = express.Router();

/**
 * POST /webhooks/stripe
 * Stripe webhook handler - requires raw body for signature verification
 */
router.post('/webhooks/stripe', express.raw({ type: 'application/json' }), async (req, res) => {
    await handleLambdaRequest(req, res, 'stripe_webhook');
});

/**
 * POST /webhooks/paypal
 * PayPal webhook handler
 */
router.post('/webhooks/paypal', async (req, res) => {
    await handleLambdaRequest(req, res, 'paypal_webhook');
});

export default router;
