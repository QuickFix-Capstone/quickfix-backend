# Phase 0: Messaging System Foundations - Detailed Explanation

## Why Two Tables?

We use **two separate DynamoDB tables** because they serve different purposes and have different access patterns:

### Table 1: `quickfix_conversations` - The "Inbox"
**Purpose**: Show each user their list of conversations (like WhatsApp/Messenger inbox)

**What it does**:
- Lists all conversations for a user
- Shows unread message counts
- Displays last message preview
- Enables sorting by most recent activity

**Access Pattern**: "Show me all MY conversations"

### Table 2: `quickfix_messages` - The "Chat History"
**Purpose**: Store the actual messages in each conversation

**What it does**:
- Stores every message sent
- Enables pagination (load older messages)
- Maintains chronological order
- Supports message search (future)

**Access Pattern**: "Show me all messages in THIS conversation"

---

## Visual Example: How It Works

### Scenario: Customer Jane messages Provider John about Job #1001

#### Step 1: Create Conversation

When Jane first messages John, we create **2 rows** in `quickfix_conversations`:

**Row 1 (Jane's inbox entry)**:
```json
{
  "userId": "customer_jane_123",           ← Jane's view
  "conversationId": "conv_abc",
  "otherUserId": "provider_john_456",      ← She's talking to John
  "otherUserName": "John Smith",
  "otherUserType": "provider",
  "jobId": "1001",
  "jobTitle": "Fix Kitchen Sink",
  "lastMessageAt": 1704384000000,
  "lastMessagePreview": "Hello, when can you start?",
  "unreadCount": 0,                        ← Jane sent it, so she's read it
  "createdAt": 1704384000000
}
```

**Row 2 (John's inbox entry)**:
```json
{
  "userId": "provider_john_456",           ← John's view
  "conversationId": "conv_abc",            ← Same conversation!
  "otherUserId": "customer_jane_123",      ← He's talking to Jane
  "otherUserName": "Jane Doe",
  "otherUserType": "customer",
  "jobId": "1001",
  "jobTitle": "Fix Kitchen Sink",
  "lastMessageAt": 1704384000000,
  "lastMessagePreview": "Hello, when can you start?",
  "unreadCount": 1,                        ← John hasn't read it yet!
  "createdAt": 1704384000000
}
```

**Why 2 rows?**
- Each user has their own "inbox entry"
- Each user has their own unread count
- Enables fast "show my conversations" query

#### Step 2: Store Message

The actual message goes in `quickfix_messages`:

```json
{
  "conversationId": "conv_abc",            ← Links to conversation
  "ts": 1704384000000,                     ← Timestamp (sort key)
  "senderId": "customer_jane_123",
  "senderName": "Jane Doe",
  "senderType": "customer",
  "text": "Hello, when can you start?",
  "attachments": [],
  "readBy": ["customer_jane_123"],         ← Only Jane has read it
  "createdAt": "2026-01-04T14:00:00Z"
}
```

---

## Complete Schema Specifications

### Table 1: `quickfix_conversations`

#### Primary Key Design
```
Partition Key: userId (String)
Sort Key: conversationId (String)
```

**Why this design?**
- Query: "Get all conversations for userId" → Very fast!
- Single query returns user's entire inbox
- Can sort by lastMessageAt for "most recent first"

#### Full Schema

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `userId` | String (PK) | User viewing the conversation | `"customer_jane_123"` |
| `conversationId` | String (SK) | Unique conversation ID | `"550e8400-e29b-41d4-a716-446655440000"` |
| `otherUserId` | String | The other person in conversation | `"provider_john_456"` |
| `otherUserName` | String | Display name of other user | `"John Smith"` |
| `otherUserType` | String | `"customer"` or `"provider"` | `"provider"` |
| `jobId` | String (optional) | Related job | `"1001"` |
| `jobTitle` | String (optional) | Job title for context | `"Fix Kitchen Sink"` |
| `lastMessageAt` | Number | Timestamp of last message (ms) | `1704384060000` |
| `lastMessagePreview` | String | First 100 chars of last message | `"I can start tomorrow..."` |
| `unreadCount` | Number | Number of unread messages | `2` |
| `createdAt` | Number | When conversation started | `1704380000000` |

---

### Table 2: `quickfix_messages`

#### Primary Key Design
```
Partition Key: conversationId (String)
Sort Key: ts (Number - timestamp in milliseconds)
```

**Why this design?**
- Query: "Get all messages in conversation" → Very fast!
- Automatic chronological sorting (ts is the sort key)
- Easy pagination using timestamps
- Can query "messages before timestamp X"

#### Full Schema

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `conversationId` | String (PK) | Which conversation | `"conv_abc"` |
| `ts` | Number (SK) | Timestamp in milliseconds | `1704384060000` |
| `senderId` | String | Who sent the message | `"provider_john_456"` |
| `senderName` | String | Sender's display name | `"John Smith"` |
| `senderType` | String | `"customer"` or `"provider"` | `"provider"` |
| `text` | String | Message content | `"I can start tomorrow at 9 AM"` |
| `attachments` | List | Array of attachment objects | `[{type: "image", url: "..."}]` |
| `readBy` | List | Array of userIds who read it | `["provider_john_456"]` |
| `createdAt` | String | ISO timestamp | `"2026-01-04T14:01:00Z"` |

---

## Summary

### Two Tables = Two Purposes

**`quickfix_conversations`**:
- ✅ Fast inbox queries
- ✅ Per-user unread counts
- ✅ Last message preview
- ✅ Sort by recent activity
- 📊 Small table (2 rows per conversation)

**`quickfix_messages`**:
- ✅ Complete message history
- ✅ Chronological ordering
- ✅ Easy pagination
- ✅ Message search (future)
- 📊 Large table (grows with messages)
