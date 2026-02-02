"""
AWS SES Email Service for QuickFix Booking Confirmation Workflow

This module provides email sending functionality using AWS SES for:
- Booking confirmation requests to providers
- Booking confirmation notifications to customers
"""

import os
import boto3
from botocore.exceptions import ClientError
from typing import Dict, Optional
import logging

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class SESEmailService:
    """AWS SES Email Service for QuickFix"""
    
    def __init__(self):
        """Initialize SES client"""
        self.ses_region = os.environ.get('AWS_SES_REGION', 'us-east-1')
        self.sender_email = os.environ.get('SES_SENDER_EMAIL')
        self.confirmation_url = os.environ.get('BOOKING_CONFIRMATION_URL', '')
        
        if not self.sender_email:
            raise ValueError("SES_SENDER_EMAIL environment variable is required")
        
        self.ses_client = boto3.client('ses', region_name=self.ses_region)
    
    def send_booking_confirmation_email(
        self,
        provider_email: str,
        provider_name: str,
        booking_details: Dict,
        confirmation_token: str
    ) -> bool:
        """
        Send booking confirmation request email to provider.
        
        Args:
            provider_email: Provider's email address
            provider_name: Provider's full name
            booking_details: Dictionary containing booking information
            confirmation_token: Unique confirmation token
            
        Returns:
            bool: True if email sent successfully, False otherwise
        """
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
            
            # Create HTML email body
            html_body = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                    .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                    .header {{ background-color: #4CAF50; color: white; padding: 20px; text-align: center; border-radius: 5px 5px 0 0; }}
                    .content {{ background-color: #f9f9f9; padding: 30px; border: 1px solid #ddd; }}
                    .booking-details {{ background-color: white; padding: 20px; margin: 20px 0; border-left: 4px solid #4CAF50; }}
                    .detail-row {{ margin: 10px 0; }}
                    .label {{ font-weight: bold; color: #555; }}
                    .button {{ display: inline-block; padding: 15px 30px; background-color: #4CAF50; color: white; text-decoration: none; border-radius: 5px; margin: 20px 0; font-weight: bold; }}
                    .button:hover {{ background-color: #45a049; }}
                    .footer {{ text-align: center; padding: 20px; color: #777; font-size: 12px; }}
                    .warning {{ background-color: #fff3cd; border: 1px solid #ffc107; padding: 10px; margin: 15px 0; border-radius: 3px; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>🔧 QuickFix</h1>
                        <p>New Booking Request</p>
                    </div>
                    
                    <div class="content">
                        <h2>Hi {provider_name},</h2>
                        <p>You have received a new booking request!</p>
                        
                        <div class="booking-details">
                            <h3>Booking Details</h3>
                            <div class="detail-row">
                                <span class="label">Booking ID:</span> #{booking_id}
                            </div>
                            <div class="detail-row">
                                <span class="label">Service:</span> {service_category.title()}
                            </div>
                            {f'<div class="detail-row"><span class="label">Description:</span> {service_description}</div>' if service_description else ''}
                            <div class="detail-row">
                                <span class="label">Date:</span> {scheduled_date}
                            </div>
                            <div class="detail-row">
                                <span class="label">Time:</span> {scheduled_time}
                            </div>
                            <div class="detail-row">
                                <span class="label">Location:</span> {service_address}
                            </div>
                            <div class="detail-row">
                                <span class="label">Customer:</span> {customer_name}
                            </div>
                            <div class="detail-row">
                                <span class="label">Estimated Price:</span> {price_text}
                            </div>
                        </div>
                        
                        <div style="text-align: center;">
                            <a href="{confirmation_link}" class="button">
                                ✓ Confirm Booking
                            </a>
                        </div>
                        
                        <div class="warning">
                            <strong>⏰ Important:</strong> This confirmation link will expire in 7 days.
                        </div>
                        
                        <p style="margin-top: 20px; font-size: 14px; color: #666;">
                            If you cannot accept this booking, simply ignore this email. 
                            The customer will be notified if you don't respond.
                        </p>
                    </div>
                    
                    <div class="footer">
                        <p>This is an automated email from QuickFix.</p>
                        <p>If you have questions, please contact support.</p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            # Create plain text version
            text_body = f"""
QuickFix - New Booking Request

Hi {provider_name},

You have received a new booking request!

BOOKING DETAILS
---------------
Booking ID: #{booking_id}
Service: {service_category.title()}
{f'Description: {service_description}' if service_description else ''}
Date: {scheduled_date}
Time: {scheduled_time}
Location: {service_address}
Customer: {customer_name}
Estimated Price: {price_text}

CONFIRM BOOKING
---------------
Click the link below to confirm this booking:
{confirmation_link}

IMPORTANT: This confirmation link will expire in 7 days.

If you cannot accept this booking, simply ignore this email.

---
This is an automated email from QuickFix.
            """
            
            # Send email
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
            
            message_id = response.get('MessageId')
            logger.info(f"Booking confirmation email sent to {provider_email}. MessageId: {message_id}")
            return True
            
        except ClientError as e:
            logger.error(f"Failed to send booking confirmation email: {e.response['Error']['Message']}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error sending booking confirmation email: {str(e)}")
            return False
    
    def send_booking_confirmed_notification(
        self,
        customer_email: str,
        customer_name: str,
        booking_details: Dict
    ) -> bool:
        """
        Send booking confirmation notification to customer.
        
        Args:
            customer_email: Customer's email address
            customer_name: Customer's full name
            booking_details: Dictionary containing booking information
            
        Returns:
            bool: True if email sent successfully, False otherwise
        """
        try:
            # Extract booking details
            booking_id = booking_details.get('booking_id', 'N/A')
            service_category = booking_details.get('service_category', 'Service')
            scheduled_date = booking_details.get('scheduled_date', 'TBD')
            scheduled_time = booking_details.get('scheduled_time', 'TBD')
            provider_name = booking_details.get('provider_name', 'Your service provider')
            
            # Create email subject
            subject = f"Booking Confirmed #{booking_id} - QuickFix"
            
            # Create HTML email body
            html_body = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                    .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                    .header {{ background-color: #4CAF50; color: white; padding: 20px; text-align: center; border-radius: 5px 5px 0 0; }}
                    .content {{ background-color: #f9f9f9; padding: 30px; border: 1px solid #ddd; }}
                    .success-box {{ background-color: #d4edda; border: 1px solid #c3e6cb; padding: 20px; margin: 20px 0; border-radius: 5px; text-align: center; }}
                    .booking-details {{ background-color: white; padding: 20px; margin: 20px 0; border-left: 4px solid #4CAF50; }}
                    .detail-row {{ margin: 10px 0; }}
                    .label {{ font-weight: bold; color: #555; }}
                    .footer {{ text-align: center; padding: 20px; color: #777; font-size: 12px; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>🔧 QuickFix</h1>
                        <p>Booking Confirmed</p>
                    </div>
                    
                    <div class="content">
                        <h2>Hi {customer_name},</h2>
                        
                        <div class="success-box">
                            <h3 style="color: #155724; margin: 0;">✓ Your booking has been confirmed!</h3>
                        </div>
                        
                        <p>Great news! {provider_name} has confirmed your booking.</p>
                        
                        <div class="booking-details">
                            <h3>Booking Details</h3>
                            <div class="detail-row">
                                <span class="label">Booking ID:</span> #{booking_id}
                            </div>
                            <div class="detail-row">
                                <span class="label">Service:</span> {service_category.title()}
                            </div>
                            <div class="detail-row">
                                <span class="label">Date:</span> {scheduled_date}
                            </div>
                            <div class="detail-row">
                                <span class="label">Time:</span> {scheduled_time}
                            </div>
                            <div class="detail-row">
                                <span class="label">Provider:</span> {provider_name}
                            </div>
                        </div>
                        
                        <p style="margin-top: 20px;">
                            Your service provider will contact you soon to finalize the details.
                        </p>
                        
                        <p style="margin-top: 20px; font-size: 14px; color: #666;">
                            You can view and manage your bookings in your QuickFix dashboard.
                        </p>
                    </div>
                    
                    <div class="footer">
                        <p>This is an automated email from QuickFix.</p>
                        <p>If you have questions, please contact support.</p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            # Create plain text version
            text_body = f"""
QuickFix - Booking Confirmed

Hi {customer_name},

✓ Your booking has been confirmed!

Great news! {provider_name} has confirmed your booking.

BOOKING DETAILS
---------------
Booking ID: #{booking_id}
Service: {service_category.title()}
Date: {scheduled_date}
Time: {scheduled_time}
Provider: {provider_name}

Your service provider will contact you soon to finalize the details.

You can view and manage your bookings in your QuickFix dashboard.

---
This is an automated email from QuickFix.
            """
            
            # Send email
            response = self.ses_client.send_email(
                Source=self.sender_email,
                Destination={'ToAddresses': [customer_email]},
                Message={
                    'Subject': {'Data': subject, 'Charset': 'UTF-8'},
                    'Body': {
                        'Text': {'Data': text_body, 'Charset': 'UTF-8'},
                        'Html': {'Data': html_body, 'Charset': 'UTF-8'}
                    }
                }
            )
            
            message_id = response.get('MessageId')
            logger.info(f"Booking confirmed notification sent to {customer_email}. MessageId: {message_id}")
            return True
            
        except ClientError as e:
            logger.error(f"Failed to send booking confirmed notification: {e.response['Error']['Message']}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error sending booking confirmed notification: {str(e)}")
            return False


# Convenience functions for easy import
def send_booking_confirmation_email(
    provider_email: str,
    provider_name: str,
    booking_details: Dict,
    confirmation_token: str
) -> bool:
    """Send booking confirmation email to provider"""
    service = SESEmailService()
    return service.send_booking_confirmation_email(
        provider_email, provider_name, booking_details, confirmation_token
    )


def send_booking_confirmed_notification(
    customer_email: str,
    customer_name: str,
    booking_details: Dict
) -> bool:
    """Send booking confirmed notification to customer"""
    service = SESEmailService()
    return service.send_booking_confirmed_notification(
        customer_email, customer_name, booking_details
    )
