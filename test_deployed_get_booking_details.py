#!/usr/bin/env python3
"""
Test script for the deployed get_booking_details API endpoint
Tests the API with image retrieval functionality
"""

import requests
import json
import sys

# API Configuration
API_BASE_URL = "https://kfvf20j7j9.execute-api.us-east-2.amazonaws.com"
TOKEN_FILE = "/tmp/customer_jwt_token.txt"

def load_token():
    """Load JWT token from file"""
    try:
        with open(TOKEN_FILE, 'r') as f:
            return f.read().strip()
    except FileNotFoundError:
        print(f"❌ Token file not found: {TOKEN_FILE}")
        print("💡 Run: bash get_customer_token.sh")
        sys.exit(1)

def test_get_booking_details(booking_id):
    """Test the GET /customer/bookings/{booking_id} endpoint"""
    
    token = load_token()
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
        
        print(f"\n✅ Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            booking = data.get('booking', {})
            
            print("\n📋 Booking Details:")
            print(f"   Booking ID: {booking.get('booking_id')}")
            print(f"   Customer: {booking.get('customer', {}).get('name')}")
            print(f"   Provider: {booking.get('provider', {}).get('name')}")
            print(f"   Business: {booking.get('provider', {}).get('business_name')}")
            print(f"   Service: {booking.get('service', {}).get('category')} - {booking.get('service', {}).get('description')}")
            print(f"   Status: {booking.get('status')}")
            print(f"   Date: {booking.get('schedule', {}).get('date')}")
            print(f"   Time: {booking.get('schedule', {}).get('time')}")
            print(f"   Location: {booking.get('location', {}).get('address')}, {booking.get('location', {}).get('city')}")
            
            images = booking.get('images', [])
            print(f"\n🖼️  Images: {len(images)} found")
            if images:
                for img in images:
                    print(f"   - Order {img.get('order')}: {img.get('url')[:100]}...")
            else:
                print("   No images attached to this booking")
            
            print("\n📄 Full Response:")
            print(json.dumps(data, indent=2))
            
            return True
            
        else:
            print(f"\n❌ Error Response:")
            print(json.dumps(response.json(), indent=2))
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"\n❌ Request failed: {str(e)}")
        return False
    except json.JSONDecodeError as e:
        print(f"\n❌ Failed to parse JSON response: {str(e)}")
        print(f"Response text: {response.text}")
        return False

def test_unauthorized_access():
    """Test accessing a booking without authentication"""
    
    url = f"{API_BASE_URL}/customer/bookings/84"
    
    print(f"\n🔒 Testing unauthorized access (no token)")
    print(f"📍 URL: {url}")
    print("=" * 80)
    
    try:
        response = requests.get(url)
        print(f"\n✅ Status Code: {response.status_code}")
        
        if response.status_code == 401:
            print("✅ Correctly rejected unauthorized request")
        else:
            print(f"⚠️  Expected 401, got {response.status_code}")
            
        print(f"Response: {response.text}")
        
    except Exception as e:
        print(f"❌ Request failed: {str(e)}")

if __name__ == "__main__":
    print("🚀 Testing deployed get_booking_details API")
    print("=" * 80)
    
    # Test with booking that has images (booking_id 84)
    print("\n📌 Test 1: Get booking with images (booking_id=84)")
    test_get_booking_details(84)
    
    # Test with booking that has no images (booking_id 79)
    print("\n\n📌 Test 2: Get booking without images (booking_id=79)")
    test_get_booking_details(79)
    
    # Test unauthorized access
    print("\n\n📌 Test 3: Unauthorized access")
    test_unauthorized_access()
    
    print("\n" + "=" * 80)
    print("✅ All tests completed!")
