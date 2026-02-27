-- Add assigned_at timestamp to capture provider assignment time for jobs.
ALTER TABLE jobs
ADD COLUMN assigned_at TIMESTAMP NULL COMMENT 'Timestamp when provider was assigned';

-- Backfill existing already-assigned jobs using updated_at as best approximation.
UPDATE jobs
SET assigned_at = updated_at
WHERE status IN ('assigned', 'in_progress', 'completed')
  AND assigned_at IS NULL;
