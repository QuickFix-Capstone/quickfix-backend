# Testing send_message in Postman

## Lambda 3: send_message

### Endpoint
`POST https://kfvf20j7j9.execute-api.us-east-2.amazonaws.com/prod/messages`

---

## Step-by-Step Postman Setup

### 1. Get Your JWT Token
- Log in to your QuickFix app
- Open DevTools (F12) → Console
- Run: `localStorage.getItem('oidc.user:...')` 
- Copy the `id_token` value

### 2. Create Request in Postman

**Method**: `POST`

**URL**:
```
https://kfvf20j7j9.execute-api.us-east-2.amazonaws.com/prod/messages
```

**Headers**:
```
Authorization: Bearer YOUR_JWT_TOKEN_HERE
Content-Type: application/json
```

**Body** (select `raw` and `JSON`):
```json
{
  "conversationId": "a103818f-ed02-4f47-9dd3-def9e2a5bfcd",
  "text": "Hello, when can you start?"
}
```

### 3. Click Send!

---

## Expected Response

**Success (201 Created)**:
```json
{
  "messageId": 1767577800000,
  "conversationId": "a103818f-ed02-4f47-9dd3-def9e2a5bfcd",
  "senderId": "2",
  "senderName": "KunPeng Yang",
  "senderType": "customer",
  "text": "Hello, when can you start?",
  "timestamp": 1767577800000,
  "createdAt": "2026-01-05T02:36:40Z"
}
```

---

## Test Scenarios

### Test 1: Send First Message
```json
{
  "conversationId": "a103818f-ed02-4f47-9dd3-def9e2a5bfcd",
  "text": "Hello, when can you start?"
}
```

### Test 2: Send Follow-up Message
```json
{
  "conversationId": "a103818f-ed02-4f47-9dd3-def9e2a5bfcd",
  "text": "Can you provide a quote for the work?"
}
```

### Test 3: Send Long Message
```json
{
  "conversationId": "a103818f-ed02-4f47-9dd3-def9e2a5bfcd",
  "text": "I need help with fixing my kitchen sink. It's been leaking for a few days now and I'm worried about water damage. The leak seems to be coming from under the sink. Can you come take a look this week?"
}
```

### Test 4: Missing conversationId (should fail with 400)
```json
{
  "text": "Hello"
}
```

### Test 5: Empty text (should fail with 400)
```json
{
  "conversationId": "a103818f-ed02-4f47-9dd3-def9e2a5bfcd",
  "text": ""
}
```

### Test 6: Invalid conversationId (should fail with 403)
```json
{
  "conversationId": "invalid-conversation-id",
  "text": "Hello"
}
```

---

## What Happens When You Send a Message

1. ✅ **Validates JWT** - Checks you're authenticated
2. ✅ **Gets user info** - Looks up your name from MySQL
3. ✅ **Verifies conversation** - Checks you're part of this conversation
4. ✅ **Creates message** - Adds to `quickfix_messages` table
5. ✅ **Updates sender's conversation** - Sets last message preview
6. ✅ **Updates recipient's conversation** - Increments unread count
7. ✅ **Returns message** - With timestamp and ID

---

## Verify It Worked

After sending a message, you can verify it worked by:

### 1. Check DynamoDB Messages Table
```bash
aws dynamodb query \
  --table-name quickfix_messages \
  --key-condition-expression "conversation_id = :convId" \
  --expression-attribute-values '{":convId":{"S":"a103818f-ed02-4f47-9dd3-def9e2a5bfcd"}}' \
  --no-cli-pager
```

### 2. List Conversations (should show updated preview)
**GET** `https://kfvf20j7j9.execute-api.us-east-2.amazonaws.com/prod/messages/conversations`

Should show:
```json
{
  "lastMessage": {
    "preview": "Hello, when can you start?",
    "timestamp": 1767577800000
  },
  "unreadCount": 1
}
```

---

## Common Errors

### 401 Unauthorized
- JWT token expired or invalid
- Get a fresh token from your app

### 400 Bad Request
- Missing `conversationId` or `text`
- Empty `text` field
- Check request body format

### 403 Forbidden
- You're not part of this conversation
- Verify the conversationId is correct
- Make sure you created the conversation first

### 500 Internal Server Error
- Check CloudWatch logs: `/aws/lambda/send_message`
- Common causes: Database connection, DynamoDB permissions

---

## Quick Test Checklist

- [ ] Get fresh JWT token
- [ ] Set Authorization header
- [ ] Set Content-Type: application/json
- [ ] Use valid conversationId
- [ ] Send message with text
- [ ] Verify 201 response
- [ ] Check message appears in conversation
- [ ] Verify unread count incremented

---

## Next: Test Lambda 4 (list_messages)

After sending messages, test retrieving them:

**GET** `https://kfvf20j7j9.execute-api.us-east-2.amazonaws.com/prod/messages/{conversationId}`

This will show all messages you just sent!
