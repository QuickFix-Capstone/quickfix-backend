# Update Application Status API - Quick Reference

## ✅ Backend is Correct

The backend API is working as designed. Here's what it expects:

### Endpoint
```
PUT /prod/job/{job_id}/applications/{application_id}
```

### Request Body
```json
{
  "action": "accept"
}
```
**OR**
```json
{
  "action": "reject"
}
```

### ⚠️ Common Mistakes

**WRONG** ❌:
```json
{
  "status": "accept"     // Wrong parameter name
}
```

**WRONG** ❌:
```json
{
  "action": "accepted"   // Wrong value (should be "accept", not "accepted")
}
```

**CORRECT** ✅:
```json
{
  "action": "accept"     // Correct!
}
```

---

## Frontend Fix

### Current (Incorrect) Code
```javascript
// ❌ WRONG
fetch(`${API_BASE}/job/${jobId}/applications/${applicationId}`, {
  method: 'PUT',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({ status: "accepted" })  // WRONG!
})
```

### Fixed Code
```javascript
// ✅ CORRECT
fetch(`${API_BASE}/job/${jobId}/applications/${applicationId}`, {
  method: 'PUT',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({ action: "accept" })  // CORRECT!
})
```

---

## Complete Examples

### Accept Application
```javascript
const acceptApplication = async (jobId, applicationId, token) => {
  const response = await fetch(
    `https://kfvf20j7j9.execute-api.us-east-2.amazonaws.com/prod/job/${jobId}/applications/${applicationId}`,
    {
      method: 'PUT',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ action: "accept" })  // ✅ Use "accept"
    }
  );
  
  return await response.json();
};
```

### Reject Application
```javascript
const rejectApplication = async (jobId, applicationId, token) => {
  const response = await fetch(
    `https://kfvf20j7j9.execute-api.us-east-2.amazonaws.com/prod/job/${jobId}/applications/${applicationId}`,
    {
      method: 'PUT',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ action: "reject" })  // ✅ Use "reject"
    }
  );
  
  return await response.json();
};
```

---

## Testing in Terminal

### Test Accept
```bash
curl -X PUT "https://kfvf20j7j9.execute-api.us-east-2.amazonaws.com/prod/job/1001/applications/7" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"action": "accept"}'
```

### Test Reject
```bash
curl -X PUT "https://kfvf20j7j9.execute-api.us-east-2.amazonaws.com/prod/job/1001/applications/7" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"action": "reject"}'
```

---

## Backend Validation

The backend validates the `action` parameter:

```python
action = data.get("action")
if action not in ["accept", "reject"]:
    return _response(400, {"message": "Invalid action. Must be 'accept' or 'reject'"})
```

**Valid values**: `"accept"` or `"reject"` (lowercase, no "ed" suffix)

---

## Summary

**The backend is NOT the problem.** The frontend needs to:

1. ✅ Use parameter name: `"action"` (not `"status"`)
2. ✅ Use value: `"accept"` (not `"accepted"`)
3. ✅ Use value: `"reject"` (not `"rejected"`)

This is a **frontend fix** - update the request body to match the API specification.
