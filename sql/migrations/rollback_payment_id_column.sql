-- Rollback Migration: Rename payment_id column back to id
-- This rollback script reverts the payment_id column name back to 'id'

-- Rename payment_id back to id
ALTER TABLE `payment` CHANGE COLUMN `payment_id` `id` int NOT NULL AUTO_INCREMENT;

-- Verify the rollback worked correctly
-- SELECT * FROM `payment` LIMIT 5;