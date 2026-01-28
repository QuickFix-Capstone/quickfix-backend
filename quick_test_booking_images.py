#!/usr/bin/env python3
"""
Quick test script to verify get_booking_details returns image URLs
Run: python3 quick_test_booking_images.py [booking_id]
"""

import boto3
import requests
import json
import sys

# Configuration
USER_POOL_ID = "us-east-2_45z5OMePi"
CLIENT_ID = "p2u5qdegml3hp60n6ohu52n2b"
REGION = "us-east-2"
EMAIL = "ykphrfly@gmail.com"
PASSWORD = "Yang@860101"
API_BASE_URL = "https://kfvf20j7j9.execute-api.us-east-2.amazonaws.com"

def get_token():
    """Get fresh Cognito token"""
    client = boto3.client('cognito-idp', region_name=REGION)
    response = client.initiate_auth(
        ClientId=CLIENT_ID,
        AuthFlow='USER_PASSWORD_AUTH',
        AuthParameters={'USERNAME': EMAIL, 'PASSWORD': PASSWORD}
    )
    return response['AuthenticationResult']['IdToken']

def test_booking(booking_id):
    """Test booking details endpoint"""
    print(f"🔐 Getting fresh token...")
    token = get_token()
    print(f"✅ Token obtained\n")
    
    url = f"{API_BASE_URL}/customer/bookings/{booking_id}"
    headers = {"Authorization": f"Bearer {token}"}
    
    print(f"📡 Calling: GET /customer/bookings/{booking_id}")
    response = requests.get(url, headers=headers)
    
    print(f"📊 Status: {response.status_code}\n")
    
    if response.status_code == 200:
        data = response.json()
        booking = data['booking']
        
        print(f"✅ Booking #{booking['booking_id']}")
        print(f"   Service: {booking['service']['category']}")
        print(f"   Status: {booking['status']}")
        print(f"   Date: {booking['schedule']['date']} at {booking['schedule']['time']}")
        
        images = booking.get('images', [])
        print(f"\n🖼️  Images: {len(images)}")
        
        if images:
            for i, img in enumerate(images, 1):
                print(f"\n   Image {i} (order: {img['order']}):")
                print(f"   {img['url'][:80]}...")
                print(f"   ...{img['url'][-40:]}")
            print(f"\n✅ SUCCESS! Image URLs are returned and ready for frontend!")
        else:
            print(f"   ℹ️  No images for this booking")
        
        return True
    else:
        print(f"❌ Error: {response.text}")
        return False

if __name__ == "__main__":
    booking_id = sys.argv[1] if len(sys.argv) > 1 else "84"
    print("=" * 80)
    print(f"Testing get_booking_details with booking_id={booking_id}")
    print("=" * 80 + "\n")
    
    try:
        test_booking(booking_id)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)
    
    print("\n" + "=" * 80)
