# WebSocket Messaging Migration Plan

## Executive Summary

This document outlines the migration plan from HTTP-based polling to WebSocket-based real-time messaging for the QuickFix application.

**Current State:** HTTP REST API with 5 endpoints (polling required for real-time updates)  
**Target State:** WebSocket API with real-time bidirectional communication  
**Migration Strategy:** Phased approach with backward compatibility

---

## Table of Contents

1. [Current Architecture Analysis](#current-architecture-analysis)
2. [Target WebSocket Architecture](#target-websocket-architecture)
3. [Migration Phases](#migration-phases)
4. [Implementation Details](#implementation-details)
5. [Testing Strategy](#testing-strategy)
6. [Deployment Plan](#deployment-plan)
7. [Rollback Strategy](#rollback-strategy)

---

## 1. Current Architecture Analysis

### Existing HTTP API Endpoints

**Base URL:** `https://kfvf20j7j9.execute-api.us-east-2.amazonaws.com/prod`

| Endpoint | Method | Purpose | Lambda |
|----------|--------|---------|--------|
| `/messages/conversations` | POST | Create conversation | `create_conversation` |
| `/messages/conversations` | GET | List conversations | `list_conversations` |
| `/messages` | POST | Send message | `send_message` |
| `/messages/{conversationId}` | GET | List messages | `list_messages` |
| `/messages/conversations/{conversationId}/read` | PUT | Mark as read | `mark_conversation_read` |

### DynamoDB Tables

1. **quickfix_conversations**
   - Partition Key: `userId` (String)
   - Sort Key: `conversationId` (String)
   - Attributes: `otherUserId`, `otherUserName`, `otherUserType`, `jobId`, `jobTitle`, `lastMessageAt`, `lastMessagePreview`, `unreadCount`, `createdAt`

2. **quickfix_messages**
   - Partition Key: `conversation_id` (String)
   - Sort Key: `ts` (Number - timestamp)
   - Attributes: `senderId`, `senderName`, `senderType`, `text`, `attachments`, `readBy`, `createdAt`

3. **quickfix-ws-connections** (Already exists!)
   - Partition Key: `userId` (String)
   - Sort Key: `connectionId` (String)
   - GSI1: `connectionId` (for reverse lookup)
   - Attributes: `connectedAt`, `ttl`, `role`, `stage`

### Existing WebSocket Infrastructure

✅ **Already Implemented:**

- WebSocket connection handler (`lambda/websocket/connect/handler.py`)
- WebSocket disconnect handler (`lambda/websocket/disconnect/handler.py`)
- WebSocket ping/pong handler (`lambda/websocket/ping/handler.py`)
- Connection tracking table (`quickfix-ws-connections`)
- Notification service (`src/utils/ws_notification_service.py`)

### Current Limitations

❌ **Problems with HTTP Polling:**
- High latency (5-30 second delays)
- Increased AWS costs (frequent API calls)
- Poor user experience (messages don't appear instantly)
- Battery drain on mobile devices
- Scalability issues with many concurrent users
- No typing indicators or presence detection

---

## 2. Target WebSocket Architecture

### WebSocket API Structure

**WebSocket URL:** `wss://{api-id}.execute-api.us-east-2.amazonaws.com/prod`

### Message Flow

```
Client                    API Gateway WS              Lambda                  DynamoDB
  |                            |                         |                        |
  |------ Connect + JWT ------>|                         |                        |
  |                            |---- $connect --------->|                        |
  |                            |                         |--- Store connection -->|
  |<----- Connected ----------|                         |                        |
  |                            |                         |                        |
  |-- Send Message (action) -->|                         |                        |
  |                            |---- sendMessage ------>|                        |
  |                            |                         |--- Save message ------>|
  |                            |                         |--- Get recipient conn->|
  |                            |<--- Post to connection-|                        |
  |<--- Receive Message -------|                         |                        |
  |                            |                         |                        |
  |-- Typing Indicator ------->|                         |                        |
  |                            |---- typing ----------->|                        |
  |                            |<--- Notify recipient --|                        |
  |<--- Typing Event ----------|                         |                        |
```

### WebSocket Routes

| Route | Purpose | Lambda Handler |
|-------|---------|----------------|
| `$connect` | Establish connection | `websocket/connect` (exists) |
| `$disconnect` | Clean up connection | `websocket/disconnect` (exists) |
| `$default` | Handle unknown routes | `websocket/default` (new) |
| `ping` | Keep-alive | `websocket/ping` (exists) |
| `sendMessage` | Send a message | `websocket/send_message` (new) |
| `getMessages` | Fetch message history | `websocket/get_messages` (new) |
| `getConversations` | Fetch conversations | `websocket/get_conversations` (new) |
| `markRead` | Mark conversation as read | `websocket/mark_read` (new) |
| `typing` | Typing indicator | `websocket/typing` (new) |

### Message Protocol

All WebSocket messages use JSON format:

**Client → Server (Request):**
```json
{
  "action": "sendMessage",
  "data": {
    "conversationId": "uuid",
    "text": "Hello!"
  },
  "requestId": "client-generated-uuid"
}
```

**Server → Client (Response):**
```json
{
  "type": "response",
  "action": "sendMessage",
  "requestId": "client-generated-uuid",
  "success": true,
  "data": {
    "messageId": 1704384000000,
    "timestamp": 1704384000000
  }
}
```

**Server → Client (Push Event):**
```json
{
  "type": "event",
  "event": "newMessage",
  "data": {
    "conversationId": "uuid",
    "messageId": 1704384000000,
    "senderId": "2",
    "senderName": "John Doe",
    "text": "Hello!",
    "timestamp": 1704384000000
  }
}
```

---

## 3. Migration Phases

### Phase 1: WebSocket Infrastructure Setup (Week 1)
**Goal:** Set up WebSocket API Gateway and core handlers

**Tasks:**
1. Create WebSocket API Gateway (if not exists)
2. Configure routes and integrations
3. Implement core message handlers
4. Set up CloudWatch logging
5. Create deployment scripts

**Deliverables:**
- WebSocket API Gateway configured
- 5 new Lambda functions deployed
- Infrastructure as code scripts

### Phase 2: Backend Implementation (Week 2)
**Goal:** Implement all WebSocket message handlers

**Tasks:**
1. Implement `sendMessage` handler
2. Implement `getMessages` handler
3. Implement `getConversations` handler
4. Implement `markRead` handler
5. Implement `typing` handler
6. Add real-time notification logic
7. Update existing HTTP handlers to send WebSocket notifications

**Deliverables:**
- All WebSocket handlers functional
- Real-time notifications working
- HTTP API still functional (backward compatibility)

### Phase 3: Frontend Migration (Week 3)
**Goal:** Update React frontend to use WebSocket

**Tasks:**
1. Create WebSocket connection manager
2. Implement reconnection logic
3. Update messaging components
4. Add typing indicators
5. Add presence detection
6. Implement optimistic UI updates
7. Add offline message queue

**Deliverables:**
- React WebSocket client library
- Updated messaging UI components
- Feature parity with HTTP version

### Phase 4: Testing & Optimization (Week 4)
**Goal:** Comprehensive testing and performance optimization

**Tasks:**
1. Unit tests for all handlers
2. Integration tests
3. Load testing (1000+ concurrent connections)
4. Latency optimization
5. Error handling improvements
6. Security audit

**Deliverables:**
- Test suite with 90%+ coverage
- Performance benchmarks
- Security audit report

### Phase 5: Production Rollout (Week 5)
**Goal:** Gradual rollout to production users

**Tasks:**
1. Deploy to staging environment
2. Beta testing with 10% of users
3. Monitor metrics and errors
4. Gradual rollout to 50%, then 100%
5. Deprecate HTTP polling (keep endpoints for fallback)

**Deliverables:**
- Production deployment
- Monitoring dashboards
- Incident response plan

---

## 4. Implementation Details

### 4.1 New Lambda Functions

#### A. `websocket/send_message/handler.py`

**Purpose:** Handle incoming messages from WebSocket clients

**Input:**
```json
{
  "action": "sendMessage",
  "data": {
    "conversationId": "uuid",
    "text": "Hello!"
  }
}
```

**Logic:**
1. Extract user ID from connection
2. Validate conversation membership
3. Save message to DynamoDB
4. Update conversation metadata
5. Get recipient's WebSocket connections
6. Push message to recipient in real-time
7. Return success response to sender

**Output:**
```json
{
  "type": "response",
  "success": true,
  "data": {
    "messageId": 1704384000000
  }
}
```


#### B. `websocket/get_messages/handler.py`

**Purpose:** Fetch message history via WebSocket

**Input:**
```json
{
  "action": "getMessages",
  "data": {
    "conversationId": "uuid",
    "limit": 50,
    "before": 1704384000000
  }
}
```

**Logic:**
1. Validate conversation access
2. Query messages from DynamoDB
3. Return paginated results

**Output:**
```json
{
  "type": "response",
  "success": true,
  "data": {
    "messages": [...],
    "hasMore": false
  }
}
```

#### C. `websocket/get_conversations/handler.py`

**Purpose:** Fetch conversation list via WebSocket

**Input:**
```json
{
  "action": "getConversations",
  "data": {
    "limit": 20
  }
}
```

**Output:**
```json
{
  "type": "response",
  "success": true,
  "data": {
    "conversations": [...],
    "total": 5
  }
}
```

#### D. `websocket/mark_read/handler.py`

**Purpose:** Mark conversation as read

**Input:**
```json
{
  "action": "markRead",
  "data": {
    "conversationId": "uuid"
  }
}
```

**Logic:**
1. Reset unread count to 0
2. Notify sender that message was read (read receipts)

#### E. `websocket/typing/handler.py`

**Purpose:** Broadcast typing indicators

**Input:**
```json
{
  "action": "typing",
  "data": {
    "conversationId": "uuid",
    "isTyping": true
  }
}
```

**Logic:**
1. Get recipient connection
2. Push typing event to recipient
3. No database storage (ephemeral)

**Output to Recipient:**
```json
{
  "type": "event",
  "event": "typing",
  "data": {
    "conversationId": "uuid",
    "userId": "2",
    "userName": "John Doe",
    "isTyping": true
  }
}
```

### 4.2 Enhanced Notification Service

Update `src/utils/ws_notification_service.py` to support message types:

```python
class NotificationService:
    def notify_new_message(self, recipient_id: str, message_data: dict):
        """Push new message to recipient"""
        payload = {
            "type": "event",
            "event": "newMessage",
            "data": message_data
        }
        self.notify_users([recipient_id], payload)
    
    def notify_typing(self, recipient_id: str, sender_id: str, sender_name: str, conversation_id: str, is_typing: bool):
        """Push typing indicator"""
        payload = {
            "type": "event",
            "event": "typing",
            "data": {
                "conversationId": conversation_id,
                "userId": sender_id,
                "userName": sender_name,
                "isTyping": is_typing
            }
        }
        self.notify_users([recipient_id], payload)
    
    def notify_read_receipt(self, recipient_id: str, conversation_id: str, reader_id: str):
        """Push read receipt"""
        payload = {
            "type": "event",
            "event": "messageRead",
            "data": {
                "conversationId": conversation_id,
                "readBy": reader_id,
                "timestamp": int(time.time() * 1000)
            }
        }
        self.notify_users([recipient_id], payload)
```

### 4.3 Frontend WebSocket Client

Create `src/services/websocket.js`:

```javascript
class WebSocketClient {
  constructor(token) {
    this.token = token;
    this.ws = null;
    this.listeners = new Map();
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 5;
    this.reconnectDelay = 1000;
    this.pendingRequests = new Map();
  }

  connect() {
    const wsUrl = `wss://kfvf20j7j9.execute-api.us-east-2.amazonaws.com/prod?token=${this.token}`;
    
    this.ws = new WebSocket(wsUrl);
    
    this.ws.onopen = () => {
      console.log('WebSocket connected');
      this.reconnectAttempts = 0;
      this.emit('connected');
      this.startPingInterval();
    };
    
    this.ws.onmessage = (event) => {
      const message = JSON.parse(event.data);
      this.handleMessage(message);
    };
    
    this.ws.onerror = (error) => {
      console.error('WebSocket error:', error);
      this.emit('error', error);
    };
    
    this.ws.onclose = () => {
      console.log('WebSocket disconnected');
      this.emit('disconnected');
      this.stopPingInterval();
      this.attemptReconnect();
    };
  }

  handleMessage(message) {
    if (message.type === 'response') {
      // Handle request response
      const callback = this.pendingRequests.get(message.requestId);
      if (callback) {
        callback(message);
        this.pendingRequests.delete(message.requestId);
      }
    } else if (message.type === 'event') {
      // Handle push event
      this.emit(message.event, message.data);
    }
  }

  send(action, data) {
    return new Promise((resolve, reject) => {
      const requestId = this.generateRequestId();
      const message = {
        action,
        data,
        requestId
      };
      
      this.pendingRequests.set(requestId, (response) => {
        if (response.success) {
          resolve(response.data);
        } else {
          reject(new Error(response.error || 'Request failed'));
        }
      });
      
      this.ws.send(JSON.stringify(message));
      
      // Timeout after 30 seconds
      setTimeout(() => {
        if (this.pendingRequests.has(requestId)) {
          this.pendingRequests.delete(requestId);
          reject(new Error('Request timeout'));
        }
      }, 30000);
    });
  }

  sendMessage(conversationId, text) {
    return this.send('sendMessage', { conversationId, text });
  }

  getMessages(conversationId, limit = 50, before = null) {
    return this.send('getMessages', { conversationId, limit, before });
  }

  getConversations(limit = 20) {
    return this.send('getConversations', { limit });
  }

  markRead(conversationId) {
    return this.send('markRead', { conversationId });
  }

  sendTyping(conversationId, isTyping) {
    // Fire and forget (no response needed)
    const message = {
      action: 'typing',
      data: { conversationId, isTyping }
    };
    this.ws.send(JSON.stringify(message));
  }

  on(event, callback) {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, []);
    }
    this.listeners.get(event).push(callback);
  }

  off(event, callback) {
    if (this.listeners.has(event)) {
      const callbacks = this.listeners.get(event);
      const index = callbacks.indexOf(callback);
      if (index > -1) {
        callbacks.splice(index, 1);
      }
    }
  }

  emit(event, data) {
    if (this.listeners.has(event)) {
      this.listeners.get(event).forEach(callback => callback(data));
    }
  }

  startPingInterval() {
    this.pingInterval = setInterval(() => {
      if (this.ws.readyState === WebSocket.OPEN) {
        this.ws.send(JSON.stringify({ action: 'ping' }));
      }
    }, 30000); // Ping every 30 seconds
  }

  stopPingInterval() {
    if (this.pingInterval) {
      clearInterval(this.pingInterval);
    }
  }

  attemptReconnect() {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1);
      console.log(`Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts})`);
      setTimeout(() => this.connect(), delay);
    } else {
      console.error('Max reconnection attempts reached');
      this.emit('reconnectFailed');
    }
  }

  disconnect() {
    if (this.ws) {
      this.ws.close();
    }
  }

  generateRequestId() {
    return `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
  }
}

export default WebSocketClient;
```

### 4.4 React Hook for WebSocket

Create `src/hooks/useWebSocket.js`:

```javascript
import { useEffect, useRef, useState } from 'react';
import { useAuth } from 'react-oidc-context';
import WebSocketClient from '../services/websocket';

export function useWebSocket() {
  const auth = useAuth();
  const [isConnected, setIsConnected] = useState(false);
  const wsRef = useRef(null);

  useEffect(() => {
    if (auth.user?.id_token) {
      const ws = new WebSocketClient(auth.user.id_token);
      
      ws.on('connected', () => setIsConnected(true));
      ws.on('disconnected', () => setIsConnected(false));
      
      ws.connect();
      wsRef.current = ws;

      return () => {
        ws.disconnect();
      };
    }
  }, [auth.user?.id_token]);

  return {
    ws: wsRef.current,
    isConnected
  };
}
```

### 4.5 Updated React Messaging Component

```javascript
import React, { useState, useEffect } from 'react';
import { useWebSocket } from '../hooks/useWebSocket';

function MessagingPage() {
  const { ws, isConnected } = useWebSocket();
  const [conversations, setConversations] = useState([]);
  const [selectedConversation, setSelectedConversation] = useState(null);
  const [messages, setMessages] = useState([]);
  const [newMessage, setNewMessage] = useState('');
  const [typingUsers, setTypingUsers] = useState(new Set());

  useEffect(() => {
    if (!ws || !isConnected) return;

    // Load conversations
    ws.getConversations().then(data => {
      setConversations(data.conversations);
    });

    // Listen for new messages
    ws.on('newMessage', (data) => {
      if (selectedConversation?.conversationId === data.conversationId) {
        setMessages(prev => [...prev, data]);
      }
      // Update conversation preview
      setConversations(prev => 
        prev.map(conv => 
          conv.conversationId === data.conversationId
            ? { ...conv, lastMessage: { preview: data.text, timestamp: data.timestamp } }
            : conv
        )
      );
    });

    // Listen for typing indicators
    ws.on('typing', (data) => {
      if (selectedConversation?.conversationId === data.conversationId) {
        if (data.isTyping) {
          setTypingUsers(prev => new Set(prev).add(data.userId));
        } else {
          setTypingUsers(prev => {
            const next = new Set(prev);
            next.delete(data.userId);
            return next;
          });
        }
      }
    });

    // Listen for read receipts
    ws.on('messageRead', (data) => {
      // Update UI to show message was read
      console.log('Message read:', data);
    });

  }, [ws, isConnected, selectedConversation]);

  async function selectConversation(conversation) {
    setSelectedConversation(conversation);
    const data = await ws.getMessages(conversation.conversationId);
    setMessages(data.messages.reverse());
    await ws.markRead(conversation.conversationId);
  }

  async function handleSendMessage(e) {
    e.preventDefault();
    if (!newMessage.trim() || !selectedConversation) return;

    try {
      const result = await ws.sendMessage(selectedConversation.conversationId, newMessage);
      
      // Add message to UI (optimistic update)
      const sentMessage = {
        messageId: result.messageId,
        text: newMessage,
        senderId: 'me',
        timestamp: result.timestamp
      };
      setMessages(prev => [...prev, sentMessage]);
      setNewMessage('');
    } catch (error) {
      console.error('Failed to send message:', error);
      alert('Failed to send message');
    }
  }

  function handleTyping(e) {
    setNewMessage(e.target.value);
    
    // Send typing indicator
    if (selectedConversation) {
      ws.sendTyping(selectedConversation.conversationId, e.target.value.length > 0);
    }
  }

  return (
    <div className="messaging-container">
      <div className="connection-status">
        {isConnected ? '🟢 Connected' : '🔴 Disconnected'}
      </div>
      
      {/* Conversations list */}
      <div className="conversations-sidebar">
        {conversations.map(conv => (
          <div key={conv.conversationId} onClick={() => selectConversation(conv)}>
            {conv.otherUser.name}
          </div>
        ))}
      </div>

      {/* Messages */}
      <div className="messages-panel">
        {messages.map(msg => (
          <div key={msg.messageId}>{msg.text}</div>
        ))}
        
        {typingUsers.size > 0 && (
          <div className="typing-indicator">Someone is typing...</div>
        )}

        <form onSubmit={handleSendMessage}>
          <input
            type="text"
            value={newMessage}
            onChange={handleTyping}
            placeholder="Type a message..."
          />
          <button type="submit">Send</button>
        </form>
      </div>
    </div>
  );
}

export default MessagingPage;
```

---

## 5. Testing Strategy

### 5.1 Unit Tests

**Lambda Handlers:**
- Test each WebSocket handler with mock events
- Test error handling (invalid input, unauthorized access)
- Test DynamoDB operations

**Frontend:**
- Test WebSocket client connection/disconnection
- Test message sending/receiving
- Test reconnection logic
- Test typing indicators

### 5.2 Integration Tests

**End-to-End Scenarios:**
1. User connects to WebSocket
2. User sends message
3. Recipient receives message in real-time
4. User disconnects and reconnects
5. User receives offline messages
6. Typing indicators work correctly
7. Read receipts work correctly

### 5.3 Load Testing

**Tools:** Artillery, AWS Lambda load testing

**Scenarios:**
- 100 concurrent connections
- 1000 concurrent connections
- 10,000 messages per minute
- Connection churn (frequent connect/disconnect)

**Metrics to Monitor:**
- Connection establishment time
- Message delivery latency (p50, p95, p99)
- Lambda cold start times
- DynamoDB throttling
- WebSocket connection errors

### 5.4 Security Testing

**Checklist:**
- JWT token validation
- Authorization checks (conversation membership)
- Input sanitization (XSS prevention)
- Rate limiting
- Connection limits per user
- Message size limits

---

## 6. Deployment Plan

### 6.1 Infrastructure Setup

**Step 1: Create WebSocket API Gateway**
```bash
aws apigatewayv2 create-api \
  --name quickfix-websocket \
  --protocol-type WEBSOCKET \
  --route-selection-expression '$request.body.action' \
  --region us-east-2
```

**Step 2: Deploy Lambda Functions**
```bash
# Deploy all WebSocket handlers
./deploy/deploy_websocket_send_message.sh
./deploy/deploy_websocket_get_messages.sh
./deploy/deploy_websocket_get_conversations.sh
./deploy/deploy_websocket_mark_read.sh
./deploy/deploy_websocket_typing.sh
```

**Step 3: Configure Routes**
```bash
# Create routes for each action
./deploy/setup_websocket_routes.sh
```

**Step 4: Deploy API Gateway Stage**
```bash
aws apigatewayv2 create-deployment \
  --api-id {api-id} \
  --stage-name prod \
  --region us-east-2
```

### 6.2 Gradual Rollout

**Phase 1: Internal Testing (Week 1)**
- Deploy to staging environment
- Test with development team
- Fix critical bugs

**Phase 2: Beta Testing (Week 2)**
- Enable for 10% of users (feature flag)
- Monitor error rates and latency
- Collect user feedback

**Phase 3: Gradual Rollout (Week 3-4)**
- 25% of users
- 50% of users
- 75% of users
- 100% of users

**Phase 4: HTTP API Deprecation (Week 5+)**
- Keep HTTP endpoints as fallback
- Add deprecation warnings
- Monitor usage metrics
- Eventually remove HTTP endpoints (6 months later)

### 6.3 Monitoring & Alerts

**CloudWatch Metrics:**
- WebSocket connection count
- Message delivery rate
- Lambda invocation count
- Lambda error rate
- Lambda duration (p50, p95, p99)
- DynamoDB read/write capacity

**CloudWatch Alarms:**
- Error rate > 1%
- Lambda duration > 3 seconds
- DynamoDB throttling
- WebSocket connection failures > 5%

**CloudWatch Logs:**
- All Lambda function logs
- API Gateway access logs
- Error logs with stack traces

---

## 7. Rollback Strategy

### 7.1 Immediate Rollback (< 1 hour)

**If critical issues occur:**

1. **Disable WebSocket in Frontend**
   ```javascript
   // Feature flag in config
   const USE_WEBSOCKET = false;
   ```

2. **Revert to HTTP Polling**
   - Frontend automatically falls back to HTTP API
   - No backend changes needed

3. **Monitor Recovery**
   - Verify HTTP endpoints working
   - Check error rates return to normal

### 7.2 Partial Rollback

**If issues affect specific features:**

1. Disable problematic WebSocket routes
2. Keep working routes active
3. Fall back to HTTP for affected features

### 7.3 Full Rollback (> 1 hour)

**If fundamental architecture issues:**

1. Revert frontend code to previous version
2. Disable WebSocket API Gateway
3. Keep HTTP API as primary
4. Conduct post-mortem analysis
5. Fix issues before retry

---

## 8. Cost Analysis

### Current HTTP API Costs (Estimated)

**Assumptions:**
- 1000 active users
- 50 messages per user per day
- Polling every 5 seconds when app is open
- Average 2 hours app usage per day

**Monthly Costs:**
- API Gateway: ~$100 (14.4M requests)
- Lambda: ~$50 (14.4M invocations)
- DynamoDB: ~$20 (read/write operations)
- **Total: ~$170/month**

### WebSocket API Costs (Estimated)

**Assumptions:**
- 1000 active users
- 50 messages per user per day
- Average 2 hours connection time per day

**Monthly Costs:**
- API Gateway: ~$30 (connection minutes + messages)
- Lambda: ~$15 (only on actual messages)
- DynamoDB: ~$20 (same as before)
- **Total: ~$65/month**

**Savings: ~$105/month (62% reduction)**

---

## 9. Success Metrics

### Performance Metrics

- Message delivery latency < 500ms (p95)
- Connection establishment < 2 seconds
- Reconnection time < 5 seconds
- 99.9% message delivery success rate

### User Experience Metrics

- Real-time message delivery (no polling delay)
- Typing indicators working
- Read receipts working
- Offline message queue working

### Business Metrics

- 62% cost reduction
- Improved user engagement
- Reduced support tickets related to messaging
- Higher user satisfaction scores

---

## 10. Timeline Summary

| Week | Phase | Key Deliverables |
|------|-------|------------------|
| 1 | Infrastructure Setup | WebSocket API Gateway, core handlers |
| 2 | Backend Implementation | All WebSocket handlers, notifications |
| 3 | Frontend Migration | React WebSocket client, updated UI |
| 4 | Testing & Optimization | Test suite, load testing, security audit |
| 5 | Production Rollout | Gradual rollout, monitoring, deprecation |

**Total Duration: 5 weeks**

---

## 11. Next Steps

1. **Review and approve this plan** with stakeholders
2. **Assign team members** to each phase
3. **Set up project tracking** (Jira, GitHub Projects)
4. **Create detailed technical specs** for each Lambda function
5. **Begin Phase 1: Infrastructure Setup**

---

## Appendix A: File Structure

```
lambda/
├── websocket/
│   ├── connect/              # ✅ Exists
│   ├── disconnect/           # ✅ Exists
│   ├── ping/                 # ✅ Exists
│   ├── send_message/         # 🆕 New
│   ├── get_messages/         # 🆕 New
│   ├── get_conversations/    # 🆕 New
│   ├── mark_read/            # 🆕 New
│   └── typing/               # 🆕 New

src/
├── utils/
│   └── ws_notification_service.py  # ✅ Exists (needs enhancement)

deploy/
├── deploy_websocket_send_message.sh      # 🆕 New
├── deploy_websocket_get_messages.sh      # 🆕 New
├── deploy_websocket_get_conversations.sh # 🆕 New
├── deploy_websocket_mark_read.sh         # 🆕 New
├── deploy_websocket_typing.sh            # 🆕 New
└── setup_websocket_routes.sh             # 🆕 New

frontend/src/
├── services/
│   └── websocket.js          # 🆕 New
├── hooks/
│   └── useWebSocket.js       # 🆕 New
└── components/
    └── MessagingPage.jsx     # 🔄 Update
```

---

## Appendix B: Environment Variables

**Lambda Environment Variables:**
```bash
WS_CONNECTIONS_TABLE=quickfix-ws-connections
WS_MANAGEMENT_ENDPOINT=https://{api-id}.execute-api.us-east-2.amazonaws.com/prod
COGNITO_USERPOOL_ID=us-east-2_45z5OMePi
COGNITO_CLIENT_ID=p2u5qdegml3hp60n6ohu52n2b
COGNITO_REGION=us-east-2
MYSQL_HOST=quickfix-mysql.cno624c2aarh.us-east-2.rds.amazonaws.com
MYSQL_USER=admin
MYSQL_PASSWORD=QuickFix123!
MYSQL_DATABASE=quickfix
```

---

## Appendix C: API Comparison

| Feature | HTTP API | WebSocket API |
|---------|----------|---------------|
| Real-time messages | ❌ (polling) | ✅ Instant |
| Typing indicators | ❌ | ✅ |
| Read receipts | ❌ | ✅ |
| Presence detection | ❌ | ✅ |
| Latency | 5-30 seconds | < 500ms |
| Battery usage | High | Low |
| Cost | $170/month | $65/month |
| Scalability | Limited | Excellent |
| Offline support | ❌ | ✅ (with queue) |

---

**Document Version:** 1.0  
**Last Updated:** February 15, 2026  
**Author:** QuickFix Development Team  
**Status:** Draft - Pending Approval
