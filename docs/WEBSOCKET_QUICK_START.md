# WebSocket Messaging - Quick Start Guide

## Overview

This guide provides a quick reference for implementing WebSocket-based real-time messaging in QuickFix.

---

## Current vs. Target Architecture

### Current (HTTP Polling)
```
Client → API Gateway → Lambda → DynamoDB
         (every 5 seconds)
```

### Target (WebSocket)
```
Client ←→ WebSocket API ←→ Lambda ←→ DynamoDB
         (persistent connection, instant push)
```

---

## Quick Implementation Checklist

### Backend (5 New Lambda Functions)

- [ ] `websocket/send_message` - Send messages
- [ ] `websocket/get_messages` - Fetch message history
- [ ] `websocket/get_conversations` - Fetch conversation list
- [ ] `websocket/mark_read` - Mark as read
- [ ] `websocket/typing` - Typing indicators

### Frontend (React)

- [ ] WebSocket client service (`src/services/websocket.js`)
- [ ] React hook (`src/hooks/useWebSocket.js`)
- [ ] Update messaging components
- [ ] Add typing indicators
- [ ] Add reconnection logic

### Infrastructure

- [ ] WebSocket API Gateway
- [ ] Route configurations
- [ ] Lambda permissions
- [ ] CloudWatch monitoring

---

## Message Protocol

### Client → Server (Request)
```json
{
  "action": "sendMessage",
  "data": { "conversationId": "uuid", "text": "Hello!" },
  "requestId": "unique-id"
}
```

### Server → Client (Response)
```json
{
  "type": "response",
  "action": "sendMessage",
  "requestId": "unique-id",
  "success": true,
  "data": { "messageId": 1704384000000 }
}
```

### Server → Client (Push Event)
```json
{
  "type": "event",
  "event": "newMessage",
  "data": {
    "conversationId": "uuid",
    "messageId": 1704384000000,
    "senderId": "2",
    "text": "Hello!",
    "timestamp": 1704384000000
  }
}
```

---

## WebSocket Actions

| Action | Purpose | Request Data | Response Data |
|--------|---------|--------------|---------------|
| `sendMessage` | Send a message | `conversationId`, `text` | `messageId`, `timestamp` |
| `getMessages` | Fetch history | `conversationId`, `limit`, `before` | `messages[]`, `hasMore` |
| `getConversations` | List conversations | `limit` | `conversations[]`, `total` |
| `markRead` | Mark as read | `conversationId` | `success` |
| `typing` | Typing indicator | `conversationId`, `isTyping` | (no response) |
| `ping` | Keep-alive | (none) | `type: "PONG"` |

---

## WebSocket Events (Server → Client)

| Event | When Triggered | Data |
|-------|----------------|------|
| `newMessage` | Someone sends a message | Full message object |
| `typing` | Someone is typing | `userId`, `userName`, `isTyping` |
| `messageRead` | Someone reads your message | `conversationId`, `readBy`, `timestamp` |

---

## Frontend Usage Example

### 1. Connect to WebSocket

```javascript
import { useWebSocket } from '../hooks/useWebSocket';

function MessagingPage() {
  const { ws, isConnected } = useWebSocket();
  
  // ws is the WebSocket client instance
  // isConnected is true when connected
}
```

### 2. Send a Message

```javascript
async function sendMessage() {
  try {
    const result = await ws.sendMessage(conversationId, 'Hello!');
    console.log('Message sent:', result.messageId);
  } catch (error) {
    console.error('Failed to send:', error);
  }
}
```

### 3. Listen for New Messages

```javascript
useEffect(() => {
  if (!ws) return;
  
  const handleNewMessage = (data) => {
    console.log('New message:', data);
    setMessages(prev => [...prev, data]);
  };
  
  ws.on('newMessage', handleNewMessage);
  
  return () => {
    ws.off('newMessage', handleNewMessage);
  };
}, [ws]);
```

### 4. Send Typing Indicator

```javascript
function handleTyping(e) {
  setNewMessage(e.target.value);
  ws.sendTyping(conversationId, e.target.value.length > 0);
}
```

### 5. Listen for Typing Indicators

```javascript
useEffect(() => {
  if (!ws) return;
  
  ws.on('typing', (data) => {
    if (data.isTyping) {
      setTypingUsers(prev => new Set(prev).add(data.userId));
    } else {
      setTypingUsers(prev => {
        const next = new Set(prev);
        next.delete(data.userId);
        return next;
      });
    }
  });
}, [ws]);
```

---

## Deployment Commands

### 1. Deploy Lambda Functions

```bash
# Deploy all WebSocket handlers
cd deploy

./deploy_websocket_send_message.sh
./deploy_websocket_get_messages.sh
./deploy_websocket_get_conversations.sh
./deploy_websocket_mark_read.sh
./deploy_websocket_typing.sh
```

### 2. Setup WebSocket API Gateway

```bash
# Create WebSocket API
aws apigatewayv2 create-api \
  --name quickfix-websocket \
  --protocol-type WEBSOCKET \
  --route-selection-expression '$request.body.action' \
  --region us-east-2

# Configure routes
./setup_websocket_routes.sh

# Deploy to prod stage
aws apigatewayv2 create-deployment \
  --api-id {api-id} \
  --stage-name prod \
  --region us-east-2
```

### 3. Test WebSocket Connection

```bash
# Install wscat for testing
npm install -g wscat

# Connect to WebSocket
wscat -c "wss://{api-id}.execute-api.us-east-2.amazonaws.com/prod?token={jwt-token}"

# Send a message
{"action":"sendMessage","data":{"conversationId":"uuid","text":"Hello!"}}

# Send ping
{"action":"ping"}
```

---

## Testing Checklist

### Manual Testing

- [ ] Connect to WebSocket with valid JWT
- [ ] Send a message
- [ ] Receive a message in real-time
- [ ] Typing indicators work
- [ ] Read receipts work
- [ ] Reconnection after disconnect
- [ ] Offline message queue

### Load Testing

- [ ] 100 concurrent connections
- [ ] 1000 concurrent connections
- [ ] 10,000 messages per minute
- [ ] Connection churn test

### Security Testing

- [ ] JWT validation
- [ ] Authorization checks
- [ ] Input sanitization
- [ ] Rate limiting
- [ ] Connection limits

---

## Monitoring

### CloudWatch Metrics to Watch

- `WebSocketConnectionCount` - Active connections
- `MessageDeliveryRate` - Messages per second
- `LambdaInvocations` - Handler invocations
- `LambdaErrors` - Error rate
- `LambdaDuration` - Latency (p50, p95, p99)
- `DynamoDBThrottling` - Database throttling

### CloudWatch Alarms

```bash
# Create alarm for high error rate
aws cloudwatch put-metric-alarm \
  --alarm-name websocket-high-error-rate \
  --metric-name Errors \
  --namespace AWS/Lambda \
  --statistic Sum \
  --period 300 \
  --threshold 10 \
  --comparison-operator GreaterThanThreshold
```

---

## Troubleshooting

### Connection Issues

**Problem:** WebSocket connection fails

**Solutions:**
1. Check JWT token is valid and not expired
2. Verify WebSocket URL is correct
3. Check CORS settings
4. Review CloudWatch logs for connection handler

### Message Not Delivered

**Problem:** Message sent but not received

**Solutions:**
1. Check recipient has active WebSocket connection
2. Verify conversation membership
3. Check DynamoDB for message record
4. Review Lambda logs for errors

### High Latency

**Problem:** Messages take > 1 second to deliver

**Solutions:**
1. Check Lambda cold starts
2. Optimize DynamoDB queries
3. Review network latency
4. Check Lambda memory allocation

---

## Cost Optimization

### Tips to Reduce Costs

1. **Implement connection pooling** - Reuse connections
2. **Use Lambda reserved concurrency** - Avoid cold starts
3. **Optimize DynamoDB queries** - Use indexes efficiently
4. **Implement message batching** - Send multiple messages together
5. **Set appropriate TTL** - Clean up old connections

### Expected Costs (1000 users)

- WebSocket API: ~$30/month
- Lambda: ~$15/month
- DynamoDB: ~$20/month
- **Total: ~$65/month**

---

## Migration Strategy

### Phase 1: Parallel Run (Week 1-2)
- Deploy WebSocket alongside HTTP API
- Test with internal users
- Keep HTTP as fallback

### Phase 2: Gradual Rollout (Week 3-4)
- Enable WebSocket for 10% of users
- Monitor metrics and errors
- Gradually increase to 100%

### Phase 3: Deprecation (Week 5+)
- Add deprecation warnings to HTTP API
- Monitor usage metrics
- Remove HTTP endpoints after 6 months

---

## Rollback Plan

### Immediate Rollback (< 1 hour)

```javascript
// In frontend config
const USE_WEBSOCKET = false; // Disable WebSocket

// Frontend automatically falls back to HTTP polling
```

### Full Rollback

1. Revert frontend code
2. Disable WebSocket API Gateway
3. Keep HTTP API as primary
4. Conduct post-mortem

---

## Key Benefits

✅ **Real-time messaging** - Instant delivery (< 500ms)  
✅ **Typing indicators** - See when someone is typing  
✅ **Read receipts** - Know when messages are read  
✅ **Lower costs** - 62% cost reduction  
✅ **Better UX** - No polling delays  
✅ **Scalability** - Handle 10,000+ concurrent users  

---

## Resources

- **Full Migration Plan:** `docs/WEBSOCKET_MESSAGING_MIGRATION_PLAN.md`
- **Current HTTP API:** `docs/FRONTEND_MESSAGING_API.md`
- **DynamoDB Guide:** `docs/DYNAMODB_MESSAGES_GUIDE.md`
- **WebSocket RFC:** https://tools.ietf.org/html/rfc6455
- **AWS WebSocket API:** https://docs.aws.amazon.com/apigateway/latest/developerguide/apigateway-websocket-api.html

---

**Last Updated:** February 15, 2026  
**Status:** Ready for Implementation
