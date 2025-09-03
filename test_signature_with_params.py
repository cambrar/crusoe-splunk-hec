#!/usr/bin/env python3
"""Test signature generation with query parameters using our implementation."""

import os
from dotenv import load_dotenv
from config import CrusoeConfig
from crusoe_client import CrusoeClient
import requests

def test_signature_with_params():
    """Test our signature generation with query parameters."""
    
    load_dotenv()
    
    print("=== TESTING OUR SIGNATURE WITH QUERY PARAMS ===")
    
    try:
        config = CrusoeConfig.from_env()
        client = CrusoeClient(config)
        
        # Test the exact same parameters that are failing
        url = f"{config.base_url}/organizations/{config.organization_id}/audit-logs"
        params = {
            'start_time': '2025-09-03T16:07:36.778033+00:00',
            'end_time': '2025-09-03T17:07:36.778033+00:00',
            'limit': 100
        }
        
        print(f"URL: {url}")
        print(f"Params: {params}")
        
        # Generate signature with our implementation
        auth_headers = client._create_crusoe_signature("GET", url, params=params)
        
        print(f"Generated headers: {auth_headers}")
        
        # Extract signature details for debugging
        auth_header = auth_headers['Authorization']
        timestamp = auth_headers['X-Crusoe-Timestamp']
        
        # Parse the auth header to see the signature
        parts = auth_header.replace('Bearer ', '').split(':')
        version = parts[0]
        access_key = parts[1]
        signature = parts[2]
        
        print(f"Version: {version}")
        print(f"Access Key: {access_key}")
        print(f"Signature: {signature}")
        print(f"Timestamp: {timestamp}")
        
        # Let's also manually check what our canonicalized query params look like
        sorted_params = sorted(params.items())
        canonicalized = "&".join([f"{k}={v}" for k, v in sorted_params])
        print(f"Canonicalized query params: {canonicalized}")
        
        # Check the payload that was signed
        org_id = config.organization_id
        http_path = f"organizations/{org_id}/audit-logs"
        api_version = "/v1alpha5/"
        payload = f"{api_version}{http_path}\n{canonicalized}\nGET\n{timestamp}\n"
        print(f"Signed payload: {repr(payload)}")
        
        # Test the request
        print(f"\n=== MAKING REQUEST ===")
        response = requests.get(url, headers=auth_headers, params=params, timeout=10)
        
        print(f"Response Status: {response.status_code}")
        print(f"Request URL: {response.url}")
        
        if response.status_code == 200:
            print(f"✅ SUCCESS!")
            data = response.json()
            print(f"Number of logs: {len(data.get('items', []))}")
        else:
            print(f"❌ Failed: {response.text}")
            
            # Compare with manual working signature
            print(f"\n=== MANUAL COMPARISON ===")
            
            import hmac
            import hashlib
            import base64
            import datetime
            
            access_key = os.getenv('CRUSOE_ACCESS_KEY_ID')
            secret_key = os.getenv('CRUSOE_SECRET_ACCESS_KEY')
            
            # Manual signature generation (like your working example but with params)
            dt_manual = str(datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0)).replace(" ", "T")
            payload_manual = f"{api_version}{http_path}\n{canonicalized}\nGET\n{dt_manual}\n"
            
            decoded = base64.urlsafe_b64decode(secret_key + '=' * (-len(secret_key) % 4))
            signature_manual = base64.urlsafe_b64encode(
                hmac.new(decoded, msg=bytes(payload_manual, 'ascii'), digestmod=hashlib.sha256).digest()
            ).decode('ascii').rstrip("=")
            
            print(f"Manual payload: {repr(payload_manual)}")
            print(f"Manual signature: {signature_manual}")
            print(f"Our payload:    {repr(payload)}")
            print(f"Our signature:  {signature}")
            print(f"Payloads match: {payload_manual == payload}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_signature_with_params()
