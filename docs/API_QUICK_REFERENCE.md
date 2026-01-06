# QuickFix Messaging API - Quick Reference

## Base URL
```
https://kfvf20j7j9.execute-api.us-east-2.amazonaws.com/prod
```

## Authentication
All endpoints require JWT token:
```
Authorization: Bearer YOUR_JWT_TOKEN
```

---

## Messaging APIs (5)

### 1. Create Conversation
```http
POST /messages/conversations
{
  "otherUserId": "SP-xxx",
  "jobId": "1001"  // optional
}
```

### 2. List Conversations (Inbox)
```http
GET /messages/conversations?limit=20
```

### 3. Send Message
```http
POST /messages
{
  "conversationId": "xxx",
  "text": "Hello!"
}
```

### 4. List Messages (History)
```http
GET /messages/{conversationId}?limit=50&before=1767581062206
```

### 5. Mark as Read
```http
PUT /messages/conversations/{conversationId}/read
```

---

## Notification APIs (3)

### 6. List Notifications
```http
GET /notifications/my?limit=20&nextToken=xxx
```

### 7. Get Unread Count (Badge)
```http
GET /notifications/unread-count
```

### 8. Mark Notifications Read
```http
POST /notifications/mark-read
{
  "items": [
    {"notif_sort": "NOTIF#2026-01-05T10:00:00Z#MSG#1767581062206"}
  ]
}
```

---

## JavaScript Examples

### Send Message
```javascript
const response = await fetch(`${BASE_URL}/messages`, {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    conversationId: 'xxx',
    text: 'Hello!'
  })
});
const message = await response.json();
```

### Get Unread Count
```javascript
const response = await fetch(`${BASE_URL}/notifications/unread-count`, {
  headers: { 'Authorization': `Bearer ${token}` }
});
const { unreadCount } = await response.json();
```

---

## Response Formats

### Conversation
```json
{
  "conversationId": "xxx",
  "otherUser": {
    "userId": "SP-xxx",
    "name": "walter",
    "type": "provider"
  },
  "jobId": "1001",
  "jobTitle": "Fix Kitchen Sink",
  "lastMessage": {
    "preview": "Hello!",
    "timestamp": 1767581062206
  },
  "unreadCount": 2,
  "createdAt": 1767576511608
}
```

### Message
```json
{
  "messageId": 1767581062206,
  "senderId": "2",
  "senderName": "John",
  "senderType": "customer",
  "text": "Hello!",
  "timestamp": 1767581062206,
  "createdAt": "2026-01-05T02:44:22Z"
}
```

### Notification
```json
{
  "notif_sort": "NOTIF#2026-01-06T00:39:49Z#MSG#1767659987428",
  "type": "NEW_MESSAGE",
  "conversation_id": "xxx",
  "from_name": "walter",
  "preview": "Hello!",
  "created_at": "2026-01-06T00:39:49Z",
  "is_read": false,
  "message_id": 1767659987428
}
```

---

## Common Patterns

### Load Conversations
```javascript
const { conversations } = await fetch(
  `${BASE_URL}/messages/conversations`,
  { headers: { 'Authorization': `Bearer ${token}` }}
).then(r => r.json());
```

### Mark Conversation as Read (on open)
```javascript
await fetch(
  `${BASE_URL}/messages/conversations/${convId}/read`,
  { 
    method: 'PUT',
    headers: { 'Authorization': `Bearer ${token}` }
  }
);
```

### Poll for New Messages
```javascript
setInterval(async () => {
  const { messages } = await fetch(
    `${BASE_URL}/messages/${convId}`,
    { headers: { 'Authorization': `Bearer ${token}` }}
  ).then(r => r.json());
  
  setMessages(messages);
}, 5000);  // Every 5 seconds
```

---

## Error Codes

- `401` - Unauthorized (token expired)
- `400` - Bad Request (missing fields)
- `403` - Forbidden (not your conversation)
- `404` - Not Found (user/conversation doesn't exist)
- `500` - Server Error

---

## Full Documentation
See `FRONTEND_API_GUIDE.md` for complete details, examples, and best practices.
