# QuickFix Messaging & Notifications API - Frontend Integration Guide

## Overview

This guide provides everything your frontend team needs to integrate the QuickFix messaging and notification system.

**Base URL**: `https://kfvf20j7j9.execute-api.us-east-2.amazonaws.com/prod`

**Authentication**: All endpoints require JWT token in Authorization header.

---

## Table of Contents

1. [Authentication](#authentication)
2. [Messaging APIs](#messaging-apis)
3. [Notification APIs](#notification-apis)
4. [Common Patterns](#common-patterns)
5. [Error Handling](#error-handling)
6. [Example Flows](#example-flows)

---

## Authentication

All API requests require a JWT token from AWS Cognito.

### Headers Required:
```javascript
{
  "Authorization": "Bearer YOUR_JWT_TOKEN",
  "Content-Type": "application/json"  // For POST/PUT requests
}
```

### Getting JWT Token:
```javascript
// From your auth context (react-oidc-context)
const token = auth.user?.id_token;
```

---

## Messaging APIs

### 1. Create Conversation

**Endpoint**: `POST /messages/conversations`

**Purpose**: Start a new conversation with another user (or get existing one)

**Request**:
```javascript
POST /messages/conversations
Authorization: Bearer {token}
Content-Type: application/json

{
  "otherUserId": "SP-ad86b044-9f9b-49b6-a53d-d3847afabe3c",  // Required
  "jobId": "1001"  // Optional - link to a job
}
```

**Response** (201 Created):
```json
{
  "conversationId": "a103818f-ed02-4f47-9dd3-def9e2a5bfcd",
  "otherUser": {
    "userId": "SP-ad86b044-9f9b-49b6-a53d-d3847afabe3c",
    "name": "walter",
    "type": "provider"
  },
  "jobId": "1001",
  "jobTitle": "Fix Kitchen Sink Leak",
  "createdAt": 1767576511608
}
```

**Frontend Usage**:
```javascript
async function createConversation(otherUserId, jobId = null) {
  const response = await fetch(`${BASE_URL}/messages/conversations`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${auth.user.id_token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ otherUserId, jobId })
  });
  
  if (!response.ok) throw new Error('Failed to create conversation');
  return await response.json();
}
```

---

### 2. List Conversations

**Endpoint**: `GET /messages/conversations`

**Purpose**: Get user's inbox (all conversations)

**Request**:
```javascript
GET /messages/conversations?limit=20
Authorization: Bearer {token}
```

**Query Parameters**:
- `limit` (optional): Number of conversations to return (default: 20, max: 50)

**Response** (200 OK):
```json
{
  "conversations": [
    {
      "conversationId": "a103818f-ed02-4f47-9dd3-def9e2a5bfcd",
      "otherUser": {
        "userId": "SP-ad86b044-9f9b-49b6-a53d-d3847afabe3c",
        "name": "walter",
        "type": "provider"
      },
      "jobId": "1001",
      "jobTitle": "Fix Kitchen Sink Leak",
      "lastMessage": {
        "preview": "Hello, when can you start?",
        "timestamp": 1767581062206
      },
      "unreadCount": 2,
      "createdAt": 1767576511608
    }
  ],
  "total": 1
}
```

**Frontend Usage**:
```javascript
async function listConversations(limit = 20) {
  const response = await fetch(
    `${BASE_URL}/messages/conversations?limit=${limit}`,
    {
      headers: {
        'Authorization': `Bearer ${auth.user.id_token}`
      }
    }
  );
  
  if (!response.ok) throw new Error('Failed to fetch conversations');
  return await response.json();
}
```

**UI Display**:
```jsx
{conversations.map(conv => (
  <ConversationItem key={conv.conversationId}>
    <Avatar name={conv.otherUser.name} />
    <div>
      <h3>{conv.otherUser.name}</h3>
      {conv.jobTitle && <p className="job">{conv.jobTitle}</p>}
      <p className="preview">{conv.lastMessage.preview}</p>
    </div>
    {conv.unreadCount > 0 && (
      <Badge>{conv.unreadCount}</Badge>
    )}
  </ConversationItem>
))}
```

---

### 3. Send Message

**Endpoint**: `POST /messages`

**Purpose**: Send a message in a conversation

**Request**:
```javascript
POST /messages
Authorization: Bearer {token}
Content-Type: application/json

{
  "conversationId": "a103818f-ed02-4f47-9dd3-def9e2a5bfcd",
  "text": "Hello, when can you start?"
}
```

**Response** (201 Created):
```json
{
  "messageId": 1767581062206,
  "conversationId": "a103818f-ed02-4f47-9dd3-def9e2a5bfcd",
  "senderId": "2",
  "senderName": "KunPeng Yang",
  "senderType": "customer",
  "text": "Hello, when can you start?",
  "timestamp": 1767581062206,
  "createdAt": "2026-01-05T02:44:22Z"
}
```

**Frontend Usage**:
```javascript
async function sendMessage(conversationId, text) {
  const response = await fetch(`${BASE_URL}/messages`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${auth.user.id_token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ conversationId, text })
  });
  
  if (!response.ok) throw new Error('Failed to send message');
  return await response.json();
}
```

**UI Pattern**:
```jsx
function MessageInput({ conversationId, onSent }) {
  const [text, setText] = useState('');
  
  const handleSend = async () => {
    if (!text.trim()) return;
    
    const message = await sendMessage(conversationId, text);
    setText('');
    onSent(message);  // Add to message list
  };
  
  return (
    <div className="message-input">
      <input 
        value={text}
        onChange={(e) => setText(e.target.value)}
        onKeyPress={(e) => e.key === 'Enter' && handleSend()}
        placeholder="Type a message..."
      />
      <button onClick={handleSend}>Send</button>
    </div>
  );
}
```

---

### 4. List Messages

**Endpoint**: `GET /messages/{conversationId}`

**Purpose**: Get message history for a conversation

**Request**:
```javascript
GET /messages/a103818f-ed02-4f47-9dd3-def9e2a5bfcd?limit=50
Authorization: Bearer {token}
```

**Query Parameters**:
- `limit` (optional): Number of messages (default: 50, max: 100)
- `before` (optional): Timestamp for pagination (get messages before this time)

**Response** (200 OK):
```json
{
  "messages": [
    {
      "messageId": 1767581062206,
      "senderId": "2",
      "senderName": "KunPeng Yang",
      "senderType": "customer",
      "text": "Hello, when can you start?",
      "timestamp": 1767581062206,
      "readBy": ["2"],
      "createdAt": "2026-01-05T02:44:22Z"
    }
  ],
  "total": 1,
  "hasMore": false
}
```

**Frontend Usage**:
```javascript
async function listMessages(conversationId, limit = 50, before = null) {
  let url = `${BASE_URL}/messages/${conversationId}?limit=${limit}`;
  if (before) url += `&before=${before}`;
  
  const response = await fetch(url, {
    headers: {
      'Authorization': `Bearer ${auth.user.id_token}`
    }
  });
  
  if (!response.ok) throw new Error('Failed to fetch messages');
  return await response.json();
}
```

**Infinite Scroll Pattern**:
```jsx
function MessageList({ conversationId }) {
  const [messages, setMessages] = useState([]);
  const [hasMore, setHasMore] = useState(true);
  
  const loadMore = async () => {
    if (!hasMore) return;
    
    const oldestTimestamp = messages[0]?.timestamp;
    const data = await listMessages(conversationId, 50, oldestTimestamp);
    
    setMessages([...data.messages, ...messages]);
    setHasMore(data.hasMore);
  };
  
  return (
    <div className="message-list">
      {hasMore && <button onClick={loadMore}>Load More</button>}
      {messages.map(msg => (
        <Message key={msg.messageId} message={msg} />
      ))}
    </div>
  );
}
```

---

### 5. Mark Conversation as Read

**Endpoint**: `PUT /messages/conversations/{conversationId}/read`

**Purpose**: Reset unread count when user opens conversation

**Request**:
```javascript
PUT /messages/conversations/a103818f-ed02-4f47-9dd3-def9e2a5bfcd/read
Authorization: Bearer {token}
```

**Response** (200 OK):
```json
{
  "conversationId": "a103818f-ed02-4f47-9dd3-def9e2a5bfcd",
  "unreadCount": 0,
  "message": "Conversation marked as read"
}
```

**Frontend Usage**:
```javascript
async function markConversationRead(conversationId) {
  const response = await fetch(
    `${BASE_URL}/messages/conversations/${conversationId}/read`,
    {
      method: 'PUT',
      headers: {
        'Authorization': `Bearer ${auth.user.id_token}`
      }
    }
  );
  
  if (!response.ok) throw new Error('Failed to mark as read');
  return await response.json();
}
```

**Auto-mark as Read**:
```jsx
useEffect(() => {
  // Mark as read when conversation is opened
  if (conversationId) {
    markConversationRead(conversationId);
  }
}, [conversationId]);
```

---

## Notification APIs

### 6. List Notifications

**Endpoint**: `GET /notifications/my`

**Purpose**: Get user's notifications

**Request**:
```javascript
GET /notifications/my?limit=20
Authorization: Bearer {token}
```

**Query Parameters**:
- `limit` (optional): Number of notifications (default: 20, max: 50)
- `nextToken` (optional): Pagination token from previous response

**Response** (200 OK):
```json
{
  "notifications": [
    {
      "notif_sort": "NOTIF#2026-01-06T00:39:49.241538Z#MSG#1767659987428",
      "type": "NEW_MESSAGE",
      "conversation_id": "a103818f-ed02-4f47-9dd3-def9e2a5bfcd",
      "from_name": "walter",
      "preview": "Hello, when can you start?",
      "created_at": "2026-01-06T00:39:49.241538Z",
      "is_read": false,
      "message_id": 1767659987428
    }
  ],
  "total": 1,
  "nextToken": "eyJ..."  // Only if more results available
}
```

**Frontend Usage**:
```javascript
async function listNotifications(limit = 20, nextToken = null) {
  let url = `${BASE_URL}/notifications/my?limit=${limit}`;
  if (nextToken) url += `&nextToken=${nextToken}`;
  
  const response = await fetch(url, {
    headers: {
      'Authorization': `Bearer ${auth.user.id_token}`
    }
  });
  
  if (!response.ok) throw new Error('Failed to fetch notifications');
  return await response.json();
}
```

---

### 7. Get Unread Count

**Endpoint**: `GET /notifications/unread-count`

**Purpose**: Get count of unread notifications (for badge)

**Request**:
```javascript
GET /notifications/unread-count
Authorization: Bearer {token}
```

**Response** (200 OK):
```json
{
  "unreadCount": 5
}
```

**Frontend Usage**:
```javascript
async function getUnreadCount() {
  const response = await fetch(`${BASE_URL}/notifications/unread-count`, {
    headers: {
      'Authorization': `Bearer ${auth.user.id_token}`
    }
  });
  
  if (!response.ok) throw new Error('Failed to get unread count');
  return await response.json();
}
```

**Badge Display**:
```jsx
function NotificationBell() {
  const [unreadCount, setUnreadCount] = useState(0);
  
  useEffect(() => {
    // Poll every 30 seconds
    const interval = setInterval(async () => {
      const { unreadCount } = await getUnreadCount();
      setUnreadCount(unreadCount);
    }, 30000);
    
    return () => clearInterval(interval);
  }, []);
  
  return (
    <div className="notification-bell">
      <BellIcon />
      {unreadCount > 0 && <Badge>{unreadCount}</Badge>}
    </div>
  );
}
```

---

### 8. Mark Notifications as Read

**Endpoint**: `POST /notifications/mark-read`

**Purpose**: Mark notifications as read

**Request**:
```javascript
POST /notifications/mark-read
Authorization: Bearer {token}
Content-Type: application/json

{
  "items": [
    {"notif_sort": "NOTIF#2026-01-05T10:00:00Z#MSG#1767581062206"},
    {"notif_sort": "NOTIF#2026-01-05T09:55:00Z#MSG#1767580900000"}
  ]
}
```

**Response** (200 OK):
```json
{
  "updated": 2,
  "message": "2 notification(s) marked as read"
}
```

**Frontend Usage**:
```javascript
async function markNotificationsRead(notificationIds) {
  const items = notificationIds.map(id => ({ notif_sort: id }));
  
  const response = await fetch(`${BASE_URL}/notifications/mark-read`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${auth.user.id_token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ items })
  });
  
  if (!response.ok) throw new Error('Failed to mark notifications as read');
  return await response.json();
}
```

**Mark Single Notification**:
```jsx
function NotificationItem({ notification, onRead }) {
  const handleClick = async () => {
    await markNotificationsRead([notification.notif_sort]);
    onRead(notification.notif_sort);
  };
  
  return (
    <div 
      className={notification.is_read ? 'read' : 'unread'}
      onClick={handleClick}
    >
      <p><strong>{notification.from_name}</strong></p>
      <p>{notification.preview}</p>
      <span>{formatDate(notification.created_at)}</span>
    </div>
  );
}
```

---

## Common Patterns

### 1. Complete Messaging Flow

```jsx
function MessagingPage() {
  const [conversations, setConversations] = useState([]);
  const [selectedConv, setSelectedConv] = useState(null);
  const [messages, setMessages] = useState([]);
  
  // Load conversations on mount
  useEffect(() => {
    loadConversations();
  }, []);
  
  // Load messages when conversation selected
  useEffect(() => {
    if (selectedConv) {
      loadMessages(selectedConv.conversationId);
      markConversationRead(selectedConv.conversationId);
    }
  }, [selectedConv]);
  
  const loadConversations = async () => {
    const data = await listConversations();
    setConversations(data.conversations);
  };
  
  const loadMessages = async (convId) => {
    const data = await listMessages(convId);
    setMessages(data.messages);
  };
  
  const handleSendMessage = async (text) => {
    const message = await sendMessage(selectedConv.conversationId, text);
    setMessages([...messages, message]);
  };
  
  return (
    <div className="messaging-page">
      <ConversationList 
        conversations={conversations}
        onSelect={setSelectedConv}
      />
      {selectedConv && (
        <MessageView 
          messages={messages}
          onSend={handleSendMessage}
        />
      )}
    </div>
  );
}
```

### 2. Start Conversation from Job

```jsx
function JobDetails({ job }) {
  const navigate = useNavigate();
  
  const handleContactProvider = async () => {
    // Create conversation with provider
    const conv = await createConversation(
      job.assigned_provider_id,
      job.job_id
    );
    
    // Navigate to messages with this conversation
    navigate(`/messages/${conv.conversationId}`);
  };
  
  return (
    <div>
      <h2>{job.title}</h2>
      <button onClick={handleContactProvider}>
        Message Provider
      </button>
    </div>
  );
}
```

### 3. Real-time Updates (Polling)

```jsx
function useMessagePolling(conversationId, interval = 5000) {
  const [messages, setMessages] = useState([]);
  
  useEffect(() => {
    if (!conversationId) return;
    
    const poll = async () => {
      const data = await listMessages(conversationId);
      setMessages(data.messages);
    };
    
    poll(); // Initial load
    const timer = setInterval(poll, interval);
    
    return () => clearInterval(timer);
  }, [conversationId, interval]);
  
  return messages;
}
```

---

## Error Handling

### Common Error Responses:

**401 Unauthorized**:
```json
{
  "message": "Unauthorized"
}
```
→ JWT token expired or invalid. Refresh token or redirect to login.

**400 Bad Request**:
```json
{
  "message": "conversationId is required"
}
```
→ Missing or invalid request parameters.

**403 Forbidden**:
```json
{
  "message": "You are not part of this conversation"
}
```
→ User trying to access conversation they don't own.

**404 Not Found**:
```json
{
  "message": "User not found"
}
```
→ Referenced user doesn't exist.

**500 Internal Server Error**:
```json
{
  "message": "Internal Server Error"
}
```
→ Server error. Retry or contact support.

### Error Handling Pattern:

```javascript
async function apiCall(url, options) {
  try {
    const response = await fetch(url, options);
    
    if (response.status === 401) {
      // Token expired - refresh or logout
      auth.signoutRedirect();
      return;
    }
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.message || 'API request failed');
    }
    
    return await response.json();
  } catch (error) {
    console.error('API Error:', error);
    toast.error(error.message);
    throw error;
  }
}
```

---

## Example Flows

### Flow 1: Customer Messages Provider about Job

```
1. Customer views job details
2. Clicks "Contact Provider"
3. Frontend calls: POST /messages/conversations
   - otherUserId: provider's ID
   - jobId: job ID
4. Receives conversationId
5. Navigate to /messages/{conversationId}
6. Frontend calls: GET /messages/{conversationId}
7. Display messages
8. Customer types and sends message
9. Frontend calls: POST /messages
10. Provider receives notification automatically
```

### Flow 2: Provider Checks Notifications

```
1. Provider logs in
2. Frontend calls: GET /notifications/unread-count
3. Display badge with count
4. Provider clicks notification bell
5. Frontend calls: GET /notifications/my
6. Display notification list
7. Provider clicks notification
8. Frontend calls: POST /notifications/mark-read
9. Navigate to conversation
10. Frontend calls: PUT /messages/conversations/{id}/read
```

---

## Best Practices

### 1. Token Management
```javascript
// Always check token before API calls
const getAuthHeaders = () => {
  const token = auth.user?.id_token;
  if (!token) throw new Error('Not authenticated');
  
  return {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  };
};
```

### 2. Loading States
```jsx
const [loading, setLoading] = useState(false);

const loadData = async () => {
  setLoading(true);
  try {
    const data = await listConversations();
    setConversations(data.conversations);
  } catch (error) {
    toast.error('Failed to load conversations');
  } finally {
    setLoading(false);
  }
};
```

### 3. Optimistic Updates
```jsx
const handleSend = async (text) => {
  // Add message optimistically
  const tempMessage = {
    messageId: Date.now(),
    text,
    senderId: currentUserId,
    timestamp: Date.now(),
    pending: true
  };
  
  setMessages([...messages, tempMessage]);
  
  try {
    const message = await sendMessage(conversationId, text);
    // Replace temp with real message
    setMessages(msgs => 
      msgs.map(m => m.messageId === tempMessage.messageId ? message : m)
    );
  } catch (error) {
    // Remove temp message on error
    setMessages(msgs => msgs.filter(m => m.messageId !== tempMessage.messageId));
    toast.error('Failed to send message');
  }
};
```

### 4. Date Formatting
```javascript
function formatMessageTime(timestamp) {
  const date = new Date(timestamp);
  const now = new Date();
  const diff = now - date;
  
  if (diff < 60000) return 'Just now';
  if (diff < 3600000) return `${Math.floor(diff / 60000)}m ago`;
  if (diff < 86400000) return date.toLocaleTimeString('en-US', { 
    hour: 'numeric', 
    minute: '2-digit' 
  });
  return date.toLocaleDateString('en-US', { 
    month: 'short', 
    day: 'numeric' 
  });
}
```

---

## Testing

### Test with Postman:

1. Get JWT token from your app's localStorage
2. Import the API endpoints
3. Set Authorization header
4. Test each endpoint

### Sample Test Flow:

```bash
# 1. Create conversation
POST /messages/conversations
Body: {"otherUserId": "SP-xxx", "jobId": "1001"}

# 2. Send message
POST /messages
Body: {"conversationId": "xxx", "text": "Hello"}

# 3. List messages
GET /messages/{conversationId}

# 4. Check notifications
GET /notifications/unread-count
```

---

## Support

For issues or questions:
- Check error messages in browser console
- Verify JWT token is valid
- Ensure all required fields are provided
- Check API response status codes

**API is ready for integration!** 🚀
