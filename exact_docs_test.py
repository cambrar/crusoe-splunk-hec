#!/usr/bin/env python3
"""Test exactly replicating the Crusoe API documentation example."""

import os
import hmac
import hashlib
import base64
import datetime
import requests
import json
from dotenv import load_dotenv

def test_exact_docs_example():
    """Test using the exact example from Crusoe documentation."""
    load_dotenv()
    
    access_key = os.getenv('CRUSOE_ACCESS_KEY_ID')
    secret_key = os.getenv('CRUSOE_SECRET_ACCESS_KEY')
    
    print("=== EXACT DOCUMENTATION EXAMPLE TEST ===")
    print(f"Access Key: {access_key}")
    print(f"Secret Key: {secret_key}")
    
    # Use the exact format from the documentation Python sample
    api_access_key = access_key
    api_secret_key = secret_key
    
    request_path = "/capacities"  # From the docs example
    request_verb = "GET"
    
    # Query params from the docs example
    query_params = {
        "product_name": "a100.8x",
        "location": "us-northcentral1-a"
    }
    query_params_str = "&".join([f"{k}={v}" for k, v in sorted(query_params.items())])
    
    signature_version = "1.0"
    api_version = "/v1alpha5"
    
    # Timestamp format exactly as in docs
    dt = str(datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0))
    dt = dt.replace(" ", "T")
    
    print(f"\nRequest details:")
    print(f"Path: {api_version + request_path}")
    print(f"Query params: {query_params_str}")
    print(f"Method: {request_verb}")
    print(f"Timestamp: {dt}")
    
    # Build payload exactly as in docs
    payload = api_version + request_path + "\n" + query_params_str + "\n" + request_verb + "\n{0}\n".format(dt)
    
    print(f"\nPayload for signing:")
    print(repr(payload))
    
    # Decode secret and create signature exactly as in docs
    decoded = base64.urlsafe_b64decode(api_secret_key + '=' * (-len(api_secret_key) % 4))
    signature = base64.urlsafe_b64encode(hmac.new(decoded, msg=bytes(payload, 'ascii'), digestmod=hashlib.sha256).digest()).decode('ascii').rstrip("=")
    
    print(f"\nGenerated signature: {signature}")
    
    # Make request exactly as in docs
    full_url = 'https://api.crusoecloud.com' + api_version + request_path
    headers = {
        'X-Crusoe-Timestamp': dt, 
        'Authorization': 'Bearer {0}:{1}:{2}'.format(signature_version, api_access_key, signature)
    }
    
    print(f"\nRequest URL: {full_url}")
    print(f"Headers: {headers}")
    
    try:
        response = requests.get(
            full_url,
            headers=headers,
            params=query_params,
        )
        
        print(f"\nResponse Status: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                print(f"✅ SUCCESS! Response: {json.dumps(data, indent=2)}")
            except:
                print(f"✅ SUCCESS! Response: {response.text}")
        else:
            print(f"❌ Error Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Request failed: {e}")

    # Also test the simple /locations endpoint without query params
    print(f"\n" + "="*60)
    print("=== TESTING SIMPLE LOCATIONS ENDPOINT ===")
    
    request_path = "/locations"
    query_params_str = ""
    
    payload = api_version + request_path + "\n" + query_params_str + "\n" + request_verb + "\n{0}\n".format(dt)
    
    print(f"Simple payload: {repr(payload)}")
    
    signature = base64.urlsafe_b64encode(hmac.new(decoded, msg=bytes(payload, 'ascii'), digestmod=hashlib.sha256).digest()).decode('ascii').rstrip("=")
    
    full_url = 'https://api.crusoecloud.com' + api_version + request_path
    headers = {
        'X-Crusoe-Timestamp': dt, 
        'Authorization': 'Bearer {0}:{1}:{2}'.format(signature_version, api_access_key, signature)
    }
    
    try:
        response = requests.get(full_url, headers=headers)
        
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                print(f"✅ SUCCESS! Locations: {json.dumps(data, indent=2)[:300]}...")
            except:
                print(f"✅ SUCCESS! Response: {response.text[:300]}...")
        else:
            print(f"❌ Error: {response.text}")
            
    except Exception as e:
        print(f"❌ Request failed: {e}")

if __name__ == "__main__":
    test_exact_docs_example()
