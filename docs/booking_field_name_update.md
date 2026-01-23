# Field Name Update: customer_address → service_address

## Change Summary

**Date**: 2026-01-01

### What Changed

Renamed address-related fields in the `bookings` table to clarify that these represent the **service location** (where the work will be performed), not the customer's home address.

### Field Mappings

| Old Name | New Name |
|----------|----------|
| `customer_address` | `service_address` |
| `customer_city` | `service_city` |
| `customer_state` | `service_state` |
| `customer_postal_code` | `service_postal_code` |

### Why This Matters

- **Clarity**: Service location may be different from customer's profile address
- **Flexibility**: Customers can book services for rental properties, offices, etc.
- **Accuracy**: Field names now accurately describe what they store

### Files Updated

**Database Schema:**
- `sql/quickfix-mysql.sql`
- `sql/migrations/create_bookings_table.sql`
- `quickfix-mySql.session.sql`

**Lambda Functions:**
- `lambda/bookings/create_booking/handler.py`
- `lambda/bookings/get_customer_bookings/handler.py`
- `lambda/bookings/get_booking_details/handler.py`
- `lambda/bookings/update_booking/handler.py`

### API Impact

**Request fields updated:**
```json
{
  "service_address": "123 Main St",     // was: customer_address
  "service_city": "Toronto",            // was: customer_city
  "service_state": "ON",                // was: customer_state
  "service_postal_code": "M5H 1J9"      // was: customer_postal_code
}
```

**Response fields updated:**
```json
{
  "location": {
    "address": "123 Main St",           // from service_address
    "city": "Toronto",                  // from service_city
    "state": "ON",                      // from service_state
    "postal_code": "M5H 1J9"            // from service_postal_code
  }
}
```

### Migration Status

✅ All files updated  
⏳ Database migration not yet run  
⏳ Lambda functions not yet deployed

**Next steps:**
1. Run database migration with updated field names
2. Deploy updated Lambda functions
3. Update frontend to use new field names
