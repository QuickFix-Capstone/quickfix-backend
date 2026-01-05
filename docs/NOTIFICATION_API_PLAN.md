# QuickFix Notification API - Implementation Plan

## Overview
Implement real-time notifications for new messages using DynamoDB Streams and a dedicated notifications table.

---

## Phase 2: Notifications

### 1. DynamoDB Table

**Table Name**: `quickfix_notifications`

**Schema**:
- **PK**: `user_sub` (String) - Recipient's cognito_sub
- **SK**: `notif_sort` (String) - Format: `NOTIF#<ISO_TIME>#MSG#<message_id>`
- **Attributes**:
  - `type`: "NEW_MESSAGE"
  - `conversation_id`: String
  - `from_sub`: Sender's cognito_sub
  - `from_name`: Sender's display name
  - `preview`: Message preview (first 100 chars)
  - `created_at`: ISO timestamp
  - `is_read`: Boolean (default: false)
  - `message_id`: Number (timestamp)
  - `ttl`: Number (optional, for auto-cleanup after 30 days)

**Optional GSI** (for fast unread count):
- **GSI1PK**: `user_sub`
- **GSI1SK**: `READ#<0|1>#<created_at>`

**CLI Command**:
```bash
aws dynamodb create-table \
  --table-name quickfix_notifications \
  --attribute-definitions \
    AttributeName=user_sub,AttributeType=S \
    AttributeName=notif_sort,AttributeType=S \
  --key-schema \
    AttributeName=user_sub,KeyType=HASH \
    AttributeName=notif_sort,KeyType=RANGE \
  --billing-mode PAY_PER_REQUEST \
  --stream-specification StreamEnabled=true,StreamViewType=NEW_IMAGE \
  --region us-east-2
```

---

### 2. DynamoDB Streams Trigger

**Trigger**: `quickfix_messages` table → DynamoDB Stream → Lambda

**Lambda**: `notify_on_new_message`

**Logic**:
1. Stream receives INSERT event from `quickfix_messages`
2. Extract: `conversation_id`, `senderId`, `senderName`, `text`, `ts`
3. Query `quickfix_conversations` to get `otherUserId` (recipient)
4. Get recipient's `cognito_sub` from MySQL
5. Create notification in `quickfix_notifications`:
   ```python
   {
       'user_sub': recipient_cognito_sub,
       'notif_sort': f"NOTIF#{iso_time}#MSG#{message_id}",
       'type': 'NEW_MESSAGE',
       'conversation_id': conversation_id,
       'from_sub': sender_cognito_sub,
       'from_name': sender_name,
       'preview': text[:100],
       'created_at': iso_time,
       'is_read': False,
       'message_id': ts,
       'ttl': int(time.time()) + 2592000  # 30 days
   }
   ```
6. Use conditional put with `message_id` to avoid duplicates on retries

**IAM Permissions**:
- `dynamodb:GetRecords`
- `dynamodb:GetShardIterator`
- `dynamodb:DescribeStream`
- `dynamodb:ListStreams`
- `dynamodb:PutItem` (for quickfix_notifications)
- `dynamodb:Query` (for quickfix_conversations)

---

### 3. API Endpoints

#### 3.1 List Notifications
**Endpoint**: `GET /notifications/my?limit=20&nextToken=...`

**Lambda**: `list_my_notifications`

**Logic**:
- Extract `user_sub` from JWT
- Query `quickfix_notifications` where PK = `user_sub`
- Sort by SK descending (newest first)
- Return items + `nextToken` for pagination

**Response**:
```json
{
  "notifications": [
    {
      "notif_sort": "NOTIF#2026-01-05T10:00:00Z#MSG#1767581062206",
      "type": "NEW_MESSAGE",
      "conversation_id": "a103818f-ed02-4f47-9dd3-def9e2a5bfcd",
      "from_name": "walter",
      "preview": "Hello, when can you start?",
      "created_at": "2026-01-05T10:00:00Z",
      "is_read": false,
      "message_id": 1767581062206
    }
  ],
  "nextToken": "eyJ..."
}
```

---

#### 3.2 Get Unread Count
**Endpoint**: `GET /notifications/unread-count`

**Lambda**: `get_unread_count`

**Logic** (Option 1 - with GSI):
- Query GSI1 where `GSI1PK = user_sub` AND `begins_with(GSI1SK, "READ#0#")`
- Use `Select=COUNT`

**Logic** (Option 2 - without GSI, starter):
- Query PK = `user_sub`
- Filter `is_read = false` in application code
- Return count

**Response**:
```json
{
  "unreadCount": 5
}
```

---

#### 3.3 Mark Notifications as Read
**Endpoint**: `POST /notifications/mark-read`

**Lambda**: `mark_notifications_read`

**Request Body**:
```json
{
  "items": [
    {"notif_sort": "NOTIF#2026-01-05T10:00:00Z#MSG#1767581062206"},
    {"notif_sort": "NOTIF#2026-01-05T09:55:00Z#MSG#1767580900000"}
  ]
}
```

**Logic**:
- Extract `user_sub` from JWT
- For each item:
  - `UpdateItem` where PK = `user_sub`, SK = `notif_sort`
  - Set `is_read = true`
  - If using GSI: update `GSI1SK` from `READ#0#...` to `READ#1#...`

**Response**:
```json
{
  "updated": 2,
  "message": "Notifications marked as read"
}
```

---

### 4. Security Rules

**Enforcement in Lambda**:
- User can ONLY access notifications where `PK = their own cognito_sub`
- Validate JWT `sub` claim matches `user_sub` in all operations
- Return 403 if user tries to access another user's notifications

---

### 5. Implementation Steps

1. **Create DynamoDB table** with Streams enabled
2. **Enable Streams** on `quickfix_messages` table
3. **Create `notify_on_new_message` Lambda**
   - Configure DynamoDB Stream trigger
   - Add IAM permissions
4. **Create 3 API Lambdas**:
   - `list_my_notifications`
   - `get_unread_count`
   - `mark_notifications_read`
5. **Configure API Gateway routes** with JWT auth
6. **Test end-to-end flow**:
   - Send message → verify notification created
   - List notifications → verify appears
   - Mark as read → verify count decreases

---

### 6. Optional Enhancements

- **GSI for fast unread count** (recommended for production)
- **TTL for auto-cleanup** (delete notifications after 30 days)
- **Batch operations** for marking multiple as read
- **Push notifications** (future: integrate with SNS/FCM)

---

## Summary

**New Resources**:
- 1 DynamoDB table (`quickfix_notifications`)
- 1 Stream trigger Lambda (`notify_on_new_message`)
- 3 API Lambdas (list, count, mark-read)
- 3 API Gateway routes

**Estimated Time**: 4-6 hours

**Dependencies**: Phase 1 (Messaging) must be complete
