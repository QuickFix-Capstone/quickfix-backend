# Unassign Job API

## Endpoint
```
PUT /prod/job/{job_id}/unassign
```

## Description
Allows a customer to unassign a service provider from their job, returning the job to "open" status. This enables the customer to receive new applications from other providers.

## Authentication
- **Required**: JWT token (Cognito)
- **Authorization**: Only the job owner (customer) can unassign providers

## Path Parameters
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `job_id` | integer | Yes | The ID of the job to unassign |

## Request Headers
```
Authorization: Bearer <JWT_TOKEN>
Content-Type: application/json
```

## Request Body
None required.

## Success Response

**Code**: `200 OK`

**Response Body**:
```json
{
  "message": "Provider unassigned successfully",
  "job": {
    "job_id": 1,
    "title": "Fix leaking kitchen sink",
    "status": "open",
    "assigned_provider_id": null,
    "created_at": "2026-01-03T10:30:00",
    "updated_at": "2026-01-04T04:30:00"
  }
}
```

## Error Responses

### 400 Bad Request - Job Not Assigned
**Condition**: Job is not currently in "assigned" status

**Response Body**:
```json
{
  "message": "Cannot unassign provider from job with status 'open'. Only jobs with status 'assigned' can be unassigned."
}
```

### 400 Bad Request - No Provider Assigned
**Condition**: Job has no assigned provider

**Response Body**:
```json
{
  "message": "Job is not currently assigned to a provider"
}
```

### 401 Unauthorized
**Condition**: Missing or invalid JWT token

**Response Body**:
```json
{
  "message": "Unauthorized: Missing identity"
}
```

### 403 Forbidden
**Condition**: User is not the job owner

**Response Body**:
```json
{
  "message": "Forbidden: You can only unassign providers from your own jobs"
}
```

### 404 Not Found - Job
**Condition**: Job with specified ID doesn't exist

**Response Body**:
```json
{
  "message": "Job not found"
}
```

### 404 Not Found - Customer
**Condition**: Customer profile not found for authenticated user

**Response Body**:
```json
{
  "message": "Customer profile not found"
}
```

### 500 Internal Server Error
**Condition**: Database connection failed or unexpected error

**Response Body**:
```json
{
  "message": "Internal server error"
}
```

## Business Logic

### What Happens When Unassigning
1. Job status changes from `"assigned"` to `"open"`
2. `assigned_provider_id` is set to `NULL`
3. All existing job applications remain in their current state:
   - Accepted application stays accepted (historical record)
   - Rejected applications stay rejected
   - Pending applications stay pending
4. New providers can now apply to the re-opened job

### Status Restrictions
You can **only** unassign a provider from jobs with status `"assigned"`.

**Cannot unassign from**:
- `"open"` - No provider assigned yet
- `"in_progress"` - Work has started
- `"completed"` - Work is finished
- `"cancelled"` - Job is cancelled

## Example Usage

### cURL Example
```bash
# Get your JWT token from Cognito authentication
TOKEN="eyJraWQiOiJ..."

# Unassign provider from job ID 1
curl -X PUT "https://your-api-gateway-url/prod/job/1/unassign" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json"
```

### JavaScript (Fetch) Example
```javascript
const unassignProvider = async (jobId) => {
  const token = localStorage.getItem('jwt_token');
  
  const response = await fetch(
    `https://your-api-gateway-url/prod/job/${jobId}/unassign`,
    {
      method: 'PUT',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
    }
  );
  
  const data = await response.json();
  
  if (response.ok) {
    console.log('Provider unassigned:', data.job);
    return data;
  } else {
    console.error('Error:', data.message);
    throw new Error(data.message);
  }
};

// Usage
unassignProvider(1)
  .then(result => console.log('Success:', result))
  .catch(error => console.error('Failed:', error));
```

## Database Changes

### SQL Operation
```sql
UPDATE jobs 
SET status = 'open', assigned_provider_id = NULL
WHERE job_id = ? AND customer_id = ?
```

### Affected Tables
- **jobs**: `status` and `assigned_provider_id` columns updated
- **job_applications**: No changes (applications remain in current state)

## Testing

### Prerequisites
1. Valid JWT token from authenticated customer
2. Job in database with `status = 'assigned'` and `assigned_provider_id` set
3. Customer must own the job

### Test Scenario 1: Successful Unassignment
```bash
# Setup: Job 1 has status='assigned', assigned_provider_id='prov123'
curl -X PUT "https://api.example.com/prod/job/1/unassign" \
  -H "Authorization: Bearer $TOKEN"

# Expected: 200 OK
# Job status → 'open'
# assigned_provider_id → NULL
```

### Test Scenario 2: Already Open Job
```bash
# Setup: Job 2 has status='open'
curl -X PUT "https://api.example.com/prod/job/2/unassign" \
  -H "Authorization: Bearer $TOKEN"

# Expected: 400 Bad Request
# Message: "Cannot unassign provider from job with status 'open'..."
```

### Test Scenario 3: Unauthorized User
```bash
# Setup: Use JWT from different customer
curl -X PUT "https://api.example.com/prod/job/1/unassign" \
  -H "Authorization: Bearer $OTHER_USER_TOKEN"

# Expected: 403 Forbidden
# Message: "Forbidden: You can only unassign providers from your own jobs"
```

### Test Scenario 4: Job In Progress
```bash
# Setup: Job 3 has status='in_progress'
curl -X PUT "https://api.example.com/prod/job/3/unassign" \
  -H "Authorization: Bearer $TOKEN"

# Expected: 400 Bad Request
# Message: "Cannot unassign provider from job with status 'in_progress'..."
```

## Related Endpoints
- `GET /prod/job/{job_id}` - Get job details
- `PUT /prod/job/{job_id}/application/{application_id}` - Accept/reject applications
- `PUT /prod/job/{job_id}` - Update job details
- `GET /prod/customer/jobs` - List customer's jobs
