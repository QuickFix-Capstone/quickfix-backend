# Testing mark_conversation_read in Postman

## Lambda 5: mark_conversation_read

### Endpoint
`PUT https://kfvf20j7j9.execute-api.us-east-2.amazonaws.com/prod/messages/conversations/{conversationId}/read`

---

## Postman Setup

**Method**: `PUT`

**URL**:
```
https://kfvf20j7j9.execute-api.us-east-2.amazonaws.com/prod/messages/conversations/a103818f-ed02-4f47-9dd3-def9e2a5bfcd/read
```

**Headers**:
```
Authorization: Bearer YOUR_JWT_TOKEN_HERE
```

**Body**: None required (this is a PUT request with no body)

---

## Expected Response (200 OK)

```json
{
  "conversationId": "a103818f-ed02-4f47-9dd3-def9e2a5bfcd",
  "unreadCount": 0,
  "message": "Conversation marked as read"
}
```

---

## What It Does

1. ✅ Verifies user is part of the conversation
2. ✅ Resets `unreadCount` to 0 in `quickfix_conversations` table
3. ✅ Returns confirmation

---

## Complete Testing Flow

### Step 1: Create Conversation
`POST /messages/conversations`
```json
{
  "otherUserId": "SP-ad86b044-9f9b-49b6-a53d-d3847afabe3c",
  "jobId": "1001"
}
```

### Step 2: Send Messages (creates unread count)
`POST /messages`
```json
{
  "conversationId": "a103818f-ed02-4f47-9dd3-def9e2a5bfcd",
  "text": "Hello!"
}
```

### Step 3: List Conversations (check unread count)
`GET /messages/conversations`

Response shows:
```json
{
  "unreadCount": 1
}
```

### Step 4: Mark as Read
`PUT /messages/conversations/a103818f-ed02-4f47-9dd3-def9e2a5bfcd/read`

### Step 5: List Conversations Again (verify unread = 0)
`GET /messages/conversations`

Response shows:
```json
{
  "unreadCount": 0
}
```

---

## All 5 Messaging API Endpoints

| # | Method | Endpoint | Purpose |
|---|--------|----------|---------|
| 1 | POST | `/messages/conversations` | Create conversation |
| 2 | GET | `/messages/conversations` | List user's conversations |
| 3 | POST | `/messages` | Send message |
| 4 | GET | `/messages/{conversationId}` | List messages in conversation |
| 5 | PUT | `/messages/conversations/{conversationId}/read` | Mark conversation as read |

---

## Testing Checklist

- [ ] Get fresh JWT token
- [ ] Test create_conversation
- [ ] Test send_message (2-3 messages)
- [ ] Test list_conversations (verify unread count > 0)
- [ ] Test list_messages (see sent messages)
- [ ] Test mark_conversation_read
- [ ] Test list_conversations again (verify unread count = 0)

---

## Success! 🎉

All 5 Phase 1 messaging APIs are deployed and ready to use!
