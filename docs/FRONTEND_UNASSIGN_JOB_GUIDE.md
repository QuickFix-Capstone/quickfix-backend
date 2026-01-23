# Unassign Job - Frontend Integration Guide

## ✅ Endpoint Status: DEPLOYED & READY

**Endpoint**: `https://kfvf20j7j9.execute-api.us-east-2.amazonaws.com/job/{job_id}/unassign`  
**Method**: `PUT`  
**Authorization**: JWT Required (Cognito)  
**Status**: Active

---

## Quick Start

### Basic Usage

```javascript
const unassignProvider = async (jobId) => {
  const token = localStorage.getItem('jwt_token'); // or however you store the token
  
  const response = await fetch(
    `https://kfvf20j7j9.execute-api.us-east-2.amazonaws.com/job/${jobId}/unassign`,
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
    return data; // Success
  } else {
    throw new Error(data.message);
  }
};
```

---

## Request Details

### Headers Required
```
Authorization: Bearer <JWT_TOKEN>
Content-Type: application/json
```

### Path Parameters
- `job_id` (required): The ID of the job to unassign

### Request Body
**None required** - This is a simple PUT request with no body.

---

## Response Format

### Success Response (200 OK)

```json
{
  "message": "Provider unassigned successfully",
  "job": {
    "job_id": 4,
    "title": "Install ceiling fan",
    "status": "open",
    "assigned_provider_id": null,
    "created_at": "2026-01-03T10:30:00",
    "updated_at": "2026-01-04T04:30:00"
  }
}
```

### Error Responses

#### 400 Bad Request - Job Not Assigned
```json
{
  "message": "Cannot unassign provider from job with status 'open'. Only jobs with status 'assigned' can be unassigned."
}
```

#### 400 Bad Request - No Provider
```json
{
  "message": "Job is not currently assigned to a provider"
}
```

#### 401 Unauthorized
```json
{
  "message": "Unauthorized"
}
```

#### 403 Forbidden - Not Job Owner
```json
{
  "message": "Forbidden: You can only unassign providers from your own jobs"
}
```

#### 404 Not Found
```json
{
  "message": "Job not found"
}
```

---

## React Integration Examples

### Example 1: Simple Button Component

```jsx
import React, { useState } from 'react';
import { useAuth } from 'react-oidc-context';

const UnassignButton = ({ jobId, onSuccess }) => {
  const auth = useAuth();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleUnassign = async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch(
        `https://kfvf20j7j9.execute-api.us-east-2.amazonaws.com/job/${jobId}/unassign`,
        {
          method: 'PUT',
          headers: {
            'Authorization': `Bearer ${auth.user?.id_token}`,
            'Content-Type': 'application/json'
          }
        }
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.message);
      }

      // Success!
      alert('Provider unassigned successfully!');
      if (onSuccess) onSuccess(data.job);

    } catch (err) {
      setError(err.message);
      alert(`Error: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <button 
        onClick={handleUnassign} 
        disabled={loading}
        className="btn-unassign"
      >
        {loading ? 'Unassigning...' : 'Unassign Provider'}
      </button>
      {error && <p className="error">{error}</p>}
    </div>
  );
};

export default UnassignButton;
```

### Example 2: Complete Job Management Component

```jsx
import React, { useState, useEffect } from 'react';
import { useAuth } from 'react-oidc-context';

const JobDetails = ({ jobId }) => {
  const auth = useAuth();
  const [job, setJob] = useState(null);
  const [loading, setLoading] = useState(false);

  const API_BASE = 'https://kfvf20j7j9.execute-api.us-east-2.amazonaws.com';

  // Fetch job details
  const fetchJob = async () => {
    const response = await fetch(`${API_BASE}/job/${jobId}`, {
      headers: {
        'Authorization': `Bearer ${auth.user?.id_token}`
      }
    });
    const data = await response.json();
    setJob(data.job);
  };

  useEffect(() => {
    fetchJob();
  }, [jobId]);

  // Unassign provider
  const handleUnassign = async () => {
    if (!confirm('Are you sure you want to unassign this provider?')) {
      return;
    }

    setLoading(true);

    try {
      const response = await fetch(
        `${API_BASE}/job/${jobId}/unassign`,
        {
          method: 'PUT',
          headers: {
            'Authorization': `Bearer ${auth.user?.id_token}`,
            'Content-Type': 'application/json'
          }
        }
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.message);
      }

      // Update local state
      setJob(data.job);
      alert('Provider unassigned successfully! Job is now open for new applications.');

    } catch (error) {
      alert(`Error: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  if (!job) return <div>Loading...</div>;

  return (
    <div className="job-details">
      <h2>{job.title}</h2>
      <p>Status: <strong>{job.status}</strong></p>
      
      {job.status === 'assigned' && job.assigned_provider_id && (
        <div className="assigned-section">
          <p>Assigned to: {job.assigned_provider_id}</p>
          <button 
            onClick={handleUnassign}
            disabled={loading}
            className="btn-danger"
          >
            {loading ? 'Unassigning...' : 'Unassign Provider'}
          </button>
        </div>
      )}

      {job.status === 'open' && (
        <p className="info">This job is open for applications</p>
      )}
    </div>
  );
};

export default JobDetails;
```

### Example 3: With Error Handling & Toast Notifications

```jsx
import React, { useState } from 'react';
import { useAuth } from 'react-oidc-context';
import { toast } from 'react-toastify'; // or your preferred toast library

const UnassignProviderButton = ({ job, onJobUpdated }) => {
  const auth = useAuth();
  const [isUnassigning, setIsUnassigning] = useState(false);

  const unassignProvider = async () => {
    // Validation
    if (job.status !== 'assigned') {
      toast.error('This job is not currently assigned to a provider');
      return;
    }

    if (!window.confirm('Are you sure you want to unassign this provider? The job will be reopened for new applications.')) {
      return;
    }

    setIsUnassigning(true);

    try {
      const response = await fetch(
        `https://kfvf20j7j9.execute-api.us-east-2.amazonaws.com/job/${job.job_id}/unassign`,
        {
          method: 'PUT',
          headers: {
            'Authorization': `Bearer ${auth.user?.id_token}`,
            'Content-Type': 'application/json'
          }
        }
      );

      const data = await response.json();

      if (!response.ok) {
        // Handle specific error cases
        if (response.status === 403) {
          toast.error('You do not have permission to unassign this job');
        } else if (response.status === 404) {
          toast.error('Job not found');
        } else {
          toast.error(data.message || 'Failed to unassign provider');
        }
        return;
      }

      // Success!
      toast.success('Provider unassigned successfully!');
      
      // Update parent component
      if (onJobUpdated) {
        onJobUpdated(data.job);
      }

    } catch (error) {
      console.error('Unassign error:', error);
      toast.error('Network error. Please try again.');
    } finally {
      setIsUnassigning(false);
    }
  };

  // Only show button if job is assigned
  if (job.status !== 'assigned') {
    return null;
  }

  return (
    <button
      onClick={unassignProvider}
      disabled={isUnassigning}
      className="btn btn-warning"
    >
      {isUnassigning ? (
        <>
          <span className="spinner"></span>
          Unassigning...
        </>
      ) : (
        'Unassign Provider'
      )}
    </button>
  );
};

export default UnassignProviderButton;
```

---

## Business Logic & Rules

### When Can You Unassign?
✅ Job status is `"assigned"`  
✅ You are the job owner (customer)  
✅ Provider is currently assigned

### When Can't You Unassign?
❌ Job status is `"open"` (no provider assigned)  
❌ Job status is `"in_progress"` (work has started)  
❌ Job status is `"completed"` (work is done)  
❌ Job status is `"cancelled"`  
❌ You are not the job owner

### What Happens After Unassign?
1. Job status changes: `"assigned"` → `"open"`
2. `assigned_provider_id` is cleared to `null`
3. All job applications remain in their current state:
   - Accepted application stays accepted (historical record)
   - Rejected applications stay rejected
   - Pending applications stay pending
4. New providers can now apply to the job

---

## Testing

### Test Scenario 1: Successful Unassignment
```javascript
// Prerequisites: Job 4 has status='assigned'
const result = await unassignProvider(4);
console.log(result);
// Expected: { message: "Provider unassigned successfully", job: {...} }
// Job status should now be "open"
```

### Test Scenario 2: Job Not Assigned
```javascript
// Prerequisites: Job 1 has status='open'
try {
  await unassignProvider(1);
} catch (error) {
  console.log(error.message);
  // Expected: "Cannot unassign provider from job with status 'open'..."
}
```

### Test Scenario 3: Not Job Owner
```javascript
// Prerequisites: Using JWT from different customer
try {
  await unassignProvider(4);
} catch (error) {
  console.log(error.message);
  // Expected: "Forbidden: You can only unassign providers from your own jobs"
}
```

---

## Common Use Cases

### Use Case 1: Job Details Page
Show "Unassign Provider" button when job is assigned:
```jsx
{job.status === 'assigned' && (
  <UnassignButton jobId={job.job_id} onSuccess={refreshJob} />
)}
```

### Use Case 2: My Jobs List
Add unassign action to each assigned job:
```jsx
{jobs.map(job => (
  <div key={job.job_id}>
    <h3>{job.title}</h3>
    <span className={`status-${job.status}`}>{job.status}</span>
    {job.status === 'assigned' && (
      <button onClick={() => handleUnassign(job.job_id)}>
        Unassign
      </button>
    )}
  </div>
))}
```

### Use Case 3: Provider Management
Allow customer to unassign and choose a different provider:
```jsx
const switchProvider = async (jobId) => {
  // 1. Unassign current provider
  await unassignProvider(jobId);
  
  // 2. Navigate to applications page
  navigate(`/job/${jobId}/applications`);
  
  // 3. Customer can now accept a different application
};
```

---

## Error Handling Best Practices

```javascript
const unassignWithErrorHandling = async (jobId) => {
  try {
    const response = await fetch(
      `https://kfvf20j7j9.execute-api.us-east-2.amazonaws.com/job/${jobId}/unassign`,
      {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      }
    );

    const data = await response.json();

    if (!response.ok) {
      // Handle specific status codes
      switch (response.status) {
        case 400:
          throw new Error(data.message || 'Invalid request');
        case 401:
          // Redirect to login
          window.location.href = '/login';
          return;
        case 403:
          throw new Error('You do not have permission to unassign this job');
        case 404:
          throw new Error('Job not found');
        default:
          throw new Error('An unexpected error occurred');
      }
    }

    return data;

  } catch (error) {
    console.error('Unassign error:', error);
    throw error;
  }
};
```

---

## TypeScript Types (Optional)

```typescript
interface Job {
  job_id: number;
  title: string;
  status: 'open' | 'assigned' | 'in_progress' | 'completed' | 'cancelled';
  assigned_provider_id: string | null;
  created_at: string;
  updated_at: string;
}

interface UnassignResponse {
  message: string;
  job: Job;
}

interface ErrorResponse {
  message: string;
}

const unassignProvider = async (jobId: number): Promise<UnassignResponse> => {
  const token = localStorage.getItem('jwt_token');
  
  const response = await fetch(
    `https://kfvf20j7j9.execute-api.us-east-2.amazonaws.com/job/${jobId}/unassign`,
    {
      method: 'PUT',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
    }
  );

  const data = await response.json();

  if (!response.ok) {
    throw new Error((data as ErrorResponse).message);
  }

  return data as UnassignResponse;
};
```

---

## Summary

- **Endpoint**: `PUT /job/{job_id}/unassign`
- **Auth**: JWT token required in Authorization header
- **Purpose**: Unassign provider from job, return job to "open" status
- **When to use**: When customer wants to remove assigned provider and reopen job
- **Result**: Job status → "open", assigned_provider_id → null

For more details, see:
- [API Documentation](file:///Users/ykpfly/Desktop/capStone/quickfix_backend/docs/api/unassign_job_api.md)
- [Backend Testing Guide](file:///Users/ykpfly/Desktop/capStone/quickfix_backend/docs/FRONTEND_TESTING_GUIDE.md)
