# Frontend Testing Guide - Job Applications API

## Quick Test Checklist

### Test Data Available
- **Job 1**: 2 applications (App 1: SP-001, App 2: SP-005) - Status: open
- **Job 3**: 2 applications (App 3: SP-002, App 4: SP-005) - Status: open  
- **Job 4**: 1 application (App 5: SP-002) - Status: assigned

---

## Test 1: View Job Applications

### API Call
```javascript
const jobId = 3; // or 1, 3, 4
const token = "your-jwt-token-here";

fetch(`https://kfvf20j7j9.execute-api.us-east-2.amazonaws.com/prod/job/${jobId}/applications`, {
  method: 'GET',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  }
})
.then(res => res.json())
.then(data => console.log('Applications:', data))
.catch(err => console.error('Error:', err));
```

### Expected Response
```json
{
  "job_id": 3,
  "application_count": 2,
  "applications": [
    {
      "application_id": 3,
      "provider": {
        "provider_id": "SP-002",
        "name": "Emily Rogers",
        "business_name": "Rogers Electrical",
        "rating": 4.6,
        "phone": null,
        "completed_jobs": 0
      },
      "proposed_price": 200.0,
      "message": "Licensed electrician with 10+ years experience...",
      "status": "pending",
      "created_at": "2026-01-04T00:50:25"
    },
    {
      "application_id": 4,
      "provider": {
        "provider_id": "SP-005",
        "name": "David Wilson",
        "business_name": "Wilson Handyman Services",
        "rating": 4.5,
        "phone": null,
        "completed_jobs": 0
      },
      "proposed_price": 150.0,
      "message": "Handyman service - we handle all types of repairs...",
      "status": "pending",
      "created_at": "2026-01-04T00:50:25"
    }
  ]
}
```

---

## Test 2: Accept Application

### API Call
```javascript
const jobId = 3;
const applicationId = 3;
const token = "your-jwt-token-here";

fetch(`https://kfvf20j7j9.execute-api.us-east-2.amazonaws.com/prod/job/${jobId}/applications/${applicationId}`, {
  method: 'PUT',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({ action: 'accept' })
})
.then(res => res.json())
.then(data => console.log('Accept result:', data))
.catch(err => console.error('Error:', err));
```

### Expected Response
```json
{
  "message": "Application accepted successfully",
  "application": {
    "application_id": 3,
    "job_id": 3,
    "provider_id": "SP-002",
    "status": "accepted",
    "created_at": "2026-01-04T00:50:25"
  },
  "job": {
    "job_id": 3,
    "status": "assigned",
    "assigned_provider_id": "SP-002"
  }
}
```

### What Happens
- ✅ Application 3 → `accepted`
- ✅ Job 3 → `assigned` to SP-002
- ✅ Application 4 → automatically `rejected`

---

## Test 3: Reject Application

### API Call
```javascript
const jobId = 1;
const applicationId = 2;
const token = "your-jwt-token-here";

fetch(`https://kfvf20j7j9.execute-api.us-east-2.amazonaws.com/prod/job/${jobId}/applications/${applicationId}`, {
  method: 'PUT',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({ action: 'reject' })
})
.then(res => res.json())
.then(data => console.log('Reject result:', data))
.catch(err => console.error('Error:', err));
```

### Expected Response
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

---

## Test 4: Unassign Provider from Job

### API Call
```javascript
const jobId = 4; // Job must be in "assigned" status
const token = "your-jwt-token-here";

fetch(`https://kfvf20j7j9.execute-api.us-east-2.amazonaws.com/prod/job/${jobId}/unassign`, {
  method: 'PUT',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  }
})
.then(res => res.json())
.then(data => console.log('Unassign result:', data))
.catch(err => console.error('Error:', err));
```

### Expected Response
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

### What Happens
- ✅ Job status changes from `assigned` → `open`
- ✅ `assigned_provider_id` cleared to `null`
- ✅ All job applications remain in current state (accepted stays accepted, rejected stays rejected)
- ✅ New providers can now apply to the job

### Error Cases

**Job Not Assigned (400)**:
```json
{
  "message": "Cannot unassign provider from job with status 'open'. Only jobs with status 'assigned' can be unassigned."
}
```

**Not Job Owner (403)**:
```json
{
  "message": "Forbidden: You can only unassign providers from your own jobs"
}
```

**Job In Progress (400)**:
```json
{
  "message": "Cannot unassign provider from job with status 'in_progress'. Only jobs with status 'assigned' can be unassigned."
}
```

---

## Complete React Component Example

```jsx
import React, { useState, useEffect } from 'react';
import { useAuth } from 'react-oidc-context';

const JobApplications = ({ jobId }) => {
  const auth = useAuth();
  const [applications, setApplications] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const API_BASE = 'https://kfvf20j7j9.execute-api.us-east-2.amazonaws.com/prod';

  // Fetch applications
  useEffect(() => {
    fetchApplications();
  }, [jobId]);

  const fetchApplications = async () => {
    try {
      setLoading(true);
      const response = await fetch(`${API_BASE}/job/${jobId}/applications`, {
        headers: {
          'Authorization': `Bearer ${auth.user?.id_token}`,
          'Content-Type': 'application/json'
        }
      });

      if (!response.ok) throw new Error('Failed to fetch applications');
      
      const data = await response.json();
      setApplications(data.applications);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  // Accept application
  const handleAccept = async (applicationId) => {
    try {
      const response = await fetch(
        `${API_BASE}/job/${jobId}/applications/${applicationId}`,
        {
          method: 'PUT',
          headers: {
            'Authorization': `Bearer ${auth.user?.id_token}`,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({ action: 'accept' })
        }
      );

      if (!response.ok) throw new Error('Failed to accept application');
      
      const data = await response.json();
      alert(data.message);
      fetchApplications(); // Refresh list
    } catch (err) {
      alert('Error: ' + err.message);
    }
  };

  // Reject application
  const handleReject = async (applicationId) => {
    try {
      const response = await fetch(
        `${API_BASE}/job/${jobId}/applications/${applicationId}`,
        {
          method: 'PUT',
          headers: {
            'Authorization': `Bearer ${auth.user?.id_token}`,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({ action: 'reject' })
        }
      );

      if (!response.ok) throw new Error('Failed to reject application');
      
      const data = await response.json();
      alert(data.message);
      fetchApplications(); // Refresh list
    } catch (err) {
      alert('Error: ' + err.message);
    }
  };

  if (loading) return <div>Loading applications...</div>;
  if (error) return <div>Error: {error}</div>;

  return (
    <div className="applications-container">
      <h2>Job Applications ({applications.length})</h2>
      
      {applications.length === 0 ? (
        <p>No applications yet</p>
      ) : (
        applications.map(app => (
          <div key={app.application_id} className="application-card">
            <h3>{app.provider.name}</h3>
            <p><strong>Business:</strong> {app.provider.business_name}</p>
            <p><strong>Rating:</strong> {app.provider.rating} ⭐</p>
            <p><strong>Completed Jobs:</strong> {app.provider.completed_jobs}</p>
            <p><strong>Proposed Price:</strong> ${app.proposed_price}</p>
            <p><strong>Message:</strong> {app.message}</p>
            <p><strong>Status:</strong> {app.status}</p>
            
            {app.status === 'pending' && (
              <div className="actions">
                <button 
                  onClick={() => handleAccept(app.application_id)}
                  className="btn-accept"
                >
                  Accept
                </button>
                <button 
                  onClick={() => handleReject(app.application_id)}
                  className="btn-reject"
                >
                  Reject
                </button>
              </div>
            )}
          </div>
        ))
      )}
    </div>
  );
};

export default JobApplications;
```

---

## Error Handling

```javascript
const handleApiCall = async (url, options) => {
  try {
    const response = await fetch(url, options);
    const data = await response.json();
    
    if (!response.ok) {
      // Handle specific errors
      switch (response.status) {
        case 401:
          console.error('Unauthorized - check JWT token');
          break;
        case 403:
          console.error('Forbidden - not your job');
          break;
        case 404:
          console.error('Not found - invalid job/application ID');
          break;
        case 400:
          console.error('Bad request:', data.message);
          break;
        default:
          console.error('Error:', data.message);
      }
      throw new Error(data.message);
    }
    
    return data;
  } catch (error) {
    console.error('API Error:', error);
    throw error;
  }
};
```

---

## Testing Checklist

- [ ] Can view applications for Job 1
- [ ] Can view applications for Job 3
- [ ] Can accept an application (verify other apps auto-rejected)
- [ ] Can reject an application
- [ ] Can unassign provider from assigned job
- [ ] Error shown when trying to unassign from non-assigned job
- [ ] Error shown when trying to accept already-accepted application
- [ ] Error shown when trying to access another customer's job
- [ ] CORS headers working (no browser errors)
- [ ] JWT token properly sent in Authorization header
