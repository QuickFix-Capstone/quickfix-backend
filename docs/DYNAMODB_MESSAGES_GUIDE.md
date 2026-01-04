# DynamoDB Table: quickfix_messages - Visualization & Access Guide

## Table Overview

**Table Name**: `quickfix_messages`  
**Status**: ✅ ACTIVE  
**Region**: us-east-2  
**Billing Mode**: PAY_PER_REQUEST (On-Demand)  
**Created**: 2026-01-04  
**Current Items**: 0 (empty)

---

## Table Schema

### Primary Key
- **Partition Key (HASH)**: `conversation_id` (String)
- **Sort Key (RANGE)**: `ts` (Number - timestamp)

### Key Design
This is a **composite key** structure optimized for messaging/chat:
- `conversation_id`: Groups messages by conversation
- `ts`: Orders messages chronologically within each conversation

### Example Item Structure
```json
{
  "conversation_id": "customer_123_provider_456",
  "ts": 1704384000000,
  "sender_id": "customer_123",
  "sender_type": "customer",
  "message": "Hello, when can you start the job?",
  "read": false,
  "created_at": "2026-01-04T14:00:00Z"
}
```

---

## Current Table Status

```
Items: 0
Size: 0 bytes
Read Capacity: On-Demand (12,000 RCU/sec warm)
Write Capacity: On-Demand (4,000 WCU/sec warm)
```

**Table is currently empty** - No messages have been added yet.

---

## AWS CLI Commands

### View All Messages
```bash
aws dynamodb scan \
  --table-name quickfix_messages \
  --region us-east-2 \
  --no-cli-pager
```

### Query Messages for Specific Conversation
```bash
aws dynamodb query \
  --table-name quickfix_messages \
  --key-condition-expression "conversation_id = :conv_id" \
  --expression-attribute-values '{":conv_id":{"S":"customer_123_provider_456"}}' \
  --region us-east-2 \
  --no-cli-pager
```

### Get Latest 10 Messages in Conversation
```bash
aws dynamodb query \
  --table-name quickfix_messages \
  --key-condition-expression "conversation_id = :conv_id" \
  --expression-attribute-values '{":conv_id":{"S":"customer_123_provider_456"}}' \
  --scan-index-forward false \
  --limit 10 \
  --region us-east-2 \
  --no-cli-pager
```

### Add Sample Message
```bash
aws dynamodb put-item \
  --table-name quickfix_messages \
  --item '{
    "conversation_id": {"S": "customer_1_provider_SP-001"},
    "ts": {"N": "1704384000000"},
    "sender_id": {"S": "customer_1"},
    "sender_type": {"S": "customer"},
    "message": {"S": "Hello, when can you start?"},
    "read": {"BOOL": false}
  }' \
  --region us-east-2
```

### Count Items in Table
```bash
aws dynamodb scan \
  --table-name quickfix_messages \
  --select COUNT \
  --region us-east-2 \
  --no-cli-pager
```

---

## Python Helper Script

Save this as `view_dynamodb_messages.py`:

```python
#!/usr/bin/env python3
"""
DynamoDB Messages Viewer
Displays messages from quickfix_messages table in a readable format
"""

import boto3
from datetime import datetime
from boto3.dynamodb.conditions import Key

# Initialize DynamoDB
dynamodb = boto3.resource('dynamodb', region_name='us-east-2')
table = dynamodb.Table('quickfix_messages')

def view_all_messages():
    """Scan and display all messages"""
    response = table.scan()
    items = response.get('Items', [])
    
    if not items:
        print("📭 Table is empty - no messages found")
        return
    
    print(f"📊 Found {len(items)} messages\n")
    print("=" * 80)
    
    for item in items:
        print(f"Conversation: {item.get('conversation_id')}")
        print(f"Timestamp: {datetime.fromtimestamp(int(item.get('ts', 0))/1000)}")
        print(f"From: {item.get('sender_id')} ({item.get('sender_type')})")
        print(f"Message: {item.get('message')}")
        print(f"Read: {'✓' if item.get('read') else '✗'}")
        print("-" * 80)

def view_conversation(conversation_id):
    """Query messages for specific conversation"""
    response = table.query(
        KeyConditionExpression=Key('conversation_id').eq(conversation_id),
        ScanIndexForward=True  # Oldest first
    )
    
    items = response.get('Items', [])
    
    if not items:
        print(f"📭 No messages found for conversation: {conversation_id}")
        return
    
    print(f"💬 Conversation: {conversation_id}")
    print(f"📊 {len(items)} messages\n")
    print("=" * 80)
    
    for item in items:
        timestamp = datetime.fromtimestamp(int(item.get('ts', 0))/1000)
        sender = item.get('sender_id')
        message = item.get('message')
        read_status = '✓' if item.get('read') else '✗'
        
        print(f"[{timestamp}] {sender}: {message} (Read: {read_status})")
    
    print("=" * 80)

def get_table_stats():
    """Display table statistics"""
    response = table.scan(Select='COUNT')
    count = response.get('Count', 0)
    
    print("📊 Table Statistics")
    print("=" * 80)
    print(f"Table Name: quickfix_messages")
    print(f"Total Messages: {count}")
    print(f"Region: us-east-2")
    print("=" * 80)

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        # View specific conversation
        conversation_id = sys.argv[1]
        view_conversation(conversation_id)
    else:
        # View all messages
        get_table_stats()
        print()
        view_all_messages()
```

**Usage**:
```bash
# View all messages
python3 view_dynamodb_messages.py

# View specific conversation
python3 view_dynamodb_messages.py "customer_1_provider_SP-001"
```

---

## Integration with Backend

### Python Lambda Code Example

```python
import boto3
from datetime import datetime

dynamodb = boto3.resource('dynamodb', region_name='us-east-2')
table = dynamodb.Table('quickfix_messages')

def send_message(conversation_id, sender_id, sender_type, message):
    """Send a message to DynamoDB"""
    timestamp = int(datetime.now().timestamp() * 1000)
    
    item = {
        'conversation_id': conversation_id,
        'ts': timestamp,
        'sender_id': sender_id,
        'sender_type': sender_type,  # 'customer' or 'provider'
        'message': message,
        'read': False,
        'created_at': datetime.now().isoformat()
    }
    
    table.put_item(Item=item)
    return item

def get_conversation_messages(conversation_id, limit=50):
    """Get messages for a conversation"""
    response = table.query(
        KeyConditionExpression=Key('conversation_id').eq(conversation_id),
        ScanIndexForward=False,  # Newest first
        Limit=limit
    )
    
    return response.get('Items', [])

def mark_as_read(conversation_id, timestamp):
    """Mark a message as read"""
    table.update_item(
        Key={
            'conversation_id': conversation_id,
            'ts': timestamp
        },
        UpdateExpression='SET #read = :true',
        ExpressionAttributeNames={'#read': 'read'},
        ExpressionAttributeValues={':true': True}
    )
```

---

## Web Console Access

You can also view the table in the AWS Console:

1. Go to: https://console.aws.amazon.com/dynamodbv2/
2. Select region: **us-east-2**
3. Click on table: **quickfix_messages**
4. Click "Explore table items" to view data

---

## Next Steps

### To Populate the Table:

**Option 1: Add Sample Data**
```bash
# Run the sample data script
python3 add_sample_messages.py
```

**Option 2: Create API Endpoint**
Create a Lambda function to handle message sending:
- `POST /messages` - Send new message
- `GET /messages/{conversation_id}` - Get conversation messages
- `PUT /messages/{conversation_id}/{ts}` - Mark as read

**Option 3: Manual Insert**
Use AWS CLI to add test messages (see examples above)

---

## Monitoring & Costs

### CloudWatch Metrics
- Read/Write capacity usage
- Throttled requests
- System errors

### Cost Estimation
**Pay-Per-Request Pricing**:
- $1.25 per million write requests
- $0.25 per million read requests
- First 25 GB storage free

**Typical Usage** (1000 messages/day):
- ~$0.04/month for writes
- ~$0.01/month for reads
- **Total**: ~$0.05/month

---

## Troubleshooting

### Table Not Found
```bash
# Verify table exists
aws dynamodb list-tables --region us-east-2
```

### Permission Denied
```bash
# Check AWS credentials
aws sts get-caller-identity

# Verify IAM permissions for DynamoDB
```

### Query Returns No Results
- Check if table is empty: `aws dynamodb scan --table-name quickfix_messages --select COUNT`
- Verify conversation_id matches exactly (case-sensitive)
- Check region is correct (us-east-2)
