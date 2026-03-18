# Frontend: Message Read Receipts Integration Guide

This guide covers the frontend changes needed to support message read receipts with the current backend.

## What Changed

When a user opens a conversation and marks it as read:

- The backend resets `unreadCount` for that conversation
- The backend updates `readBy` on each unread message in `quickfix_messages`
- The backend returns `lastReadMessageId` and `readAt`
- The other participant receives a `conversationRead` websocket event with the same fields

## WebSocket Event Contract

The sender receives this push event when the other user reads the conversation:

```json
{
  "type": "event",
  "event": "conversationRead",
  "data": {
    "conversationId": "conv-uuid-123",
    "readByUserId": "7",
    "lastReadMessageId": "1704384000000",
    "readAt": 1704384050000
  }
}
```

Field meaning:

- `conversationId`: conversation that was read
- `readByUserId`: user who opened and read the conversation
- `lastReadMessageId`: newest message now confirmed read
- `readAt`: read timestamp in milliseconds

## `markRead` Response Contract

When the active user calls websocket `markRead`, the success response is:

```json
{
  "type": "response",
  "action": "markRead",
  "requestId": "req-004",
  "success": true,
  "data": {
    "conversationId": "conv-uuid-123",
    "unreadCount": 0,
    "lastReadMessageId": "1704384000000",
    "readAt": 1704384050000
  }
}
```

The HTTP fallback `PUT /messages/conversations/{conversationId}/read` now returns the same read-receipt fields:

```json
{
  "conversationId": "conv-uuid-123",
  "unreadCount": 0,
  "lastReadMessageId": "1704384000000",
  "readAt": 1704384050000,
  "message": "Conversation marked as read"
}
```

## Expected Message Shape

Messages returned from `getMessages` already include:

```json
{
  "messageId": 1704384000000,
  "senderId": "42",
  "text": "Hello",
  "timestamp": 1704384000000,
  "readBy": ["42", "7"],
  "createdAt": "2026-01-04T16:00:00Z"
}
```

Frontend rule:

- A sent message should be shown as read when the other participant's ID appears in `readBy`
- For live updates, use `lastReadMessageId` to mark all eligible sent messages up to that message as read

## Recommended Frontend State Update

Use the read event to update only your own sent messages in that conversation.

```ts
function applyConversationReadReceipt(messages, eventData, currentUserId) {
  const lastReadId = Number(eventData.lastReadMessageId);
  if (!lastReadId) return messages;

  return messages.map((message) => {
    const isOwnMessage = String(message.senderId) === String(currentUserId);
    const isInRange = Number(message.messageId) <= lastReadId;
    if (!isOwnMessage || !isInRange) return message;

    const readBy = new Set(message.readBy || []);
    readBy.add(String(eventData.readByUserId));

    return {
      ...message,
      readBy: Array.from(readBy),
      readAt: eventData.readAt ?? message.readAt,
    };
  });
}
```

## React WebSocket Example

```ts
useEffect(() => {
  if (!ws) return;

  const unsubscribe = ws.on("conversationRead", (data) => {
    if (data.conversationId !== activeConversationId) return;
    if (!data.lastReadMessageId) return;

    setMessages((prev) =>
      applyConversationReadReceipt(prev, data, currentUserId)
    );
  });

  return unsubscribe;
}, [ws, activeConversationId, currentUserId]);
```

## When To Call `markRead`

- Call `markRead(conversationId)` after loading messages for the opened conversation
- Also call it when returning to an already-open conversation after receiving new messages
- Do not call it for background conversations the user has not viewed

## UI Recommendation

For sent messages:

- No other reader in `readBy`: show `Sent` or single check
- Other participant added to `readBy`: show `Read` or double check

For received messages:

- Do not show outgoing read-receipt indicators

## Refresh Behavior

On refresh, do not rely only on cached websocket events.

- Reload messages from `getMessages`
- Use persisted `readBy` arrays to reconstruct read state
- Websocket `conversationRead` should only be treated as the real-time update path

## Edge Cases

- If `lastReadMessageId` is `null`, do not force-read messages locally
- If a websocket event arrives before messages finish loading, apply it after message hydration
- If the same event is received twice, the `readBy` update should remain idempotent

## Frontend Checklist

- Subscribe to `conversationRead`
- Use `lastReadMessageId` instead of expecting a single `messageId`
- Update only the current user's sent messages
- Persist read state from `getMessages.readBy` after refresh
- Clear local conversation `unreadCount` after successful `markRead`
