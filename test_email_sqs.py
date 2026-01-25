#!/usr/bin/env python3
"""
Test script to verify SQS email service works locally
"""
import json
import os
import boto3
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_sqs_email():
    """Test sending an email via SQS"""

    # Initialize SQS client
    sqs = boto3.client('sqs', region_name='us-east-2')
    queue_url = 'https://sqs.us-east-2.amazonaws.com/008971679867/booking-email-queue'

    # Create test email data
    email_data = {
        'email_type': 'booking_confirmation',
        'booking_data': {
            'provider_email': 'ykphrfly@gmail.com',
            'provider_name': 'Test Provider',
            'booking_details': {
                'booking_id': 999,
                'service_category': 'PEST_CONTROL',
                'service_description': 'Test booking from local script',
                'scheduled_date': '2026-01-31',
                'scheduled_time': '14:00',
                'service_address': '123 Test St, Test City, ON',
                'customer_name': 'Test Customer',
                'estimated_price': 150.00
            },
            'confirmation_token': 'test-token-12345'
        }
    }

    try:
        # Send message to SQS
        print("📤 Sending email message to SQS queue...")
        response = sqs.send_message(
            QueueUrl=queue_url,
            MessageBody=json.dumps(email_data)
        )

        message_id = response.get('MessageId')
        print(f"✅ Message sent successfully!")
        print(f"   Message ID: {message_id}")
        print(f"   Queue URL: {queue_url}")

        # Check queue attributes
        print("\n📊 Checking queue status...")
        attrs = sqs.get_queue_attributes(
            QueueUrl=queue_url,
            AttributeNames=['ApproximateNumberOfMessages', 'ApproximateNumberOfMessagesNotVisible']
        )

        print(f"   Messages in queue: {attrs['Attributes']['ApproximateNumberOfMessages']}")
        print(f"   Messages in flight: {attrs['Attributes']['ApproximateNumberOfMessagesNotVisible']}")

        print("\n✅ SQS email service is working!")
        print("   Check your email for the booking confirmation.")

        return True

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("Testing SQS Email Service")
    print("=" * 60)
    test_sqs_email()
