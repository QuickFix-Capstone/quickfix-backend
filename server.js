import "dotenv/config";
import express from "express";
import cors from "cors";
import stripeRoutes from "./routes/stripe.js";

import ordersRoutes from "./routes/orders.js";
import paymentsRoutes from "./routes/payments.js";
import webhooksRoutes from "./routes/webhooks.js";

const app = express();
const PORT = process.env.PORT || 3000;

app.use(cors({
    origin: process.env.FRONTEND_URL || "http://localhost:5173",
    credentials: true
}));

// Function to selectively apply JSON middleware
const jsonMiddleware = express.json();

app.use((req, res, next) => {
    if (req.originalUrl.includes('/stripe/webhook')) {
        // Webhook needs raw body, handled in the route or skipped here
        next();
    } else {
        jsonMiddleware(req, res, next);
    }
});

app.use("/", stripeRoutes);
app.use("/", ordersRoutes);
app.use("/", paymentsRoutes);
app.use("/", webhooksRoutes);

app.listen(PORT, () => {
    console.log(`Server running on port ${PORT}`);
});
