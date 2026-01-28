-- Migration: Add pending_reschedule status to bookings table
-- Date: 2026-01-27
-- Description: Add new status option for customers who want to reschedule their booking
USE quickfix;
-- Add pending_reschedule to the status ENUM
ALTER TABLE bookings
MODIFY COLUMN status ENUM(
        'pending',
        'pending_confirmation',
        'confirmed',
        'pending_reschedule',
        -- NEW: Customer wants to reschedule
        'in_progress',
        'completed',
        'cancelled'
    ) NOT NULL DEFAULT 'pending';
-- Verify the change
DESCRIBE bookings;
SELECT COLUMN_TYPE
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_SCHEMA = 'quickfix'
    AND TABLE_NAME = 'bookings'
    AND COLUMN_NAME = 'status';