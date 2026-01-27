"""
Optimized AWS SES Email Service with timeout handling and retry logic
"""

import os
import boto3
from botocore.exceptions import ClientError, ConnectTimeoutError, ReadTimeoutError
from botocore.config import Config
from typing import Dict, Optional
import logging
import time

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class OptimizedSESEmailService:
    """Optimized AWS SES Email Service with timeout handling"""
    
    def __init__(self):
        """Initialize SES client with optimized configuration"""
        self.ses_region = os.environ.get('AWS_SES_REGION', 'us-east-1')
        self.sender_email = os.environ.get('SES_SENDER_EMAIL')
        self.confirmation_url = os.environ.get('BOOKING_CONFIRMATION_URL', '')
        
        if not self.sender_email:
            raise ValueError("SES_SENDER_EMAIL environment variable is required")
        
        # Optimized boto3 configuration
        config = Config(
            region_name=self.ses_region,
            retries={
                'max_attempts': 2,  # Reduced retries for faster failure
                'mode': 'standard'
            },
            connect_timeout=5,  # 5 second connection timeout
            read_timeout=10,    # 10 second read timeout
            max_pool_connections=10
        )
        
        self.ses_client = boto3.client('ses', config=config)
    
    def send_booking_confirmation_email(
        self,
        provider_email: str,
        provider_name: str,
        booking_details: Dict,
        confirmation_token: str,
        timeout_seconds: int = 15
    ) -> bool:
        """
        Send booking confirmation request email to provider with timeout handling.
        
        Args:
            provider_email: Provider's email address
            provider_name: Provider's full name
            booking_details: Dictionary containing booking information
            confirmation_token: Unique confirmation token
            timeout_seconds: Maximum time to wait for email sending
            
        Returns:
            bool: True if email sent successfully, False otherwise
        """
        start_time = time.time()
        
        try:
            # Build confirmation URL
            confirmation_link = f"{self.confirmation_url}?token={confirmation_token}"
            
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
            
            # Simplified HTML email body (smaller payload)
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
                            Date: {scheduled_date} at {scheduled_time}<br>
                            Location: {service_address}<br>
                            Customer: {customer_name}<br>
                            Price: {price_text}
                        </div>
                        <p style="text-align: center;">
                            <a href="{confirmation_link}" class="button">Confirm Booking</a>
                        </p>
                        <p><small>Link expires in 7 days. Ignore this email if you cannot accept.</small></p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            # Simplified plain text version
            text_body = f"""
QuickFix - New Booking Request

Hi {provider_name},

New booking request #{booking_id}:
- Service: {service_category.title()}
- Date: {scheduled_date} at {scheduled_time}
- Location: {service_address}
- Customer: {customer_name}
- Price: {price_text}

Confirm: {confirmation_link}

Link expires in 7 days.
            """
            
            # Check timeout before sending
            if time.time() - start_time > timeout_seconds:
                logger.warning(f"Email preparation took too long, aborting send to {provider_email}")
                return False
            
            # Send email with timeout handling
            response = self.ses_client.send_email(
                Source=self.sender_email,
                Destination={'ToAddresses': [provider_email]},
                Message={
                    'Subject': {'Data': subject, 'Charset': 'UTF-8'},
                    'Body': {
                        'Text': {'Data': text_body, 'Charset': 'UTF-8'},
                        'Html': {'Data': html_body, 'Charset': 'UTF-8'}
                    }
                }
            )
            
            elapsed_time = time.time() - start_time
            message_id = response.get('MessageId')
            logger.info(f"Email sent to {provider_email} in {elapsed_time:.2f}s. MessageId: {message_id}")
            return True
            
        except (ConnectTimeoutError, ReadTimeoutError) as e:
            elapsed_time = time.time() - start_time
            logger.error(f"Email timeout after {elapsed_time:.2f}s to {provider_email}: {str(e)}")
            return False
            
        except ClientError as e:
            elapsed_time = time.time() - start_time
            error_code = e.response['Error']['Code']
            logger.error(f"SES ClientError after {elapsed_time:.2f}s: {error_code} - {e.response['Error']['Message']}")
            return False
            
        except Exception as e:
            elapsed_time = time.time() - start_time
            logger.error(f"Unexpected email error after {elapsed_time:.2f}s: {str(e)}")
            return False


# Convenience function with timeout
def send_booking_confirmation_email_fast(
    provider_email: str,
    provider_name: str,
    booking_details: Dict,
    confirmation_token: str,
    timeout_seconds: int = 15
) -> bool:
    """Send booking confirmation email with timeout handling"""
    try:
        service = OptimizedSESEmailService()
        return service.send_booking_confirmation_email(
            provider_email, provider_name, booking_details, confirmation_token, timeout_seconds
        )
    except Exception as e:
        logger.error(f"Failed to initialize SES service: {str(e)}")
        return False