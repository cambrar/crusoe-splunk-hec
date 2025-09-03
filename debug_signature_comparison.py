#!/usr/bin/env python3
"""Debug signature generation by comparing working vs current implementation."""

import os
import hmac
import hashlib
import base64
import datetime
import requests
import json
from dotenv import load_dotenv
from crusoe_client import CrusoeClient
from config import CrusoeConfig

def debug_signature_comparison():
    """Compare signatures between working manual code and our implementation."""
    
    load_dotenv()
    
    access_key = os.getenv('CRUSOE_ACCESS_KEY_ID')
    secret_key = os.getenv('CRUSOE_SECRET_ACCESS_KEY')
    org_id = os.getenv('CRUSOE_ORG_ID')
    
    print("=== SIGNATURE COMPARISON DEBUG ===")
    print(f"Access Key: {access_key}")
    print(f"Secret Key: {secret_key[:10]}...")
    print(f"Org ID: {org_id}")
    
    # Test 1: Working manual implementation (no query params)
    print(f"\n=== TEST 1: WORKING MANUAL IMPLEMENTATION ===")
    
    request_path = f"organizations/{org_id}/audit-logs"
    request_verb = "GET"
    query_params = ""  # Empty as in working example
    
    signature_version = "1.0"
    api_version = "/v1alpha5/"
    
    dt = str(datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0))
    dt = dt.replace(" ", "T")
    
    payload = api_version + request_path + "\n" + query_params + "\n" + request_verb + "\n{0}\n".format(dt)
    decoded = base64.urlsafe_b64decode(secret_key + '=' * (-len(secret_key) % 4))
    signature = base64.urlsafe_b64encode(hmac.new(decoded, msg=bytes(payload, 'ascii'), digestmod=hashlib.sha256).digest()).decode('ascii').rstrip("=")
    
    print(f"Manual payload: {repr(payload)}")
    print(f"Manual signature: {signature}")
    
    # Test with no query params
    url = 'https://api.crusoecloud.com' + api_version + request_path
    headers = {
        'X-Crusoe-Timestamp': dt, 
        'Authorization': f'Bearer {signature_version}:{access_key}:{signature}'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        print(f"Manual request status: {response.status_code}")
        if response.status_code == 200:
            print(f"✅ Manual request SUCCESS!")
        else:
            print(f"❌ Manual request failed: {response.text}")
    except Exception as e:
        print(f"❌ Manual request error: {e}")
    
    # Test 2: Our implementation
    print(f"\n=== TEST 2: OUR IMPLEMENTATION ===")
    
    try:
        config = CrusoeConfig.from_env()
        client = CrusoeClient(config)
        
        # Let's manually call the _create_crusoe_signature method to see what it generates
        url = f"{config.base_url}/organizations/{config.organization_id}/audit-logs"
        auth_headers = client._create_crusoe_signature("GET", url, params=None)
        
        print(f"Our URL: {url}")
        print(f"Our headers: {auth_headers}")
        
        # Extract the signature from our implementation for comparison
        auth_header = auth_headers['Authorization']
        our_signature = auth_header.split(':')[-1]
        our_timestamp = auth_headers['X-Crusoe-Timestamp']
        
        print(f"Our signature: {our_signature}")
        print(f"Our timestamp: {our_timestamp}")
        
        # Compare timestamps and signatures
        print(f"\n=== COMPARISON ===")
        print(f"Manual timestamp: {dt}")
        print(f"Our timestamp:    {our_timestamp}")
        print(f"Timestamps match: {dt == our_timestamp}")
        
        print(f"Manual signature: {signature}")
        print(f"Our signature:    {our_signature}")
        print(f"Signatures match: {signature == our_signature}")
        
        # Test our implementation with no query params
        response = requests.get(url, headers=auth_headers, timeout=10)
        print(f"Our request status: {response.status_code}")
        if response.status_code == 200:
            print(f"✅ Our request SUCCESS!")
        else:
            print(f"❌ Our request failed: {response.text}")
            
    except Exception as e:
        print(f"❌ Our implementation error: {e}")
    
    # Test 3: Our implementation with query params (the failing case)
    print(f"\n=== TEST 3: OUR IMPLEMENTATION WITH QUERY PARAMS ===")
    
    try:
        query_params_dict = {
            'start_time': '2025-09-03T16:01:28.259931+00:00',
            'end_time': '2025-09-03T17:01:28.259931+00:00',
            'limit': 100
        }
        
        # Test our signature generation
        auth_headers = client._create_crusoe_signature("GET", url, params=None)
        
        # Make request with query params
        response = requests.get(url, headers=auth_headers, params=query_params_dict, timeout=10)
        print(f"Our request with params status: {response.status_code}")
        if response.status_code == 200:
            print(f"✅ Our request with params SUCCESS!")
        else:
            print(f"❌ Our request with params failed: {response.text}")
            
    except Exception as e:
        print(f"❌ Our implementation with params error: {e}")
    
    print(f"\n=== DEBUGGING HINTS ===")
    print("1. Check if timestamps are causing issues (different formats)")
    print("2. Check if the path construction is different")
    print("3. Check if there are any whitespace/encoding issues")

if __name__ == "__main__":
    debug_signature_comparison()
