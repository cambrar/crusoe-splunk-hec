#!/usr/bin/env python3
"""Simple authentication test for Crusoe API."""

import os
import requests
import base64
import hmac
import hashlib
from datetime import datetime
from urllib.parse import quote
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_basic_key_auth():
    """Test using access key and secret as basic auth."""
    access_key = os.getenv('CRUSOE_ACCESS_KEY_ID')
    secret_key = os.getenv('CRUSOE_SECRET_ACCESS_KEY')
    org_id = os.getenv('CRUSOE_ORG_ID')
    
    print("=== Testing Basic Auth ===")
    
    # Try basic auth with username:password
    url = f"https://api.crusoecloud.com/v1alpha5/organizations"
    
    auth = (access_key, secret_key)
    response = requests.get(url, auth=auth)
    
    print(f"Basic Auth Status: {response.status_code}")
    print(f"Response: {response.text[:200]}...")
    
    return response.status_code == 200

def test_api_key_header():
    """Test using access key in different header formats."""
    access_key = os.getenv('CRUSOE_ACCESS_KEY_ID')
    secret_key = os.getenv('CRUSOE_SECRET_ACCESS_KEY')
    
    print("\\n=== Testing API Key Headers ===")
    
    url = f"https://api.crusoecloud.com/v1alpha5/organizations"
    
    headers_to_try = [
        {'X-API-Key': access_key},
        {'X-API-Token': access_key},
        {'API-Key': access_key},
        {'Authorization': f'API-Key {access_key}'},
        {'Authorization': f'Token {access_key}'},
        {'Authorization': f'{access_key}:{secret_key}'},
        {'X-Access-Key': access_key, 'X-Secret-Key': secret_key},
    ]
    
    for i, headers in enumerate(headers_to_try):
        print(f"\\nTrying headers {i+1}: {list(headers.keys())}")
        response = requests.get(url, headers=headers)
        print(f"  Status: {response.status_code}")
        
        if response.status_code != 401 and response.status_code != 404:
            print(f"  Response: {response.text[:200]}...")
            if response.status_code == 200:
                print(f"  ✅ Success with headers: {headers}")
                return headers
    
    return None

def test_token_exchange():
    """Test if we need to exchange access key for a token first."""
    access_key = os.getenv('CRUSOE_ACCESS_KEY_ID')
    secret_key = os.getenv('CRUSOE_SECRET_ACCESS_KEY')
    
    print("\\n=== Testing Token Exchange ===")
    
    # Common token exchange endpoints
    token_endpoints = [
        "https://api.crusoecloud.com/v1alpha5/auth/token",
        "https://api.crusoecloud.com/v1alpha5/token",
        "https://api.crusoecloud.com/auth/token",
        "https://auth.crusoecloud.com/token",
    ]
    
    for endpoint in token_endpoints:
        print(f"\\nTrying token endpoint: {endpoint}")
        
        # Try POST with credentials
        data = {
            'access_key': access_key,
            'secret_key': secret_key,
            'grant_type': 'client_credentials'
        }
        
        try:
            response = requests.post(endpoint, json=data)
            print(f"  Status: {response.status_code}")
            
            if response.status_code == 200:
                print(f"  ✅ Token exchange successful!")
                print(f"  Response: {response.text}")
                return response.json()
            elif response.status_code != 404:
                print(f"  Response: {response.text[:200]}...")
                
        except Exception as e:
            print(f"  Error: {str(e)}")
    
    return None

def check_endpoints():
    """Check what endpoints are available."""
    print("\\n=== Checking Available Endpoints ===")
    
    base_urls = [
        "https://api.crusoecloud.com/v1alpha5",
        "https://api.crusoecloud.com/v1",
        "https://api.crusoecloud.com",
    ]
    
    for base_url in base_urls:
        print(f"\\nTesting base URL: {base_url}")
        
        endpoints_to_try = [
            "",
            "/",
            "/health",
            "/status",
            "/version",
            "/organizations",
            "/auth",
        ]
        
        for endpoint in endpoints_to_try:
            url = f"{base_url}{endpoint}"
            try:
                response = requests.get(url, timeout=5)
                if response.status_code != 404:
                    print(f"  {endpoint or '/'}: {response.status_code}")
                    if response.status_code == 200:
                        print(f"    Response: {response.text[:100]}...")
            except:
                pass

def main():
    """Run authentication tests."""
    print("Crusoe API Authentication Tests")
    print("=" * 40)
    
    access_key = os.getenv('CRUSOE_ACCESS_KEY_ID')
    secret_key = os.getenv('CRUSOE_SECRET_ACCESS_KEY')
    
    if not access_key or not secret_key:
        print("❌ Access key or secret key not set!")
        return
    
    print(f"Testing with:")
    print(f"  Access Key: {access_key[:8]}...")
    print(f"  Secret Key: {secret_key[:8]}...")
    
    # Try different authentication methods
    if test_basic_key_auth():
        print("\\n✅ Basic auth works!")
        return
    
    working_headers = test_api_key_header()
    if working_headers:
        print(f"\\n✅ Found working headers: {working_headers}")
        return
    
    token_data = test_token_exchange()
    if token_data:
        print(f"\\n✅ Token exchange works: {token_data}")
        return
    
    # Check what endpoints are available
    check_endpoints()
    
    print("\\n❌ All authentication methods failed")
    print("\\nNext steps:")
    print("1. Double-check your access key and secret key from Crusoe console")
    print("2. Verify these keys have audit log permissions")
    print("3. Check if there's a different API endpoint or version")
    print("4. Contact Crusoe support for authentication guidance")

if __name__ == "__main__":
    main()
