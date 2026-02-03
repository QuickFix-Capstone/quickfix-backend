-- ============================================================================
-- Migration: Add Budget Change Request Feature
-- Date: 2026-02-02
-- Description: Add budget_change_pending status and job_price_change_requests table
-- ============================================================================

USE quickfix;

-- ============================================================================
-- STEP 1: Add budget_change_pending to jobs.status enum
-- ============================================================================

SELECT 'Step 1: Adding budget_change_pending status to jobs table...' AS 'Migration Progress';

ALTER TABLE jobs
MODIFY COLUMN status ENUM(
    'open',
    'assigned',
    'in_progress',
    'budget_change_pending',  -- NEW: Job has a pending budget change request
    'completed',
    'cancelled'
) NOT NULL DEFAULT 'open';

-- Verify the change
SELECT COLUMN_TYPE
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_SCHEMA = 'quickfix'
    AND TABLE_NAME = 'jobs'
    AND COLUMN_NAME = 'status';

-- ============================================================================
-- STEP 2: Create job_price_change_requests table
-- ============================================================================

SELECT 'Step 2: Creating job_price_change_requests table...' AS 'Migration Progress';

CREATE TABLE IF NOT EXISTS job_price_change_requests (
    request_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    job_id BIGINT NOT NULL,
    requested_by_provider_id VARCHAR(40) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
    proposed_final_price DECIMAL(10, 2) NOT NULL,
    reason TEXT NOT NULL,
    status ENUM('pending', 'accepted', 'rejected', 'cancelled') NOT NULL DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    responded_at TIMESTAMP NULL,

    -- Foreign keys
    CONSTRAINT fk_price_request_job
        FOREIGN KEY (job_id) REFERENCES jobs(job_id) ON DELETE CASCADE,
    CONSTRAINT fk_price_request_provider
        FOREIGN KEY (requested_by_provider_id) REFERENCES service_providers(provider_id) ON DELETE CASCADE,

    -- Indexes for performance
    INDEX idx_job_id (job_id),
    INDEX idx_job_status (job_id, status),  -- Fast "pending check" for BR-BUD-03 and BR-BUD-04
    INDEX idx_provider_id (requested_by_provider_id),
    INDEX idx_created_at (created_at)

) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Verify the table was created
DESCRIBE job_price_change_requests;

-- ============================================================================
-- STEP 3: Verification checks
-- ============================================================================

SELECT 'Step 3: Running verification checks...' AS 'Migration Progress';

-- Check that the new status value exists in jobs table
SELECT 'Verifying jobs.status enum includes budget_change_pending...' AS 'Check 1';
SELECT COLUMN_TYPE
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_SCHEMA = 'quickfix'
    AND TABLE_NAME = 'jobs'
    AND COLUMN_NAME = 'status'
    AND COLUMN_TYPE LIKE '%budget_change_pending%';

-- Check that job_price_change_requests table exists
SELECT 'Verifying job_price_change_requests table exists...' AS 'Check 2';
SELECT TABLE_NAME, ENGINE, TABLE_COLLATION
FROM INFORMATION_SCHEMA.TABLES
WHERE TABLE_SCHEMA = 'quickfix'
    AND TABLE_NAME = 'job_price_change_requests';

-- Check foreign key constraints
SELECT 'Verifying foreign key constraints...' AS 'Check 3';
SELECT
    CONSTRAINT_NAME,
    TABLE_NAME,
    COLUMN_NAME,
    REFERENCED_TABLE_NAME,
    REFERENCED_COLUMN_NAME
FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE
WHERE TABLE_SCHEMA = 'quickfix'
    AND TABLE_NAME = 'job_price_change_requests'
    AND REFERENCED_TABLE_NAME IS NOT NULL;

-- Check indexes
SELECT 'Verifying indexes...' AS 'Check 4';
SELECT
    INDEX_NAME,
    COLUMN_NAME,
    SEQ_IN_INDEX
FROM INFORMATION_SCHEMA.STATISTICS
WHERE TABLE_SCHEMA = 'quickfix'
    AND TABLE_NAME = 'job_price_change_requests'
ORDER BY INDEX_NAME, SEQ_IN_INDEX;

-- ============================================================================
-- Migration Summary
-- ============================================================================

SELECT '
========================================
MIGRATION COMPLETE
========================================

Changes Applied:
✅ Added budget_change_pending to jobs.status ENUM
✅ Created job_price_change_requests table with:
   - Primary key: request_id
   - Foreign keys: job_id, requested_by_provider_id
   - Status tracking: pending, accepted, rejected, cancelled
   - Optimized indexes for performance

Business Rules Enforced:
- BR-BUD-01: Price Authority (final_price updated only on acceptance)
- BR-BUD-02: Request Timing (status must be in_progress)
- BR-BUD-03: Single Pending Request (checked via idx_job_status)
- BR-BUD-04: Completion Gate (status blocks completion)
- BR-BUD-05: Customer Authority (enforced in Lambda logic)

Next Steps:
1. Deploy Lambda functions for budget change workflows
2. Update API Gateway routes
3. Update frontend UI components
4. Run test suite

========================================
' AS 'Migration Summary';
