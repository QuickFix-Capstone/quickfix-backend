#!/bin/bash
# Add test messages to DynamoDB
# Usage: ./add_test_message.sh

TABLE_NAME="quickfix_messages"
REGION="us-east-2"

echo "📝 Adding test messages to DynamoDB..."
echo ""

# Message 1
echo "Adding message 1..."
aws dynamodb put-item \
    --table-name $TABLE_NAME \
    --item '{
        "conversation_id": {"S": "customer_1_provider_SP-001"},
        "ts": {"N": "1704384000000"},
        "sender_id": {"S": "customer_1"},
        "sender_type": {"S": "customer"},
        "message": {"S": "Hello, when can you start the plumbing job?"},
        "read": {"BOOL": false}
    }' \
    --region $REGION

# Message 2
echo "Adding message 2..."
aws dynamodb put-item \
    --table-name $TABLE_NAME \
    --item '{
        "conversation_id": {"S": "customer_1_provider_SP-001"},
        "ts": {"N": "1704384060000"},
        "sender_id": {"S": "SP-001"},
        "sender_type": {"S": "provider"},
        "message": {"S": "I can start tomorrow at 9 AM. Does that work for you?"},
        "read": {"BOOL": false}
    }' \
    --region $REGION

# Message 3
echo "Adding message 3..."
aws dynamodb put-item \
    --table-name $TABLE_NAME \
    --item '{
        "conversation_id": {"S": "customer_1_provider_SP-001"},
        "ts": {"N": "1704384120000"},
        "sender_id": {"S": "customer_1"},
        "sender_type": {"S": "customer"},
        "message": {"S": "Perfect! See you tomorrow at 9 AM."},
        "read": {"BOOL": true}
    }' \
    --region $REGION

echo ""
echo "✅ Added 3 test messages!"
echo ""
echo "View them with: ./view_messages.sh"
echo "Or view specific conversation: ./view_messages.sh customer_1_provider_SP-001"
