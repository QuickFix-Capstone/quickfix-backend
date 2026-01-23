# DynamoDB Tables Created - Summary

## ✅ Tables Successfully Created

### Table 1: `quickfix_conversations`
**Status**: ✅ ACTIVE  
**Created**: 2026-01-04  
**Region**: us-east-2  
**ARN**: `arn:aws:dynamodb:us-east-2:008971679867:table/quickfix_conversations`

**Schema**:
- **Partition Key**: `userId` (String)
- **Sort Key**: `conversationId` (String)
- **Billing**: Pay-per-request (on-demand)

**Purpose**: Stores each user's inbox view of conversations

---

### Table 2: `quickfix_messages`
**Status**: ✅ ACTIVE  
**Created**: 2026-01-04  
**Region**: us-east-2  
**ARN**: `arn:aws:dynamodb:us-east-2:008971679867:table/quickfix_messages`

**Schema**:
- **Partition Key**: `conversation_id` (String)
- **Sort Key**: `ts` (Number)
- **Billing**: Pay-per-request (on-demand)

**Purpose**: Stores all messages in chronological order

---

## AWS CLI Commands Used

### Create quickfix_conversations
```bash
aws dynamodb create-table \
  --table-name quickfix_conversations \
  --attribute-definitions \
    AttributeName=userId,AttributeType=S \
    AttributeName=conversationId,AttributeType=S \
  --key-schema \
    AttributeName=userId,KeyType=HASH \
    AttributeName=conversationId,KeyType=RANGE \
  --billing-mode PAY_PER_REQUEST \
  --region us-east-2
```

### Verify quickfix_messages (already existed)
```bash
aws dynamodb describe-table \
  --table-name quickfix_messages \
  --region us-east-2
```

---

## Verification Commands

### List all tables
```bash
aws dynamodb list-tables --region us-east-2
```

### Check table status
```bash
# quickfix_conversations
aws dynamodb describe-table \
  --table-name quickfix_conversations \
  --region us-east-2 \
  --query 'Table.TableStatus'

# quickfix_messages  
aws dynamodb describe-table \
  --table-name quickfix_messages \
  --region us-east-2 \
  --query 'Table.TableStatus'
```

### View table details
```bash
# Conversations table
aws dynamodb describe-table \
  --table-name quickfix_conversations \
  --region us-east-2

# Messages table
aws dynamodb describe-table \
  --table-name quickfix_messages \
  --region us-east-2
```

---

## Next Steps

✅ **Phase 0 Complete**: Tables created and verified  
⏳ **Phase 1 Next**: Implement 5 Lambda functions
- create_conversation
- list_conversations
- send_message
- list_messages
- mark_conversation_read

---

## Cost Estimate

**Billing Mode**: Pay-per-request (on-demand)

**Pricing**:
- Write: $1.25 per million requests
- Read: $0.25 per million requests
- Storage: $0.25 per GB/month

**Estimated Monthly Cost** (1000 messages/day):
- Writes: ~$0.04
- Reads: ~$0.02
- Storage: ~$0.01
- **Total**: ~$0.07/month

---

## Table Comparison

| Feature | quickfix_conversations | quickfix_messages |
|---------|----------------------|-------------------|
| **Purpose** | User's inbox | Message history |
| **Partition Key** | userId | conversation_id |
| **Sort Key** | conversationId | ts (timestamp) |
| **Rows per conversation** | 2 (one per user) | Many (all messages) |
| **Size** | Small | Large (grows over time) |
| **Query pattern** | "My conversations" | "Messages in conversation" |

---

## Important Notes

⚠️ **Attribute Name Difference**:
- `quickfix_conversations` uses `conversationId` (camelCase)
- `quickfix_messages` uses `conversation_id` (snake_case)

Make sure Lambda functions use the correct attribute names!

**Recommendation**: Standardize on one naming convention in Phase 1 implementation.
