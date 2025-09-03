#!/usr/bin/env python3
"""Debug script for Crusoe Cloud API authentication - step by step following docs exactly."""

import os
import hmac
import hashlib
import base64
import datetime
import requests
import json
from dotenv import load_dotenv

def debug_crusoe_signature_step_by_step():
    """Debug Crusoe signature generation following the documentation example exactly."""
    load_dotenv()
    
    access_key = os.getenv('CRUSOE_ACCESS_KEY_ID')
    secret_key = os.getenv('CRUSOE_SECRET_ACCESS_KEY')
    
    if not access_key or not secret_key:
        print("Error: CRUSOE_ACCESS_KEY_ID and CRUSOE_SECRET_ACCESS_KEY must be set")
        return
    
    print(f"Access Key: {access_key}")
    print(f"Secret Key: {secret_key}")
    print(f"Secret Key Length: {len(secret_key)}")
    
    # Using the exact example from documentation
    request_path = "/v1alpha5/locations"
    request_verb = "GET"
    query_params = ""  # No query params for locations endpoint
    
    # Test with a fixed timestamp first (like in docs example)
    test_timestamp = "2022-03-01T01:23:45+09:00"
    
    print(f"\n=== Testing with fixed timestamp from docs ===")
    print(f"Path: {request_path}")
    print(f"Query params: '{query_params}'")
    print(f"Method: {request_verb}")
    print(f"Timestamp: {test_timestamp}")
    
    # Create payload exactly as documented
    api_version = "/v1alpha5"
    payload = f"{request_path}\n{query_params}\n{request_verb}\n{test_timestamp}\n"
    
    print(f"\nSignature payload:")
    print(repr(payload))
    
    # Decode secret key
    try:
        # Try without padding first
        decoded_secret = base64.urlsafe_b64decode(secret_key)
        print(f"Secret decoded without padding: {len(decoded_secret)} bytes")
    except Exception as e1:
        try:
            # Try with padding
            secret_key_padded = secret_key + '=' * (-len(secret_key) % 4)
            decoded_secret = base64.urlsafe_b64decode(secret_key_padded)
            print(f"Secret decoded with padding: {len(decoded_secret)} bytes")
        except Exception as e2:
            print(f"Failed to decode secret both ways: {e1}, {e2}")
            return
    
    # Create HMAC signature
    signature_bytes = hmac.new(
        decoded_secret,
        payload.encode('ascii'),
        hashlib.sha256
    ).digest()
    
    # Base64 encode without padding
    signature = base64.urlsafe_b64encode(signature_bytes).decode('ascii').rstrip("=")
    
    print(f"Generated signature: {signature}")
    
    # Create auth header
    signature_version = "1.0"
    auth_value = f"{signature_version}:{access_key}:{signature}"
    
    print(f"Authorization: Bearer {auth_value}")
    
    # Test with current timestamp
    print(f"\n=== Testing with current timestamp ===")
    
    # Try different timestamp formats
    dt = datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0)
    
    timestamp_formats = [
        dt.isoformat(),  # 2024-01-01T12:00:00+00:00
        dt.isoformat().replace("+00:00", "Z"),  # 2024-01-01T12:00:00Z
        str(dt).replace(" ", "T"),  # From Python sample code
    ]
    
    for i, current_timestamp in enumerate(timestamp_formats, 1):
        print(f"\nFormat {i}: {current_timestamp}")
        
        # Create payload with current timestamp
        current_payload = f"{request_path}\n{query_params}\n{request_verb}\n{current_timestamp}\n"
        
        # Create signature
        current_signature_bytes = hmac.new(
            decoded_secret,
            current_payload.encode('ascii'),
            hashlib.sha256
        ).digest()
        
        current_signature = base64.urlsafe_b64encode(current_signature_bytes).decode('ascii').rstrip("=")
        current_auth_value = f"{signature_version}:{access_key}:{current_signature}"
        
        # Test the request
        headers = {
            'X-Crusoe-Timestamp': current_timestamp,
            'Authorization': f"Bearer {current_auth_value}",
            'Content-Type': 'application/json'
        }
        
        try:
            url = 'https://api.crusoecloud.com/v1alpha5/locations'
            response = requests.get(url, headers=headers, timeout=10)
            
            print(f"  Status: {response.status_code}")
            
            if response.status_code == 200:
                print(f"  SUCCESS! ✅")
                data = response.json()
                print(f"  Response: {json.dumps(data, indent=2)[:200]}...")
                return  # Stop on first success
            else:
                print(f"  Failed: {response.text}")
                
        except Exception as e:
            print(f"  Error: {e}")
    
    # Try with Python sample code approach
    print(f"\n=== Testing with Python sample code approach ===")
    
    # Exactly as in the documentation Python sample
    api_version = "/v1alpha5"
    request_path = "/locations"  # Note: different from full path
    request_verb = "GET"
    query_params = ""
    
    dt = str(datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0))
    dt = dt.replace(" ", "T")  # Exactly as in sample
    
    payload = api_version + request_path + "\n" + query_params + "\n" + request_verb + "\n{0}\n".format(dt)
    
    print(f"Sample code payload: {repr(payload)}")
    
    signature_bytes = hmac.new(decoded_secret, payload.encode('ascii'), hashlib.sha256).digest()
    signature = base64.urlsafe_b64encode(signature_bytes).decode('ascii').rstrip("=")
    auth_value = f"{signature_version}:{access_key}:{signature}"
    
    headers = {
        'X-Crusoe-Timestamp': dt,
        'Authorization': f"Bearer {auth_value}",
        'Content-Type': 'application/json'
    }
    
    try:
        url = 'https://api.crusoecloud.com' + api_version + request_path
        response = requests.get(url, headers=headers, timeout=10)
        
        print(f"Sample approach - Status: {response.status_code}")
        
        if response.status_code == 200:
            print(f"SUCCESS with sample code approach! ✅")
            data = response.json()
            print(f"Response: {json.dumps(data, indent=2)[:200]}...")
        else:
            print(f"Sample approach failed: {response.text}")
            
    except Exception as e:
        print(f"Sample approach error: {e}")

if __name__ == "__main__":
    debug_crusoe_signature_step_by_step()
