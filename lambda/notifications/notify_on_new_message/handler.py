import json
import os
import time
from datetime import datetime
from decimal import Decimal

try:
    from src.db.rds_main import get_connection
except ModuleNotFoundError:
    import sys
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(current_dir, "../../.."))
    if project_root not in sys.path:
        sys.path.append(project_root)
    from src.db.rds_main import get_connection

import boto3

# Initialize DynamoDB
dynamodb = boto3.resource('dynamodb', region_name='us-east-2')
conversations_table = dynamodb.Table('quickfix_conversations')
notifications_table = dynamodb.Table('quickfix_notifications')


def handler(event, context):
    """
    DynamoDB Stream trigger for quickfix_messages table.
    Creates notifications when new messages are inserted.
    
    Event structure:
    {
        "Records": [
            {
                "eventName": "INSERT",
                "dynamodb": {
                    "NewImage": {
                        "conversation_id": {"S": "..."},
                        "ts": {"N": "1767581062206"},
                        "senderId": {"S": "2"},
                        "senderName": {"S": "KunPeng Yang"},
                        "text": {"S": "Hello!"},
                        ...
                    }
                }
            }
        ]
    }
    """
    
    print(f"Processing {len(event['Records'])} records")
    
    for record in event['Records']:
        # Only process INSERT events
        if record['eventName'] != 'INSERT':
            print(f"Skipping {record['eventName']} event")
            continue
        
        try:
            # Extract message data from DynamoDB Stream
            new_image = record['dynamodb']['NewImage']
            
            conversation_id = new_image['conversation_id']['S']
            message_id = int(new_image['ts']['N'])
            sender_id = new_image['senderId']['S']
            sender_name = new_image['senderName']['S']
            text = new_image['text']['S']
            
            print(f"New message in conversation {conversation_id} from {sender_name}")
            
            # Get conversation details to find recipient
            # We need to query both conversation entries to find the OTHER user
            conv_response = conversations_table.query(
                IndexName=None,  # Query on primary key
                KeyConditionExpression=boto3.dynamodb.conditions.Key('conversationId').eq(conversation_id),
                FilterExpression=boto3.dynamodb.conditions.Attr('userId').ne(sender_id)
            )
            
            # Alternative: Query by conversationId as SK (but we need userId as PK)
            # Let's scan for this conversation and filter
            conv_response = conversations_table.scan(
                FilterExpression=boto3.dynamodb.conditions.Attr('conversationId').eq(conversation_id) & 
                                boto3.dynamodb.conditions.Attr('userId').ne(sender_id)
            )
            
            if not conv_response.get('Items'):
                print(f"No recipient found for conversation {conversation_id}")
                continue
            
            recipient_item = conv_response['Items'][0]
            recipient_user_id = recipient_item['userId']
            
            print(f"Recipient user_id: {recipient_user_id}")
            
            # Get recipient's cognito_sub from MySQL
            mysql_conn = get_connection()
            if not mysql_conn:
                print("Failed to connect to MySQL")
                continue
            
            try:
                with mysql_conn.cursor() as cur:
                    # Check if customer
                    if recipient_user_id.isdigit():
                        cur.execute(
                            "SELECT cognito_sub FROM customers WHERE customer_id = %s",
                            (recipient_user_id,)
                        )
                    else:
                        # Provider ID (starts with SP-)
                        cur.execute(
                            "SELECT cognito_sub FROM service_providers WHERE provider_id = %s",
                            (recipient_user_id,)
                        )
                    
                    user_row = cur.fetchone()
                    if not user_row:
                        print(f"User {recipient_user_id} not found in MySQL")
                        continue
                    
                    recipient_cognito_sub = user_row['cognito_sub']
                    
            finally:
                mysql_conn.close()
            
            # Get sender's cognito_sub
            mysql_conn = get_connection()
            try:
                with mysql_conn.cursor() as cur:
                    if sender_id.isdigit():
                        cur.execute(
                            "SELECT cognito_sub FROM customers WHERE customer_id = %s",
                            (sender_id,)
                        )
                    else:
                        cur.execute(
                            "SELECT cognito_sub FROM service_providers WHERE provider_id = %s",
                            (sender_id,)
                        )
                    
                    sender_row = cur.fetchone()
                    sender_cognito_sub = sender_row['cognito_sub'] if sender_row else sender_id
                    
            finally:
                mysql_conn.close()
            
            # Create notification
            iso_time = datetime.utcnow().isoformat() + 'Z'
            notif_sort = f"NOTIF#{iso_time}#MSG#{message_id}"
            preview = text[:100] if len(text) > 100 else text
            ttl = int(time.time()) + 2592000  # 30 days
            
            # Use conditional put to avoid duplicates
            try:
                notifications_table.put_item(
                    Item={
                        'user_sub': recipient_cognito_sub,
                        'notif_sort': notif_sort,
                        'type': 'NEW_MESSAGE',
                        'conversation_id': conversation_id,
                        'from_sub': sender_cognito_sub,
                        'from_name': sender_name,
                        'preview': preview,
                        'created_at': iso_time,
                        'is_read': False,
                        'message_id': message_id,
                        'ttl': ttl
                    },
                    ConditionExpression='attribute_not_exists(notif_sort)'  # Prevent duplicates
                )
                
                print(f"✅ Notification created for {recipient_cognito_sub}")
                
            except dynamodb.meta.client.exceptions.ConditionalCheckFailedException:
                print(f"Notification already exists for message {message_id}")
            
        except Exception as e:
            print(f"Error processing record: {e}")
            import traceback
            traceback.print_exc()
            # Continue processing other records
            continue
    
    return {
        'statusCode': 200,
        'body': json.dumps(f'Processed {len(event["Records"])} records')
    }
