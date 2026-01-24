# Database Schema Review Summary

## 🔍 Issues Found

### 1. **Critical Type Mismatches** ⚠️

All three tables have `provider_id` columns with **incorrect data types**:

| Table | Current Type | Should Be | Issue |
|-------|-------------|-----------|-------|
| `bookings` | `VARCHAR(40)` | `BIGINT` | Foreign key type mismatch |
| `jobs` | `VARCHAR(40)` | `BIGINT` | Foreign key type mismatch |
| `job_applications` | `VARCHAR(40)` | `BIGINT` | Foreign key type mismatch |

**Impact:** This causes foreign key constraint issues and prevents proper referential integrity with `service_providers.provider_id` (which is `BIGINT`).

---

### 2. **Missing Booking Confirmation Workflow Fields**

The `bookings` table is missing fields required for the email confirmation workflow:

- ❌ `confirmation_token` - For secure email confirmation links
- ❌ `confirmation_token_expires_at` - Token expiration (7 days)
- ❌ `confirmed_at` - Timestamp when provider confirmed
- ❌ `job_id` - Link to job created after confirmation

---

### 3. **Missing Bidirectional Relationship**

The `jobs` table doesn't have a reference back to `bookings`:

- ❌ `booking_id` - Link to booking if job was created from a booking
- ❌ `final_price` - Actual final price (bookings has it, jobs should too)
- ❌ `completed_at` - Completion timestamp

---

### 4. **Missing Timestamps in Job Applications**

The `job_applications` table lacks important tracking fields:

- ❌ `updated_at` - Track when application status changes
- ❌ `responded_at` - Track when provider's application was accepted/rejected

---

## ✅ Recommended Changes

### Bookings Table Updates

```sql
-- Fix type mismatch
ALTER TABLE bookings MODIFY COLUMN provider_id BIGINT NOT NULL;

-- Add confirmation workflow fields
ALTER TABLE bookings
ADD COLUMN confirmation_token VARCHAR(64) NULL,
ADD COLUMN confirmation_token_expires_at TIMESTAMP NULL,
ADD COLUMN confirmed_at TIMESTAMP NULL,
ADD COLUMN job_id BIGINT NULL,
ADD INDEX idx_confirmation_token (confirmation_token),
ADD CONSTRAINT fk_booking_job 
    FOREIGN KEY (job_id) REFERENCES jobs(job_id) ON DELETE SET NULL;

-- Update status enum
ALTER TABLE bookings 
MODIFY COLUMN status ENUM(
    'pending_confirmation',  -- NEW
    'pending',
    'confirmed',
    'in_progress',
    'completed',
    'cancelled'
) NOT NULL DEFAULT 'pending_confirmation';
```

### Jobs Table Updates

```sql
-- Fix type mismatch
ALTER TABLE jobs MODIFY COLUMN assigned_provider_id BIGINT NULL;

-- Add booking relationship and missing fields
ALTER TABLE jobs
ADD COLUMN booking_id BIGINT NULL,
ADD COLUMN final_price DECIMAL(10, 2) NULL,
ADD COLUMN completed_at TIMESTAMP NULL,
ADD INDEX idx_booking_id (booking_id),
ADD CONSTRAINT fk_job_booking 
    FOREIGN KEY (booking_id) REFERENCES bookings(booking_id) ON DELETE SET NULL,
ADD CONSTRAINT fk_job_assigned_provider 
    FOREIGN KEY (assigned_provider_id) 
    REFERENCES service_providers(provider_id) ON DELETE SET NULL;
```

### Job Applications Table Updates

```sql
-- Fix type mismatch
ALTER TABLE job_applications MODIFY COLUMN provider_id BIGINT NOT NULL;

-- Add foreign key and timestamps
ALTER TABLE job_applications
ADD CONSTRAINT fk_application_provider 
    FOREIGN KEY (provider_id) 
    REFERENCES service_providers(provider_id) ON DELETE CASCADE,
ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
ADD COLUMN responded_at TIMESTAMP NULL;
```

---

## 📋 New Booking Workflow

The updated schema supports this workflow:

1. **Customer creates booking** → Status: `pending_confirmation`
   - System generates `confirmation_token`
   - Sets `confirmation_token_expires_at` (7 days)
   - Sends email to provider with confirmation link

2. **Provider clicks email link** → Calls `/bookings/confirm` API
   - Validates token and expiration
   - Updates status to `confirmed`
   - Sets `confirmed_at` timestamp
   - **Creates job record** from booking
   - Links booking to job via `job_id`
   - Links job to booking via `booking_id`

3. **Job lifecycle continues** → Provider performs service
   - Job status: `assigned` → `in_progress` → `completed`
   - Booking status mirrors job status
   - `final_price` recorded in both tables

---

## 🚀 Migration Files Created

### 1. **Review Document**
📄 `QuickFix.session.sql` (in frontend directory)
- Complete schema review
- All issues documented
- Verification queries included

### 2. **Migration Script**
📄 `quickfix_backend/sql/migrations/update_booking_workflow_schema.sql`
- Safe, step-by-step migration
- Handles foreign key constraints properly
- Includes verification queries
- Ready to execute

---

## ⚡ How to Apply Migration

### Option 1: Local Database (Recommended for Testing)

```bash
# Navigate to backend directory
cd /Users/ykpfly/Desktop/capstone/quickfix_backend

# Run migration
mysql -h localhost -u root -p quickfix < sql/migrations/update_booking_workflow_schema.sql
```

### Option 2: AWS RDS Database

```bash
# Run migration on production
mysql -h quickfix-mysql.cno624c2aarh.us-east-2.rds.amazonaws.com \
  -u admin -p quickfix < sql/migrations/update_booking_workflow_schema.sql
```

---

## 🔍 Post-Migration Verification

After running the migration, verify the changes:

```sql
-- Check table structures
DESCRIBE bookings;
DESCRIBE jobs;
DESCRIBE job_applications;

-- Verify foreign keys
SELECT 
    TABLE_NAME,
    CONSTRAINT_NAME,
    REFERENCED_TABLE_NAME
FROM information_schema.KEY_COLUMN_USAGE
WHERE TABLE_SCHEMA = 'quickfix'
    AND TABLE_NAME IN ('bookings', 'jobs', 'job_applications')
    AND REFERENCED_TABLE_NAME IS NOT NULL;

-- Check data type consistency
SELECT 
    TABLE_NAME,
    COLUMN_NAME,
    COLUMN_TYPE
FROM information_schema.COLUMNS
WHERE TABLE_SCHEMA = 'quickfix'
    AND COLUMN_NAME LIKE '%provider_id%';
```

---

## 📊 Schema Relationships

```
customers (customer_id)
    ↓
bookings (customer_id, provider_id, job_id)
    ↕ (bidirectional)
jobs (job_id, customer_id, assigned_provider_id, booking_id)
    ↓
job_applications (job_id, provider_id)
    ↓
service_providers (provider_id)
```

---

## ⚠️ Important Notes

1. **Backup First**: Always backup your database before running migrations
2. **Test Locally**: Test the migration on a local/dev database first
3. **Check Dependencies**: Ensure no Lambda functions are currently writing to these tables during migration
4. **Type Conversion**: The VARCHAR(40) → BIGINT conversion requires existing data to be numeric
5. **Default Status**: New bookings will default to `pending_confirmation` status

---

## 🎯 Next Steps

1. ✅ Review the migration script
2. ⬜ Backup database
3. ⬜ Run migration on local/dev database
4. ⬜ Test booking creation with new workflow
5. ⬜ Update Lambda handlers to use new fields
6. ⬜ Deploy to production

---

## 📝 Questions?

- **Q: Will existing bookings break?**
  - A: No, existing bookings will keep their current status. Only new bookings will use `pending_confirmation`.

- **Q: What happens to existing VARCHAR provider_id values?**
  - A: If they're numeric strings, they'll convert automatically. Non-numeric values will cause an error.

- **Q: Can I rollback?**
  - A: Yes, but you'll need to drop the new columns and revert the type changes. Backup first!

---

**Created:** 2026-01-23  
**Author:** Antigravity AI  
**Version:** 1.0
