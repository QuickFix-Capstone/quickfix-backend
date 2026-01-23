# Job Application API Analysis

## Database Schema

The `job_applications` table has the following structure:

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
    UNIQUE KEY unique_application (job_id, provider_id),
    INDEX idx_job_id (job_id),
    INDEX idx_provider_id (provider_id)
);
```

**Key Points:**
- Status can be: `pending`, `accepted`, `rejected`
- Unique constraint on `(job_id, provider_id)` - one application per provider per job
- Includes `proposed_price` and `message` fields

---

## Existing APIs

### ✅ Customer-Side APIs (Already Implemented)

#### 1. **GET /jobs/{job_id}/applications**
- **Handler**: [`lambda/jobs/get_job_applications/handler.py`](file:///Users/ykpfly/Desktop/capstone/quickfix_backend/lambda/jobs/get_job_applications/handler.py)
- **Purpose**: View all applications for a specific job
- **Auth**: Customer JWT (must own the job)
- **Returns**: List of applications with provider details

#### 2. **PUT /job/{job_id}/applications/{application_id}**
- **Handler**: [`lambda/jobs/update_application_status/handler.py`](file:///Users/ykpfly/Desktop/capstone/quickfix_backend/lambda/jobs/update_application_status/handler.py)
- **Purpose**: Accept or reject a job application
- **Auth**: Customer JWT (must own the job)
- **Actions**:
  - `accept`: Sets application to "accepted", assigns job to provider, rejects other pending applications
  - `reject`: Sets application to "rejected"

**Documentation**: [job_applications_api.md](file:///Users/ykpfly/Desktop/capstone/quickfix_backend/docs/api/job_applications_api.md)

---

## ❌ Missing Provider-Side APIs

### Critical Gap Identified

**Service providers currently have NO APIs to:**

1. ❌ **Create/Submit a job application** (apply to a job)
2. ❌ **View their own applications** (see jobs they've applied to)
3. ❌ **Withdraw an application** (cancel a pending application)
4. ❌ **View available jobs to apply to** (browse open jobs)

---

## 🎯 Recommended Provider-Side APIs

### 1. **POST /provider/jobs/{job_id}/apply**
**Purpose**: Service provider applies to a job

**Request Body**:
```json
{
  "proposed_price": 150.00,
  "message": "I have 10 years of experience in plumbing..."
}
```

**Logic**:
- Extract `provider_id` from JWT (cognito_sub → service_providers table)
- Validate job exists and is in "open" status
- Check provider hasn't already applied (unique constraint)
- Insert into `job_applications` with status "pending"

**Response**:
```json
{
  "message": "Application submitted successfully",
  "application": {
    "application_id": 123,
    "job_id": 45,
    "provider_id": "SP-001",
    "proposed_price": 150.00,
    "message": "I have 10 years of experience...",
    "status": "pending",
    "created_at": "2026-01-22T21:00:00"
  }
}
```

---

### 2. **GET /provider/applications**
**Purpose**: View all applications submitted by the provider

**Query Parameters**:
- `status` (optional): Filter by status (pending/accepted/rejected)
- `limit` (optional): Pagination limit
- `offset` (optional): Pagination offset

**Response**:
```json
{
  "applications": [
    {
      "application_id": 123,
      "job": {
        "job_id": 45,
        "title": "Fix leaking pipe",
        "category": "Plumbing",
        "location": "Toronto, ON",
        "budget_min": 100.00,
        "budget_max": 200.00,
        "status": "open",
        "customer_name": "John Doe"
      },
      "proposed_price": 150.00,
      "message": "I have 10 years...",
      "status": "pending",
      "created_at": "2026-01-22T21:00:00"
    }
  ],
  "total": 5
}
```

---

### 3. **DELETE /provider/applications/{application_id}**
**Purpose**: Withdraw a pending application

**Logic**:
- Verify provider owns the application
- Check application status is "pending"
- Delete the application record

**Response**:
```json
{
  "message": "Application withdrawn successfully"
}
```

---

### 4. **GET /provider/jobs/available**
**Purpose**: Browse open jobs that provider can apply to

**Query Parameters**:
- `category` (optional): Filter by service category
- `location_city` (optional): Filter by city
- `limit` (optional): Pagination limit
- `offset` (optional): Pagination offset

**Response**:
```json
{
  "jobs": [
    {
      "job_id": 45,
      "title": "Fix leaking pipe",
      "description": "Kitchen sink is leaking...",
      "category": "Plumbing",
      "location_address": "123 Main St",
      "location_city": "Toronto",
      "budget_min": 100.00,
      "budget_max": 200.00,
      "preferred_date": "2026-01-25",
      "created_at": "2026-01-22T20:00:00",
      "application_count": 3,
      "has_applied": false
    }
  ],
  "total": 12
}
```

---

### 5. **PUT /provider/applications/{application_id}** (Optional)
**Purpose**: Update a pending application (change price/message)

**Request Body**:
```json
{
  "proposed_price": 175.00,
  "message": "Updated proposal with more details..."
}
```

**Logic**:
- Verify provider owns the application
- Check application status is "pending"
- Update `proposed_price` and/or `message`

---

## Implementation Priority

### High Priority (Must Have)
1. ✅ **POST /provider/jobs/{job_id}/apply** - Core functionality
2. ✅ **GET /provider/applications** - View own applications
3. ✅ **GET /provider/jobs/available** - Browse jobs to apply to

### Medium Priority (Should Have)
4. **DELETE /provider/applications/{application_id}** - Withdraw application

### Low Priority (Nice to Have)
5. **PUT /provider/applications/{application_id}** - Update pending application

---

## Related Files

- **Schema**: [quickfix-mySql.session.sql:136-148](file:///Users/ykpfly/Desktop/capstone/quickfix_backend/quickfix-mySql.session.sql#L136-L148)
- **Customer APIs**: [job_applications_api.md](file:///Users/ykpfly/Desktop/capstone/quickfix_backend/docs/api/job_applications_api.md)
- **Update Status Handler**: [update_application_status/handler.py](file:///Users/ykpfly/Desktop/capstone/quickfix_backend/lambda/jobs/update_application_status/handler.py)
- **Get Applications Handler**: [get_job_applications/handler.py](file:///Users/ykpfly/Desktop/capstone/quickfix_backend/lambda/jobs/get_job_applications/handler.py)

---

## Next Steps

> [!IMPORTANT]
> Service providers currently cannot interact with the job application system. The following APIs need to be implemented to enable the complete job application workflow.

**Recommended Action**: Implement the three high-priority provider-side APIs to enable:
1. Providers applying to jobs
2. Providers viewing their application history
3. Providers browsing available jobs
