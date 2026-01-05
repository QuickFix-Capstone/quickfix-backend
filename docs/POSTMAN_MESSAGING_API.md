# Postman Testing Guide - Messaging APIs

## Setup

### 1. Get Your JWT Token

First, you need a valid JWT token from your frontend:

1. Log in to your QuickFix app
2. Open browser DevTools (F12)
3. Go to Console tab
4. Run: `localStorage.getItem('oidc.user:https://cognito-idp.us-east-2.amazonaws.com/us-east-2_45z5OMePi:p2u5qdeglm3hp60n6ohu52n2b')`
5. Copy the `id_token` value

**OR** use this test token (expires quickly):
```
eyJraWQiOiJuQnVPclY3bjJ5d1hha2pYV1lqSUw2dXl1Y05MR3M5RHhBTUtFVUJBVUNFPSIsImFsZyI6IlJTMjU2In0...
```

---

## API 1: Create Conversation

**Endpoint**: `POST /messages/conversations`

### Postman Setup

**Method**: `POST`

**URL**: 
```
https://kfvf20j7j9.execute-api.us-east-2.amazonaws.com/prod/messages/conversations
```

**Headers**:
```
Authorization: Bearer YOUR_JWT_TOKEN_HERE
Content-Type: application/json
```

**Body** (raw JSON):
```json
{
  "otherUserId": "SP-ad86b044-9f9b-49b6-a53d-d3847afabe3c",
  "jobId": "1001"
}
```

**Expected Response** (201 Created):
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

---

## API 2: List Conversations

**Endpoint**: `GET /messages/conversations`

### Postman Setup

**Method**: `GET`

**URL**: 
```
https://kfvf20j7j9.execute-api.us-east-2.amazonaws.com/prod/messages/conversations
```

**Query Parameters** (optional):
- `limit`: `10` (default: 20, max: 50)

**Full URL with params**:
```
https://kfvf20j7j9.execute-api.us-east-2.amazonaws.com/prod/messages/conversations?limit=10
```

**Headers**:
```
Authorization: Bearer YOUR_JWT_TOKEN_HERE
```

**Expected Response** (200 OK):
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
        "preview": "",
        "timestamp": 0
      },
      "unreadCount": 0,
      "createdAt": 1767576511608
    }
  ],
  "total": 1
}
```

---

## Step-by-Step: Testing in Postman

### Test 1: Create a Conversation

1. **Open Postman**
2. **Create new request**
3. **Set method to POST**
4. **Enter URL**: `https://kfvf20j7j9.execute-api.us-east-2.amazonaws.com/prod/messages/conversations`
5. **Go to Headers tab**:
   - Key: `Authorization`, Value: `Bearer YOUR_JWT_TOKEN`
   - Key: `Content-Type`, Value: `application/json`
6. **Go to Body tab**:
   - Select `raw`
   - Select `JSON` from dropdown
   - Paste:
     ```json
     {
       "otherUserId": "SP-ad86b044-9f9b-49b6-a53d-d3847afabe3c",
       "jobId": "1001"
     }
     ```
7. **Click Send**
8. **Check response** - should get 201 with conversationId

### Test 2: List Conversations

1. **Create new request**
2. **Set method to GET**
3. **Enter URL**: `https://kfvf20j7j9.execute-api.us-east-2.amazonaws.com/prod/messages/conversations?limit=10`
4. **Go to Headers tab**:
   - Key: `Authorization`, Value: `Bearer YOUR_JWT_TOKEN`
5. **Click Send**
6. **Check response** - should see array of conversations

---

## Common Issues & Solutions

### 401 Unauthorized
**Problem**: Invalid or expired JWT token

**Solution**: 
1. Get a fresh token from your app
2. Make sure you include `Bearer ` before the token
3. Check token hasn't expired (tokens expire in 1 hour)

### 404 Not Found
**Problem**: User doesn't exist in database

**Solution**:
- Verify the cognito_sub exists in `customers` or `service_providers` table
- Make sure you're logged in to the app first

### 500 Internal Server Error
**Problem**: Server-side error

**Solution**:
- Check CloudWatch logs: `/aws/lambda/list_conversations`
- Common causes: Database connection, DynamoDB permissions

### CORS Error
**Problem**: Browser blocking request

**Solution**:
- Use Postman (not browser)
- Or add CORS extension to browser
- API already has CORS headers configured

---

## Postman Collection

Save this as a Postman collection for easy reuse:

```json
{
  "info": {
    "name": "QuickFix Messaging API",
    "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
  },
  "item": [
    {
      "name": "Create Conversation",
      "request": {
        "method": "POST",
        "header": [
          {
            "key": "Authorization",
            "value": "Bearer {{jwt_token}}",
            "type": "text"
          },
          {
            "key": "Content-Type",
            "value": "application/json",
            "type": "text"
          }
        ],
        "body": {
          "mode": "raw",
          "raw": "{\n  \"otherUserId\": \"SP-ad86b044-9f9b-49b6-a53d-d3847afabe3c\",\n  \"jobId\": \"1001\"\n}"
        },
        "url": {
          "raw": "https://kfvf20j7j9.execute-api.us-east-2.amazonaws.com/prod/messages/conversations",
          "protocol": "https",
          "host": ["kfvf20j7j9", "execute-api", "us-east-2", "amazonaws", "com"],
          "path": ["prod", "messages", "conversations"]
        }
      }
    },
    {
      "name": "List Conversations",
      "request": {
        "method": "GET",
        "header": [
          {
            "key": "Authorization",
            "value": "Bearer {{jwt_token}}",
            "type": "text"
          }
        ],
        "url": {
          "raw": "https://kfvf20j7j9.execute-api.us-east-2.amazonaws.com/prod/messages/conversations?limit=10",
          "protocol": "https",
          "host": ["kfvf20j7j9", "execute-api", "us-east-2", "amazonaws", "com"],
          "path": ["prod", "messages", "conversations"],
          "query": [
            {
              "key": "limit",
              "value": "10"
            }
          ]
        }
      }
    }
  ],
  "variable": [
    {
      "key": "jwt_token",
      "value": "YOUR_JWT_TOKEN_HERE"
    }
  ]
}
```

### How to Import Collection:

1. Copy the JSON above
2. Open Postman
3. Click **Import** button
4. Paste JSON
5. Click **Import**
6. Set the `jwt_token` variable in the collection

---

## Quick Test Checklist

- [ ] Get fresh JWT token from app
- [ ] Test POST /messages/conversations (create)
- [ ] Verify 201 response with conversationId
- [ ] Test GET /messages/conversations (list)
- [ ] Verify 200 response with conversations array
- [ ] Test with different limit values (5, 10, 20)
- [ ] Test with expired token (should get 401)

---

## Next Steps

Once these 2 APIs work:
1. ✅ create_conversation
2. ✅ list_conversations
3. ⏳ send_message (next to implement)
4. ⏳ list_messages
5. ⏳ mark_conversation_read
