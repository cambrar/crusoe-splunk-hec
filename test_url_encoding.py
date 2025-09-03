#!/usr/bin/env python3
"""Test URL encoding in signature generation."""

import os
import hmac
import hashlib
import base64
import datetime
import requests
from urllib.parse import quote_plus, urlencode
from dotenv import load_dotenv

def test_url_encoding():
    """Test different URL encoding approaches in signature."""
    
    load_dotenv()
    
    access_key = os.getenv('CRUSOE_ACCESS_KEY_ID')
    secret_key = os.getenv('CRUSOE_SECRET_ACCESS_KEY')
    org_id = os.getenv('CRUSOE_ORG_ID')
    
    print("=== URL ENCODING SIGNATURE TEST ===")
    
    # Test parameters
    params = {
        'start_time': '2025-09-03T16:07:36.778033+00:00',
        'end_time': '2025-09-03T17:07:36.778033+00:00',
        'limit': 100
    }
    
    request_path = f"organizations/{org_id}/audit-logs"
    request_verb = "GET"
    signature_version = "1.0"
    api_version = "/v1alpha5/"
    
    dt = str(datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0)).replace(" ", "T")
    
    url = f'https://api.crusoecloud.com{api_version}{request_path}'
    
    # Test 1: Unencoded query params in signature (our current approach)
    print(f"\n=== TEST 1: UNENCODED QUERY PARAMS IN SIGNATURE ===")
    sorted_params = sorted(params.items())
    unencoded_query = "&".join([f"{k}={v}" for k, v in sorted_params])
    
    payload1 = f"{api_version}{request_path}\n{unencoded_query}\n{request_verb}\n{dt}\n"
    print(f"Payload: {repr(payload1)}")
    
    decoded = base64.urlsafe_b64decode(secret_key + '=' * (-len(secret_key) % 4))
    signature1 = base64.urlsafe_b64encode(
        hmac.new(decoded, msg=bytes(payload1, 'ascii'), digestmod=hashlib.sha256).digest()
    ).decode('ascii').rstrip("=")
    
    headers1 = {
        'X-Crusoe-Timestamp': dt,
        'Authorization': f'Bearer {signature_version}:{access_key}:{signature1}'
    }
    
    response1 = requests.get(url, headers=headers1, params=params, timeout=10)
    print(f"Status: {response1.status_code}")
    if response1.status_code != 200:
        print(f"Error: {response1.text}")
    
    # Test 2: URL-encoded query params in signature
    print(f"\n=== TEST 2: URL-ENCODED QUERY PARAMS IN SIGNATURE ===")
    encoded_query = urlencode(sorted_params)
    
    payload2 = f"{api_version}{request_path}\n{encoded_query}\n{request_verb}\n{dt}\n"
    print(f"Payload: {repr(payload2)}")
    
    signature2 = base64.urlsafe_b64encode(
        hmac.new(decoded, msg=bytes(payload2, 'ascii'), digestmod=hashlib.sha256).digest()
    ).decode('ascii').rstrip("=")
    
    headers2 = {
        'X-Crusoe-Timestamp': dt,
        'Authorization': f'Bearer {signature_version}:{access_key}:{signature2}'
    }
    
    response2 = requests.get(url, headers=headers2, params=params, timeout=10)
    print(f"Status: {response2.status_code}")
    if response2.status_code != 200:
        print(f"Error: {response2.text}")
    else:
        print(f"✅ SUCCESS with URL-encoded signature!")
    
    # Test 3: Manual URL encoding (quote_plus)
    print(f"\n=== TEST 3: MANUAL URL ENCODING (quote_plus) ===")
    manual_encoded_query = "&".join([f"{k}={quote_plus(str(v))}" for k, v in sorted_params])
    
    payload3 = f"{api_version}{request_path}\n{manual_encoded_query}\n{request_verb}\n{dt}\n"
    print(f"Payload: {repr(payload3)}")
    
    signature3 = base64.urlsafe_b64encode(
        hmac.new(decoded, msg=bytes(payload3, 'ascii'), digestmod=hashlib.sha256).digest()
    ).decode('ascii').rstrip("=")
    
    headers3 = {
        'X-Crusoe-Timestamp': dt,
        'Authorization': f'Bearer {signature_version}:{access_key}:{signature3}'
    }
    
    response3 = requests.get(url, headers=headers3, params=params, timeout=10)
    print(f"Status: {response3.status_code}")
    if response3.status_code != 200:
        print(f"Error: {response3.text}")
    else:
        print(f"✅ SUCCESS with manual encoding!")
    
    # Show the differences
    print(f"\n=== QUERY STRING COMPARISON ===")
    print(f"Unencoded:     {unencoded_query}")
    print(f"urlencode():   {encoded_query}")
    print(f"quote_plus():  {manual_encoded_query}")
    
    # Show actual request URL
    print(f"\nActual request URL: {response1.url}")

if __name__ == "__main__":
    test_url_encoding()
