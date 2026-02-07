# QuickFix WebSocket API - Quick Reference

Quick reference guide for service provider WebSocket integration.

---

## Connection URL

```
wss://<API_ID>.execute-api.<REGION>.amazonaws.com/<STAGE>?token=<JWT_TOKEN>
```

**Example:**
```javascript
const ws = new WebSocket(
  `wss://your-api-id.execute-api.us-east-2.amazonaws.com/prod?token=${idToken}`
);
```

---

## Authentication

- **Required**: Cognito JWT ID Token
- **Method**: Query parameter `?token=<JWT_TOKEN>`
- **Token Source**: AWS Cognito User Pool
- **Validation**: Backend validates JWT signature and claims

---

## Routes

| Route | Description |
|-------|-------------|
| `$connect` | Establish connection (automatic) |
| `$disconnect` | Close connection (automatic) |
| `ping` | Keep-alive heartbeat |

---

## Message Types

### Outgoing (Client → Server)

#### Ping
```json
{
  "action": "ping"
}
```

### Incoming (Server → Client)

#### PONG
```json
{
  "type": "PONG",
  "ts": 1704380000
}
```

#### JOB_STATUS_CHANGED
```json
{
  "type": "JOB_STATUS_CHANGED",
  "jobId": "1001",
  "oldStatus": "open",
  "newStatus": "assigned",
  "changedAt": "2026-02-07T16:30:00.000Z",
  "changedBy": "customer-cognito-sub-id"
}
```

---

## Connection Lifecycle

```
1. Connect with JWT token
   ↓
2. Backend validates token
   ↓
3. Connection stored in DynamoDB
   ↓
4. Send ping every 30s
   ↓
5. Receive notifications
   ↓
6. Disconnect or timeout (2 hours)
```

---

## Minimal Implementation

```javascript
const ws = new WebSocket(
  `wss://your-api-id.execute-api.us-east-2.amazonaws.com/prod?token=${idToken}`
);

ws.onopen = () => {
  console.log('Connected');
  
  // Start ping interval
  setInterval(() => {
    ws.send(JSON.stringify({ action: 'ping' }));
  }, 30000);
};

ws.onmessage = (event) => {
  const message = JSON.parse(event.data);
  
  if (message.type === 'JOB_STATUS_CHANGED') {
    console.log(`Job ${message.jobId}: ${message.oldStatus} → ${message.newStatus}`);
    // Update your UI
  }
};

ws.onerror = (error) => console.error('Error:', error);
ws.onclose = () => console.log('Disconnected');
```

---

## Job Status Values

| Status | Description |
|--------|-------------|
| `open` | Job is open for applications |
| `assigned` | Provider has been assigned |
| `in_progress` | Work is in progress |
| `completed` | Work is completed |
| `cancelled` | Job was cancelled |

---

## Common Status Transitions

```
open → assigned        (Customer accepts your application)
assigned → in_progress (You start the work)
in_progress → completed (You finish the work)
assigned → cancelled   (Job is cancelled)
```

---

## Error Codes

| Code | Meaning | Action |
|------|---------|--------|
| 1000 | Normal closure | No action needed |
| 1008 | Policy violation (401) | Refresh JWT token |
| 1011 | Server error | Retry connection |

---

## Best Practices

✅ **DO:**
- Send ping every 30 seconds
- Implement automatic reconnection with exponential backoff
- Validate JWT token before connecting
- Handle all message types gracefully
- Log errors for debugging

❌ **DON'T:**
- Connect without a valid JWT token
- Forget to implement ping/pong
- Ignore connection errors
- Assume connection is always alive
- Send messages other than ping (not supported yet)

---

## Testing Connection

```bash
# Using wscat (install: npm install -g wscat)
wscat -c "wss://your-api-id.execute-api.us-east-2.amazonaws.com/prod?token=YOUR_JWT_TOKEN"

# Send ping
> {"action":"ping"}

# Expected response
< {"type":"PONG","ts":1704380000}
```

---

## Configuration Checklist

- [ ] WebSocket URL configured
- [ ] Cognito User Pool ID configured
- [ ] Cognito Client ID configured
- [ ] JWT token retrieval implemented
- [ ] Connection handler implemented
- [ ] Message handler implemented
- [ ] Ping/pong implemented
- [ ] Reconnection logic implemented
- [ ] Error handling implemented
- [ ] UI notifications implemented

---

## Support

For detailed documentation, see: `WEBSOCKET_API_PROVIDER.md`
