# Update Booking API - Frontend Documentation

## Endpoint
```
PUT /customer/bookings/{booking_id}
```

**Base URL**: `https://kfvf20j7j9.execute-api.us-east-2.amazonaws.com`

**Full URL**: `https://kfvf20j7j9.execute-api.us-east-2.amazonaws.com/customer/bookings/{booking_id}`

**Authorization**: Bearer token (JWT) required

---

## What Can Be Updated

### 1. Cancel Booking
```json
{
  "status": "cancelled",
  "notes": "No longer needed"
}
```

### 2. Reschedule Date/Time
```json
{
  "scheduled_date": "2026-02-15",
  "scheduled_time": "14:30:00",
  "notes": "Rescheduled to next week"
}
```

### 3. Update Service Address
```json
{
  "service_address": "456 New Street",
  "service_city": "Toronto",
  "service_state": "ON",
  "service_postal_code": "M5H 2N2"
}
```

### 4. Request More Time (Delayed Decision)
```json
{
  "status": "pending_reschedule",
  "notes": "Customer needs more time to decide"
}
```

### 5. Combined Update
```json
{
  "scheduled_date": "2026-02-15",
  "scheduled_time": "14:30:00",
  "service_address": "456 New Street",
  "service_city": "Toronto",
  "notes": "Rescheduled with new address"
}
```

---

## Field Restrictions by Booking Status

| Current Status | Allowed Updates |
|----------------|----------------|
| `pending` | ✅ All fields (status, date, time, address, notes) |
| `pending_confirmation` | ⚠️ Status and notes only |
| `confirmed` | ✅ Status, date, time, notes |
| `pending_reschedule` | ✅ Status, date, time, notes |
| `in_progress` | ❌ No updates allowed |
| `completed` | ❌ No updates allowed |
| `cancelled` | ❌ No updates allowed |

---

## Status Transitions

| From Status | Can Change To |
|-------------|---------------|
| `pending` | `cancelled`, `pending_reschedule` |
| `pending_confirmation` | `cancelled` |
| `confirmed` | `cancelled`, `pending_reschedule` |
| `pending_reschedule` | `cancelled`, `confirmed` |
| Others | No transitions allowed |

---

## Request Example

```javascript
const updateBooking = async (bookingId, updates) => {
  const response = await fetch(
    `https://kfvf20j7j9.execute-api.us-east-2.amazonaws.com/customer/bookings/${bookingId}`,
    {
      method: 'PUT',
      headers: {
        'Authorization': `Bearer ${jwtToken}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(updates)
    }
  );
  
  return await response.json();
};

// Usage examples:
// Cancel booking
await updateBooking(123, { 
  status: 'cancelled', 
  notes: 'No longer needed' 
});

// Reschedule
await updateBooking(123, {
  scheduled_date: '2026-02-15',
  scheduled_time: '14:30:00',
  notes: 'Rescheduled to next week'
});

// Update address
await updateBooking(123, {
  service_address: '456 New Street',
  service_city: 'Toronto',
  service_state: 'ON',
  service_postal_code: 'M5H 2N2'
});
```

---

## Response Format

### Success (200 OK)
```json
{
  "message": "Booking updated successfully",
  "booking": {
    "booking_id": 123,
    "customer": {
      "customer_id": 14,
      "name": "John Doe",
      "email": "john@example.com",
      "phone": "1234567890"
    },
    "provider": {
      "provider_id": "SP-123",
      "name": "Provider Name",
      "business_name": "Business Name"
    },
    "service": {
      "category": "PLUMBING",
      "description": "Pipe Repair"
    },
    "schedule": {
      "date": "2026-02-15",
      "time": "14:30:00"
    },
    "status": "confirmed",
    "location": {
      "address": "456 New Street",
      "city": "Toronto",
      "state": "ON",
      "postal_code": "M5H 2N2"
    },
    "pricing": {
      "estimated_price": 150.00,
      "final_price": null
    },
    "notes": "Rescheduled to next week",
    "timestamps": {
      "created_at": "2026-01-28T10:00:00",
      "updated_at": "2026-01-28T14:00:00",
      "completed_at": null
    }
  }
}
```

### Error Responses

#### 400 Bad Request - Invalid Field for Status
```json
{
  "message": "Cannot update 'scheduled_date' when booking status is 'cancelled'"
}
```

#### 400 Bad Request - Invalid Status Transition
```json
{
  "message": "Cannot change status from 'completed' to 'cancelled'"
}
```

#### 400 Bad Request - Past Date
```json
{
  "message": "Scheduled date and time must be in the future"
}
```

#### 404 Not Found
```json
{
  "message": "Booking not found"
}
```

#### 403 Forbidden
```json
{
  "message": "You can only update your own bookings"
}
```

---

## Validation Rules

### Date/Time Validation
- ✅ Must be in the future
- ✅ Format: `YYYY-MM-DD` for date, `HH:MM:SS` for time
- ❌ Past dates/times are rejected

### Auto Status Changes
- If a `confirmed` booking is rescheduled (date/time changed), status automatically changes to `pending_reschedule`

### Read-Only Fields
These fields **cannot** be updated by customers:
- ❌ `estimated_price`
- ❌ `final_price`
- ❌ `service_category`
- ❌ `service_description`
- ❌ `provider_id`
- ❌ `customer_id`

---

## Common Use Cases

### Use Case 1: Customer Cancels Booking
```javascript
await updateBooking(bookingId, {
  status: 'cancelled',
  notes: 'Customer no longer needs service'
});
```

### Use Case 2: Customer Reschedules
```javascript
await updateBooking(bookingId, {
  scheduled_date: '2026-03-01',
  scheduled_time: '10:00:00',
  notes: 'Rescheduled due to conflict'
});
```

### Use Case 3: Customer Needs More Time
```javascript
await updateBooking(bookingId, {
  status: 'pending_reschedule',
  notes: 'Customer needs to check availability'
});
```

### Use Case 4: Customer Updates Address
```javascript
await updateBooking(bookingId, {
  service_address: '789 Oak Avenue',
  service_city: 'Mississauga',
  service_state: 'ON',
  service_postal_code: 'L5M 1A1',
  notes: 'Updated service location'
});
```

---

## Error Handling Example

```javascript
const handleUpdateBooking = async (bookingId, updates) => {
  try {
    const response = await fetch(
      `https://kfvf20j7j9.execute-api.us-east-2.amazonaws.com/customer/bookings/${bookingId}`,
      {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${jwtToken}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(updates)
      }
    );
    
    const data = await response.json();
    
    if (!response.ok) {
      // Handle error
      throw new Error(data.message || 'Failed to update booking');
    }
    
    // Success
    console.log('Booking updated:', data.booking);
    return data.booking;
    
  } catch (error) {
    console.error('Update failed:', error.message);
    throw error;
  }
};
```

---

## Notes

- All updates require valid JWT authentication
- Customer can only update their own bookings
- Updates are validated based on current booking status
- Response format matches `GET /customer/bookings/{booking_id}` structure
- All timestamps are in ISO 8601 format
