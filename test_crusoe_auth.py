#!/usr/bin/env python3
"""Test script for Crusoe Cloud API authentication using the correct signature method."""

import os
import hmac
import hashlib
import base64
import datetime
import requests
import json
from dotenv import load_dotenv

def create_crusoe_signature(access_key_id: str, secret_key: str, method: str, path: str, query_params: str = "") -> tuple[str, str]:
    """Create Crusoe Cloud API signature according to their documentation.
    
    Args:
        access_key_id: API access key ID
        secret_key: API secret key
        method: HTTP method (GET, POST, etc.)
        path: Request path (e.g., '/v1alpha5/locations')
        query_params: Canonicalized query parameters
        
    Returns:
        Tuple of (timestamp, authorization_header)
    """
    # Create timestamp in RFC3339 format like the documentation example
    dt = datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0)
    timestamp = dt.isoformat()  # Keep the exact RFC3339 format
    
    # Create signature payload as per Crusoe documentation:
    # http_path + "\n" + canonicalized_query_params + "\n" + http_verb + "\n" + timestamp + "\n"
    payload = f"{path}\n{query_params}\n{method}\n{timestamp}\n"
    
    print(f"Signature payload:")
    print(repr(payload))
    
    # Decode the secret key from base64
    secret_key_padded = secret_key + '=' * (-len(secret_key) % 4)
    decoded_secret = base64.urlsafe_b64decode(secret_key_padded)
    
    # Create HMAC-SHA256 signature
    signature_bytes = hmac.new(
        decoded_secret,
        payload.encode('ascii'),
        hashlib.sha256
    ).digest()
    
    # Base64 encode the signature (without padding)
    signature = base64.urlsafe_b64encode(signature_bytes).decode('ascii').rstrip("=")
    
    # Create authorization header: Bearer version:access_key_id:signature
    signature_version = "1.0"
    auth_value = f"{signature_version}:{access_key_id}:{signature}"
    
    return timestamp, f"Bearer {auth_value}"

def test_crusoe_api():
    """Test the Crusoe API with correct authentication."""
    load_dotenv()
    
    access_key = os.getenv('CRUSOE_ACCESS_KEY_ID')
    secret_key = os.getenv('CRUSOE_SECRET_ACCESS_KEY')
    
    if not access_key or not secret_key:
        print("Error: CRUSOE_ACCESS_KEY_ID and CRUSOE_SECRET_ACCESS_KEY must be set in .env file")
        return
    
    print(f"Using access key: {access_key}")
    print(f"Secret key length: {len(secret_key)} characters")
    
    # Test with locations endpoint (should be publicly accessible)
    url = 'https://api.crusoecloud.com/v1alpha5/locations'
    path = '/v1alpha5/locations'
    method = 'GET'
    
    try:
        timestamp, auth_header = create_crusoe_signature(access_key, secret_key, method, path)
        
        headers = {
            'X-Crusoe-Timestamp': timestamp,
            'Authorization': auth_header,
            'Content-Type': 'application/json'
        }
        
        print(f"\nRequest headers:")
        print(f"X-Crusoe-Timestamp: {timestamp}")
        print(f"Authorization: {auth_header}")
        
        response = requests.get(url, headers=headers)
        
        print(f"\nResponse Status: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Success! Response: {json.dumps(data, indent=2)[:500]}...")
        else:
            print(f"Error Response: {response.text}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_crusoe_api()
