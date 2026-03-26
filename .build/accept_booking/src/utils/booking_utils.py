"""
Booking Utility Functions for QuickFix

This module provides utility functions for the booking confirmation workflow:
- Token generation for email confirmation
- Converting confirmed bookings to jobs
"""

import hashlib
from datetime import datetime
from typing import Optional
import logging

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def generate_confirmation_token(booking_id: int, provider_id: str) -> str:
    """
    Generate a unique SHA-256 confirmation token for booking email confirmation.
    
    The token is generated from:
    - booking_id
    - provider_id
    - current timestamp (for uniqueness)
    
    Args:
        booking_id: The booking ID
        provider_id: The provider's ID
        
    Returns:
        str: 64-character hexadecimal token
        
    Example:
        >>> token = generate_confirmation_token(123, "SP-001")
        >>> len(token)
        64
    """
    # Create unique data string
    timestamp = datetime.utcnow().isoformat()
    data = f"{booking_id}:{provider_id}:{timestamp}"
    
    # Generate SHA-256 hash
    token = hashlib.sha256(data.encode()).hexdigest()
    
    logger.info(f"Generated confirmation token for booking {booking_id}")
    return token


def convert_booking_to_job(booking_id: int, conn) -> dict:
    """
    Convert a confirmed booking into a job.
    
    This function:
    1. Fetches the booking details
    2. Creates a new job with status='assigned'
    3. Updates booking status to 'confirmed' and sets confirmed_at
    4. Links the booking to the job (booking.job_id and job.booking_id)
    5. Returns the created job_id
    
    Args:
        booking_id: The booking ID to convert
        conn: Database connection object (pymysql connection)
        
    Returns:
        dict: Result with structure:
            {
                "success": bool,
                "job_id": int (if successful),
                "error": str (if failed)
            }
    """
    try:
        cur = conn.cursor()
        
        # Step 1: Fetch booking details
        cur.execute("""
            SELECT 
                customer_id,
                provider_id,
                service_category,
                service_description,
                scheduled_date,
                scheduled_time,
                service_address,
                service_city,
                service_state,
                service_postal_code,
                service_lat,
                service_lng,
                estimated_price,
                job_id,
                status
            FROM bookings
            WHERE booking_id = %s
        """, (booking_id,))
        
        booking = cur.fetchone()
        
        if not booking:
            return {
                "success": False,
                "error": f"Booking {booking_id} not found"
            }
        
        if booking['job_id']:
            logger.warning(f"Booking {booking_id} already has job {booking['job_id']}")
            return {
                "success": True,
                "job_id": booking['job_id']
            }
        
        # Step 2: Create job from booking
        job_title = f"{booking['service_category'].title()} Service"
        job_description = booking['service_description'] or f"{booking['service_category'].title()} service requested"
        
        cur.execute("""
            INSERT INTO jobs (
                customer_id,
                title,
                description,
                category,
                location_address,
                location_city,
                location_state,
                location_zip,
                location_lat,
                location_lng,
                preferred_date,
                preferred_time,
                budget_min,
                budget_max,
                status,
                assigned_provider_id,
                booking_id,
                assigned_at,
                created_at,
                updated_at
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW(), NOW()
            )
        """, (
            booking['customer_id'],
            job_title,
            job_description,
            booking['service_category'],
            booking['service_address'],
            booking['service_city'],
            booking['service_state'],
            booking['service_postal_code'],
            booking['service_lat'],
            booking['service_lng'],
            booking['scheduled_date'],
            booking['scheduled_time'],
            booking['estimated_price'],  # budget_min
            booking['estimated_price'],  # budget_max
            'assigned',  # status - job is already assigned to provider
            booking['provider_id'],
            booking_id
        ))
        
        job_id = cur.lastrowid
        
        # Step 3: Update booking with job_id and set status to confirmed
        cur.execute("""
            UPDATE bookings
            SET job_id = %s,
                status = 'confirmed',
                confirmed_at = NOW()
            WHERE booking_id = %s
        """, (job_id, booking_id))
        
        conn.commit()
        
        logger.info(f"Successfully converted booking {booking_id} to job {job_id}")
        return {
            "success": True,
            "job_id": job_id
        }
        
    except Exception as e:
        logger.error(f"Error converting booking {booking_id} to job: {str(e)}")
        conn.rollback()
        return {
            "success": False,
            "error": str(e)
        }


def validate_confirmation_token(token: str, conn) -> dict:
    """
    Validate a confirmation token and return validation result.
    
    Args:
        token: The confirmation token to validate
        conn: Database connection object
        
    Returns:
        dict: Validation result with structure:
            {
                "valid": bool,
                "booking_id": int (if valid),
                "error": str (if invalid),
                "error_code": str (if invalid)
            }
    """
    try:
        cur = conn.cursor()
        
        cur.execute("""
            SELECT 
                booking_id,
                provider_id,
                customer_id,
                status,
                confirmation_token_expires_at,
                job_id,
                NOW() > confirmation_token_expires_at AS is_expired
            FROM bookings
            WHERE confirmation_token = %s
        """, (token,))
        
        result = cur.fetchone()
        
        # Token not found
        if not result:
            logger.warning(f"Invalid confirmation token: {token[:16]}...")
            return {
                "valid": False,
                "error": "Confirmation token not found",
                "error_code": "TOKEN_NOT_FOUND"
            }
        
        # Token expired
        if result['is_expired']:
            logger.warning(f"Expired confirmation token for booking {result['booking_id']}")
            return {
                "valid": False,
                "error": "Confirmation token has expired",
                "error_code": "TOKEN_EXPIRED",
                "booking_id": result['booking_id']
            }
        
        # Booking already confirmed
        if result['status'] == 'confirmed':
            logger.warning(f"Booking {result['booking_id']} already confirmed")
            return {
                "valid": False,
                "error": "Booking has already been confirmed",
                "error_code": "ALREADY_CONFIRMED",
                "booking_id": result['booking_id']
            }
        
        # Booking not in pending_confirmation status
        if result['status'] != 'pending_confirmation':
            logger.warning(f"Booking {result['booking_id']} has invalid status: {result['status']}")
            return {
                "valid": False,
                "error": f"Booking status is '{result['status']}', expected 'pending_confirmation'",
                "error_code": "INVALID_STATUS",
                "booking_id": result['booking_id']
            }
        
        # Token is valid
        logger.info(f"Token validated successfully for booking {result['booking_id']}")
        return {
            "valid": True,
            "booking_id": result['booking_id'],
            "provider_id": result['provider_id'],
            "customer_id": result['customer_id']
        }
        
    except Exception as e:
        logger.error(f"Error validating confirmation token: {str(e)}")
        return {
            "valid": False,
            "error": "Database error during token validation",
            "error_code": "DATABASE_ERROR"
        }
