"""
Simplified Lambda function for processing booking confirmation emails
Triggered by SQS messages from create_booking Lambda
"""

import json
import os
import boto3
from botocore.exceptions import ClientError
from typing import Dict, Any


def send_booking_confirmation_email_simple(
    provider_email: str,
    provider_name: str,
    booking_details: Dict,
    confirmation_token: str
) -> bool:
    """Send booking confirmation email using SES"""
    try:
        # Initialize SES client
        ses_region = os.environ.get('AWS_SES_REGION', 'us-east-1')
        sender_email = os.environ.get('SES_SENDER_EMAIL')
        
        if not sender_email:
            print("❌ SES_SENDER_EMAIL environment variable not set")
            return False
        
        ses_client = boto3.client('ses', region_name=ses_region)
        
        # Extract booking details
        booking_id = booking_details.get('booking_id', 'N/A')
        service_category = booking_details.get('service_category', 'Service')
        service_description = booking_details.get('service_description', '')
        scheduled_date = booking_details.get('scheduled_date', 'TBD')
        scheduled_time = booking_details.get('scheduled_time', 'TBD')
        service_address = booking_details.get('service_address', 'N/A')
        customer_name = booking_details.get('customer_name', 'Customer')
        estimated_price = booking_details.get('estimated_price')
        
        # Format price
        price_text = f"${estimated_price:.2f}" if estimated_price else "To be determined"
        
        # Create email subject
        subject = f"New Booking Request #{booking_id} - QuickFix"
        
        # Create HTML email body
        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #4CAF50; color: white; padding: 15px; text-align: center; }}
                .content {{ padding: 20px; border: 1px solid #ddd; }}
                .details {{ background-color: #f9f9f9; padding: 15px; margin: 15px 0; }}
                .button {{ display: inline-block; padding: 12px 24px; background-color: #4CAF50; color: white; text-decoration: none; border-radius: 4px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h2>🔧 QuickFix - New Booking Request</h2>
                </div>
                <div class="content">
                    <p>Hi {provider_name},</p>
                    <p>You have a new booking request!</p>
                    <div class="details">
                        <strong>Booking #{booking_id}</strong><br>
                        Service: {service_category.title()}<br>
                        {f'Description: {service_description}<br>' if service_description else ''}
                        Date: {scheduled_date} at {scheduled_time}<br>
                        Location: {service_address}<br>
                        Customer: {customer_name}<br>
                        Price: {price_text}
                    </div>
                    <p><strong>Confirmation Token:</strong> {confirmation_token}</p>
                    <p><small>This is a test email from the async email processing system.</small></p>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Create plain text version
        text_body = f"""
QuickFix - New Booking Request

Hi {provider_name},

New booking request #{booking_id}:
- Service: {service_category.title()}
{f'- Description: {service_description}' if service_description else ''}
- Date: {scheduled_date} at {scheduled_time}
- Location: {service_address}
- Customer: {customer_name}
- Price: {price_text}

Confirmation Token: {confirmation_token}

This is a test email from the async email processing system.
        """
        
        # Send email
        response = ses_client.send_email(
            Source=sender_email,
            Destination={'ToAddresses': [provider_email]},
            Message={
                'Subject': {'Data': subject, 'Charset': 'UTF-8'},
                'Body': {
                    'Text': {'Data': text_body, 'Charset': 'UTF-8'},
                    'Html': {'Data': html_body, 'Charset': 'UTF-8'}
                }
            }
        )
        
        message_id = response.get('MessageId')
        print(f"✅ Email sent to {provider_email}. MessageId: {message_id}")
        return True
        
    except ClientError as e:
        print(f"❌ SES ClientError: {e.response['Error']['Message']}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
        return False


def handler(event, context):
    """
    Process booking confirmation emails from SQS queue
    """
    
    processed_count = 0
    failed_count = 0
    
    print(f"📧 Processing {len(event.get('Records', []))} email messages...")
    
    # Process each SQS record
    for record in event.get('Records', []):
        try:
            # Parse SQS message
            message_body = json.loads(record['body'])
            email_type = message_body.get('email_type')
            
            print(f"📨 Processing email type: {email_type}")
            
            if email_type != 'booking_confirmation':
                print(f"⚠️  Skipping unknown email type: {email_type}")
                continue
            
            booking_data = message_body.get('booking_data', {})
            
            # Validate required fields
            required_fields = ['provider_email', 'provider_name', 'booking_details', 'confirmation_token']
            missing_fields = [field for field in required_fields if not booking_data.get(field)]
            
            if missing_fields:
                print(f"❌ Missing required fields: {missing_fields}")
                failed_count += 1
                continue
            
            # Send the email
            email_sent = send_booking_confirmation_email_simple(
                provider_email=booking_data['provider_email'],
                provider_name=booking_data['provider_name'],
                booking_details=booking_data['booking_details'],
                confirmation_token=booking_data['confirmation_token']
            )
            
            if email_sent:
                print(f"✅ Email sent successfully to {booking_data['provider_email']}")
                processed_count += 1
            else:
                print(f"❌ Failed to send email to {booking_data['provider_email']}")
                failed_count += 1
                
        except json.JSONDecodeError as e:
            print(f"❌ Invalid JSON in SQS message: {e}")
            failed_count += 1
            
        except Exception as e:
            print(f"❌ Error processing email: {e}")
            failed_count += 1
    
    print(f"📊 Processing complete: {processed_count} sent, {failed_count} failed")
    
    # Return processing summary
    return {
        'statusCode': 200,
        'body': json.dumps({
            'processed': processed_count,
            'failed': failed_count,
            'total_records': len(event.get('Records', []))
        })
    }


# Local testing
if __name__ == "__main__":
    test_event = {
        "Records": [
            {
                "body": json.dumps({
                    "email_type": "booking_confirmation",
                    "booking_data": {
                        "provider_email": "test@example.com",
                        "provider_name": "John Doe",
                        "booking_details": {
                            "booking_id": 123,
                            "service_category": "plumber",
                            "service_description": "Fix sink",
                            "scheduled_date": "2026-01-15",
                            "scheduled_time": "14:00",
                            "service_address": "123 Main St",
                            "customer_name": "Jane Smith",
                            "estimated_price": 150.00
                        },
                        "confirmation_token": "test-token-123"
                    }
                })
            }
        ]
    }
    
    print("🔍 Testing email processing...")
    result = handler(test_event, None)
    print("Result:")
    print(json.dumps(result, indent=2))