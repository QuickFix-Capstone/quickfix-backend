# QuickFix WebSocket Messaging – Frontend Integration Guide

Complete integration guide for **Customer** and **Service Provider** frontends to implement real-time messaging using the QuickFix WebSocket API.

---

## Table of Contents

1. [Overview](#1-overview)
2. [Prerequisites](#2-prerequisites)
3. [Connection Setup](#3-connection-setup)
4. [Message Protocol](#4-message-protocol)
5. [Actions Reference](#5-actions-reference)
6. [Push Events Reference](#6-push-events-reference)
7. [Error Handling](#7-error-handling)
8. [WebSocket Client Class](#8-websocket-client-class)
9. [React Hook](#9-react-hook)
10. [Full React Component Example](#10-full-react-component-example)
11. [Best Practices](#11-best-practices)
12. [Testing with wscat](#12-testing-with-wscat)
13. [HTTP Fallback (Backward Compatibility)](#13-http-fallback-backward-compatibility)

---

## 1. Overview

The WebSocket API provides **real-time, bidirectional messaging** for both customers and service providers. Both user types connect to the **same** WebSocket endpoint and use the **same** actions. The backend identifies the user type automatically from the JWT token.

### What You Can Do

| Feature | Action | Push Event |
|---------|--------|------------|
| Send a message | `sendMessage` | Recipient gets `newMessage` |
| Fetch message history | `getMessages` | — |
| List conversations | `getConversations` | — |
| Mark conversation read | `markRead` | Other party gets `conversationRead` |
| Typing indicator | `typing` | Other party gets `typing` |
| Keep-alive | `ping` | `PONG` |

### Architecture

```
Customer App ──┐                                   ┌── DynamoDB (messages)
               ├── WebSocket API ── Lambda Handler ─┤
Provider App ──┘                                   └── DynamoDB (conversations)
```

---

## 2. Prerequisites

| Item | Details |
|------|---------|
| **WebSocket URL** | `wss://<API_ID>.execute-api.us-east-2.amazonaws.com/prod` |
| **Auth** | Cognito JWT **ID Token** passed as query param `?token=<JWT>` |
| **User Pool** | Same Cognito User Pool for both customers and providers |
| **Conversation** | Must be created via HTTP `POST /messages/conversations` before messaging |

> [!IMPORTANT]
> The WebSocket API does **not** support creating conversations. Use the existing HTTP endpoint `POST /messages/conversations` to create a conversation first, then use the WebSocket for messaging within that conversation.

---

## 3. Connection Setup

### Connecting

```javascript
const WS_URL = 'wss://<API_ID>.execute-api.us-east-2.amazonaws.com/prod';
const token = auth.user.id_token; // Cognito ID token

const ws = new WebSocket(`${WS_URL}?token=${token}`);
```

### Connection Lifecycle

```
1. Client opens WebSocket with ?token=<JWT>
   ↓
2. Backend validates JWT → stores connection in DynamoDB
   ↓
3. Connection is OPEN → start sending ping every 30s
   ↓
4. Send/receive messages in real time
   ↓
5. On disconnect → auto-reconnect with exponential backoff
   ↓
6. Connection auto-expires after 2 hours (refresh with ping)
```

### Keep-Alive (Required)

Send a `ping` action every **30 seconds** to prevent timeout:

```javascript
setInterval(() => {
  if (ws.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify({ action: 'ping' }));
  }
}, 30000);
```

**Response:**
```json
{ "type": "PONG", "ts": 1704380000 }
```

---

## 4. Message Protocol

All messages between client and server are JSON. There are three message shapes:

### 4.1 Request (Client → Server)

```json
{
  "action": "<actionName>",
  "data": { ... },
  "requestId": "<client-generated-unique-id>"
}
```

- `action` – route name (e.g. `sendMessage`, `getMessages`)
- `data` – action-specific payload
- `requestId` – optional but recommended; used to match the response to your request

### 4.2 Response (Server → Client)

**Success:**
```json
{
  "type": "response",
  "action": "<actionName>",
  "requestId": "<your-requestId>",
  "success": true,
  "data": { ... }
}
```

**Error:**
```json
{
  "type": "response",
  "action": "<actionName>",
  "requestId": "<your-requestId>",
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "conversationId and text are required"
  }
}
```

### 4.3 Push Event (Server → Client, unsolicited)

```json
{
  "type": "event",
  "event": "<eventName>",
  "data": { ... }
}
```

Push events arrive **without you asking** – e.g. when the other person sends you a message.

---

## 5. Actions Reference

### 5.1 `sendMessage`

Send a text message in an existing conversation.

**Request:**
```json
{
  "action": "sendMessage",
  "requestId": "req-001",
  "data": {
    "conversationId": "conv-uuid-123",
    "text": "Hello! When can you come fix my sink?"
  }
}
```

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `conversationId` | string | ✅ | UUID of the conversation |
| `text` | string | ✅ | Message text (whitespace-trimmed, max preview 100 chars) |

**Success Response:**
```json
{
  "type": "response",
  "action": "sendMessage",
  "requestId": "req-001",
  "success": true,
  "data": {
    "messageId": 1704384000000,
    "conversationId": "conv-uuid-123",
    "senderId": "42",
    "senderName": "Jane Doe",
    "senderType": "customer",
    "text": "Hello! When can you come fix my sink?",
    "timestamp": 1704384000000,
    "createdAt": "2026-01-04T16:00:00Z"
  }
}
```

**Side Effects:**
- Message saved to `quickfix_messages` table
- Sender's conversation metadata updated (`lastMessageAt`, `lastMessagePreview`)
- Recipient's conversation updated (same + `unreadCount` incremented)
- Recipient receives a **`newMessage`** push event in real time

---

### 5.2 `getMessages`

Fetch message history for a conversation (paginated, newest first).

**Request:**
```json
{
  "action": "getMessages",
  "requestId": "req-002",
  "data": {
    "conversationId": "conv-uuid-123",
    "limit": 50,
    "before": 1704384000000
  }
}
```

| Field | Type | Required | Default | Notes |
|-------|------|----------|---------|-------|
| `conversationId` | string | ✅ | — | UUID of the conversation |
| `limit` | number | ❌ | `50` | 1–100 |
| `before` | number | ❌ | — | Timestamp (ms); fetch messages older than this for pagination |

**Success Response:**
```json
{
  "type": "response",
  "action": "getMessages",
  "requestId": "req-002",
  "success": true,
  "data": {
    "messages": [
      {
        "messageId": 1704384000000,
        "senderId": "42",
        "senderName": "Jane Doe",
        "senderType": "customer",
        "text": "Hello!",
        "timestamp": 1704384000000,
        "readBy": ["42"],
        "createdAt": "2026-01-04T16:00:00Z"
      }
    ],
    "total": 1,
    "hasMore": false
  }
}
```

> [!NOTE]
> Messages are returned **newest first** (descending by timestamp). Reverse the array if you need chronological order for display.

**Pagination Example:**
```javascript
// First page
const page1 = await ws.send('getMessages', { conversationId: 'conv-123', limit: 20 });

// Next page – use the oldest timestamp from page1
if (page1.hasMore) {
  const oldest = page1.messages[page1.messages.length - 1].timestamp;
  const page2 = await ws.send('getMessages', { conversationId: 'conv-123', limit: 20, before: oldest });
}
```

---

### 5.3 `getConversations`

List all conversations for the authenticated user, sorted by most recent message.

**Request:**
```json
{
  "action": "getConversations",
  "requestId": "req-003",
  "data": {
    "limit": 20
  }
}
```

| Field | Type | Required | Default | Notes |
|-------|------|----------|---------|-------|
| `limit` | number | ❌ | `20` | 1–50 |

**Success Response:**
```json
{
  "type": "response",
  "action": "getConversations",
  "requestId": "req-003",
  "success": true,
  "data": {
    "conversations": [
      {
        "conversationId": "conv-uuid-123",
        "otherUser": {
          "userId": "7",
          "name": "Mike's Plumbing",
          "type": "provider"
        },
        "jobId": "1001",
        "jobTitle": "Fix kitchen sink",
        "lastMessage": {
          "preview": "I'll be there at 3pm",
          "timestamp": 1704384000000
        },
        "unreadCount": 2,
        "createdAt": 1704380000000
      }
    ],
    "total": 1
  }
}
```

| Field | Description |
|-------|-------------|
| `otherUser.userId` | App-level user ID of the other party |
| `otherUser.name` | Display name of the other party |
| `otherUser.type` | `"customer"` or `"provider"` |
| `jobId` | ID of the job this conversation is about |
| `jobTitle` | Title of the job |
| `unreadCount` | Number of unread messages |
| `lastMessage.preview` | First 100 chars of the most recent message |
| `lastMessage.timestamp` | Timestamp (ms) of the most recent message |

---

### 5.4 `markRead`

Mark a conversation as read—resets `unreadCount` to `0`.

**Request:**
```json
{
  "action": "markRead",
  "requestId": "req-004",
  "data": {
    "conversationId": "conv-uuid-123"
  }
}
```

| Field | Type | Required |
|-------|------|----------|
| `conversationId` | string | ✅ |

**Success Response:**
```json
{
  "type": "response",
  "action": "markRead",
  "requestId": "req-004",
  "success": true,
  "data": {
    "conversationId": "conv-uuid-123",
    "unreadCount": 0
  }
}
```

**Side Effects:**
- The other user receives a **`conversationRead`** push event

---

### 5.5 `typing`

Send a typing indicator to the other user. This is **ephemeral** (not stored in the database).

**Request:**
```json
{
  "action": "typing",
  "data": {
    "conversationId": "conv-uuid-123",
    "isTyping": true
  }
}
```

| Field | Type | Required | Default | Notes |
|-------|------|----------|---------|-------|
| `conversationId` | string | ✅ | — | — |
| `isTyping` | boolean | ❌ | `true` | `true` = started typing, `false` = stopped |

**Success Response:**
```json
{
  "type": "response",
  "action": "typing",
  "success": true,
  "data": {
    "conversationId": "conv-uuid-123",
    "isTyping": true
  }
}
```

**Side Effects:**
- The other user receives a **`typing`** push event

> [!TIP]
> **Debounce typing events.** Don't send `typing` on every keystroke. Instead, send `isTyping: true` when the user starts typing and `isTyping: false` after 2–3 seconds of inactivity. This reduces unnecessary WebSocket traffic.

---

## 6. Push Events Reference

Push events are messages sent **from the server to your client without a corresponding request**. Subscribe to these to update your UI in real time.

### 6.1 `newMessage`

Received when the other user sends you a message.

```json
{
  "type": "event",
  "event": "newMessage",
  "data": {
    "conversationId": "conv-uuid-123",
    "messageId": 1704384000000,
    "senderId": "7",
    "senderName": "Mike's Plumbing",
    "senderType": "provider",
    "text": "I'll be there at 3pm",
    "timestamp": 1704384000000,
    "createdAt": "2026-01-04T16:00:00Z"
  }
}
```

**Frontend Actions:**
- Append the message to the chat view if the conversation is open
- Update the conversation list preview and timestamp
- Increment unread count badge if the conversation is not currently active
- Play a notification sound (optional)

---

### 6.2 `typing`

Received when the other user starts or stops typing.

```json
{
  "type": "event",
  "event": "typing",
  "data": {
    "conversationId": "conv-uuid-123",
    "userId": "7",
    "userName": "Mike's Plumbing",
    "isTyping": true
  }
}
```

**Frontend Actions:**
- Show "Mike's Plumbing is typing…" indicator in the chat view
- Hide the indicator when `isTyping: false` is received
- Auto-hide after a timeout (e.g. 5 seconds) in case the `false` event is missed

---

### 6.3 `conversationRead`

Received when the other user reads your messages (i.e. they called `markRead`).

```json
{
  "type": "event",
  "event": "conversationRead",
  "data": {
    "conversationId": "conv-uuid-123",
    "readByUserId": "7"
  }
}
```

**Frontend Actions:**
- Show read receipt indicators (e.g. double checkmarks) on your sent messages
- Update message status from "delivered" to "read"

---

## 7. Error Handling

### Error Response Format

```json
{
  "type": "response",
  "action": "<actionName>",
  "requestId": "<your-requestId>",
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable description"
  }
}
```

### Error Codes

| Code | Meaning | Recommended Action |
|------|---------|-------------------|
| `UNAUTHORIZED` | Connection not authenticated | Reconnect with a fresh JWT token |
| `USER_NOT_FOUND` | User not found in database | Verify the user account exists |
| `VALIDATION_ERROR` | Missing or invalid request fields | Check your request payload |
| `FORBIDDEN` | Not a member of this conversation | Verify the `conversationId` |
| `DDB_ERROR` | Server-side database error | Retry after a delay |
| `REQUEST_FAILED` | Generic failure | Retry or report to support |

### Connection Error Codes

| WebSocket Close Code | Meaning | Action |
|---------------------|---------|--------|
| `1000` | Normal closure | No action |
| `1008` | Policy violation (auth failed) | Refresh Cognito token, reconnect |
| `1011` | Server error | Retry with backoff |

---

## 8. WebSocket Client Class

A copy-paste ready client class for both Customer and Provider frontends.

```javascript
// src/services/WebSocketMessagingClient.js

class WebSocketMessagingClient {
  constructor(wsUrl, token) {
    this.wsUrl = wsUrl;
    this.token = token;
    this.ws = null;
    this.listeners = new Map();
    this.pendingRequests = new Map();
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 5;
    this.reconnectDelay = 1000;
    this.pingInterval = null;
  }

  // ── Connection Management ──────────────────────────

  connect() {
    const url = `${this.wsUrl}?token=${this.token}`;
    this.ws = new WebSocket(url);

    this.ws.onopen = () => {
      console.log('✅ WebSocket connected');
      this.reconnectAttempts = 0;
      this.reconnectDelay = 1000;
      this._startPing();
      this._emit('connected');
    };

    this.ws.onmessage = (event) => {
      const msg = JSON.parse(event.data);
      this._handleMessage(msg);
    };

    this.ws.onerror = (error) => {
      console.error('❌ WebSocket error:', error);
      this._emit('error', error);
    };

    this.ws.onclose = () => {
      console.log('🔌 WebSocket disconnected');
      this._stopPing();
      this._emit('disconnected');
      this._attemptReconnect();
    };
  }

  disconnect() {
    this.maxReconnectAttempts = 0; // prevent auto-reconnect
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
    this._stopPing();
  }

  updateToken(newToken) {
    this.token = newToken;
  }

  // ── Messaging Actions ─────────────────────────────

  sendMessage(conversationId, text) {
    return this._request('sendMessage', { conversationId, text });
  }

  getMessages(conversationId, limit = 50, before = null) {
    const data = { conversationId, limit };
    if (before !== null) data.before = before;
    return this._request('getMessages', data);
  }

  getConversations(limit = 20) {
    return this._request('getConversations', { limit });
  }

  markRead(conversationId) {
    return this._request('markRead', { conversationId });
  }

  sendTyping(conversationId, isTyping = true) {
    // Fire-and-forget (no promise needed)
    this._send({ action: 'typing', data: { conversationId, isTyping } });
  }

  // ── Event Subscription ────────────────────────────

  on(event, callback) {
    if (!this.listeners.has(event)) this.listeners.set(event, []);
    this.listeners.get(event).push(callback);
    return () => this.off(event, callback); // return unsubscribe function
  }

  off(event, callback) {
    const cbs = this.listeners.get(event);
    if (cbs) {
      const idx = cbs.indexOf(callback);
      if (idx > -1) cbs.splice(idx, 1);
    }
  }

  // ── Internal Methods ──────────────────────────────

  _request(action, data) {
    return new Promise((resolve, reject) => {
      const requestId = `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;

      this.pendingRequests.set(requestId, { resolve, reject });
      this._send({ action, data, requestId });

      // Timeout after 30 seconds
      setTimeout(() => {
        if (this.pendingRequests.has(requestId)) {
          this.pendingRequests.delete(requestId);
          reject(new Error(`Request timeout: ${action}`));
        }
      }, 30000);
    });
  }

  _send(payload) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(payload));
    } else {
      console.warn('WebSocket not open, cannot send:', payload.action);
    }
  }

  _handleMessage(msg) {
    if (msg.type === 'PONG') return;

    if (msg.type === 'response' && msg.requestId) {
      const pending = this.pendingRequests.get(msg.requestId);
      if (pending) {
        this.pendingRequests.delete(msg.requestId);
        if (msg.success) {
          pending.resolve(msg.data);
        } else {
          pending.reject(new Error(msg.error?.message || 'Request failed'));
        }
      }
    } else if (msg.type === 'event') {
      this._emit(msg.event, msg.data);
    }
  }

  _emit(event, data) {
    const cbs = this.listeners.get(event);
    if (cbs) cbs.forEach(cb => cb(data));
  }

  _startPing() {
    this.pingInterval = setInterval(() => {
      this._send({ action: 'ping' });
    }, 30000);
  }

  _stopPing() {
    if (this.pingInterval) {
      clearInterval(this.pingInterval);
      this.pingInterval = null;
    }
  }

  _attemptReconnect() {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1);
      console.log(`🔄 Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts})`);
      setTimeout(() => this.connect(), delay);
    } else {
      this._emit('reconnectFailed');
    }
  }
}

export default WebSocketMessagingClient;
```

---

## 9. React Hook

```javascript
// src/hooks/useMessagingWebSocket.js

import { useEffect, useRef, useState, useCallback } from 'react';
import { useAuth } from 'react-oidc-context';
import WebSocketMessagingClient from '../services/WebSocketMessagingClient';

const WS_URL = 'wss://<API_ID>.execute-api.us-east-2.amazonaws.com/prod';

export function useMessagingWebSocket() {
  const auth = useAuth();
  const [isConnected, setIsConnected] = useState(false);
  const wsRef = useRef(null);

  useEffect(() => {
    const token = auth.user?.id_token;
    if (!token) return;

    const client = new WebSocketMessagingClient(WS_URL, token);

    client.on('connected', () => setIsConnected(true));
    client.on('disconnected', () => setIsConnected(false));
    client.on('reconnectFailed', () => setIsConnected(false));

    client.connect();
    wsRef.current = client;

    return () => {
      client.disconnect();
      wsRef.current = null;
    };
  }, [auth.user?.id_token]);

  return { ws: wsRef.current, isConnected };
}
```

---

## 10. Full React Component Example

Works identically for **Customer** and **Provider** apps.

```javascript
// src/pages/MessagingPage.jsx

import React, { useState, useEffect, useRef } from 'react';
import { useMessagingWebSocket } from '../hooks/useMessagingWebSocket';

function MessagingPage() {
  const { ws, isConnected } = useMessagingWebSocket();
  const [conversations, setConversations] = useState([]);
  const [activeConvId, setActiveConvId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [inputText, setInputText] = useState('');
  const [typingUser, setTypingUser] = useState(null);
  const typingTimeout = useRef(null);

  // ── Load conversations on connect ─────────────────
  useEffect(() => {
    if (!ws || !isConnected) return;
    ws.getConversations().then(data => setConversations(data.conversations));
  }, [ws, isConnected]);

  // ── Subscribe to push events ──────────────────────
  useEffect(() => {
    if (!ws) return;

    const unsubMessage = ws.on('newMessage', (data) => {
      // Append to chat if this conversation is open
      if (data.conversationId === activeConvId) {
        setMessages(prev => [...prev, data]);
      }
      // Update conversation list preview
      setConversations(prev =>
        prev.map(c =>
          c.conversationId === data.conversationId
            ? {
                ...c,
                lastMessage: { preview: data.text, timestamp: data.timestamp },
                unreadCount: data.conversationId === activeConvId ? 0 : c.unreadCount + 1,
              }
            : c
        )
      );
    });

    const unsubTyping = ws.on('typing', (data) => {
      if (data.conversationId === activeConvId) {
        if (data.isTyping) {
          setTypingUser(data.userName);
          // Auto-clear after 5 seconds
          clearTimeout(typingTimeout.current);
          typingTimeout.current = setTimeout(() => setTypingUser(null), 5000);
        } else {
          setTypingUser(null);
        }
      }
    });

    const unsubRead = ws.on('conversationRead', (data) => {
      console.log(`${data.readByUserId} read conversation ${data.conversationId}`);
      // Update your UI to show read receipts
    });

    return () => {
      unsubMessage();
      unsubTyping();
      unsubRead();
    };
  }, [ws, activeConvId]);

  // ── Select a conversation ─────────────────────────
  async function openConversation(convId) {
    setActiveConvId(convId);
    setMessages([]);
    setTypingUser(null);

    const data = await ws.getMessages(convId);
    setMessages(data.messages.reverse()); // API returns newest-first

    await ws.markRead(convId);
    // Reset unread count locally
    setConversations(prev =>
      prev.map(c => (c.conversationId === convId ? { ...c, unreadCount: 0 } : c))
    );
  }

  // ── Send a message ────────────────────────────────
  async function handleSend(e) {
    e.preventDefault();
    if (!inputText.trim() || !activeConvId) return;

    try {
      const result = await ws.sendMessage(activeConvId, inputText);
      setMessages(prev => [...prev, result]);
      setInputText('');
      ws.sendTyping(activeConvId, false);
    } catch (err) {
      alert('Failed to send: ' + err.message);
    }
  }

  // ── Typing indicator ─────────────────────────────
  let sendTypingTimeout = useRef(null);
  function handleInputChange(e) {
    setInputText(e.target.value);
    if (!activeConvId || !ws) return;

    ws.sendTyping(activeConvId, true);
    clearTimeout(sendTypingTimeout.current);
    sendTypingTimeout.current = setTimeout(() => {
      ws.sendTyping(activeConvId, false);
    }, 2000);
  }

  // ── Render ────────────────────────────────────────
  return (
    <div style={{ display: 'flex', height: '100vh' }}>
      {/* Connection indicator */}
      <div style={{ position: 'fixed', top: 8, right: 8 }}>
        {isConnected ? '🟢 Connected' : '🔴 Disconnected'}
      </div>

      {/* Sidebar: conversation list */}
      <div style={{ width: 300, borderRight: '1px solid #ccc', overflowY: 'auto' }}>
        {conversations.map(c => (
          <div
            key={c.conversationId}
            onClick={() => openConversation(c.conversationId)}
            style={{
              padding: 12, cursor: 'pointer',
              background: c.conversationId === activeConvId ? '#e3f2fd' : 'transparent'
            }}
          >
            <strong>{c.otherUser.name}</strong>
            {c.unreadCount > 0 && <span> ({c.unreadCount})</span>}
            <div style={{ fontSize: 12, color: '#666' }}>
              {c.lastMessage.preview}
            </div>
          </div>
        ))}
      </div>

      {/* Main: messages */}
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
        <div style={{ flex: 1, overflowY: 'auto', padding: 16 }}>
          {messages.map(m => (
            <div key={m.messageId} style={{ marginBottom: 8 }}>
              <strong>{m.senderName}:</strong> {m.text}
            </div>
          ))}
          {typingUser && (
            <div style={{ color: '#999', fontStyle: 'italic' }}>
              {typingUser} is typing…
            </div>
          )}
        </div>

        <form onSubmit={handleSend} style={{ display: 'flex', padding: 8 }}>
          <input
            value={inputText}
            onChange={handleInputChange}
            placeholder="Type a message…"
            style={{ flex: 1, padding: 8 }}
          />
          <button type="submit" style={{ padding: '8px 16px' }}>Send</button>
        </form>
      </div>
    </div>
  );
}

export default MessagingPage;
```

---

## 11. Best Practices

### For Both Frontends

| Practice | Details |
|----------|---------|
| **Debounce typing events** | Send `typing: true` once, then `typing: false` after 2s of inactivity |
| **Auto-clear typing indicator** | Clear after 5s even if no `typing: false` is received |
| **Reconnect with backoff** | Use exponential backoff: 1s → 2s → 4s → 8s → 16s (max 30s) |
| **Token refresh on reconnect** | If the JWT expires, refresh it before reconnecting |
| **Optimistic UI** | Show the sent message immediately; remove on error |
| **Mark read on open** | Call `markRead()` when the user opens/views a conversation |
| **Reverse messages** | `getMessages` returns newest-first; call `.reverse()` for display |
| **Clean up on unmount** | Call `ws.disconnect()` when the component unmounts or user logs out |

### Typing Indicator – Recommended Pattern

```javascript
let typingTimer = null;

function onInputChange(text) {
  ws.sendTyping(conversationId, true);

  clearTimeout(typingTimer);
  typingTimer = setTimeout(() => {
    ws.sendTyping(conversationId, false);
  }, 2000); // 2 seconds after user stops typing
}
```

### Handling Offline / Disconnection

```javascript
// Queue messages when offline
const messageQueue = [];

function sendMessage(conversationId, text) {
  if (isConnected) {
    return ws.sendMessage(conversationId, text);
  } else {
    messageQueue.push({ conversationId, text });
    return Promise.resolve({ queued: true });
  }
}

// Flush queue on reconnect
ws.on('connected', async () => {
  while (messageQueue.length > 0) {
    const msg = messageQueue.shift();
    await ws.sendMessage(msg.conversationId, msg.text);
  }
});
```

---

## 12. Testing with wscat

```bash
# Install wscat
npm install -g wscat

# Connect (replace with your actual API ID and JWT token)
wscat -c "wss://<API_ID>.execute-api.us-east-2.amazonaws.com/prod?token=<JWT_TOKEN>"

# Test ping
> {"action":"ping"}
< {"type":"PONG","ts":1704380000}

# Get conversations
> {"action":"getConversations","data":{"limit":10},"requestId":"test-1"}
< {"type":"response","action":"getConversations","requestId":"test-1","success":true,"data":{...}}

# Send a message
> {"action":"sendMessage","data":{"conversationId":"YOUR-CONV-ID","text":"Hello from wscat!"},"requestId":"test-2"}
< {"type":"response","action":"sendMessage","requestId":"test-2","success":true,"data":{...}}

# Get messages
> {"action":"getMessages","data":{"conversationId":"YOUR-CONV-ID","limit":10},"requestId":"test-3"}
< {"type":"response","action":"getMessages","requestId":"test-3","success":true,"data":{...}}

# Mark read
> {"action":"markRead","data":{"conversationId":"YOUR-CONV-ID"},"requestId":"test-4"}

# Typing indicator
> {"action":"typing","data":{"conversationId":"YOUR-CONV-ID","isTyping":true}}
```

---

## 13. HTTP Fallback (Backward Compatibility)

The existing HTTP REST API remains fully functional. Use it as a fallback if the WebSocket connection fails.

| HTTP Endpoint | Equivalent WS Action |
|---------------|---------------------|
| `POST /messages/conversations` | *(No WS equivalent – use HTTP to create conversations)* |
| `GET /messages/conversations` | `getConversations` |
| `POST /messages` | `sendMessage` |
| `GET /messages/{conversationId}` | `getMessages` |
| `PUT /messages/conversations/{conversationId}/read` | `markRead` |

**Base URL:** `https://kfvf20j7j9.execute-api.us-east-2.amazonaws.com/prod`

> [!WARNING]
> The HTTP API does **not** support typing indicators or push events. These features are WebSocket-only.

---

**Last Updated:** February 22, 2026
**Status:** Phase 2 Complete – Ready for Frontend Integration
