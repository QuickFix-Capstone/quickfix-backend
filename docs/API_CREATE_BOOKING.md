# Create Booking API Documentation

## Endpoint
**POST** `/bookings`

## Overview
Creates a new booking for a customer with a service provider. The booking will be created with a `pending_confirmation` status and an email will be sent to the provider for confirmation.

## Authentication
**Required**: Yes

- Requires JWT token from AWS Cognito
- Token must be passed in the `Authorization` header
- The customer's identity is extracted from the JWT `sub` claim

**Header:**
```
Authorization: Bearer <JWT_TOKEN>
```

---

## Request Body

### Content-Type
`application/json`

### Required Fields

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `provider_id` | string/number | ID of the service provider | `"SP-001"` or `123` |
| `service_category` | string | Category of service requested | `"plumber"`, `"electrician"`, `"cleaner"` |
| `service_description` | string | Detailed description of the service needed | `"Fix leaking kitchen sink"` |
| `scheduled_date` | string | Date for the service (YYYY-MM-DD format) | `"2026-01-15"` |
| `scheduled_time` | string | Time for the service (HH:MM format, 24-hour) | `"14:00"` |
| `service_address` | string | Street address where service is needed | `"123 Main St"` |
| `service_city` | string | City name | `"Toronto"` |
| `service_state` | string | State/Province code | `"ON"` |
| `service_postal_code` | string | Postal/ZIP code | `"M5H 1J9"` |

### Optional Fields

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `estimated_price` | number | Estimated price for the service (decimal) | `150.00` |
| `notes` | string | Additional notes or special instructions | `"Please call before arriving"` |

### Validation Rules

- `scheduled_date` must be in the future (not today or past dates)
- `scheduled_date` format: `YYYY-MM-DD`
- `scheduled_time` format: `HH:MM` (24-hour format)
- `provider_id` must reference an existing, active service provider
- `estimated_price` must be a positive decimal number if provided

---

## Request Example

```json
{
  "provider_id": "SP-001",
  "service_category": "plumber",
  "service_description": "Fix leaking kitchen sink and replace faucet",
  "scheduled_date": "2026-02-15",
  "scheduled_time": "14:00",
  "service_address": "123 Main St, Apt 4B",
  "service_city": "Toronto",
  "service_state": "ON",
  "service_postal_code": "M5H 1J9",
  "estimated_price": 150.00,
  "notes": "Please call 15 minutes before arriving. Parking available in visitor lot."
}
```

### Minimal Request (Required Fields Only)

```json
{
  "provider_id": "SP-001",
  "service_category": "electrician",
  "service_description": "Install ceiling fan in bedroom",
  "scheduled_date": "2026-02-20",
  "scheduled_time": "10:00",
  "service_address": "456 Oak Avenue",
  "service_city": "Vancouver",
  "service_state": "BC",
  "service_postal_code": "V6B 2M9"
}
```

---

## Success Response

### Status Code: `201 Created`

### Response Body

```json
{
  "message": "Booking created successfully",
  "booking": {
    "booking_id": 1234,
    "customer_id": 567,
    "provider_id": "SP-001",
    "provider_name": "John's Plumbing Services",
    "service_category": "plumber",
    "service_description": "Fix leaking kitchen sink and replace faucet",
    "scheduled_date": "2026-02-15",
    "scheduled_time": "14:00:00",
    "status": "pending_confirmation",
    "service_address": "123 Main St, Apt 4B",
    "service_city": "Toronto",
    "service_state": "ON",
    "service_postal_code": "M5H 1J9",
    "estimated_price": 150.00,
    "final_price": null,
    "notes": "Please call 15 minutes before arriving. Parking available in visitor lot.",
    "created_at": "2026-01-26T15:30:00.000Z",
    "updated_at": "2026-01-26T15:30:00.000Z"
  }
}
```

### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `booking_id` | number | Unique booking identifier |
| `customer_id` | number | ID of the customer who made the booking |
| `provider_id` | string/number | ID of the service provider |
| `provider_name` | string | Name of the service provider |
| `service_category` | string | Category of service |
| `service_description` | string | Description of the service |
| `scheduled_date` | string | Scheduled date (YYYY-MM-DD) |
| `scheduled_time` | string | Scheduled time (HH:MM:SS) |
| `status` | string | Booking status (always `"pending_confirmation"` on creation) |
| `service_address` | string | Service location address |
| `service_city` | string | Service location city |
| `service_state` | string | Service location state/province |
| `service_postal_code` | string | Service location postal code |
| `estimated_price` | number/null | Estimated price if provided |
| `final_price` | number/null | Final price (null until job is completed) |
| `notes` | string/null | Additional notes |
| `created_at` | string | Timestamp when booking was created (ISO 8601) |
| `updated_at` | string | Timestamp when booking was last updated (ISO 8601) |

---

## Error Responses

### 400 Bad Request

#### Missing Required Fields
```json
{
  "message": "Missing required fields",
  "missing": ["scheduled_date", "scheduled_time"]
}
```

#### Invalid Date Format
```json
{
  "message": "Invalid date format. Use YYYY-MM-DD"
}
```

#### Invalid Time Format
```json
{
  "message": "Invalid time format. Use HH:MM"
}
```

#### Date in Past
```json
{
  "message": "Scheduled date must be in the future"
}
```

#### Invalid JSON Body
```json
{
  "message": "Invalid JSON body"
}
```

#### Provider Not Active
```json
{
  "message": "Service provider is not active"
}
```

#### Data Constraint Violation
```json
{
  "message": "Failed to create booking due to data constraint"
}
```

---

### 401 Unauthorized

#### Missing Authorization
```json
{
  "message": "Unauthorized: Missing identity"
}
```

#### Missing Cognito Sub
```json
{
  "message": "Unauthorized: Missing cognito_sub"
}
```

---

### 404 Not Found

#### Customer Profile Not Found
```json
{
  "message": "Customer profile not found"
}
```
*This occurs when the authenticated user doesn't have a customer profile in the database.*

#### Service Provider Not Found
```json
{
  "message": "Service provider not found"
}
```

---

### 500 Internal Server Error

#### Database Connection Failed
```json
{
  "message": "Database connection failed"
}
```

#### General Server Error
```json
{
  "message": "Internal server error"
}
```

---

## Booking Status Flow

1. **pending_confirmation** - Initial status when booking is created. Provider receives email.
2. **confirmed** - Provider accepts the booking.
3. **in_progress** - Service is currently being performed.
4. **completed** - Service has been completed.
5. **cancelled** - Booking was cancelled.

---

## Email Notifications

Upon successful booking creation:
- A confirmation email is sent to the service provider
- Email includes booking details and a confirmation link
- Confirmation token expires in 7 days
- Email processing is asynchronous (non-blocking)
- Booking creation succeeds even if email fails to send

---

## Implementation Notes for Frontend

### Setting Estimated Price

The `estimated_price` field is **optional** but recommended when:
- The customer has discussed pricing with the provider beforehand
- You want to display an estimated cost to the user
- The service has a standard rate

**Frontend Implementation Example:**

```javascript
// Example React function
const createBooking = async (bookingData) => {
  const token = await getAuthToken(); // Get JWT from Cognito

  const requestBody = {
    provider_id: bookingData.providerId,
    service_category: bookingData.category,
    service_description: bookingData.description,
    scheduled_date: bookingData.date, // Format: "2026-02-15"
    scheduled_time: bookingData.time, // Format: "14:00"
    service_address: bookingData.address,
    service_city: bookingData.city,
    service_state: bookingData.state,
    service_postal_code: bookingData.postalCode,
    estimated_price: bookingData.estimatedPrice, // Optional: e.g., 150.00
    notes: bookingData.notes // Optional
  };

  const response = await fetch('https://api.yourapp.com/bookings', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    },
    body: JSON.stringify(requestBody)
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.message);
  }

  return await response.json();
};
```

### UI Recommendations

1. **Estimated Price Input:**
   - Display as optional field with label: "Estimated Price (Optional)"
   - Use currency input component with proper formatting
   - Show currency symbol (e.g., $, CAD)
   - Validate that value is positive if provided

2. **Date/Time Selection:**
   - Use date picker that disables past dates
   - Use time picker with 15 or 30-minute intervals
   - Show timezone to user
   - Consider provider availability if available

3. **Address Fields:**
   - Consider using address autocomplete (Google Places API)
   - Pre-fill from customer profile if available
   - Validate postal code format

4. **Error Handling:**
   - Display validation errors inline with form fields
   - Show user-friendly messages for server errors
   - Handle 404 errors gracefully (redirect to provider search if provider not found)

---

## Testing

### cURL Example

```bash
curl -X POST https://api.yourapp.com/bookings \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -d '{
    "provider_id": "SP-001",
    "service_category": "plumber",
    "service_description": "Fix leaking kitchen sink",
    "scheduled_date": "2026-02-15",
    "scheduled_time": "14:00",
    "service_address": "123 Main St",
    "service_city": "Toronto",
    "service_state": "ON",
    "service_postal_code": "M5H 1J9",
    "estimated_price": 150.00,
    "notes": "Please call before arriving"
  }'
```

---

## Support

For questions or issues, please contact the backend team or refer to:
- [Booking System Quickstart](booking_system_quickstart.md)
- [Booking Confirmation Workflow](BOOKING_CONFIRMATION_WORKFLOW_PLAN.md)
