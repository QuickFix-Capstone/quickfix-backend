import express from "express";
import db from "../db.js";

const router = express.Router();

router.get("/orders/:id", (req, res) => {
    const { id } = req.params;
    db.query("SELECT * FROM orders WHERE id=?", [id], (err, rows) => {
        if (err) return res.status(500).json({ error: err.message });
        if (!rows.length) return res.status(404).json({ error: "Order not found" });
        res.json(rows[0]);
    });
});

// Mock Booking Route
router.post("/booking", (req, res) => {
    console.log("Mock Booking Request:", req.body);
    // Return a fake booking ID so frontend flow works
    res.json({
        booking_id: 12345,
        status: "confirmed",
        message: "Mock booking created successfully"
    });
});

export default router;
