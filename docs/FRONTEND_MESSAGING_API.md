# QuickFix Messaging API - Frontend Integration Guide

Complete documentation for integrating the QuickFix messaging system into your React frontend.

---

## Table of Contents

1. [Overview](#overview)
2. [Authentication](#authentication)
3. [API Endpoints](#api-endpoints)
4. [Integration Examples](#integration-examples)
5. [Error Handling](#error-handling)
6. [Best Practices](#best-practices)

---

## Overview

The QuickFix messaging system enables real-time communication between customers and service providers. It consists of:

- **DynamoDB Tables**: 
  - `quickfix_conversations` - Stores conversation metadata
  - `quickfix_messages` - Stores individual messages
- **5 API Endpoints**: Create conversations, list conversations, send messages, list messages, mark as read

**Base URL**: `https://kfvf20j7j9.execute-api.us-east-2.amazonaws.com/prod`

---

## Authentication

All messaging endpoints require JWT authentication via AWS Cognito.

### Getting the JWT Token

```javascript
// In your React app using react-oidc-context
import { useAuth } from 'react-oidc-context';

function MessagingComponent() {
  const auth = useAuth();
  const token = auth.user?.id_token;
  
  // Use this token in API requests
}
```

### Request Headers

```javascript
const headers = {
  'Authorization': `Bearer ${token}`,
  'Content-Type': 'application/json'
};
```

---

## API Endpoints

### 1. Create Conversation

Create a new conversation between the authenticated user and another user.

**Endpoint**: `POST /messages/conversations`

**Request Body**:
```json
{
  "otherUserId": "SP-ad86b044-9f9b-49b6-a53d-d3847afabe3c",
  "jobId": "1001"
}
```

**Response** (201 Created):
```json
{
  "conversationId": "550e8400-e29b-41d4-a716-446655440000",
  "otherUser": {
    "userId": "SP-ad86b044-9f9b-49b6-a53d-d3847afabe3c",
    "name": "John Smith",
    "type": "provider"
  },
  "jobId": "1001",
  "createdAt": 1704380000000
}
```

**React Example**:
```javascript
async function createConversation(otherUserId, jobId, token) {
  const response = await fetch(
    'https://kfvf20j7j9.execute-api.us-east-2.amazonaws.com/prod/messages/conversations',
    {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ otherUserId, jobId })
    }
  );
  
  if (!response.ok) {
    throw new Error('Failed to create conversation');
  }
  
  return await response.json();
}
```

---

### 2. List Conversations

Get all conversations for the authenticated user.

**Endpoint**: `GET /messages/conversations`

**Query Parameters**:
- `limit` (optional): Max conversations to return (default: 20, max: 50)

**Response** (200 OK):
```json
{
  "conversations": [
    {
      "conversationId": "550e8400-e29b-41d4-a716-446655440000",
      "otherUser": {
        "userId": "SP-ad86b044-9f9b-49b6-a53d-d3847afabe3c",
        "name": "John Smith",
        "type": "provider"
      },
      "jobId": "1001",
      "jobTitle": "Fix Kitchen Sink",
      "lastMessage": {
        "preview": "I can start tomorrow at 9 AM",
        "timestamp": 1704384000000
      },
      "unreadCount": 2,
      "createdAt": 1704380000000
    }
  ],
  "total": 5
}
```

**React Example**:
```javascript
async function fetchConversations(token, limit = 20) {
  const response = await fetch(
    `https://kfvf20j7j9.execute-api.us-east-2.amazonaws.com/prod/messages/conversations?limit=${limit}`,
    {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
    }
  );
  
  if (!response.ok) {
    throw new Error('Failed to fetch conversations');
  }
  
  return await response.json();
}
```

---

### 3. Send Message

Send a message in an existing conversation.

**Endpoint**: `POST /messages`

**Request Body**:
```json
{
  "conversationId": "550e8400-e29b-41d4-a716-446655440000",
  "text": "Hello, when can you start?"
}
```

**Response** (201 Created):
```json
{
  "messageId": 1704384000000,
  "conversationId": "550e8400-e29b-41d4-a716-446655440000",
  "senderId": "2",
  "senderName": "KunPeng Yang",
  "senderType": "customer",
  "text": "Hello, when can you start?",
  "timestamp": 1704384000000,
  "createdAt": "2026-01-04T14:00:00Z"
}
```

**React Example**:
```javascript
async function sendMessage(conversationId, text, token) {
  const response = await fetch(
    'https://kfvf20j7j9.execute-api.us-east-2.amazonaws.com/prod/messages',
    {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ conversationId, text })
    }
  );
  
  if (!response.ok) {
    throw new Error('Failed to send message');
  }
  
  return await response.json();
}
```

---

### 4. List Messages

Get all messages in a conversation.

**Endpoint**: `GET /messages/{conversationId}`

**Path Parameters**:
- `conversationId`: The conversation ID

**Query Parameters**:
- `limit` (optional): Max messages to return (default: 50, max: 100)
- `before` (optional): Timestamp to get messages before (for pagination)

**Response** (200 OK):
```json
{
  "messages": [
    {
      "messageId": 1704384000000,
      "senderId": "2",
      "senderName": "KunPeng Yang",
      "senderType": "customer",
      "text": "Hello, when can you start?",
      "timestamp": 1704384000000,
      "readBy": ["2"],
      "createdAt": "2026-01-04T14:00:00Z"
    }
  ],
  "total": 10,
  "hasMore": false
}
```

**React Example**:
```javascript
async function fetchMessages(conversationId, token, limit = 50, before = null) {
  let url = `https://kfvf20j7j9.execute-api.us-east-2.amazonaws.com/prod/messages/${conversationId}?limit=${limit}`;
  
  if (before) {
    url += `&before=${before}`;
  }
  
  const response = await fetch(url, {
    method: 'GET',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    }
  });
  
  if (!response.ok) {
    throw new Error('Failed to fetch messages');
  }
  
  return await response.json();
}
```

**Pagination Example**:
```javascript
// Load more messages (infinite scroll)
async function loadMoreMessages(conversationId, oldestTimestamp, token) {
  const data = await fetchMessages(conversationId, token, 50, oldestTimestamp);
  
  if (data.hasMore) {
    // There are more messages to load
    const newOldestTimestamp = data.messages[data.messages.length - 1].timestamp;
    // User can load more by calling loadMoreMessages again with newOldestTimestamp
  }
  
  return data.messages;
}
```

---

### 5. Mark Conversation as Read

Reset the unread count for a conversation to 0 and persist message-level read receipts.

**Endpoint**: `PUT /messages/conversations/{conversationId}/read`

**Path Parameters**:
- `conversationId`: The conversation ID

**Response** (200 OK):
```json
{
  "conversationId": "550e8400-e29b-41d4-a716-446655440000",
  "unreadCount": 0,
  "lastReadMessageId": "1704384000000",
  "readAt": 1704384050000,
  "message": "Conversation marked as read"
}
```

**Read Receipt Notes**:
- `lastReadMessageId` is the newest message confirmed as read
- `readAt` is the server timestamp in milliseconds
- The backend also updates `readBy` on unread messages in `quickfix_messages`
- If your app also uses websocket messaging, the other participant should receive a matching `conversationRead` push event

**React Example**:
```javascript
async function markConversationRead(conversationId, token) {
  const response = await fetch(
    `https://kfvf20j7j9.execute-api.us-east-2.amazonaws.com/prod/messages/conversations/${conversationId}/read`,
    {
      method: 'PUT',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
    }
  );
  
  if (!response.ok) {
    throw new Error('Failed to mark conversation as read');
  }
  
  return await response.json();
}
```

---

## Integration Examples

### Complete React Component Example

```javascript
import React, { useState, useEffect } from 'react';
import { useAuth } from 'react-oidc-context';

const API_BASE = 'https://kfvf20j7j9.execute-api.us-east-2.amazonaws.com/prod';

function MessagingPage() {
  const auth = useAuth();
  const [conversations, setConversations] = useState([]);
  const [selectedConversation, setSelectedConversation] = useState(null);
  const [messages, setMessages] = useState([]);
  const [newMessage, setNewMessage] = useState('');
  const [loading, setLoading] = useState(false);

  // Fetch conversations on mount
  useEffect(() => {
    if (auth.user?.id_token) {
      loadConversations();
    }
  }, [auth.user]);

  // Load conversations
  async function loadConversations() {
    try {
      setLoading(true);
      const response = await fetch(`${API_BASE}/messages/conversations`, {
        headers: {
          'Authorization': `Bearer ${auth.user.id_token}`,
          'Content-Type': 'application/json'
        }
      });
      
      if (!response.ok) throw new Error('Failed to load conversations');
      
      const data = await response.json();
      setConversations(data.conversations);
    } catch (error) {
      console.error('Error loading conversations:', error);
    } finally {
      setLoading(false);
    }
  }

  // Load messages for a conversation
  async function loadMessages(conversationId) {
    try {
      setLoading(true);
      const response = await fetch(
        `${API_BASE}/messages/${conversationId}`,
        {
          headers: {
            'Authorization': `Bearer ${auth.user.id_token}`,
            'Content-Type': 'application/json'
          }
        }
      );
      
      if (!response.ok) throw new Error('Failed to load messages');
      
      const data = await response.json();
      setMessages(data.messages.reverse()); // Oldest first for display
      
      // Mark as read
      await markAsRead(conversationId);
    } catch (error) {
      console.error('Error loading messages:', error);
    } finally {
      setLoading(false);
    }
  }

  // Send a message
  async function handleSendMessage(e) {
    e.preventDefault();
    
    if (!newMessage.trim() || !selectedConversation) return;
    
    try {
      const response = await fetch(`${API_BASE}/messages`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${auth.user.id_token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          conversationId: selectedConversation.conversationId,
          text: newMessage
        })
      });
      
      if (!response.ok) throw new Error('Failed to send message');
      
      const sentMessage = await response.json();
      
      // Add message to UI
      setMessages(prev => [...prev, sentMessage]);
      setNewMessage('');
      
      // Refresh conversations to update preview
      loadConversations();
    } catch (error) {
      console.error('Error sending message:', error);
    }
  }

  // Mark conversation as read
  async function markAsRead(conversationId) {
    try {
      await fetch(
        `${API_BASE}/messages/conversations/${conversationId}/read`,
        {
          method: 'PUT',
          headers: {
            'Authorization': `Bearer ${auth.user.id_token}`,
            'Content-Type': 'application/json'
          }
        }
      );
      
      // Update local state
      setConversations(prev => 
        prev.map(conv => 
          conv.conversationId === conversationId 
            ? { ...conv, unreadCount: 0 }
            : conv
        )
      );
    } catch (error) {
      console.error('Error marking as read:', error);
    }
  }

  // Select a conversation
  function selectConversation(conversation) {
    setSelectedConversation(conversation);
    loadMessages(conversation.conversationId);
  }

  return (
    <div className="messaging-container">
      {/* Conversations List */}
      <div className="conversations-sidebar">
        <h2>Messages</h2>
        {loading && <p>Loading...</p>}
        {conversations.map(conv => (
          <div
            key={conv.conversationId}
            className={`conversation-item ${
              selectedConversation?.conversationId === conv.conversationId 
                ? 'active' 
                : ''
            }`}
            onClick={() => selectConversation(conv)}
          >
            <div className="conversation-header">
              <strong>{conv.otherUser.name}</strong>
              {conv.unreadCount > 0 && (
                <span className="unread-badge">{conv.unreadCount}</span>
              )}
            </div>
            <div className="conversation-preview">
              {conv.lastMessage.preview}
            </div>
            <div className="conversation-meta">
              {conv.jobTitle} • {new Date(conv.lastMessage.timestamp).toLocaleDateString()}
            </div>
          </div>
        ))}
      </div>

      {/* Messages View */}
      <div className="messages-panel">
        {selectedConversation ? (
          <>
            <div className="messages-header">
              <h3>{selectedConversation.otherUser.name}</h3>
              <p>{selectedConversation.jobTitle}</p>
            </div>
            
            <div className="messages-list">
              {messages.map(msg => (
                <div
                  key={msg.messageId}
                  className={`message ${
                    msg.senderId === auth.user?.sub ? 'sent' : 'received'
                  }`}
                >
                  <div className="message-sender">{msg.senderName}</div>
                  <div className="message-text">{msg.text}</div>
                  <div className="message-time">
                    {new Date(msg.timestamp).toLocaleString()}
                  </div>
                </div>
              ))}
            </div>

            <form onSubmit={handleSendMessage} className="message-input">
              <input
                type="text"
                value={newMessage}
                onChange={(e) => setNewMessage(e.target.value)}
                placeholder="Type a message..."
              />
              <button type="submit">Send</button>
            </form>
          </>
        ) : (
          <div className="no-conversation">
            Select a conversation to start messaging
          </div>
        )}
      </div>
    </div>
  );
}

export default MessagingPage;
```

### Creating a Conversation from Job Details

```javascript
// In your JobDetails component
async function startConversation(providerId, jobId) {
  try {
    const response = await fetch(
      'https://kfvf20j7j9.execute-api.us-east-2.amazonaws.com/prod/messages/conversations',
      {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${auth.user.id_token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          otherUserId: providerId,
          jobId: jobId
        })
      }
    );
    
    if (!response.ok) {
      const error = await response.json();
      
      // Conversation already exists
      if (response.status === 409) {
        // Navigate to existing conversation
        navigate(`/messages/${error.conversationId}`);
        return;
      }
      
      throw new Error('Failed to create conversation');
    }
    
    const conversation = await response.json();
    
    // Navigate to new conversation
    navigate(`/messages/${conversation.conversationId}`);
  } catch (error) {
    console.error('Error creating conversation:', error);
    alert('Failed to start conversation');
  }
}
```

---

## Error Handling

### Common HTTP Status Codes

| Status Code | Meaning | Common Causes |
|-------------|---------|---------------|
| 200 | Success | Request completed successfully |
| 201 | Created | Resource created successfully |
| 400 | Bad Request | Missing required fields, invalid data |
| 401 | Unauthorized | Missing or invalid JWT token |
| 403 | Forbidden | User not part of conversation |
| 404 | Not Found | User or conversation not found |
| 409 | Conflict | Conversation already exists |
| 500 | Server Error | Database or internal error |

### Error Response Format

```json
{
  "message": "Error description",
  "conversationId": "existing-conversation-id" // Only for 409 errors
}
```

### Error Handling Example

```javascript
async function apiCall(url, options) {
  try {
    const response = await fetch(url, options);
    
    if (!response.ok) {
      const error = await response.json();
      
      switch (response.status) {
        case 401:
          // Token expired - redirect to login
          auth.signoutRedirect();
          break;
        case 403:
          alert('You do not have access to this conversation');
          break;
        case 404:
          alert('Conversation not found');
          break;
        case 409:
          // Conversation exists - navigate to it
          navigate(`/messages/${error.conversationId}`);
          break;
        default:
          alert(error.message || 'An error occurred');
      }
      
      throw new Error(error.message);
    }
    
    return await response.json();
  } catch (error) {
    console.error('API Error:', error);
    throw error;
  }
}
```

---

## Best Practices

### 1. Token Management

```javascript
// Always check token validity before API calls
function useApiCall() {
  const auth = useAuth();
  
  async function apiCall(url, options = {}) {
    if (!auth.user?.id_token) {
      throw new Error('Not authenticated');
    }
    
    // Check if token is expired
    const tokenExpiry = auth.user.expires_at;
    if (tokenExpiry && Date.now() / 1000 > tokenExpiry) {
      await auth.signinSilent(); // Refresh token
    }
    
    return fetch(url, {
      ...options,
      headers: {
        ...options.headers,
        'Authorization': `Bearer ${auth.user.id_token}`,
        'Content-Type': 'application/json'
      }
    });
  }
  
  return apiCall;
}
```

### 2. Real-time Updates

For real-time messaging, implement polling or WebSockets:

```javascript
// Simple polling example
useEffect(() => {
  if (!selectedConversation) return;
  
  const interval = setInterval(() => {
    loadMessages(selectedConversation.conversationId);
  }, 5000); // Poll every 5 seconds
  
  return () => clearInterval(interval);
}, [selectedConversation]);
```

### 3. Optimistic UI Updates

```javascript
async function sendMessageOptimistic(text) {
  // Add message to UI immediately
  const optimisticMessage = {
    messageId: Date.now(),
    text,
    senderId: auth.user.sub,
    senderName: 'You',
    timestamp: Date.now(),
    pending: true
  };
  
  setMessages(prev => [...prev, optimisticMessage]);
  setNewMessage('');
  
  try {
    // Send to server
    const response = await fetch(`${API_BASE}/messages`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${auth.user.id_token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        conversationId: selectedConversation.conversationId,
        text
      })
    });
    
    const sentMessage = await response.json();
    
    // Replace optimistic message with real one
    setMessages(prev => 
      prev.map(msg => 
        msg.messageId === optimisticMessage.messageId 
          ? sentMessage 
          : msg
      )
    );
  } catch (error) {
    // Remove optimistic message on error
    setMessages(prev => 
      prev.filter(msg => msg.messageId !== optimisticMessage.messageId)
    );
    alert('Failed to send message');
  }
}
```

### 4. Unread Count Badge

```javascript
// Calculate total unread messages
function UnreadBadge() {
  const [totalUnread, setTotalUnread] = useState(0);
  
  useEffect(() => {
    async function fetchUnread() {
      const data = await fetchConversations(auth.user.id_token);
      const total = data.conversations.reduce(
        (sum, conv) => sum + conv.unreadCount, 
        0
      );
      setTotalUnread(total);
    }
    
    fetchUnread();
    
    // Poll for updates
    const interval = setInterval(fetchUnread, 30000); // Every 30 seconds
    return () => clearInterval(interval);
  }, []);
  
  return totalUnread > 0 ? (
    <span className="badge">{totalUnread}</span>
  ) : null;
}
```

### 5. Message Formatting

```javascript
// Format timestamps
function formatMessageTime(timestamp) {
  const date = new Date(timestamp);
  const now = new Date();
  const diffMs = now - date;
  const diffMins = Math.floor(diffMs / 60000);
  
  if (diffMins < 1) return 'Just now';
  if (diffMins < 60) return `${diffMins}m ago`;
  
  const diffHours = Math.floor(diffMins / 60);
  if (diffHours < 24) return `${diffHours}h ago`;
  
  return date.toLocaleDateString();
}

// Truncate preview text
function truncatePreview(text, maxLength = 50) {
  if (text.length <= maxLength) return text;
  return text.substring(0, maxLength) + '...';
}
```

---

## Summary

The QuickFix messaging API provides a complete solution for customer-provider communication:

✅ **5 Endpoints**: Create, list, send, retrieve, and mark as read  
✅ **JWT Authentication**: Secure access via AWS Cognito  
✅ **Pagination Support**: Efficient loading of conversations and messages  
✅ **Unread Tracking**: Automatic unread count management  
✅ **Job Context**: Messages linked to specific jobs  

For additional help or questions, refer to the backend documentation or contact the development team.
