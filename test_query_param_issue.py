#!/usr/bin/env python3
"""Test specifically the query parameter issue."""

import os
import hmac
import hashlib
import base64
import datetime
import requests
import json
from dotenv import load_dotenv

def test_query_param_issue():
    """Test the exact same signature with and without query parameters."""
    
    load_dotenv()
    
    access_key = os.getenv('CRUSOE_ACCESS_KEY_ID')
    secret_key = os.getenv('CRUSOE_SECRET_ACCESS_KEY')
    org_id = os.getenv('CRUSOE_ORG_ID')
    
    print("=== QUERY PARAMETER ISSUE TEST ===")
    
    # Generate ONE signature and timestamp to use for all tests
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
    
    print(f"Timestamp: {dt}")
    print(f"Signature: {signature}")
    print(f"Payload: {repr(payload)}")
    
    url = 'https://api.crusoecloud.com' + api_version + request_path
    headers = {
        'X-Crusoe-Timestamp': dt, 
        'Authorization': f'Bearer {signature_version}:{access_key}:{signature}'
    }
    
    print(f"URL: {url}")
    print(f"Headers: {headers}")
    
    # Test 1: No query parameters (should work)
    print(f"\n=== TEST 1: NO QUERY PARAMETERS ===")
    try:
        response = requests.get(url, headers=headers, timeout=10)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            print(f"✅ SUCCESS without query params!")
            data = response.json()
            print(f"Number of logs: {len(data.get('items', []))}")
        else:
            print(f"❌ Failed: {response.text}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 2: With simple query parameters (limit only)
    print(f"\n=== TEST 2: WITH LIMIT PARAMETER ===")
    try:
        simple_params = {'limit': 5}
        response = requests.get(url, headers=headers, params=simple_params, timeout=10)
        print(f"Status: {response.status_code}")
        print(f"Request URL: {response.url}")
        if response.status_code == 200:
            print(f"✅ SUCCESS with limit param!")
            data = response.json()
            print(f"Number of logs: {len(data.get('items', []))}")
        else:
            print(f"❌ Failed: {response.text}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 3: With time range parameters (the failing case)
    print(f"\n=== TEST 3: WITH TIME RANGE PARAMETERS ===")
    try:
        time_params = {
            'start_time': '2025-09-03T16:01:28.259931+00:00',
            'end_time': '2025-09-03T17:01:28.259931+00:00',
            'limit': 100
        }
        response = requests.get(url, headers=headers, params=time_params, timeout=10)
        print(f"Status: {response.status_code}")
        print(f"Request URL: {response.url}")
        if response.status_code == 200:
            print(f"✅ SUCCESS with time range params!")
            data = response.json()
            print(f"Number of logs: {len(data.get('items', []))}")
        else:
            print(f"❌ Failed: {response.text}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 4: With different time format
    print(f"\n=== TEST 4: WITH DIFFERENT TIME FORMAT ===")
    try:
        # Try simpler time format
        simple_time_params = {
            'start_time': '2025-09-03T16:00:00Z',
            'end_time': '2025-09-03T17:00:00Z',
            'limit': 10
        }
        response = requests.get(url, headers=headers, params=simple_time_params, timeout=10)
        print(f"Status: {response.status_code}")
        print(f"Request URL: {response.url}")
        if response.status_code == 200:
            print(f"✅ SUCCESS with simple time format!")
            data = response.json()
            print(f"Number of logs: {len(data.get('items', []))}")
        else:
            print(f"❌ Failed: {response.text}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print(f"\n=== ANALYSIS ===")
    print("Testing if the issue is:")
    print("1. Query parameters in general")
    print("2. Specific time format/encoding")
    print("3. Combination of parameters")
    print("4. Time range validation")

if __name__ == "__main__":
    test_query_param_issue()
