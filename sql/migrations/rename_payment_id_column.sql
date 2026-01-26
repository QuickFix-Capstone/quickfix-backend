-- Migration: Rename payment.id column to payment_id
-- This migration renames the primary key column from 'id' to 'payment_id' in the payment table

-- The safest approach is to use ALTER TABLE CHANGE to rename the column directly
-- This preserves the AUTO_INCREMENT property and primary key constraint

ALTER TABLE `payment` CHANGE COLUMN `id` `payment_id` int NOT NULL AUTO_INCREMENT;

-- Verify the change worked correctly
-- SELECT * FROM `payment` LIMIT 5;

-- Note: This migration assumes no foreign key constraints reference the payment.id column
-- If there are foreign keys referencing this column, they would need to be updated as well
-- You can check for foreign keys with:
-- SELECT * FROM information_schema.KEY_COLUMN_USAGE 
-- WHERE REFERENCED_TABLE_NAME = 'payment' AND REFERENCED_COLUMN_NAME = 'id';