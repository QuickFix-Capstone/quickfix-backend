import express from 'express';
import { handleLambdaRequest } from '../utils/lambda-runner.js';

const router = express.Router();

/**
 * POST /payments/quote
 * Get payment quote with tax and fee breakdown
 */
router.post('/payments/quote', async (req, res) => {
    await handleLambdaRequest(req, res, 'payment_quote');
});

/**
 * POST /payments/stripe/create-intent
 * Create Stripe PaymentIntent
 */
router.post('/payments/stripe/create-intent', async (req, res) => {
    await handleLambdaRequest(req, res, 'stripe_create_intent');
});

/**
 * POST /payments/paypal/create-order
 * Create PayPal order
 */
router.post('/payments/paypal/create-order', async (req, res) => {
    await handleLambdaRequest(req, res, 'paypal_create_order');
});

/**
 * POST /payments/paypal/capture
 * Capture PayPal payment
 */
router.post('/payments/paypal/capture', async (req, res) => {
    await handleLambdaRequest(req, res, 'paypal_capture');
});

/**
 * GET /payments/:payment_id
 * Get payment receipt
 */
router.get('/payments/:payment_id', async (req, res) => {
    const pathParams = {
        payment_id: req.params.payment_id,
        id: req.params.payment_id
    };
    await handleLambdaRequest(req, res, 'payment_get_receipt', pathParams);
});

export default router;
