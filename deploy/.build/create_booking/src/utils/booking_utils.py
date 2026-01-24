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


def convert_booking_to_job(booking_id: int, conn) -> Optional[int]:
    """
    Convert a confirmed booking into a job.
    
    This function:
    1. Fetches the booking details
    2. Creates a new job with status='assigned'
    3. Links the booking to the job (booking.job_id and job.booking_id)
    4. Returns the created job_id
    
    Args:
        booking_id: The booking ID to convert
        conn: Database connection object (pymysql connection)
        
    Returns:
        int: The created job_id, or None if conversion failed
        
    Raises:
        ValueError: If booking not found or already has a job
        Exception: For database errors
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
                estimated_price,
                job_id
            FROM bookings
            WHERE booking_id = %s
        """, (booking_id,))
        
        booking = cur.fetchone()
        
        if not booking:
            raise ValueError(f"Booking {booking_id} not found")
        
        if booking['job_id']:
            logger.warning(f"Booking {booking_id} already has job {booking['job_id']}")
            return booking['job_id']
        
        # Step 2: Create job from booking
        # Map booking fields to job fields
        job_title = f"{booking['service_category'].title()} Service"
        job_description = booking['service_description'] or f"{booking['service_category'].title()} service requested"
        location_address = booking['service_address']
        location_city = booking['service_city']
        location_state = booking['service_state']
        location_zip = booking['service_postal_code']
        
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
                preferred_date,
                preferred_time,
                budget_min,
                budget_max,
                status,
                assigned_provider_id,
                booking_id,
                created_at,
                updated_at
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW()
            )
        """, (
            booking['customer_id'],
            job_title,
            job_description,
            booking['service_category'],
            location_address,
            location_city,
            location_state,
            location_zip,
            booking['scheduled_date'],
            booking['scheduled_time'],
            booking['estimated_price'],  # budget_min
            booking['estimated_price'],  # budget_max
            'assigned',  # status - job is already assigned to provider
            booking['provider_id'],
            booking_id
        ))
        
        job_id = cur.lastrowid
        
        # Step 3: Update booking with job_id
        cur.execute("""
            UPDATE bookings
            SET job_id = %s
            WHERE booking_id = %s
        """, (job_id, booking_id))
        
        conn.commit()
        
        logger.info(f"Successfully converted booking {booking_id} to job {job_id}")
        return job_id
        
    except ValueError as e:
        logger.error(f"Validation error converting booking to job: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Error converting booking {booking_id} to job: {str(e)}")
        conn.rollback()
        raise


def validate_confirmation_token(token: str, conn) -> Optional[dict]:
    """
    Validate a confirmation token and return booking details if valid.
    
    Args:
        token: The confirmation token to validate
        conn: Database connection object
        
    Returns:
        dict: Booking details if token is valid, None otherwise
        
    The returned dict contains:
        - booking_id
        - provider_id
        - customer_id
        - status
        - token_expires_at
        - is_expired (bool)
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
        
        if not result:
            logger.warning(f"Invalid confirmation token: {token[:16]}...")
            return None
        
        logger.info(f"Token validated for booking {result['booking_id']}")
        return result
        
    except Exception as e:
        logger.error(f"Error validating confirmation token: {str(e)}")
        return None
