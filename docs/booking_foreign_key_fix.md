# Foreign Key Type Mismatch - FIXED

## The Problem

The `bookings` table creation was failing with this error:
```
Referencing column 'provider_id' and referenced column 'provider_id' in foreign key constraint 'fk_booking_provider' are incompatible.
```

## Root Cause

**Type mismatch between tables:**
- `service_providers.provider_id` = `VARCHAR(40)` (actual database)
- `bookings.provider_id` = `BIGINT` (in our schema files)

Foreign keys require **exact type matching** between the referencing and referenced columns.

## The Fix

Changed `bookings.provider_id` from `BIGINT` to `VARCHAR(40)`:

```sql
-- Before (incorrect)
CREATE TABLE bookings (
    ...
    provider_id BIGINT NOT NULL,
    ...
);

-- After (correct)
CREATE TABLE bookings (
    ...
    provider_id VARCHAR(40) NOT NULL,  -- Matches service_providers.provider_id
    ...
);
```

## Files Updated

✅ `sql/quickfix-mysql.sql`  
✅ `sql/migrations/create_bookings_table.sql`  
✅ `quickfix-mySql.session.sql`

## Next Steps

The CREATE TABLE statement should now work correctly. Try running it again from your SQL session file.

## Note

Your `service_providers` table uses `VARCHAR(40)` for `provider_id` instead of `BIGINT AUTO_INCREMENT`. This suggests you might be using UUIDs or custom IDs for providers instead of auto-incrementing integers.
