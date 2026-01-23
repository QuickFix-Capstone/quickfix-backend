# Booking Confirmation Workflow Implementation Plan

## Overview

Implement a two-step booking workflow where customers can book service providers, which triggers an email notification to the provider. The provider must confirm the booking via email link before it becomes an active job in the system.

**Current State:**
- `bookings` table exists with status field (pending, confirmed, in_progress, completed, cancelled)
- `jobs` table exists separately for job postings
- No email notification system currently implemented

**Proposed Flow:**
1. Customer creates booking → Status: `pending_confirmation`
2. System sends confirmation email to provider with unique token
3. Provider clicks confirmation link → Booking status changes to `confirmed`
4. System automatically creates a job record from the confirmed booking
5. Job appears in provider's job list

---

## User Review Required

> [!IMPORTANT]
> **Email Service Configuration**
> This implementation uses AWS SES (Simple Email Service) for sending emails. You'll need to:
> - Verify sender email address in AWS SES
> - Move SES out of sandbox mode (or verify recipient emails for testing)
> - Add SES permissions to Lambda IAM roles

> [!IMPORTANT]
> **Booking Status Change**
> The `bookings` table status enum will be updated to include `pending_confirmation` status. This is a schema change that requires a database migration.

> [!WARNING]
> **Confirmation Token Expiration**
> Confirmation tokens will expire after 7 days. Expired bookings will need manual cleanup or automatic cancellation.

---

## Proposed Changes

### Database Schema

#### [MODIFY] bookings table
**Migration SQL:**
```sql
-- Add new status to bookings table
ALTER TABLE bookings 
MODIFY COLUMN status ENUM(
    'pending_confirmation',  -- NEW: waiting for provider confirmation
    'pending',
    'confirmed', 
    'in_progress',
    'completed',
    'cancelled'
) NOT NULL DEFAULT 'pending_confirmation';

-- Add confirmation tracking fields
ALTER TABLE bookings
ADD COLUMN confirmation_token VARCHAR(64) NULL,
ADD COLUMN confirmation_token_expires_at TIMESTAMP NULL,
ADD COLUMN confirmed_at TIMESTAMP NULL,
ADD COLUMN job_id BIGINT NULL,
ADD INDEX idx_confirmation_token (confirmation_token),
ADD CONSTRAINT fk_booking_job FOREIGN KEY (job_id) REFERENCES jobs(job_id) ON DELETE SET NULL;
```

---

### Backend Components

#### [NEW] [email_service.py](file:///Users/ykpfly/Desktop/capstone/quickfix_backend/src/email/email_service.py)

**Purpose:** Centralized email service using AWS SES

**Key Functions:**
- `send_booking_confirmation_email(provider_email, provider_name, booking_details, confirmation_token)`
- `send_booking_confirmed_notification(customer_email, customer_name, booking_details)`

**Dependencies:**
- `boto3` for AWS SES
- Email templates with HTML formatting

**Configuration:**
- Sender email from environment variable `SES_SENDER_EMAIL`
- Confirmation URL base from `BOOKING_CONFIRMATION_URL`

---

#### [MODIFY] [create_booking/handler.py](file:///Users/ykpfly/Desktop/capstone/quickfix_backend/lambda/bookings/create_booking/handler.py)

**Changes:**
1. Generate unique confirmation token (UUID + timestamp hash)
2. Set `status = 'pending_confirmation'`
3. Store token and expiration (7 days) in database
4. Retrieve provider email from `service_providers` table
5. Send confirmation email via SES
6. Return booking with `pending_confirmation` status

**New Logic:**
```python
# Generate confirmation token
confirmation_token = hashlib.sha256(
    f"{booking_id}:{provider_id}:{datetime.utcnow().isoformat()}".encode()
).hexdigest()

# Set expiration (7 days)
expires_at = datetime.utcnow() + timedelta(days=7)

# Send email
send_booking_confirmation_email(
    provider_email=provider_row['email'],
    provider_name=provider_row['name'],
    booking_details={...},
    confirmation_token=confirmation_token
)
```

---

#### [NEW] [confirm_booking/handler.py](file:///Users/ykpfly/Desktop/capstone/quickfix_backend/lambda/bookings/confirm_booking/handler.py)

**Endpoint:** `POST /bookings/confirm`

**Request Body:**
```json
{
  "token": "abc123..."
}
```

**Logic:**
1. Validate token exists and not expired
2. Check booking status is `pending_confirmation`
3. Update booking status to `confirmed`
4. Set `confirmed_at` timestamp
5. Create corresponding job record
6. Link job to booking via `job_id` field
7. Send confirmation notification to customer
8. Return success response with job details

**Response:**
```json
{
  "message": "Booking confirmed successfully",
  "booking_id": 123,
  "job_id": 456,
  "status": "confirmed"
}
```

**Error Cases:**
- 404: Token not found
- 400: Token expired
- 400: Booking already confirmed
- 500: Database error

---

#### [NEW] [convert_booking_to_job.py](file:///Users/ykpfly/Desktop/capstone/quickfix_backend/src/utils/convert_booking_to_job.py)

**Purpose:** Utility function to convert confirmed booking to job

**Function Signature:**
```python
def convert_booking_to_job(booking_id: int, conn) -> int:
    """
    Converts a confirmed booking into a job record.
    
    Args:
        booking_id: ID of the booking to convert
        conn: Database connection
        
    Returns:
        job_id: ID of created job
        
    Raises:
        ValueError: If booking not found or invalid status
    """
```

**Logic:**
1. Fetch booking details
2. Create job with:
   - `customer_id` from booking
   - `title` = f"{service_category} Service"
   - `description` = service_description
   - `category` = service_category
   - `location_address` = service_address
   - `preferred_date` = scheduled_date
   - `preferred_time` = scheduled_time
   - `budget_min` = budget_max = estimated_price
   - `status` = 'assigned'
   - `assigned_provider_id` = provider_id
3. Update booking with `job_id`
4. Return job_id

---

### API Gateway Routes

#### [NEW] POST /bookings/confirm
- **Lambda:** `confirm_booking`
- **Auth:** None (public endpoint, secured by token)
- **Method:** POST
- **Integration:** Lambda Proxy

---

### Email Templates

#### [NEW] [booking_confirmation_email.html](file:///Users/ykpfly/Desktop/capstone/quickfix_backend/src/email/templates/booking_confirmation_email.html)

**Content:**
- Provider name greeting
- Booking details (service, date, time, location)
- Customer information
- Estimated price
- Confirmation button/link
- Expiration notice (7 days)

**Confirmation URL:**
```
https://your-frontend-domain.com/provider/confirm-booking?token={confirmation_token}
```

---

#### [NEW] [booking_confirmed_notification.html](file:///Users/ykpfly/Desktop/capstone/quickfix_backend/src/email/templates/booking_confirmed_notification.html)

**Content:**
- Customer name greeting
- Confirmation message
- Provider details
- Booking details
- Next steps

---

### Environment Variables

**Add to `.env` and Lambda configuration:**
```bash
# Email Configuration
SES_SENDER_EMAIL=noreply@quickfix.com
BOOKING_CONFIRMATION_URL=https://your-frontend-domain.com/provider/confirm-booking
AWS_SES_REGION=us-east-1
```

---

### IAM Permissions

**Add to Lambda execution roles:**
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ses:SendEmail",
        "ses:SendRawEmail"
      ],
      "Resource": "*"
    }
  ]
}
```

---

## Verification Plan

### Database Migration Testing

**Test 1: Schema Migration**
```bash
# Connect to MySQL and run migration
mysql -h quickfix-mysql.cno624c2aarh.us-east-2.rds.amazonaws.com \
  -u admin -p quickfix < sql/migrations/add_booking_confirmation.sql

# Verify schema
mysql -h quickfix-mysql.cno624c2aarh.us-east-2.rds.amazonaws.com \
  -u admin -p -e "DESCRIBE bookings;" quickfix
```

**Expected:** New columns visible, status enum includes `pending_confirmation`

---

### Automated Tests

**Test 2: Email Service Unit Test**
```bash
# Create test file: test_email_service.py
python test_email_service.py
```

**Test Coverage:**
- Email formatting
- SES client initialization
- Error handling for invalid emails

---

**Test 3: Create Booking with Email**
```bash
# Update existing test to verify email sending
python test_create_booking_with_email.py
```

**Expected:**
- Booking created with `pending_confirmation` status
- Confirmation token generated and stored
- Email sent to provider (verify via SES console or test inbox)

---

**Test 4: Confirm Booking Flow**
```bash
# Create new test
python test_confirm_booking.py
```

**Test Cases:**
- Valid token → booking confirmed, job created
- Expired token → 400 error
- Invalid token → 404 error
- Already confirmed → 400 error

---

### Manual Verification

**Test 5: End-to-End Workflow**

1. **Create Booking via API:**
   ```bash
   curl -X POST https://your-api-gateway/bookings \
     -H "Authorization: Bearer <customer-jwt>" \
     -H "Content-Type: application/json" \
     -d '{
       "provider_id": "SP-001",
       "service_category": "plumber",
       "service_description": "Fix leak",
       "scheduled_date": "2026-02-01",
       "scheduled_time": "14:00",
       "service_address": "123 Main St",
       "service_city": "Toronto",
       "service_state": "ON",
       "service_postal_code": "M5H1J9"
     }'
   ```
   
2. **Check Provider Email:**
   - Verify email received with booking details
   - Verify confirmation link present
   
3. **Click Confirmation Link:**
   - Should redirect to frontend confirmation page
   - Frontend calls `/bookings/confirm` with token
   
4. **Verify Database:**
   ```sql
   SELECT * FROM bookings WHERE booking_id = <id>;
   -- Should show status='confirmed', confirmed_at set, job_id populated
   
   SELECT * FROM jobs WHERE job_id = <job_id>;
   -- Should show new job with assigned_provider_id
   ```
   
5. **Check Customer Email:**
   - Verify confirmation notification received

---

### AWS SES Setup (Required Before Testing)

**Step 1: Verify Sender Email**
```bash
aws ses verify-email-identity \
  --email-address noreply@quickfix.com \
  --region us-east-1
```

**Step 2: For Testing - Verify Test Recipient Emails**
```bash
# If SES is in sandbox mode
aws ses verify-email-identity \
  --email-address test-provider@example.com \
  --region us-east-1
```

**Step 3: Request Production Access** (Optional)
- Go to AWS SES Console → Account Dashboard
- Request production access to send to any email

---

## Implementation Order

1. ✅ Create database migration SQL file
2. ✅ Run migration on development database
3. ✅ Create email service utility
4. ✅ Create email templates
5. ✅ Update `create_booking` handler
6. ✅ Create `confirm_booking` handler
7. ✅ Create `convert_booking_to_job` utility
8. ✅ Write unit tests
9. ✅ Test locally
10. ✅ Configure AWS SES
11. ✅ Deploy Lambda functions
12. ✅ Configure API Gateway routes
13. ✅ End-to-end testing
14. ✅ Update API documentation

---

## Rollback Plan

If issues arise:
1. Revert `create_booking` handler to previous version
2. Remove API Gateway route for `/bookings/confirm`
3. Database migration rollback:
   ```sql
   ALTER TABLE bookings DROP COLUMN confirmation_token;
   ALTER TABLE bookings DROP COLUMN confirmation_token_expires_at;
   ALTER TABLE bookings DROP COLUMN confirmed_at;
   ALTER TABLE bookings DROP COLUMN job_id;
   ALTER TABLE bookings 
   MODIFY COLUMN status ENUM('pending', 'confirmed', 'in_progress', 'completed', 'cancelled') 
   NOT NULL DEFAULT 'pending';
   ```

---

## Future Enhancements

- Email retry mechanism for failed sends
- Provider dashboard to view pending confirmations
- Reminder emails for unconfirmed bookings
- SMS notifications as alternative to email
- Webhook for real-time frontend updates
