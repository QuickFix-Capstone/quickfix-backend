#!/bin/bash
# DynamoDB Messages Viewer - Simple Bash Script
# Usage: ./view_messages.sh [conversation_id]

TABLE_NAME="quickfix_messages"
REGION="us-east-2"

echo "📊 QuickFix Messages - DynamoDB Viewer"
echo "========================================"
echo ""

# Function to display all messages
view_all() {
    echo "Fetching all messages..."
    RESULT=$(aws dynamodb scan \
        --table-name $TABLE_NAME \
        --region $REGION \
        --output json 2>&1)
    
    COUNT=$(echo "$RESULT" | jq -r '.Count // 0')
    
    if [ "$COUNT" -eq 0 ]; then
        echo "📭 Table is empty - no messages found"
        echo ""
        echo "To add a test message, run:"
        echo "./add_test_message.sh"
    else
        echo "📊 Found $COUNT messages"
        echo ""
        echo "$RESULT" | jq -r '.Items[] | 
            "Conversation: \(.conversation_id.S)\n" +
            "Timestamp: \(.ts.N)\n" +
            "Sender: \(.sender_id.S) (\(.sender_type.S))\n" +
            "Message: \(.message.S)\n" +
            "Read: \(if .read.BOOL then "✓" else "✗" end)\n" +
            "---"'
    fi
}

# Function to view specific conversation
view_conversation() {
    CONV_ID=$1
    echo "Fetching messages for conversation: $CONV_ID"
    
    RESULT=$(aws dynamodb query \
        --table-name $TABLE_NAME \
        --key-condition-expression "conversation_id = :conv_id" \
        --expression-attribute-values "{\":conv_id\":{\"S\":\"$CONV_ID\"}}" \
        --region $REGION \
        --output json 2>&1)
    
    COUNT=$(echo "$RESULT" | jq -r '.Count // 0')
    
    if [ "$COUNT" -eq 0 ]; then
        echo "📭 No messages found for this conversation"
    else
        echo "💬 $COUNT messages in conversation"
        echo ""
        echo "$RESULT" | jq -r '.Items[] | 
            "[\(.ts.N)] \(.sender_id.S): \(.message.S) (Read: \(if .read.BOOL then "✓" else "✗" end))"'
    fi
}

# Main logic
if [ -z "$1" ]; then
    view_all
else
    view_conversation "$1"
fi

echo ""
echo "========================================"
