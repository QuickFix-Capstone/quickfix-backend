# Budget Change Request Feature - Implementation Plan

## Overview

This plan implements a comprehensive budget change request system that allows service providers to request additional budget during job execution, with customer approval required before the price change takes effect. The system ensures job completion cannot proceed while budget change requests are pending.

### Current System Context

**Existing Database Schema:**
- `jobs` table has `final_price` field (already exists per schema review)
- Current job statuses: `open`, `assigned`, `in_progress`, `completed`, `cancelled`
- `bookings` table has similar pricing fields: `estimated_price`, `final_price`

**Existing Backend:**
- Lambda functions in `/quickfix_backend/lambda/jobs/`
- Job update handler at `lambda/jobs/update_job/handler.py`
- Uses RDS MySQL database via `src.db.rds_main`

**Existing Frontend:**
- Customer job pages: `src/pages/customer/MyJobs.jsx`, `JobDetails.jsx`
- Provider job pages: `src/pages/ServiceProvider/JobDetailsPage.jsx`
- React with Vite, uses AWS Cognito for authentication

---

## Business Rules

> [!IMPORTANT]
> **Core Business Rules (BR-BUD-01 through BR-BUD-05)**

### BR-BUD-01: Price Authority
- `final_price` is the **agreed price** and only changes after customer accepts a budget change request
- Provider **cannot** change `jobs.final_price` directly
- Only customer approval updates the official price

### BR-BUD-02: Request Timing
- Provider can request more budget **only** when job status is `in_progress`
- Cannot request budget changes for jobs in `open`, `assigned`, `completed`, or `cancelled` status

### BR-BUD-03: Single Pending Request Rule
- Each job can have **only one** pending budget change request at a time
- New requests are blocked while a pending request exists
- Provider must wait for customer response before submitting another request

### BR-BUD-04: Completion Gate
- Job **cannot** be marked `completed` while any budget change request has status `pending`
- Provider must wait for customer approval/rejection before completing the job
- This prevents price disputes after job completion

### BR-BUD-05: Customer Authority
- **Only** the customer who owns the job can approve/reject budget change requests
- Customer approval is the sole mechanism for updating `final_price`

---

## Proposed Changes

### Database Schema

#### 1. Add New Job Status: `budget_change_pending`

**File:** SQL migration script (new file)

```sql
-- Add budget_change_pending to jobs.status enum
ALTER TABLE jobs 
MODIFY COLUMN status ENUM(
    'open',
    'assigned',
    'in_progress',
    'budget_change_pending',  -- NEW STATUS
    'completed',
    'cancelled'
) NOT NULL DEFAULT 'open';
```

**Purpose:** This status blocks job completion until customer responds to the budget change request.

---

#### 2. Create `job_price_change_requests` Table

**File:** SQL migration script (new file)

```sql
CREATE TABLE job_price_change_requests (
    request_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    job_id BIGINT NOT NULL,
    requested_by_provider_id VARCHAR(40) NOT NULL,
    proposed_final_price DECIMAL(10, 2) NOT NULL,
    reason TEXT NOT NULL,
    status ENUM('pending', 'accepted', 'rejected', 'cancelled') NOT NULL DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    responded_at TIMESTAMP NULL,

    -- Foreign keys
    CONSTRAINT fk_price_request_job
        FOREIGN KEY (job_id) REFERENCES jobs(job_id) ON DELETE CASCADE,
    CONSTRAINT fk_price_request_provider
        FOREIGN KEY (requested_by_provider_id) REFERENCES service_providers(provider_id) ON DELETE CASCADE,

    -- Indexes for performance
    INDEX idx_job_id (job_id),
    INDEX idx_job_status (job_id, status),  -- Fast "pending check"
    INDEX idx_provider_id (requested_by_provider_id),
    INDEX idx_created_at (created_at)

) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

**Field Descriptions:**
- `request_id`: Primary key
- `job_id`: Links to the job
- `requested_by_provider_id`: Provider making the request
- `proposed_final_price`: New total price being requested (must be > 0)
- `reason`: Provider's explanation for the budget increase
- `status`: Request lifecycle state
- `created_at`: When request was created
- `responded_at`: When customer accepted/rejected (NULL for pending)

---

### Backend API Endpoints

#### 3. Provider Requests Budget Change

**[NEW] POST `/jobs/{jobId}/price-change-requests`**

**Lambda:** `lambda/jobs/request_price_change/handler.py`

**Request Body:**
```json
{
  "proposed_final_price": 350.00,
  "reason": "Discovered additional water damage requiring pipe replacement"
}
```

**Validation Rules:**
1. Job exists
2. Job is assigned to this provider (`assigned_provider_id` matches)
3. Job status is `in_progress`
4. No existing pending request for this job
5. `proposed_final_price` > 0
6. `proposed_final_price` >= current `final_price` (if set)
7. `reason` is not empty (min 10 characters)

**Operations (Transaction):**
1. Insert new row into `job_price_change_requests`:
   - `job_id`, `requested_by_provider_id`, `proposed_final_price`, `reason`
   - `status = 'pending'`
2. Update `jobs.status = 'budget_change_pending'`
3. Send notification to customer (email + in-app)

**Response (200):**
```json
{
  "message": "Budget change request submitted successfully",
  "request": {
    "request_id": 123,
    "job_id": 45,
    "proposed_final_price": 350.00,
    "reason": "...",
    "status": "pending",
    "created_at": "2026-02-01T19:30:00Z"
  }
}
```

---

#### 4. Customer Accepts Budget Change

**[NEW] POST `/price-change-requests/{requestId}/accept`**

**Lambda:** `lambda/jobs/accept_price_change/handler.py`

**Validation Rules:**
1. Request exists
2. Request status is `pending`
3. Customer owns the job (`jobs.customer_id` matches authenticated user)
4. Job status is `budget_change_pending`

**Operations (Transaction):**
1. Update `job_price_change_requests`:
   - `status = 'accepted'`
   - `responded_at = NOW()`
2. Update `jobs`:
   - `final_price = proposed_final_price`
   - `status = 'in_progress'`
3. Send notification to provider (email + in-app)

**Response (200):**
```json
{
  "message": "Budget change accepted",
  "job": {
    "job_id": 45,
    "final_price": 350.00,
    "status": "in_progress"
  }
}
```

---

#### 5. Customer Rejects Budget Change

**[NEW] POST `/price-change-requests/{requestId}/reject`**

**Lambda:** `lambda/jobs/reject_price_change/handler.py`

**Validation Rules:**
1. Request exists
2. Request status is `pending`
3. Customer owns the job
4. Job status is `budget_change_pending`

**Operations (Transaction):**
1. Update `job_price_change_requests`:
   - `status = 'rejected'`
   - `responded_at = NOW()`
2. Update `jobs`:
   - `status = 'in_progress'` (return to in-progress)
   - **Do NOT change `final_price`**
3. Send notification to provider

**Response (200):**
```json
{
  "message": "Budget change rejected",
  "job": {
    "job_id": 45,
    "final_price": 250.00,  // Original price unchanged
    "status": "in_progress"
  }
}
```

---

#### 6. Update Job Completion Logic

**[MODIFY] Existing endpoint behavior**

**Lambda:** `lambda/jobs/update_job/handler.py` (or create new `complete_job` handler)

**Current Behavior:** Provider marks job as `completed`

**New Validation (Add Before Completion):**
1. Job exists
2. Provider matches `assigned_provider_id`
3. Job status is `in_progress`
4. **NEW:** Check for pending budget change requests:
   ```sql
   SELECT COUNT(*) FROM job_price_change_requests 
   WHERE job_id = ? AND status = 'pending'
   ```
   - If count > 0, return error: `"Cannot complete job while budget change request is pending"`

**Operations (if validation passes):**
1. Set `jobs.status = 'completed'`
2. Set `jobs.completed_at = NOW()`
3. Trigger review flow (existing functionality)

---

#### 7. Get Job Details (Enhanced)

**[MODIFY] GET `/jobs/{jobId}` and `/customer/jobs/{jobId}`**

**Lambda:** `lambda/jobs/get_job_details/handler.py`

**Add to Response:**
```json
{
  "job": {
    // ... existing fields ...
    "final_price": 250.00,
    "pending_price_change_request": {  // NEW: null if no pending request
      "request_id": 123,
      "proposed_final_price": 350.00,
      "reason": "...",
      "created_at": "2026-02-01T19:30:00Z"
    }
  }
}
```

**Query:**
```sql
SELECT j.*, 
       pcr.request_id, pcr.proposed_final_price, pcr.reason, pcr.created_at as request_created_at
FROM jobs j
LEFT JOIN job_price_change_requests pcr 
    ON j.job_id = pcr.job_id AND pcr.status = 'pending'
WHERE j.job_id = ?
```

---

### Frontend Components

#### 8. Provider UI - Request Budget Change

**[MODIFY] `src/pages/ServiceProvider/JobDetailsPage.jsx`**

**Changes:**

1. **Add "Request More Budget" Button** (when `status === 'in_progress'`):
```jsx
{job.status === 'in_progress' && !job.pending_price_change_request && (
  <Button onClick={() => setShowBudgetRequestModal(true)}>
    Request More Budget
  </Button>
)}
```

2. **Create Budget Request Modal:**
   - Input: `proposed_final_price` (number, required, > current final_price)
   - Textarea: `reason` (required, min 10 chars)
   - Submit button calls `POST /jobs/{jobId}/price-change-requests`

3. **Show Pending Request Banner** (when `status === 'budget_change_pending'`):
```jsx
{job.status === 'budget_change_pending' && (
  <Alert variant="warning">
    <AlertCircle className="h-4 w-4" />
    <AlertTitle>Waiting for Customer Approval</AlertTitle>
    <AlertDescription>
      You requested ${job.pending_price_change_request.proposed_final_price}.
      The customer needs to approve before you can complete this job.
    </AlertDescription>
  </Alert>
)}
```

4. **Disable "Complete Job" Button** (when `status === 'budget_change_pending'`):
```jsx
<Button 
  disabled={job.status === 'budget_change_pending'}
  onClick={handleCompleteJob}
>
  {job.status === 'budget_change_pending' 
    ? 'Waiting for Budget Approval' 
    : 'Mark as Complete'}
</Button>
```

---

#### 9. Customer UI - Approve/Reject Budget Change

**[MODIFY] `src/pages/customer/JobDetails.jsx`**

**Changes:**

1. **Show Budget Change Request Card** (when `job.pending_price_change_request` exists):
```jsx
{job.pending_price_change_request && (
  <Card className="border-orange-200 bg-orange-50">
    <CardHeader>
      <CardTitle className="flex items-center gap-2">
        <DollarSign className="h-5 w-5 text-orange-600" />
        Budget Change Request
      </CardTitle>
    </CardHeader>
    <CardContent className="space-y-4">
      <div>
        <p className="text-sm text-neutral-600">Current Price:</p>
        <p className="text-2xl font-bold">${job.final_price.toFixed(2)}</p>
      </div>
      <div>
        <p className="text-sm text-neutral-600">Requested New Price:</p>
        <p className="text-2xl font-bold text-orange-600">
          ${job.pending_price_change_request.proposed_final_price.toFixed(2)}
        </p>
        <p className="text-sm text-red-600 font-medium">
          +${(job.pending_price_change_request.proposed_final_price - job.final_price).toFixed(2)} increase
        </p>
      </div>
      <div>
        <p className="text-sm font-medium text-neutral-700">Reason:</p>
        <p className="text-neutral-600">{job.pending_price_change_request.reason}</p>
      </div>
      <div className="flex gap-3">
        <Button 
          onClick={() => handleAcceptPriceChange(job.pending_price_change_request.request_id)}
          className="bg-green-600 hover:bg-green-700"
        >
          Accept New Price
        </Button>
        <Button 
          onClick={() => handleRejectPriceChange(job.pending_price_change_request.request_id)}
          variant="outline"
          className="border-red-600 text-red-600 hover:bg-red-50"
        >
          Reject
        </Button>
      </div>
    </CardContent>
  </Card>
)}
```

2. **Add API Call Handlers:**
```javascript
const handleAcceptPriceChange = async (requestId) => {
  const token = auth.user?.id_token;
  const res = await fetch(
    `${API_BASE}/price-change-requests/${requestId}/accept`,
    {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}` }
    }
  );
  if (res.ok) {
    alert('Budget change accepted');
    fetchJobDetails(); // Refresh
  }
};

const handleRejectPriceChange = async (requestId) => {
  // Similar to accept
};
```

---

#### 10. Customer UI - Job List Status Badge

**[MODIFY] `src/pages/customer/MyJobs.jsx`**

**Update `getStatusColor` function:**
```javascript
const getStatusColor = (status) => {
  switch (status) {
    case "open":
      return "bg-green-100 text-green-800";
    case "assigned":
      return "bg-blue-100 text-blue-800";
    case "in_progress":
      return "bg-yellow-100 text-yellow-800";
    case "budget_change_pending":  // NEW
      return "bg-orange-100 text-orange-800";
    case "completed":
      return "bg-gray-100 text-gray-800";
    case "cancelled":
      return "bg-red-100 text-red-800";
    default:
      return "bg-neutral-100 text-neutral-800";
  }
};
```

---

### API Routing Configuration

#### 11. Update API Gateway Routes

**File:** AWS API Gateway configuration (or SAM/CDK template)

**Add Routes:**
```yaml
# Provider endpoint
POST /jobs/{jobId}/price-change-requests
  Integration: Lambda - request_price_change
  Authorizer: Cognito (provider group)

# Customer endpoints  
POST /price-change-requests/{requestId}/accept
  Integration: Lambda - accept_price_change
  Authorizer: Cognito (customer group)

POST /price-change-requests/{requestId}/reject
  Integration: Lambda - reject_price_change
  Authorizer: Cognito (customer group)
```

---

## Verification Plan

### Automated Tests

#### Database Migration Verification

**Test Script:** `quickfix_backend/test_budget_change_schema.py`

```python
# Verify schema changes
def test_job_status_enum_includes_budget_change_pending():
    # Query INFORMATION_SCHEMA to verify enum values
    
def test_price_change_requests_table_exists():
    # Verify table exists with correct columns and indexes
    
def test_foreign_key_constraints():
    # Verify FK relationships to jobs and service_providers
```

**Run Command:**
```bash
cd /Users/ykpfly/Desktop/capstone/quickfix_backend
python test_budget_change_schema.py
```

---

#### Backend API Tests

**Test Script:** `quickfix_backend/test_budget_change_workflow.py`

```python
# Test 1: Provider can request budget change when job is in_progress
def test_provider_request_budget_change_success():
    # Create job with status='in_progress'
    # POST /jobs/{jobId}/price-change-requests
    # Assert: 200 response, request created, job status = 'budget_change_pending'

# Test 2: Provider cannot request if job is not in_progress
def test_provider_request_blocked_wrong_status():
    # Create job with status='open'
    # POST /jobs/{jobId}/price-change-requests
    # Assert: 400 error

# Test 3: Provider cannot request if pending request exists
def test_provider_request_blocked_pending_exists():
    # Create job with existing pending request
    # POST /jobs/{jobId}/price-change-requests
    # Assert: 400 error "Pending request already exists"

# Test 4: Customer accept updates final_price
def test_customer_accept_updates_price():
    # Create pending request
    # POST /price-change-requests/{requestId}/accept
    # Assert: job.final_price = proposed_price, status = 'in_progress'

# Test 5: Customer reject does not update final_price
def test_customer_reject_keeps_original_price():
    # Create pending request
    # POST /price-change-requests/{requestId}/reject
    # Assert: job.final_price unchanged, status = 'in_progress'

# Test 6: Provider cannot complete job with pending request
def test_provider_cannot_complete_with_pending_request():
    # Create job with pending request
    # POST /jobs/{jobId}/complete
    # Assert: 400 error "Cannot complete while request pending"

# Test 7: Only job owner customer can accept/reject
def test_only_owner_can_respond():
    # Create request
    # Try to accept with different customer token
    # Assert: 403 Forbidden

# Test 8: Only assigned provider can request
def test_only_assigned_provider_can_request():
    # Create job assigned to provider A
    # Try to request with provider B token
    # Assert: 403 Forbidden
```

**Run Command:**
```bash
cd /Users/ykpfly/Desktop/capstone/quickfix_backend
python test_budget_change_workflow.py
```

---

### Manual Testing (Browser)

> [!NOTE]
> **Prerequisites:**
> - Local dev server running: `npm run dev` in `/Users/ykpfly/Desktop/capstone/quickfix-frontend`
> - Backend deployed to AWS with new Lambda functions
> - Test customer and provider accounts in Cognito

#### Manual Test Scenario 1: Happy Path

**Steps:**
1. **Customer:** Login and post a new job
2. **Provider:** Login, apply to job
3. **Customer:** Accept provider's application (job becomes `assigned`)
4. **Provider:** Start the job (status → `in_progress`)
5. **Provider:** On job details page, click "Request More Budget"
6. **Provider:** Enter new price ($350) and reason, submit
7. **Verify:** Job status badge shows "BUDGET CHANGE PENDING"
8. **Verify:** "Complete Job" button is disabled with message
9. **Customer:** Login, navigate to job details
10. **Verify:** Budget change request card is visible with:
    - Current price: $250
    - Requested price: $350
    - Reason text
    - Accept/Reject buttons
11. **Customer:** Click "Accept New Price"
12. **Verify:** Job price updates to $350
13. **Verify:** Job status returns to "IN PROGRESS"
14. **Provider:** Refresh page, verify "Complete Job" button is now enabled
15. **Provider:** Mark job as complete
16. **Verify:** Job status → "COMPLETED"

**Expected Result:** Budget change request flows smoothly from provider request → customer approval → job completion

---

#### Manual Test Scenario 2: Customer Rejects

**Steps:**
1. Follow steps 1-10 from Scenario 1
2. **Customer:** Click "Reject" button
3. **Verify:** Job price remains at original $250
4. **Verify:** Job status returns to "IN PROGRESS"
5. **Provider:** Refresh page, verify can submit new request
6. **Provider:** Try to complete job without new request
7. **Verify:** Job completes successfully

**Expected Result:** Rejection returns job to normal state without price change

---

#### Manual Test Scenario 3: Multiple Request Prevention

**Steps:**
1. **Provider:** Submit budget change request
2. **Provider:** Try to submit another request immediately
3. **Verify:** Error message: "A pending budget change request already exists"
4. **Customer:** Reject the request
5. **Provider:** Submit new request
6. **Verify:** New request succeeds

**Expected Result:** Only one pending request allowed at a time

---

#### Manual Test Scenario 4: Completion Blocked

**Steps:**
1. **Provider:** Submit budget change request (job status → `budget_change_pending`)
2. **Provider:** Try to click "Mark as Complete" button
3. **Verify:** Button is disabled
4. **Provider:** Try direct API call to complete job (using browser dev tools or Postman)
5. **Verify:** API returns 400 error with message about pending request

**Expected Result:** Job cannot be completed while request is pending

---

### Edge Case Tests

**Test Script:** `quickfix_backend/test_budget_change_edge_cases.py`

```python
# Test: Proposed price must be > 0
def test_proposed_price_validation():
    # POST with proposed_price = 0
    # Assert: 400 error

# Test: Proposed price should be >= current final_price
def test_proposed_price_must_exceed_current():
    # POST with proposed_price < current final_price
    # Assert: 400 error (or warning)

# Test: Reason cannot be empty
def test_reason_required():
    # POST with empty reason
    # Assert: 400 error

# Test: Request for non-existent job
def test_request_for_invalid_job():
    # POST /jobs/99999/price-change-requests
    # Assert: 404 error

# Test: Accept already-accepted request
def test_accept_non_pending_request():
    # Accept a request that's already accepted
    # Assert: 400 error "Request is not pending"
```

**Run Command:**
```bash
cd /Users/ykpfly/Desktop/capstone/quickfix_backend
python test_budget_change_edge_cases.py
```

---

## Documentation Updates

### 12. Update Requirements Artifacts

**[MODIFY] Project documentation files**

**Add Business Rules:**
- BR-BUD-01: Price Authority
- BR-BUD-02: Request Timing
- BR-BUD-03: Single Pending Request
- BR-BUD-04: Completion Gate
- BR-BUD-05: Customer Authority

**Add Use Cases:**
- UC-BUD-01: Provider Requests Additional Budget
- UC-BUD-02: Customer Approves Budget Change
- UC-BUD-03: Customer Rejects Budget Change
- UC-BUD-04: Provider Completes Job (with pending check)

**Update State Diagram:**
```
open → assigned → in_progress → budget_change_pending → in_progress → completed
                                      ↓
                                  (rejected)
                                      ↓
                                  in_progress
```

---

## Migration Strategy

### Phase 1: Database Schema (Non-Breaking)
1. Run migration to add `budget_change_pending` status to enum
2. Create `job_price_change_requests` table
3. Verify schema with test script

### Phase 2: Backend API (Incremental)
1. Deploy new Lambda functions:
   - `request_price_change`
   - `accept_price_change`
   - `reject_price_change`
2. Update `get_job_details` to include pending request
3. Update job completion logic with pending check
4. Configure API Gateway routes

### Phase 3: Frontend UI (Feature Flag Ready)
1. Update provider job details page with budget request UI
2. Update customer job details page with approval UI
3. Update job list status colors
4. Test locally with deployed backend

### Phase 4: Testing & Validation
1. Run automated test suite
2. Perform manual browser testing
3. Test edge cases
4. User acceptance testing

---

## Rollback Plan

If issues arise:
1. **Database:** Status enum addition is backward compatible (existing jobs unaffected)
2. **Backend:** New Lambda functions can be disabled via API Gateway
3. **Frontend:** UI changes are additive (old functionality remains)
4. **Data:** `job_price_change_requests` table can be dropped without affecting jobs table

---

## Summary

This implementation plan provides a complete budget change request system with:

✅ **5 Business Rules** enforcing price authority and workflow integrity  
✅ **3 New Lambda Functions** for request/accept/reject operations  
✅ **1 New Database Table** with proper indexes and constraints  
✅ **1 New Job Status** to block completion during pending requests  
✅ **Provider UI** for requesting budget changes  
✅ **Customer UI** for approving/rejecting requests  
✅ **Comprehensive Testing** (automated + manual scenarios)  
✅ **Documentation Updates** for requirements and state diagrams  

The system ensures customers maintain price authority while giving providers a structured way to request additional budget when unexpected work is discovered.
