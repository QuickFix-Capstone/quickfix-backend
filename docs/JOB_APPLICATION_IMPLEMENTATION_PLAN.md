# Job Application System - Complete Implementation Plan

## Overview

This plan implements a complete job application workflow for both **customers** (who post jobs) and **service providers** (who apply to jobs).

---

## Database Schema

### Current Schema (Already Exists ✅)

#### `jobs` Table
```sql
CREATE TABLE IF NOT EXISTS jobs (
    job_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    customer_id BIGINT NOT NULL,
    title VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,
    category VARCHAR(100) NULL,
    location_address VARCHAR(500) NOT NULL,
    location_city VARCHAR(100) NULL,
    location_state VARCHAR(50) NULL,
    location_zip VARCHAR(20) NULL,
    preferred_date DATE NULL,
    preferred_time TIME NULL,
    budget_min DECIMAL(10, 2) NULL,
    budget_max DECIMAL(10, 2) NULL,
    status ENUM('open', 'assigned', 'in_progress', 'completed', 'cancelled') 
           NOT NULL DEFAULT 'open',
    assigned_provider_id VARCHAR(40) NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_job_customer FOREIGN KEY (customer_id) REFERENCES customers(customer_id) ON DELETE CASCADE
);
```

#### `job_applications` Table
```sql
CREATE TABLE IF NOT EXISTS job_applications (
    application_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    job_id BIGINT NOT NULL,
    provider_id VARCHAR(40) NOT NULL,
    proposed_price DECIMAL(10, 2) NULL,
    message TEXT NULL,
    status ENUM('pending', 'accepted', 'rejected') NOT NULL DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_application_job FOREIGN KEY (job_id) REFERENCES jobs(job_id) ON DELETE CASCADE,
    UNIQUE KEY unique_application (job_id, provider_id)
);
```

**Schema Status**: ✅ No changes needed

---

## API Endpoints Summary

### Customer-Side APIs

| Endpoint | Method | Status | Purpose |
|----------|--------|--------|---------|
| `/jobs` | POST | ✅ Exists | Create a new job |
| `/customer/jobs` | GET | ✅ Exists | Get all customer's jobs |
| `/jobs/{job_id}` | GET | ✅ Exists | Get job details |
| `/jobs/{job_id}/applications` | GET | ✅ Exists | View applications for a job |
| `/job/{job_id}/applications/{application_id}` | PUT | ✅ Exists | Accept/reject application |

### Service Provider-Side APIs

| Endpoint | Method | Status | Purpose |
|----------|--------|--------|---------|
| `/provider/jobs/available` | GET | ❌ **NEW** | Browse open jobs |
| `/provider/jobs/{job_id}/apply` | POST | ❌ **NEW** | Apply to a job |
| `/provider/applications` | GET | ❌ **NEW** | View own applications |
| `/provider/applications/{application_id}` | GET | ❌ **NEW** | Get application details |
| `/provider/applications/{application_id}` | DELETE | ❌ **NEW** | Withdraw application |

---

## Proposed Changes

### Customer-Side (Already Implemented)

#### 1. ✅ GET /jobs/{job_id}/applications
**Handler**: [`lambda/jobs/get_job_applications/handler.py`](file:///Users/ykpfly/Desktop/capstone/quickfix_backend/lambda/jobs/get_job_applications/handler.py)

**Purpose**: View all applications for a specific job

**Auth**: Customer JWT (must own the job)

**Response**:
```json
{
  "job_id": 1,
  "application_count": 3,
  "applications": [
    {
      "application_id": 1,
      "provider": {
        "provider_id": "SP-001",
        "name": "John Carter",
        "business_name": "Carter Plumbing",
        "rating": 4.8,
        "phone": "416-555-1234",
        "completed_jobs": 42
      },
      "proposed_price": 150.00,
      "message": "I have 10 years of experience...",
      "status": "pending",
      "created_at": "2026-01-22T20:00:00"
    }
  ]
}
```

---

#### 2. ✅ PUT /job/{job_id}/applications/{application_id}
**Handler**: [`lambda/jobs/update_application_status/handler.py`](file:///Users/ykpfly/Desktop/capstone/quickfix_backend/lambda/jobs/update_application_status/handler.py)

**Purpose**: Accept or reject an application

**Auth**: Customer JWT (must own the job)

**Request Body**:
```json
{
  "action": "accept"  // or "reject"
}
```

**Accept Logic** (Transaction):
1. Update application → `status = 'accepted'`
2. Update job → `status = 'assigned'`, `assigned_provider_id = provider_id`
3. Reject all other pending applications

**Response**:
```json
{
  "message": "Application accepted successfully",
  "application": {
    "application_id": 1,
    "job_id": 1,
    "provider_id": "SP-001",
    "status": "accepted",
    "created_at": "2026-01-22T20:00:00"
  },
  "job": {
    "job_id": 1,
    "status": "assigned",
    "assigned_provider_id": "SP-001"
  }
}
```

---

### Service Provider-Side (New Implementations)

#### 3. ❌ NEW: GET /provider/jobs/available
**Handler**: `lambda/jobs/get_available_jobs/handler.py`

**Purpose**: Browse open jobs that providers can apply to

**Auth**: Service Provider JWT

**Query Parameters**:
- `category` (optional): Filter by service category
- `location_city` (optional): Filter by city
- `min_budget` (optional): Minimum budget filter
- `max_budget` (optional): Maximum budget filter
- `limit` (optional, default: 20): Pagination limit
- `offset` (optional, default: 0): Pagination offset

**SQL Query**:
```sql
SELECT 
    j.job_id, j.title, j.description, j.category,
    j.location_address, j.location_city, j.location_state, j.location_zip,
    j.preferred_date, j.preferred_time,
    j.budget_min, j.budget_max, j.created_at,
    c.first_name, c.last_name,
    COUNT(DISTINCT ja.application_id) as application_count,
    MAX(CASE WHEN ja.provider_id = %s THEN 1 ELSE 0 END) as has_applied
FROM jobs j
JOIN customers c ON j.customer_id = c.customer_id
LEFT JOIN job_applications ja ON j.job_id = ja.job_id
WHERE j.status = 'open'
  AND (j.category = %s OR %s IS NULL)
  AND (j.location_city = %s OR %s IS NULL)
  AND (j.budget_max >= %s OR %s IS NULL)
  AND (j.budget_min <= %s OR %s IS NULL)
GROUP BY j.job_id
ORDER BY j.created_at DESC
LIMIT %s OFFSET %s
```

**Response**:
```json
{
  "jobs": [
    {
      "job_id": 45,
      "title": "Fix leaking kitchen sink",
      "description": "Urgent plumbing repair needed...",
      "category": "Plumbing",
      "location": {
        "address": "123 Main St",
        "city": "Toronto",
        "state": "ON",
        "zip": "M5V 2T6"
      },
      "budget_min": 100.00,
      "budget_max": 200.00,
      "preferred_date": "2026-01-25",
      "preferred_time": "14:00:00",
      "customer_name": "John Doe",
      "application_count": 3,
      "has_applied": false,
      "created_at": "2026-01-22T20:00:00"
    }
  ],
  "total": 12,
  "limit": 20,
  "offset": 0
}
```

---

#### 4. ❌ NEW: POST /provider/jobs/{job_id}/apply
**Handler**: `lambda/jobs/create_application/handler.py`

**Purpose**: Service provider applies to a job

**Auth**: Service Provider JWT

**Request Body**:
```json
{
  "proposed_price": 150.00,
  "message": "I have 10 years of plumbing experience and can start immediately..."
}
```

**Validation**:
- Job must exist and be in `'open'` status
- Provider cannot have already applied (unique constraint)
- `proposed_price` must be positive (if provided)
- `message` length: 10-1000 characters

**SQL Logic**:
```sql
-- 1. Verify job exists and is open
SELECT job_id, status FROM jobs WHERE job_id = %s;

-- 2. Check if provider already applied
SELECT application_id FROM job_applications 
WHERE job_id = %s AND provider_id = %s;

-- 3. Insert application
INSERT INTO job_applications (job_id, provider_id, proposed_price, message, status)
VALUES (%s, %s, %s, %s, 'pending');
```

**Response**:
```json
{
  "message": "Application submitted successfully",
  "application": {
    "application_id": 123,
    "job_id": 45,
    "provider_id": "SP-001",
    "proposed_price": 150.00,
    "message": "I have 10 years of plumbing experience...",
    "status": "pending",
    "created_at": "2026-01-22T21:00:00"
  }
}
```

**Error Responses**:
- `400`: Job not open, already applied, invalid input
- `404`: Job not found
- `409`: Duplicate application

---

#### 5. ❌ NEW: GET /provider/applications
**Handler**: `lambda/jobs/get_provider_applications/handler.py`

**Purpose**: View all applications submitted by the provider

**Auth**: Service Provider JWT

**Query Parameters**:
- `status` (optional): Filter by status (pending/accepted/rejected)
- `limit` (optional, default: 20): Pagination limit
- `offset` (optional, default: 0): Pagination offset

**SQL Query**:
```sql
SELECT 
    ja.application_id, ja.job_id, ja.proposed_price, ja.message, 
    ja.status, ja.created_at,
    j.title, j.description, j.category, j.status as job_status,
    j.location_address, j.location_city, j.location_state,
    j.budget_min, j.budget_max, j.preferred_date,
    c.first_name, c.last_name, c.phone_number as customer_phone
FROM job_applications ja
JOIN jobs j ON ja.job_id = j.job_id
JOIN customers c ON j.customer_id = c.customer_id
WHERE ja.provider_id = %s
  AND (ja.status = %s OR %s IS NULL)
ORDER BY 
    CASE ja.status 
        WHEN 'pending' THEN 1 
        WHEN 'accepted' THEN 2 
        WHEN 'rejected' THEN 3 
    END,
    ja.created_at DESC
LIMIT %s OFFSET %s
```

**Response**:
```json
{
  "applications": [
    {
      "application_id": 123,
      "job": {
        "job_id": 45,
        "title": "Fix leaking kitchen sink",
        "description": "Urgent plumbing repair...",
        "category": "Plumbing",
        "status": "open",
        "location": {
          "address": "123 Main St",
          "city": "Toronto",
          "state": "ON"
        },
        "budget_min": 100.00,
        "budget_max": 200.00,
        "preferred_date": "2026-01-25",
        "customer_name": "John Doe",
        "customer_phone": "416-555-0001"
      },
      "proposed_price": 150.00,
      "message": "I have 10 years...",
      "status": "pending",
      "created_at": "2026-01-22T21:00:00"
    }
  ],
  "total": 5,
  "limit": 20,
  "offset": 0
}
```

---

#### 6. ❌ NEW: GET /provider/applications/{application_id}
**Handler**: `lambda/jobs/get_application_details/handler.py`

**Purpose**: Get detailed information about a specific application

**Auth**: Service Provider JWT (must own the application)

**Response**:
```json
{
  "application": {
    "application_id": 123,
    "job_id": 45,
    "proposed_price": 150.00,
    "message": "I have 10 years...",
    "status": "pending",
    "created_at": "2026-01-22T21:00:00"
  },
  "job": {
    "job_id": 45,
    "title": "Fix leaking kitchen sink",
    "description": "Urgent plumbing repair needed...",
    "category": "Plumbing",
    "status": "open",
    "location": {
      "address": "123 Main St",
      "city": "Toronto",
      "state": "ON",
      "zip": "M5V 2T6"
    },
    "budget_min": 100.00,
    "budget_max": 200.00,
    "preferred_date": "2026-01-25",
    "preferred_time": "14:00:00",
    "customer": {
      "name": "John Doe",
      "phone": "416-555-0001"
    }
  }
}
```

---

#### 7. ❌ NEW: DELETE /provider/applications/{application_id}
**Handler**: `lambda/jobs/withdraw_application/handler.py`

**Purpose**: Withdraw a pending application

**Auth**: Service Provider JWT (must own the application)

**Validation**:
- Application must exist
- Provider must own the application
- Application status must be `'pending'`

**SQL Logic**:
```sql
-- 1. Verify ownership and status
SELECT provider_id, status FROM job_applications 
WHERE application_id = %s;

-- 2. Delete application
DELETE FROM job_applications 
WHERE application_id = %s AND status = 'pending';
```

**Response**:
```json
{
  "message": "Application withdrawn successfully",
  "application_id": 123
}
```

**Error Responses**:
- `400`: Application not pending (already accepted/rejected)
- `403`: Not your application
- `404`: Application not found

---

## Verification Plan

### Automated Tests

#### Customer-Side Tests
```bash
# Test viewing applications
python3 test_get_job_applications.py

# Test accepting application
python3 test_accept_application.py

# Test rejecting application
python3 test_reject_application.py
```

#### Provider-Side Tests
```bash
# Test browsing available jobs
python3 test_get_available_jobs.py

# Test applying to job
python3 test_create_application.py

# Test viewing own applications
python3 test_get_provider_applications.py

# Test withdrawing application
python3 test_withdraw_application.py
```

### Manual Verification

#### Complete Workflow Test

1. **Customer posts job**
   - POST `/jobs` → Job created with `status='open'`

2. **Providers browse jobs**
   - GET `/provider/jobs/available` → See the new job

3. **Providers apply**
   - POST `/provider/jobs/1/apply` (Provider 1)
   - POST `/provider/jobs/1/apply` (Provider 2)
   - POST `/provider/jobs/1/apply` (Provider 3)

4. **Customer views applications**
   - GET `/jobs/1/applications` → See 3 pending applications

5. **Customer accepts one**
   - PUT `/job/1/applications/2` with `{"action": "accept"}`
   - Verify: Application 2 → `accepted`
   - Verify: Applications 1, 3 → `rejected`
   - Verify: Job → `status='assigned'`, `assigned_provider_id='SP-002'`

6. **Provider checks status**
   - GET `/provider/applications` → See accepted application

---

## Implementation Priority

### Phase 1: High Priority (Core Functionality)
1. ✅ **POST /provider/jobs/{job_id}/apply** - Enable providers to apply
2. ✅ **GET /provider/jobs/available** - Let providers browse jobs
3. ✅ **GET /provider/applications** - Let providers track their applications

### Phase 2: Medium Priority (Enhanced UX)
4. **GET /provider/applications/{application_id}** - Detailed application view
5. **DELETE /provider/applications/{application_id}** - Withdraw applications

### Phase 3: Future Enhancements
- Email notifications when application status changes
- Push notifications for new job postings matching provider skills
- Application analytics (acceptance rate, average response time)

---

## File Structure

```
lambda/jobs/
├── get_available_jobs/          # NEW - Browse open jobs
│   ├── handler.py
│   └── requirements.txt
├── create_application/          # NEW - Apply to job
│   ├── handler.py
│   └── requirements.txt
├── get_provider_applications/   # NEW - View own applications
│   ├── handler.py
│   └── requirements.txt
├── get_application_details/     # NEW - Application details
│   ├── handler.py
│   └── requirements.txt
├── withdraw_application/        # NEW - Withdraw application
│   ├── handler.py
│   └── requirements.txt
├── get_job_applications/        # EXISTS - Customer view
│   ├── handler.py
│   └── requirements.txt
└── update_application_status/   # EXISTS - Accept/reject
    ├── handler.py
    └── requirements.txt
```

---

## API Gateway Routes

### Customer Routes (Existing)
```
GET  /jobs/{job_id}/applications
PUT  /job/{job_id}/applications/{application_id}
```

### Provider Routes (New)
```
GET    /provider/jobs/available
POST   /provider/jobs/{job_id}/apply
GET    /provider/applications
GET    /provider/applications/{application_id}
DELETE /provider/applications/{application_id}
```

---

## Authentication & Authorization

### Customer Endpoints
- **Auth**: Customer JWT from Cognito
- **Verification**: `cognito_sub` → `customers.cognito_sub` → `customer_id`
- **Authorization**: Can only manage their own jobs

### Provider Endpoints
- **Auth**: Service Provider JWT from Cognito
- **Verification**: `cognito_sub` → `service_providers.cognito_sub` → `provider_id`
- **Authorization**: Can only manage their own applications

---

## Next Steps

1. Review and approve this implementation plan
2. Implement Phase 1 APIs (high priority)
3. Deploy and test in development
4. Implement Phase 2 APIs
5. Full integration testing
6. Production deployment
