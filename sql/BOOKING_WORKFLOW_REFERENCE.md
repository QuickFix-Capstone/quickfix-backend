# Booking Workflow Quick Reference

## 📊 Table Relationships

```
┌─────────────┐
│  customers  │
└──────┬──────┘
       │
       ├─────────────────────────────────┐
       │                                 │
       ▼                                 ▼
┌─────────────┐                   ┌──────────┐
│  bookings   │◄─────────────────►│   jobs   │
└──────┬──────┘   bidirectional   └────┬─────┘
       │                                │
       │                                │
       ▼                                ▼
┌──────────────────┐          ┌─────────────────┐
│service_providers │          │job_applications │
└──────────────────┘          └─────────────────┘
```

## 🔄 Booking Confirmation Workflow

### Step 1: Customer Creates Booking
```javascript
POST /bookings
{
  "provider_id": 123,
  "service_category": "plumber",
  "service_description": "Fix kitchen sink leak",
  "scheduled_date": "2026-02-01",
  "scheduled_time": "14:00",
  "service_address": "123 Main St",
  "service_city": "Toronto",
  "service_state": "ON",
  "service_postal_code": "M5H1J9",
  "estimated_price": 150.00
}
```

**Backend Actions:**
1. Create booking record with `status = 'pending_confirmation'`
2. Generate `confirmation_token` (SHA-256 hash)
3. Set `confirmation_token_expires_at` (7 days from now)
4. Send email to provider with confirmation link
5. Return booking details to customer

**Database State:**
```sql
bookings:
  booking_id: 1
  customer_id: 456
  provider_id: 123
  status: 'pending_confirmation'
  confirmation_token: 'abc123...'
  confirmation_token_expires_at: '2026-01-30 14:00:00'
  job_id: NULL
```

---

### Step 2: Provider Receives Email

**Email Content:**
```
Subject: New Booking Request - QuickFix

Hi John,

You have a new booking request!

Service: Plumber
Date: February 1, 2026 at 2:00 PM
Location: 123 Main St, Toronto, ON M5H1J9
Customer: Jane Doe
Estimated Price: $150.00

[Confirm Booking Button]
→ https://quickfix.com/provider/confirm-booking?token=abc123...

This link expires in 7 days.
```

---

### Step 3: Provider Confirms Booking
```javascript
POST /bookings/confirm
{
  "token": "abc123..."
}
```

**Backend Actions:**
1. Validate token exists and not expired
2. Check booking status is `pending_confirmation`
3. Update booking:
   - `status = 'confirmed'`
   - `confirmed_at = NOW()`
4. **Create job record** from booking:
   ```sql
   INSERT INTO jobs (
     customer_id,
     title,
     description,
     category,
     location_address,
     location_city,
     location_state,
     location_zip,
     preferred_date,
     preferred_time,
     budget_min,
     budget_max,
     status,
     assigned_provider_id,
     booking_id
   ) VALUES (
     456,
     'Plumber Service',
     'Fix kitchen sink leak',
     'plumber',
     '123 Main St',
     'Toronto',
     'ON',
     'M5H1J9',
     '2026-02-01',
     '14:00',
     150.00,
     150.00,
     'assigned',
     123,
     1
   );
   ```
5. Update booking with `job_id`
6. Send confirmation email to customer

**Database State:**
```sql
bookings:
  booking_id: 1
  status: 'confirmed'
  confirmed_at: '2026-01-23 15:30:00'
  job_id: 789

jobs:
  job_id: 789
  customer_id: 456
  assigned_provider_id: 123
  booking_id: 1
  status: 'assigned'
```

---

### Step 4: Job Lifecycle

```
assigned → in_progress → completed
```

**Update Job Status:**
```javascript
PATCH /jobs/789
{
  "status": "in_progress"
}
```

**Complete Job:**
```javascript
PATCH /jobs/789
{
  "status": "completed",
  "final_price": 175.00
}
```

**Backend Actions:**
1. Update job status
2. Set `completed_at` timestamp
3. Update booking status to match
4. Update booking `final_price`

---

## 📋 Status Flow Diagrams

### Booking Status Flow
```
pending_confirmation → confirmed → in_progress → completed
                          ↓
                      cancelled
```

### Job Status Flow
```
assigned → in_progress → completed
   ↓
cancelled
```

---

## 🗄️ Key Database Fields

### Bookings Table
| Field | Type | Purpose |
|-------|------|---------|
| `booking_id` | BIGINT | Primary key |
| `customer_id` | BIGINT | Who booked |
| `provider_id` | BIGINT | Who provides service |
| `status` | ENUM | Current booking status |
| `confirmation_token` | VARCHAR(64) | Email confirmation token |
| `confirmation_token_expires_at` | TIMESTAMP | Token expiration |
| `confirmed_at` | TIMESTAMP | When confirmed |
| `job_id` | BIGINT | Link to created job |
| `estimated_price` | DECIMAL | Initial quote |
| `final_price` | DECIMAL | Actual charge |

### Jobs Table
| Field | Type | Purpose |
|-------|------|---------|
| `job_id` | BIGINT | Primary key |
| `customer_id` | BIGINT | Job owner |
| `assigned_provider_id` | BIGINT | Assigned provider |
| `booking_id` | BIGINT | Link to booking (if from booking) |
| `status` | ENUM | Current job status |
| `budget_min` | DECIMAL | Min budget |
| `budget_max` | DECIMAL | Max budget |
| `final_price` | DECIMAL | Actual charge |
| `completed_at` | TIMESTAMP | Completion time |

### Job Applications Table
| Field | Type | Purpose |
|-------|------|---------|
| `application_id` | BIGINT | Primary key |
| `job_id` | BIGINT | Applied to which job |
| `provider_id` | BIGINT | Who applied |
| `proposed_price` | DECIMAL | Provider's quote |
| `status` | ENUM | Application status |
| `responded_at` | TIMESTAMP | When accepted/rejected |

---

## 🔍 Common Queries

### Get Pending Confirmations for Provider
```sql
SELECT 
    b.*,
    c.first_name,
    c.last_name,
    c.email
FROM bookings b
JOIN customers c ON b.customer_id = c.customer_id
WHERE b.provider_id = ?
    AND b.status = 'pending_confirmation'
    AND b.confirmation_token_expires_at > NOW()
ORDER BY b.created_at DESC;
```

### Get Active Jobs for Provider
```sql
SELECT 
    j.*,
    c.first_name,
    c.last_name,
    b.scheduled_date,
    b.scheduled_time
FROM jobs j
JOIN customers c ON j.customer_id = c.customer_id
LEFT JOIN bookings b ON j.booking_id = b.booking_id
WHERE j.assigned_provider_id = ?
    AND j.status IN ('assigned', 'in_progress')
ORDER BY b.scheduled_date, b.scheduled_time;
```

### Get Customer's Booking History
```sql
SELECT 
    b.*,
    sp.first_name AS provider_first_name,
    sp.last_name AS provider_last_name,
    sp.business_name,
    j.job_id,
    j.status AS job_status
FROM bookings b
JOIN service_providers sp ON b.provider_id = sp.provider_id
LEFT JOIN jobs j ON b.job_id = j.job_id
WHERE b.customer_id = ?
ORDER BY b.created_at DESC;
```

### Validate Confirmation Token
```sql
SELECT 
    b.*,
    sp.email AS provider_email,
    c.email AS customer_email
FROM bookings b
JOIN service_providers sp ON b.provider_id = sp.provider_id
JOIN customers c ON b.customer_id = c.customer_id
WHERE b.confirmation_token = ?
    AND b.confirmation_token_expires_at > NOW()
    AND b.status = 'pending_confirmation';
```

---

## ⚡ API Endpoints Summary

| Endpoint | Method | Auth | Purpose |
|----------|--------|------|---------|
| `/bookings` | POST | Customer JWT | Create booking |
| `/bookings/confirm` | POST | None (token) | Confirm booking |
| `/bookings/{id}` | GET | JWT | Get booking details |
| `/customer/bookings` | GET | Customer JWT | List customer bookings |
| `/provider/bookings` | GET | Provider JWT | List provider bookings |
| `/jobs/{id}` | PATCH | JWT | Update job status |
| `/provider/jobs` | GET | Provider JWT | List provider jobs |

---

## 🎯 Key Business Rules

1. **Booking Creation**
   - Default status: `pending_confirmation`
   - Token expires in 7 days
   - Email sent immediately

2. **Booking Confirmation**
   - Only valid for `pending_confirmation` status
   - Token must not be expired
   - Creates job automatically
   - Links booking ↔ job bidirectionally

3. **Job Creation from Booking**
   - Job status: `assigned` (not `open`)
   - Provider pre-assigned
   - Budget set from estimated price
   - Location copied from booking

4. **Status Synchronization**
   - Booking status should mirror job status
   - Both track completion timestamp
   - Both track final price

---

**Last Updated:** 2026-01-23  
**Version:** 1.0
