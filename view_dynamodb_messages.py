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
    
    for item in sorted(items, key=lambda x: x.get('ts', 0)):
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
