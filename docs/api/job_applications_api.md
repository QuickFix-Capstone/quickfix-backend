# Job Applications API Documentation

**Base URL**: `https://kfvf20j7j9.execute-api.us-east-2.amazonaws.com/prod`

This API allows customers to view and manage job applications from service providers.

---

## Authentication

All endpoints require JWT authentication via Cognito.

**Header**:
```
Authorization: Bearer <jwt_token>
```

---

## Endpoints

### 1. Get Job Applications

View all applications for a specific job.

**Endpoint**: `GET /jobs/{job_id}/applications`

**Authentication**: Customer JWT (must own the job)

**Path Parameters**:
- `job_id` (required): ID of the job

**Example Request**:
```javascript
fetch('https://kfvf20j7j9.execute-api.us-east-2.amazonaws.com/prod/jobs/1/applications', {
  method: 'GET',
  headers: {
    'Authorization': `Bearer ${jwtToken}`,
    'Content-Type': 'application/json'
  }
})
```

**Success Response (200 OK)**:
```json
{
  "job_id": 1,
  "application_count": 2,
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
      "proposed_price": 125.00,
      "message": "I have 15 years of plumbing experience...",
      "status": "pending",
      "created_at": "2026-01-04T00:50:25"
    }
  ]
}
```

**Error Responses**:
- `401 Unauthorized`: Missing or invalid JWT token
- `403 Forbidden`: Customer doesn't own this job
- `404 Not Found`: Job doesn't exist

---

### 2. Update Application Status

Accept or reject a job application.

**Endpoint**: `PUT /job/{job_id}/applications/{application_id}`

**Authentication**: Customer JWT (must own the job)

**Path Parameters**:
- `job_id` (required): ID of the job
- `application_id` (required): ID of the application

**Request Body**:
```json
{
  "action": "accept"  // or "reject"
}
```

#### Accept Application

**Example Request**:
```javascript
fetch('https://kfvf20j7j9.execute-api.us-east-2.amazonaws.com/prod/job/1/applications/1', {
  method: 'PUT',
  headers: {
    'Authorization': `Bearer ${jwtToken}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    action: 'accept'
  })
})
```

**Success Response (200 OK)**:
```json
{
  "message": "Application accepted successfully",
  "application": {
    "application_id": 1,
    "job_id": 1,
    "provider_id": "SP-001",
    "status": "accepted",
    "created_at": "2026-01-04T00:50:25"
  },
  "job": {
    "job_id": 1,
    "status": "assigned",
    "assigned_provider_id": "SP-001"
  }
}
```

**What Happens on Accept**:
1. Application status → `"accepted"`
2. Job status → `"assigned"`
3. Job assigned to the provider
4. All other pending applications → automatically `"rejected"`

#### Reject Application

**Example Request**:
```javascript
fetch('https://kfvf20j7j9.execute-api.us-east-2.amazonaws.com/prod/job/1/applications/2', {
  method: 'PUT',
  headers: {
    'Authorization': `Bearer ${jwtToken}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    action: 'reject'
  })
})
```

**Success Response (200 OK)**:
```json
{
  "message": "Application rejected successfully",
  "application": {
    "application_id": 2,
    "job_id": 1,
    "provider_id": "SP-005",
    "status": "rejected",
    "created_at": "2026-01-04T00:50:25"
  }
}
```

**Error Responses**:
- `400 Bad Request`: Invalid action or application already processed
- `401 Unauthorized`: Missing or invalid JWT token
- `403 Forbidden`: Customer doesn't own this job
- `404 Not Found`: Job or application doesn't exist

---

## React/Frontend Integration Examples

### Fetch Job Applications

```javascript
const getJobApplications = async (jobId, jwtToken) => {
  try {
    const response = await fetch(
      `https://kfvf20j7j9.execute-api.us-east-2.amazonaws.com/prod/jobs/${jobId}/applications`,
      {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${jwtToken}`,
          'Content-Type': 'application/json'
        }
      }
    );

    if (!response.ok) {
      throw new Error('Failed to fetch applications');
    }

    const data = await response.json();
    return data.applications;
  } catch (error) {
    console.error('Error fetching applications:', error);
    throw error;
  }
};
```

### Accept Application

```javascript
const acceptApplication = async (jobId, applicationId, jwtToken) => {
  try {
    const response = await fetch(
      `https://kfvf20j7j9.execute-api.us-east-2.amazonaws.com/prod/job/${jobId}/applications/${applicationId}`,
      {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${jwtToken}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ action: 'accept' })
      }
    );

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.message || 'Failed to accept application');
    }

    const data = await response.json();
    return data;
  } catch (error) {
    console.error('Error accepting application:', error);
    throw error;
  }
};
```

### Reject Application

```javascript
const rejectApplication = async (jobId, applicationId, jwtToken) => {
  try {
    const response = await fetch(
      `https://kfvf20j7j9.execute-api.us-east-2.amazonaws.com/prod/job/${jobId}/applications/${applicationId}`,
      {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${jwtToken}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ action: 'reject' })
      }
    );

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.message || 'Failed to reject application');
    }

    const data = await response.json();
    return data;
  } catch (error) {
    console.error('Error rejecting application:', error);
    throw error;
  }
};
```

---

## Application Status Flow

```
pending → accepted (job assigned, other apps rejected)
pending → rejected (job remains open)
```

**Note**: Once an application is accepted or rejected, it cannot be changed.

---

## Common Error Messages

| Error | Meaning | Solution |
|-------|---------|----------|
| `Unauthorized: Missing identity` | No JWT token | Include Authorization header |
| `Forbidden: You can only view applications for your own jobs` | Not job owner | Only job owner can manage applications |
| `Job not found` | Invalid job_id | Check job_id is correct |
| `Application not found` | Invalid application_id | Check application_id is correct |
| `Application already accepted` | Already processed | Cannot change status once processed |
| `Invalid action. Must be 'accept' or 'reject'` | Wrong action value | Use "accept" or "reject" |

---

## Testing

**Test Credentials**:
- Customer cognito_sub: `415b3510-a0a1-708e-6a02-dc457aec9ecc`
- Test Job IDs: 1, 3, 4
- Test Application IDs: 1, 2, 3, 4, 5

**Postman Collection**: Available in `/docs/postman/job_applications.json`
