-- Adds audit fields for customer-side PATCH edits on job_applications.
-- Safe to run repeatedly.

USE quickfix;

ALTER TABLE job_applications
ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP;

ALTER TABLE job_applications
ADD COLUMN customer_last_edited_at TIMESTAMP NULL;
