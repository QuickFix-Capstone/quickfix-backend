# Notifications Table - Creation Summary

## Table Created: quickfix_notifications

**Created**: 2026-01-05T09:26:38

### Schema

**Primary Key**:
- **PK**: `user_sub` (String) - Recipient's cognito_sub
- **SK**: `notif_sort` (String) - Format: `NOTIF#<ISO_TIME>#MSG#<message_id>`

**Attributes** (stored but not indexed):
- `type`: "NEW_MESSAGE"
- `conversation_id`: String
- `from_sub`: Sender's cognito_sub
- `from_name`: Sender's display name
- `preview`: Message preview (first 100 chars)
- `created_at`: ISO timestamp
- `is_read`: Boolean (default: false)
- `message_id`: Number (timestamp)
- `ttl`: Number (optional, for auto-cleanup)

### Configuration

- **Billing Mode**: PAY_PER_REQUEST (on-demand)
- **Streams**: ENABLED
- **Stream View Type**: NEW_IMAGE
- **Stream ARN**: `arn:aws:dynamodb:us-east-2:008971679867:table/quickfix_notifications/stream/2026-01-05T14:26:38.269`

### Access Pattern

**Query by user**:
```
PK = user_sub
SK begins_with "NOTIF#"
ScanIndexForward = false (newest first)
```

**Example Item**:
```json
{
  "user_sub": "415b3510-a0a1-708e-6a02-dc457aec9ecc",
  "notif_sort": "NOTIF#2026-01-05T10:00:00Z#MSG#1767581062206",
  "type": "NEW_MESSAGE",
  "conversation_id": "a103818f-ed02-4f47-9dd3-def9e2a5bfcd",
  "from_sub": "provider-cognito-sub",
  "from_name": "walter",
  "preview": "Hello, when can you start?",
  "created_at": "2026-01-05T10:00:00Z",
  "is_read": false,
  "message_id": 1767581062206,
  "ttl": 1770173062
}
```

### Verification Commands

**List tables**:
```bash
aws dynamodb list-tables --region us-east-2
```

**Describe table**:
```bash
aws dynamodb describe-table \
  --table-name quickfix_notifications \
  --region us-east-2
```

**Scan table** (view all items):
```bash
aws dynamodb scan \
  --table-name quickfix_notifications \
  --region us-east-2
```

### Next Steps

1. ✅ Create DynamoDB table with Streams
2. ⏳ Enable Streams on `quickfix_messages` table
3. ⏳ Create `notify_on_new_message` Lambda
4. ⏳ Configure Stream trigger
5. ⏳ Create 3 API Lambdas
