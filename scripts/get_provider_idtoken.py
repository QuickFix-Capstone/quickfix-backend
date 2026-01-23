#!/usr/bin/env python3
"""
Script to get a fresh Service Provider ID token from AWS Cognito
Usage: python3 get_provider_idtoken.py [--refresh]
"""

import boto3
import json
import sys
from datetime import datetime, timedelta

# Cognito Configuration
USER_POOL_ID = "us-east-2_45z5OMePi"
CLIENT_ID = "p2u5qdegml3hp60n6ohu52n2b"
REGION = "us-east-2"

# User Credentials
EMAIL = "ajaypersaud04@gmail.com"
PASSWORD = "Ajay@2003"


def get_fresh_id_token():
    """
    Authenticate with AWS Cognito and retrieve a fresh ID token.
    
    Returns:
        dict: Contains id_token, access_token, refresh_token, and expiration info
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
        access_token = auth_result['AccessToken']
        refresh_token = auth_result.get('RefreshToken', 'N/A')
        expires_in = auth_result['ExpiresIn']
        
        # Calculate expiration time
        expiration_time = datetime.now() + timedelta(seconds=expires_in)
        
        print("✅ Authentication successful!")
        print("")
        print("━" * 80)
        print("📋 ID TOKEN (use this for API calls):")
        print("━" * 80)
        print(id_token)
        print("")
        print("━" * 80)
        print(f"⏰ Token expires in: {expires_in} seconds (~{expires_in // 60} minutes)")
        print(f"🕐 Expiration time: {expiration_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print("")
        
        # Save to file
        token_file = '/tmp/jwt_token.txt'
        with open(token_file, 'w') as f:
            f.write(id_token)
        print(f"💾 Token saved to: {token_file}")
        print("")
        
        # Save full response to JSON
        json_file = '/tmp/cognito_tokens.json'
        token_data = {
            'id_token': id_token,
            'access_token': access_token,
            'refresh_token': refresh_token,
            'expires_in': expires_in,
            'expiration_time': expiration_time.isoformat(),
            'retrieved_at': datetime.now().isoformat()
        }
        with open(json_file, 'w') as f:
            json.dump(token_data, f, indent=2)
        print(f"💾 Full token data saved to: {json_file}")
        print("")
        
        print("💡 Usage examples:")
        print("   # Export as environment variable:")
        print(f"   export JWT_TOKEN=\"{id_token}\"")
        print("")
        print("   # Or load from file:")
        print("   export JWT_TOKEN=$(cat /tmp/jwt_token.txt)")
        print("")
        print("   # Use in curl commands:")
        print("   curl -H \"Authorization: Bearer ${JWT_TOKEN}\" https://your-api.com/endpoint")
        print("")
        
        return token_data
        
    except client.exceptions.NotAuthorizedException as e:
        print("❌ Authentication failed: Invalid username or password")
        print(f"Error: {str(e)}")
        sys.exit(1)
        
    except client.exceptions.UserNotFoundException as e:
        print("❌ Authentication failed: User not found")
        print(f"Error: {str(e)}")
        sys.exit(1)
        
    except Exception as e:
        print(f"❌ An error occurred: {str(e)}")
        sys.exit(1)


def refresh_token_using_refresh_token(refresh_token):
    """
    Use a refresh token to get a new ID token without re-entering credentials.
    
    Args:
        refresh_token (str): The refresh token from a previous authentication
        
    Returns:
        dict: Contains new id_token and access_token
    """
    try:
        client = boto3.client('cognito-idp', region_name=REGION)
        
        print("🔄 Refreshing token using refresh token...")
        
        response = client.initiate_auth(
            ClientId=CLIENT_ID,
            AuthFlow='REFRESH_TOKEN_AUTH',
            AuthParameters={
                'REFRESH_TOKEN': refresh_token
            }
        )
        
        auth_result = response['AuthenticationResult']
        id_token = auth_result['IdToken']
        access_token = auth_result['AccessToken']
        expires_in = auth_result['ExpiresIn']
        
        print("✅ Token refreshed successfully!")
        print(f"⏰ New token expires in: {expires_in} seconds (~{expires_in // 60} minutes)")
        print("")
        print("New ID Token:")
        print(id_token)
        
        return {
            'id_token': id_token,
            'access_token': access_token,
            'expires_in': expires_in
        }
        
    except Exception as e:
        print(f"❌ Token refresh failed: {str(e)}")
        print("💡 Falling back to full authentication...")
        return get_fresh_id_token()


if __name__ == "__main__":
    # Check if refresh token is provided as argument
    if len(sys.argv) > 1 and sys.argv[1] == "--refresh":
        try:
            with open('/tmp/cognito_tokens.json', 'r') as f:
                token_data = json.load(f)
                refresh_token = token_data.get('refresh_token')
                if refresh_token and refresh_token != 'N/A':
                    refresh_token_using_refresh_token(refresh_token)
                else:
                    print("⚠️  No refresh token found, performing full authentication...")
                    get_fresh_id_token()
        except FileNotFoundError:
            print("⚠️  No previous token data found, performing full authentication...")
            get_fresh_id_token()
    else:
        get_fresh_id_token()
