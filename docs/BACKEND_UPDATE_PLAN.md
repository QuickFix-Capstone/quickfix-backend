# Backend Implementation Plan: Allow Updates for pending_confirmation Status

## Current Restriction
**File**: `lambda/bookings/update_booking/handler.py`

Currently, `pending_confirmation` status only allows:
- ✅ `status` changes
- ✅ `notes` updates
- ❌ `scheduled_date` / `scheduled_time` (blocked)
- ❌ `service_address` / location fields (blocked)

## Required Changes

### 1. Update Field Restrictions (Line ~100-120)

**Current Code**:
```python
ALLOWED_FIELDS_BY_STATUS = {
    "pending": ["status", "scheduled_date", "scheduled_time", "service_address", 
                "service_city", "service_state", "service_postal_code", "notes"],
    "pending_confirmation": ["status", "notes"],  # ❌ Too restrictive
    "confirmed": ["status", "scheduled_date", "scheduled_time", "notes"],
    "pending_reschedule": ["status", "scheduled_date", "scheduled_time", "notes"],
}
```

**Updated Code**:
```python
ALLOWED_FIELDS_BY_STATUS = {
    "pending": ["status", "scheduled_date", "scheduled_time", "service_address", 
                "service_city", "service_state", "service_postal_code", "notes"],
    "pending_confirmation": ["status", "scheduled_date", "scheduled_time", 
                            "service_address", "service_city", "service_state", 
                            "service_postal_code", "notes"],  # ✅ Allow all updates
    "confirmed": ["status", "scheduled_date", "scheduled_time", "notes"],
    "pending_reschedule": ["status", "scheduled_date", "scheduled_time", "notes"],
}
```

### 2. Update Status Transition Rules (Optional)

If you want `pending_confirmation` to auto-change to `pending_reschedule` when rescheduled:

**Find** (around line 180-200):
```python
# Auto status changes
if current_status == "confirmed" and ("scheduled_date" in updates or "scheduled_time" in updates):
    updates["status"] = "pending_reschedule"
```

**Add**:
```python
# Auto status changes
if current_status == "confirmed" and ("scheduled_date" in updates or "scheduled_time" in updates):
    updates["status"] = "pending_reschedule"

# Also apply to pending_confirmation
if current_status == "pending_confirmation" and ("scheduled_date" in updates or "scheduled_time" in updates):
    updates["status"] = "pending_reschedule"
```

## Deployment Steps

1. **Edit the Lambda handler**:
   ```bash
   vim lambda/bookings/update_booking/handler.py
   ```

2. **Deploy the updated Lambda**:
   ```bash
   ./deploy/deploy_update_booking.sh
   ```

3. **Test the changes**:
   ```bash
   # Test reschedule for pending_confirmation
   curl -X PUT \
     https://kfvf20j7j9.execute-api.us-east-2.amazonaws.com/customer/bookings/80 \
     -H "Authorization: Bearer $TOKEN" \
     -H "Content-Type: application/json" \
     -d '{
       "scheduled_date": "2026-02-01",
       "scheduled_time": "10:00:00",
       "notes": "Rescheduled before confirmation"
     }'
   ```

## Frontend Changes (After Backend Update)

Update `BookingDetails.jsx` to show buttons for `pending_confirmation`:

```javascript
// Reschedule - Available for pending, pending_confirmation, confirmed, pending_reschedule
{["pending", "pending_confirmation", "confirmed", "pending_reschedule"].includes(booking.status) && (
    <Button onClick={() => setShowRescheduleModal(true)}>
        Reschedule Booking
    </Button>
)}

// Update Address - For pending and pending_confirmation
{["pending", "pending_confirmation"].includes(booking.status) && (
    <Button onClick={() => setShowAddressModal(true)}>
        Update Address
    </Button>
)}
```

## Estimated Time
- Backend edit: **2 minutes**
- Deploy: **1 minute**
- Test: **2 minutes**
- Frontend update: **1 minute**

**Total: ~6 minutes**
