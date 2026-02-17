# Customer Public Profile - Phase 1 Migrations

## Overview

Phase 1 database schema updates for the Customer Public Profile feature, allowing service providers to view customer profiles with reviews, ratings, and activity summaries.

**Date**: February 17, 2026  
**Status**: Ready to Execute

---

## Migration Files

### Individual Migration Files

1. **add_customer_profile_fields.sql**
   - Adds `display_name` column to customers table
   - Adds `profile_visibility` ENUM column (public/restricted/private)
   - Adds index on `profile_visibility`

2. **create_customer_profile_stats_table.sql**
   - Creates `customer_profile_stats` table for caching aggregated statistics
   - Includes: avg_rating, review_count, jobs_posted_6mo, completion_rate, etc.
   - Foreign key to customers table with CASCADE delete

3. **add_review_visibility_flag.sql**
   - Adds `is_visible` BOOLEAN column to reviews table
   - Adds composite indexes for efficient queries
   - Default value: TRUE (all existing reviews remain visible)

4. **create_provider_customer_interactions_table.sql**
   - Creates `provider_customer_interactions` table for access control
   - Tracks: job_view, job_application, booking, message, job_completed
   - Unique constraint prevents duplicate interactions

### Execution Scripts

- **run_customer_profile_phase1_migrations.sql** - SQL script to run all migrations
- **run_customer_profile_phase1_migration.py** - Python script to run all migrations
- **rollback_customer_profile_phase1.sql** - Rollback script (use with caution)

---

## Pre-Migration Checklist

- [ ] Database backup completed
- [ ] Reviewed all migration SQL files
- [ ] Tested migrations in development environment
- [ ] Verified no conflicting schema changes in progress
- [ ] Confirmed maintenance window scheduled (if needed)
- [ ] Notified team of migration schedule

---

## Execution Instructions

### Option 1: Using Python Script (Recommended)

```bash
# From project root directory
python3 run_customer_profile_phase1_migration.py
```

**Advantages**:
- Automatic verification after each migration
- Detailed progress output
- Error handling and rollback on failure
- Uses existing database connection configuration

### Option 2: Using MySQL Command Line

```bash
# Connect to database
mysql -h <DB_HOST> -u <DB_USER> -p <DB_NAME>

# Run master migration script
source sql/migrations/run_customer_profile_phase1_migrations.sql;
```

### Option 3: Individual Migrations

Run each migration file separately if you need more control:

```bash
mysql -h <DB_HOST> -u <DB_USER> -p <DB_NAME> < sql/migrations/add_customer_profile_fields.sql
mysql -h <DB_HOST> -u <DB_USER> -p <DB_NAME> < sql/migrations/create_customer_profile_stats_table.sql
mysql -h <DB_HOST> -u <DB_USER> -p <DB_NAME> < sql/migrations/add_review_visibility_flag.sql
mysql -h <DB_HOST> -u <DB_USER> -p <DB_NAME> < sql/migrations/create_provider_customer_interactions_table.sql
```

---

## Post-Migration Verification

After running migrations, verify the changes:

```sql
-- Check new columns in customers table
DESCRIBE customers;

-- Check new tables exist
SHOW TABLES LIKE '%customer_profile%';
SHOW TABLES LIKE '%provider_customer_interactions%';

-- Verify table structures
DESCRIBE customer_profile_stats;
DESCRIBE provider_customer_interactions;

-- Check new column in reviews
DESCRIBE reviews;

-- Verify indexes
SHOW INDEX FROM customers WHERE Key_name = 'idx_profile_visibility';
SHOW INDEX FROM reviews WHERE Key_name LIKE 'idx_%_visible';
SHOW INDEX FROM provider_customer_interactions;
```

---

## Expected Schema Changes

### customers table
- **New columns**: `display_name`, `profile_visibility`
- **New indexes**: `idx_profile_visibility`

### reviews table
- **New columns**: `is_visible`
- **New indexes**: `idx_customer_visible`, `idx_provider_visible`

### New Tables
- **customer_profile_stats**: 10 columns, 1 foreign key, 1 index
- **provider_customer_interactions**: 7 columns, 2 foreign keys, 5 indexes

---

## Rollback Instructions

**WARNING**: Rollback will delete all data in `customer_profile_stats` and `provider_customer_interactions` tables.

```bash
# Using MySQL command line
mysql -h <DB_HOST> -u <DB_USER> -p <DB_NAME> < sql/migrations/rollback_customer_profile_phase1.sql
```

**Note**: The rollback script does NOT remove `avatar_url` column as it may be used by other features.

---

## Impact Assessment

### Performance Impact
- **Minimal**: All migrations are additive (no data modification)
- New indexes may take a few seconds to build on large tables
- No downtime required for these schema changes

### Data Impact
- **Zero data loss**: All changes are additive
- Existing data remains unchanged
- Default values applied to new columns:
  - `profile_visibility`: 'restricted'
  - `is_visible`: TRUE

### Application Impact
- **Backward compatible**: Existing queries continue to work
- New columns are nullable or have defaults
- No immediate code changes required

---

## Troubleshooting

### Issue: "Column already exists" error

**Solution**: This is expected if migrations were partially run. The script uses `IF NOT EXISTS` clauses to handle this gracefully.

### Issue: Foreign key constraint fails

**Possible causes**:
- Referenced tables (customers, service_providers) don't exist
- Database user lacks ALTER TABLE privileges

**Solution**: Verify table existence and user permissions.

### Issue: Migration script hangs

**Possible causes**:
- Large table causing slow index creation
- Lock wait timeout on busy database

**Solution**: Run during low-traffic period or increase `innodb_lock_wait_timeout`.

---

## Next Steps

After Phase 1 completion:

1. **Mark Phase 1 as complete** in implementation plan
2. **Begin Phase 2**: Lambda function development
3. **Update API documentation** with new endpoints
4. **Plan integration testing** for authorization logic

---

## Support

For issues or questions:
- Check CloudWatch logs for database errors
- Review MySQL error log: `/var/log/mysql/error.log`
- Contact: Backend Team Lead

---

## Migration History

| Date | Action | Status | Notes |
|------|--------|--------|-------|
| 2026-02-17 | Created migration files | Pending | Initial Phase 1 setup |
| | | | |

---

**Document Version**: 1.0  
**Last Updated**: February 17, 2026
