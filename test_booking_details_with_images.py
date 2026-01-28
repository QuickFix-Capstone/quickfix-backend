#!/usr/bin/env python3
"""
Comprehensive test script for get_booking_details API
This script:
1. Gets a fresh customer ID token from Cognito
2. Tests the deployed get_booking_details endpoint
3. Verifies that image URLs are returned correctly
"""

import boto3
import requests
import json
import sys
from datetime import datetime, timedelta

# Cognito Configuration
USER_POOL_ID = "us-east-2_45z5OMePi"
CLIENT_ID = "p2u5qdegml3hp60n6ohu52n2b"
REGION = "us-east-2"

# Customer Credentials
EMAIL = "ykphrfly@gmail.com"
PASSWORD = "Yang@860101"

# API Configuration
API_BASE_URL = "https://kfvf20j7j9.execute-api.us-east-2.amazonaws.com"


def get_fresh_id_token():
    """
    Authenticate with AWS Cognito and retrieve a fresh ID token.
    
    Returns:
        str: The ID token
    """
    try:
        # Initialize Cognito client
        client = boto3.client('cognito-idp', region_name=REGION)
        
        print("🔐 Authenticating with AWS Cognito...")
        print(f"📧 User: {EMAIL}")
        print("")
        
        # Authenticate using USER_PASSWORD_AUTH flow
        response = client.initiate_auth(
            ClientId=CLIENT_ID,
            AuthFlow='USER_PASSWORD_AUTH',
            AuthParameters={
                'USERNAME': EMAIL,
                'PASSWORD': PASSWORD
            }
        )
        
        # Extract authentication result
        auth_result = response['AuthenticationResult']
        id_token = auth_result['IdToken']
        expires_in = auth_result['ExpiresIn']
        
        # Calculate expiration time
        expiration_time = datetime.now() + timedelta(seconds=expires_in)
        
        print("✅ Authentication successful!")
        print(f"⏰ Token expires in: {expires_in} seconds (~{expires_in // 60} minutes)")
        print(f"🕐 Expiration time: {expiration_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print("")
        
        return id_token
        
    except client.exceptions.NotAuthorizedException as e:
        print("❌ Authentication failed: Invalid username or password")
        print(f"Error: {str(e)}")
        sys.exit(1)
        
    except client.exceptions.UserNotFoundException as e:
        print("❌ Authentication failed: User not found")
        print(f"Error: {str(e)}")
        sys.exit(1)
        
    except Exception as e:
        print(f"❌ An error occurred during authentication: {str(e)}")
        sys.exit(1)


def test_get_booking_details(token, booking_id):
    """
    Test the GET /customer/bookings/{booking_id} endpoint
    
    Args:
        token: JWT ID token
        booking_id: ID of the booking to retrieve
        
    Returns:
        dict: The booking data if successful, None otherwise
    """
    
    url = f"{API_BASE_URL}/customer/bookings/{booking_id}"
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    print(f"🔍 Testing GET /customer/bookings/{booking_id}")
    print(f"📍 URL: {url}")
    print("=" * 80)
    
    try:
        response = requests.get(url, headers=headers)
        
        print(f"\n📊 Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            booking = data.get('booking', {})
            
            print("\n✅ SUCCESS! Booking retrieved successfully")
            print("\n" + "=" * 80)
            print("📋 BOOKING DETAILS")
            print("=" * 80)
            print(f"Booking ID:       {booking.get('booking_id')}")
            print(f"Customer:         {booking.get('customer', {}).get('name')}")
            print(f"Email:            {booking.get('customer', {}).get('email')}")
            print(f"Phone:            {booking.get('customer', {}).get('phone')}")
            print(f"\nProvider:         {booking.get('provider', {}).get('name')}")
            print(f"Business:         {booking.get('provider', {}).get('business_name')}")
            print(f"\nService:          {booking.get('service', {}).get('category')}")
            print(f"Description:      {booking.get('service', {}).get('description')}")
            print(f"\nStatus:           {booking.get('status')}")
            print(f"Date:             {booking.get('schedule', {}).get('date')}")
            print(f"Time:             {booking.get('schedule', {}).get('time')}")
            print(f"\nLocation:         {booking.get('location', {}).get('address')}")
            print(f"City:             {booking.get('location', {}).get('city')}, {booking.get('location', {}).get('state')} {booking.get('location', {}).get('postal_code')}")
            
            pricing = booking.get('pricing', {})
            if pricing.get('estimated_price'):
                print(f"\nEstimated Price:  ${pricing.get('estimated_price'):.2f}")
            if pricing.get('final_price'):
                print(f"Final Price:      ${pricing.get('final_price'):.2f}")
            
            if booking.get('notes'):
                print(f"\nNotes:            {booking.get('notes')}")
            
            # Display images
            images = booking.get('images', [])
            print("\n" + "=" * 80)
            print(f"🖼️  IMAGES: {len(images)} found")
            print("=" * 80)
            
            if images:
                for idx, img in enumerate(images, 1):
                    print(f"\n📸 Image {idx}:")
                    print(f"   Order:  {img.get('order')}")
                    print(f"   URL:    {img.get('url')}")
                    print("")
                    
                print("✅ Image URLs are present and can be used in frontend!")
                print("💡 These are presigned S3 URLs that expire in 1 hour")
            else:
                print("ℹ️  No images attached to this booking")
            
            # Display timestamps
            timestamps = booking.get('timestamps', {})
            print("\n" + "=" * 80)
            print("🕐 TIMESTAMPS")
            print("=" * 80)
            print(f"Created:          {timestamps.get('created_at')}")
            print(f"Updated:          {timestamps.get('updated_at')}")
            print(f"Completed:        {timestamps.get('completed_at') or 'N/A'}")
            
            return booking
            
        elif response.status_code == 401:
            print("\n❌ UNAUTHORIZED: Token is invalid or expired")
            print(response.text)
            return None
            
        elif response.status_code == 403:
            print("\n❌ FORBIDDEN: You don't have permission to view this booking")
            print(response.text)
            return None
            
        elif response.status_code == 404:
            print("\n❌ NOT FOUND: Booking does not exist")
            print(response.text)
            return None
            
        else:
            print(f"\n❌ Error Response:")
            try:
                print(json.dumps(response.json(), indent=2))
            except:
                print(response.text)
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"\n❌ Request failed: {str(e)}")
        return None
    except json.JSONDecodeError as e:
        print(f"\n❌ Failed to parse JSON response: {str(e)}")
        print(f"Response text: {response.text}")
        return None


def main():
    """Main test function"""
    
    print("=" * 80)
    print("🚀 TESTING GET_BOOKING_DETAILS API WITH IMAGE URLS")
    print("=" * 80)
    print("")
    
    # Step 1: Get fresh token
    print("STEP 1: Getting fresh ID token from Cognito")
    print("-" * 80)
    token = get_fresh_id_token()
    
    # Step 2: Test with different bookings
    print("\n" + "=" * 80)
    print("STEP 2: Testing API endpoint")
    print("=" * 80)
    print("")
    
    # Test booking IDs - you can modify these
    test_bookings = [84, 79, 75]  # Modify based on your actual booking IDs
    
    successful_tests = 0
    for booking_id in test_bookings:
        print(f"\n{'=' * 80}")
        print(f"📌 TEST: Booking ID {booking_id}")
        print("=" * 80)
        
        result = test_get_booking_details(token, booking_id)
        if result:
            successful_tests += 1
        
        print("\n")
    
    # Summary
    print("=" * 80)
    print("📊 TEST SUMMARY")
    print("=" * 80)
    print(f"Total tests:      {len(test_bookings)}")
    print(f"Successful:       {successful_tests}")
    print(f"Failed:           {len(test_bookings) - successful_tests}")
    print("")
    
    if successful_tests == len(test_bookings):
        print("✅ All tests passed!")
    elif successful_tests > 0:
        print("⚠️  Some tests failed")
    else:
        print("❌ All tests failed")
    
    print("=" * 80)


if __name__ == "__main__":
    main()
