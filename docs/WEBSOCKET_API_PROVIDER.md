# QuickFix WebSocket API - Service Provider Integration Guide

Complete documentation for integrating real-time WebSocket notifications into your service provider application.

---

## Table of Contents

1. [Overview](#overview)
2. [Authentication](#authentication)
3. [Connection Management](#connection-management)
4. [Message Types](#message-types)
5. [Integration Examples](#integration-examples)
6. [Error Handling](#error-handling)
7. [Best Practices](#best-practices)

---

## Overview

The QuickFix WebSocket API enables real-time, bidirectional communication between the backend and service provider applications. Service providers receive instant notifications about job status changes, new job applications, and other important events.

### Key Features

- **Real-time Notifications**: Receive instant updates without polling
- **Automatic Reconnection**: Built-in connection management
- **JWT Authentication**: Secure connections using Cognito tokens
- **Connection Persistence**: Connections maintained for up to 2 hours with automatic TTL refresh

### WebSocket Endpoint

```
wss://<API_ID>.execute-api.<REGION>.amazonaws.com/<STAGE>
```

**Example:**
```
wss://your-api-id.execute-api.us-east-2.amazonaws.com/prod
```

> **Note**: Replace `<API_ID>`, `<REGION>`, and `<STAGE>` with your actual AWS API Gateway WebSocket API configuration values.

---

## Authentication

All WebSocket connections require JWT authentication via AWS Cognito.

### Getting Your JWT Token

Service providers must authenticate with Cognito and obtain an ID token before establishing a WebSocket connection.

**Example using AWS Cognito SDK:**

```javascript
import { CognitoUserPool, AuthenticationDetails, CognitoUser } from 'amazon-cognito-identity-js';

const poolData = {
  UserPoolId: 'YOUR_USER_POOL_ID',
  ClientId: 'YOUR_CLIENT_ID'
};

const userPool = new CognitoUserPool(poolData);

function authenticateUser(username, password) {
  return new Promise((resolve, reject) => {
    const authenticationDetails = new AuthenticationDetails({
      Username: username,
      Password: password
    });

    const cognitoUser = new CognitoUser({
      Username: username,
      Pool: userPool
    });

    cognitoUser.authenticateUser(authenticationDetails, {
      onSuccess: (result) => {
        const idToken = result.getIdToken().getJwtToken();
        resolve(idToken);
      },
      onFailure: (err) => {
        reject(err);
      }
    });
  });
}
```

**Example using react-oidc-context:**

```javascript
import { useAuth } from 'react-oidc-context';

function WebSocketComponent() {
  const auth = useAuth();
  const idToken = auth.user?.id_token;
  
  // Use this token to connect to WebSocket
}
```

### Connection Authentication

The JWT token must be passed as a query parameter when establishing the WebSocket connection:

```javascript
const wsUrl = `wss://your-api-id.execute-api.us-east-2.amazonaws.com/prod?token=${idToken}`;
const ws = new WebSocket(wsUrl);
```

---

## Connection Management

### Establishing a Connection

```javascript
class QuickFixWebSocket {
  constructor(wsUrl, idToken) {
    this.wsUrl = wsUrl;
    this.idToken = idToken;
    this.ws = null;
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 5;
    this.reconnectDelay = 1000; // Start with 1 second
  }

  connect() {
    const url = `${this.wsUrl}?token=${this.idToken}`;
    this.ws = new WebSocket(url);

    this.ws.onopen = () => {
      console.log('WebSocket connected');
      this.reconnectAttempts = 0;
      this.reconnectDelay = 1000;
      this.startPingInterval();
    };

    this.ws.onmessage = (event) => {
      this.handleMessage(event.data);
    };

    this.ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };

    this.ws.onclose = () => {
      console.log('WebSocket disconnected');
      this.stopPingInterval();
      this.attemptReconnect();
    };
  }

  disconnect() {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
    this.stopPingInterval();
  }

  attemptReconnect() {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      console.log(`Reconnecting... Attempt ${this.reconnectAttempts}`);
      
      setTimeout(() => {
        this.connect();
      }, this.reconnectDelay);
      
      // Exponential backoff
      this.reconnectDelay = Math.min(this.reconnectDelay * 2, 30000);
    } else {
      console.error('Max reconnection attempts reached');
    }
  }

  startPingInterval() {
    // Send ping every 30 seconds to keep connection alive
    this.pingInterval = setInterval(() => {
      if (this.ws && this.ws.readyState === WebSocket.OPEN) {
        this.ws.send(JSON.stringify({ action: 'ping' }));
      }
    }, 30000);
  }

  stopPingInterval() {
    if (this.pingInterval) {
      clearInterval(this.pingInterval);
      this.pingInterval = null;
    }
  }

  handleMessage(data) {
    try {
      const message = JSON.parse(data);
      console.log('Received message:', message);
      
      // Handle different message types
      switch (message.type) {
        case 'PONG':
          // Ping response - connection is alive
          break;
        case 'JOB_STATUS_CHANGED':
          this.onJobStatusChanged(message);
          break;
        default:
          console.log('Unknown message type:', message.type);
      }
    } catch (error) {
      console.error('Error parsing message:', error);
    }
  }

  onJobStatusChanged(message) {
    // Override this method to handle job status changes
    console.log('Job status changed:', message);
  }
}
```

### Connection Lifecycle

1. **Connect**: Establish WebSocket connection with JWT token
2. **Authenticate**: Backend validates JWT and stores connection in DynamoDB
3. **Active**: Connection maintained with periodic ping/pong
4. **Disconnect**: Connection closed, removed from DynamoDB
5. **Reconnect**: Automatic reconnection with exponential backoff

### Connection Storage

When you connect, the backend stores your connection information in DynamoDB:

```javascript
{
  userId: "your-cognito-sub",           // Your Cognito user ID
  connectionId: "abc123...",            // AWS connection ID
  connectedAt: 1704380000,              // Unix timestamp
  ttl: 1704387200,                      // Expires in 2 hours
  role: "provider",                     // Your user role from Cognito groups
  stage: "prod"                         // API stage
}
```

### Keep-Alive (Ping/Pong)

Send a ping message every 30-60 seconds to keep the connection alive and refresh the TTL:

**Request:**
```javascript
ws.send(JSON.stringify({ action: 'ping' }));
```

**Response:**
```json
{
  "type": "PONG",
  "ts": 1704380000
}
```

The ping handler automatically extends your connection TTL by 2 hours.

---

## Message Types

### 1. JOB_STATUS_CHANGED

Sent when a job's status changes (e.g., customer accepts your application).

**Message Structure:**
```json
{
  "type": "JOB_STATUS_CHANGED",
  "jobId": "1001",
  "oldStatus": "open",
  "newStatus": "assigned",
  "changedAt": "2026-02-07T16:30:00.000Z",
  "changedBy": "customer-cognito-sub-id"
}
```

**Fields:**
- `type`: Always `"JOB_STATUS_CHANGED"`
- `jobId`: ID of the job that changed
- `oldStatus`: Previous job status
- `newStatus`: New job status
- `changedAt`: ISO 8601 timestamp of the change
- `changedBy`: Cognito sub of the user who made the change

**Common Status Transitions:**

| Old Status | New Status | Meaning |
|------------|------------|---------|
| `open` | `assigned` | Customer accepted your application |
| `assigned` | `in_progress` | Job work has started |
| `in_progress` | `completed` | Job work is finished |
| `assigned` | `cancelled` | Job was cancelled |

**Example Handler:**
```javascript
onJobStatusChanged(message) {
  const { jobId, oldStatus, newStatus, changedAt } = message;
  
  if (newStatus === 'assigned') {
    // Your application was accepted!
    showNotification(`Congratulations! You've been assigned to job ${jobId}`);
    updateJobList();
  } else if (newStatus === 'cancelled') {
    // Job was cancelled
    showNotification(`Job ${jobId} has been cancelled`);
    removeJobFromList(jobId);
  }
}
```

### 2. PONG

Response to ping messages to confirm connection is alive.

**Message Structure:**
```json
{
  "type": "PONG",
  "ts": 1704380000
}
```

**Fields:**
- `type`: Always `"PONG"`
- `ts`: Unix timestamp (seconds)

---

## Integration Examples

### Complete React Integration

```javascript
import React, { useEffect, useState, useCallback } from 'react';
import { useAuth } from 'react-oidc-context';

const WS_URL = 'wss://your-api-id.execute-api.us-east-2.amazonaws.com/prod';

function ProviderDashboard() {
  const auth = useAuth();
  const [wsClient, setWsClient] = useState(null);
  const [connectionStatus, setConnectionStatus] = useState('disconnected');
  const [notifications, setNotifications] = useState([]);

  // Handle job status changes
  const handleJobStatusChanged = useCallback((message) => {
    const { jobId, newStatus } = message;
    
    // Add notification
    setNotifications(prev => [...prev, {
      id: Date.now(),
      message: `Job ${jobId} status changed to ${newStatus}`,
      timestamp: new Date()
    }]);

    // Update your job list or UI
    // ... your business logic here
  }, []);

  // Initialize WebSocket connection
  useEffect(() => {
    if (!auth.user?.id_token) return;

    class WebSocketClient {
      constructor(url, token, onStatusChange, onJobStatusChanged) {
        this.url = url;
        this.token = token;
        this.ws = null;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectDelay = 1000;
        this.pingInterval = null;
        this.onStatusChange = onStatusChange;
        this.onJobStatusChanged = onJobStatusChanged;
      }

      connect() {
        const wsUrl = `${this.url}?token=${this.token}`;
        this.ws = new WebSocket(wsUrl);

        this.ws.onopen = () => {
          console.log('✅ WebSocket connected');
          this.onStatusChange('connected');
          this.reconnectAttempts = 0;
          this.reconnectDelay = 1000;
          this.startPing();
        };

        this.ws.onmessage = (event) => {
          try {
            const message = JSON.parse(event.data);
            
            switch (message.type) {
              case 'PONG':
                console.log('🏓 Pong received');
                break;
              case 'JOB_STATUS_CHANGED':
                this.onJobStatusChanged(message);
                break;
              default:
                console.log('Unknown message:', message);
            }
          } catch (error) {
            console.error('Error parsing message:', error);
          }
        };

        this.ws.onerror = (error) => {
          console.error('❌ WebSocket error:', error);
          this.onStatusChange('error');
        };

        this.ws.onclose = () => {
          console.log('🔌 WebSocket disconnected');
          this.onStatusChange('disconnected');
          this.stopPing();
          this.attemptReconnect();
        };
      }

      disconnect() {
        if (this.ws) {
          this.ws.close();
          this.ws = null;
        }
        this.stopPing();
      }

      attemptReconnect() {
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
          this.reconnectAttempts++;
          this.onStatusChange('reconnecting');
          
          setTimeout(() => {
            console.log(`🔄 Reconnecting... Attempt ${this.reconnectAttempts}`);
            this.connect();
          }, this.reconnectDelay);
          
          this.reconnectDelay = Math.min(this.reconnectDelay * 2, 30000);
        } else {
          console.error('💥 Max reconnection attempts reached');
          this.onStatusChange('failed');
        }
      }

      startPing() {
        this.pingInterval = setInterval(() => {
          if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify({ action: 'ping' }));
          }
        }, 30000);
      }

      stopPing() {
        if (this.pingInterval) {
          clearInterval(this.pingInterval);
          this.pingInterval = null;
        }
      }
    }

    const client = new WebSocketClient(
      WS_URL,
      auth.user.id_token,
      setConnectionStatus,
      handleJobStatusChanged
    );

    client.connect();
    setWsClient(client);

    return () => {
      client.disconnect();
    };
  }, [auth.user?.id_token, handleJobStatusChanged]);

  return (
    <div className="provider-dashboard">
      <div className="connection-status">
        Status: <span className={`status-${connectionStatus}`}>
          {connectionStatus}
        </span>
      </div>

      <div className="notifications">
        <h3>Recent Notifications</h3>
        {notifications.map(notif => (
          <div key={notif.id} className="notification">
            <p>{notif.message}</p>
            <small>{notif.timestamp.toLocaleString()}</small>
          </div>
        ))}
      </div>

      {/* Your dashboard content */}
    </div>
  );
}

export default ProviderDashboard;
```

### Vanilla JavaScript Integration

```javascript
// websocket-client.js
class QuickFixWebSocketClient {
  constructor(config) {
    this.wsUrl = config.wsUrl;
    this.getToken = config.getToken; // Function that returns current JWT token
    this.onJobStatusChanged = config.onJobStatusChanged || (() => {});
    this.onConnectionChange = config.onConnectionChange || (() => {});
    
    this.ws = null;
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 5;
    this.reconnectDelay = 1000;
    this.pingInterval = null;
  }

  async connect() {
    try {
      const token = await this.getToken();
      if (!token) {
        console.error('No authentication token available');
        return;
      }

      const url = `${this.wsUrl}?token=${token}`;
      this.ws = new WebSocket(url);

      this.ws.addEventListener('open', () => {
        console.log('WebSocket connected');
        this.onConnectionChange('connected');
        this.reconnectAttempts = 0;
        this.reconnectDelay = 1000;
        this.startPingInterval();
      });

      this.ws.addEventListener('message', (event) => {
        this.handleMessage(event.data);
      });

      this.ws.addEventListener('error', (error) => {
        console.error('WebSocket error:', error);
        this.onConnectionChange('error');
      });

      this.ws.addEventListener('close', () => {
        console.log('WebSocket closed');
        this.onConnectionChange('disconnected');
        this.stopPingInterval();
        this.attemptReconnect();
      });
    } catch (error) {
      console.error('Error connecting to WebSocket:', error);
    }
  }

  disconnect() {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
    this.stopPingInterval();
  }

  handleMessage(data) {
    try {
      const message = JSON.parse(data);
      
      switch (message.type) {
        case 'PONG':
          // Connection alive
          break;
        case 'JOB_STATUS_CHANGED':
          this.onJobStatusChanged(message);
          break;
        default:
          console.log('Unknown message type:', message.type);
      }
    } catch (error) {
      console.error('Error parsing message:', error);
    }
  }

  attemptReconnect() {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      this.onConnectionChange('reconnecting');
      
      setTimeout(() => {
        console.log(`Reconnecting... Attempt ${this.reconnectAttempts}`);
        this.connect();
      }, this.reconnectDelay);
      
      this.reconnectDelay = Math.min(this.reconnectDelay * 2, 30000);
    } else {
      console.error('Max reconnection attempts reached');
      this.onConnectionChange('failed');
    }
  }

  startPingInterval() {
    this.pingInterval = setInterval(() => {
      if (this.ws && this.ws.readyState === WebSocket.OPEN) {
        this.ws.send(JSON.stringify({ action: 'ping' }));
      }
    }, 30000);
  }

  stopPingInterval() {
    if (this.pingInterval) {
      clearInterval(this.pingInterval);
      this.pingInterval = null;
    }
  }
}

// Usage
const wsClient = new QuickFixWebSocketClient({
  wsUrl: 'wss://your-api-id.execute-api.us-east-2.amazonaws.com/prod',
  getToken: () => {
    // Return your current JWT token
    return localStorage.getItem('idToken');
  },
  onJobStatusChanged: (message) => {
    console.log('Job status changed:', message);
    // Update your UI
    updateJobStatus(message.jobId, message.newStatus);
  },
  onConnectionChange: (status) => {
    console.log('Connection status:', status);
    // Update connection indicator in UI
    document.getElementById('ws-status').textContent = status;
  }
});

// Connect
wsClient.connect();

// Disconnect when needed
// wsClient.disconnect();
```

---

## Error Handling

### Connection Errors

**401 Unauthorized**
- **Cause**: Invalid or expired JWT token
- **Solution**: Refresh your Cognito token and reconnect

```javascript
ws.onclose = (event) => {
  if (event.code === 1008) { // Policy violation (401)
    console.log('Authentication failed, refreshing token...');
    refreshCognitoToken().then(newToken => {
      idToken = newToken;
      connect();
    });
  }
};
```

**Connection Refused**
- **Cause**: Invalid WebSocket URL or network issues
- **Solution**: Verify URL and check network connectivity

### Message Handling Errors

```javascript
handleMessage(data) {
  try {
    const message = JSON.parse(data);
    
    // Validate message structure
    if (!message.type) {
      console.error('Invalid message: missing type field');
      return;
    }
    
    // Handle message
    this.processMessage(message);
  } catch (error) {
    console.error('Error handling message:', error);
    // Log error but don't crash
  }
}
```

### Reconnection Strategy

```javascript
attemptReconnect() {
  if (this.reconnectAttempts < this.maxReconnectAttempts) {
    this.reconnectAttempts++;
    
    // Exponential backoff: 1s, 2s, 4s, 8s, 16s
    const delay = Math.min(
      this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1),
      30000 // Max 30 seconds
    );
    
    console.log(`Reconnecting in ${delay}ms... (Attempt ${this.reconnectAttempts})`);
    
    setTimeout(() => {
      this.connect();
    }, delay);
  } else {
    console.error('Max reconnection attempts reached');
    // Notify user to manually reconnect
    this.onConnectionChange('failed');
  }
}
```

---

## Best Practices

### 1. Token Management

Always ensure your JWT token is valid before connecting:

```javascript
async function connectWithValidToken() {
  // Check token expiration
  const tokenExpiry = getTokenExpiry(idToken);
  const now = Date.now() / 1000;
  
  if (tokenExpiry && now >= tokenExpiry - 60) {
    // Token expires in less than 1 minute, refresh it
    idToken = await refreshCognitoToken();
  }
  
  // Connect with valid token
  wsClient.connect();
}
```

### 2. Connection Lifecycle Management

```javascript
// Connect when user logs in
auth.events.addAccessTokenExpiring(() => {
  console.log('Token expiring, will need to reconnect soon');
});

auth.events.addUserSignedOut(() => {
  wsClient.disconnect();
});

// Disconnect when page unloads
window.addEventListener('beforeunload', () => {
  wsClient.disconnect();
});
```

### 3. Heartbeat/Ping Strategy

```javascript
// Send ping every 30 seconds
// AWS API Gateway WebSocket idle timeout is 10 minutes by default
// But we ping more frequently to detect dead connections early
const PING_INTERVAL = 30000; // 30 seconds

startPingInterval() {
  this.pingInterval = setInterval(() => {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({ action: 'ping' }));
      
      // Set a timeout to detect if pong is not received
      this.pongTimeout = setTimeout(() => {
        console.warn('Pong not received, connection may be dead');
        this.ws.close();
      }, 5000); // 5 seconds to receive pong
    }
  }, PING_INTERVAL);
}

handleMessage(data) {
  const message = JSON.parse(data);
  
  if (message.type === 'PONG') {
    // Clear pong timeout
    if (this.pongTimeout) {
      clearTimeout(this.pongTimeout);
      this.pongTimeout = null;
    }
  }
  // ... handle other messages
}
```

### 4. UI Feedback

Provide clear visual feedback about connection status:

```javascript
function updateConnectionIndicator(status) {
  const indicator = document.getElementById('connection-indicator');
  
  switch (status) {
    case 'connected':
      indicator.className = 'status-connected';
      indicator.textContent = '● Connected';
      break;
    case 'disconnected':
      indicator.className = 'status-disconnected';
      indicator.textContent = '○ Disconnected';
      break;
    case 'reconnecting':
      indicator.className = 'status-reconnecting';
      indicator.textContent = '◐ Reconnecting...';
      break;
    case 'error':
      indicator.className = 'status-error';
      indicator.textContent = '✕ Error';
      break;
  }
}
```

### 5. Notification Handling

```javascript
onJobStatusChanged(message) {
  const { jobId, newStatus } = message;
  
  // Show browser notification (if permitted)
  if ('Notification' in window && Notification.permission === 'granted') {
    new Notification('QuickFix Job Update', {
      body: `Job ${jobId} status changed to ${newStatus}`,
      icon: '/logo.png'
    });
  }
  
  // Play sound alert
  const audio = new Audio('/notification.mp3');
  audio.play().catch(err => console.log('Audio play failed:', err));
  
  // Update UI
  updateJobInList(jobId, newStatus);
  
  // Log for analytics
  logEvent('job_status_notification_received', { jobId, newStatus });
}
```

### 6. Testing WebSocket Connection

```javascript
// Test connection manually
function testWebSocketConnection() {
  const testWs = new WebSocket(
    `wss://your-api-id.execute-api.us-east-2.amazonaws.com/prod?token=${idToken}`
  );
  
  testWs.onopen = () => {
    console.log('✅ Test connection successful');
    testWs.send(JSON.stringify({ action: 'ping' }));
  };
  
  testWs.onmessage = (event) => {
    console.log('📨 Received:', event.data);
  };
  
  testWs.onerror = (error) => {
    console.error('❌ Test connection failed:', error);
  };
  
  // Close after 5 seconds
  setTimeout(() => {
    testWs.close();
    console.log('Test connection closed');
  }, 5000);
}
```

---

## Troubleshooting

### Common Issues

| Issue | Possible Cause | Solution |
|-------|---------------|----------|
| Connection fails immediately | Invalid JWT token | Verify token is valid and not expired |
| Connection closes after a few seconds | Token validation failed | Check Cognito user pool ID and client ID |
| No messages received | Not subscribed to events | Verify your user ID is stored correctly |
| Frequent disconnections | Network instability | Implement robust reconnection logic |
| Ping/pong not working | Wrong action format | Ensure `{ action: 'ping' }` format |

### Debug Logging

```javascript
class QuickFixWebSocketClient {
  constructor(config) {
    // ... other config
    this.debug = config.debug || false;
  }

  log(...args) {
    if (this.debug) {
      console.log('[WebSocket]', ...args);
    }
  }

  connect() {
    this.log('Connecting to', this.wsUrl);
    // ... connection logic
  }

  handleMessage(data) {
    this.log('Received message:', data);
    // ... message handling
  }
}

// Enable debug mode
const wsClient = new QuickFixWebSocketClient({
  wsUrl: WS_URL,
  getToken: () => idToken,
  debug: true // Enable debug logging
});
```

---

## Additional Resources

- [AWS API Gateway WebSocket Documentation](https://docs.aws.amazon.com/apigateway/latest/developerguide/apigateway-websocket-api.html)
- [AWS Cognito Authentication](https://docs.aws.amazon.com/cognito/latest/developerguide/what-is-amazon-cognito.html)
- [WebSocket API MDN Reference](https://developer.mozilla.org/en-US/docs/Web/API/WebSocket)

---

## Support

For questions or issues with the WebSocket API, please contact the QuickFix development team or refer to the main API documentation.
