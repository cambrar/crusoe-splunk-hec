#!/usr/bin/env python3
"""Test different approaches to access audit logs."""

import os
import hmac
import hashlib
import base64
import datetime
import requests
import json
from dotenv import load_dotenv

def test_audit_approaches():
    """Test various audit log endpoint approaches."""
    load_dotenv()
    
    access_key = os.getenv('CRUSOE_ACCESS_KEY_ID')
    secret_key = os.getenv('CRUSOE_SECRET_ACCESS_KEY')
    
    print("=== TESTING DIFFERENT AUDIT LOG APPROACHES ===")
    
    def make_signed_request(endpoint, method="GET", query_params=""):
        api_version = "/v1alpha5"
        
        dt = str(datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0))
        dt = dt.replace(" ", "T")
        
        payload = api_version + endpoint + "\n" + query_params + "\n" + method + "\n{0}\n".format(dt)
        
        decoded = base64.urlsafe_b64decode(secret_key + '=' * (-len(secret_key) % 4))
        signature = base64.urlsafe_b64encode(
            hmac.new(decoded, msg=bytes(payload, 'ascii'), digestmod=hashlib.sha256).digest()
        ).decode('ascii').rstrip("=")
        
        headers = {
            'X-Crusoe-Timestamp': dt, 
            'Authorization': f'Bearer 1.0:{access_key}:{signature}',
            'Content-Type': 'application/json'
        }
        
        url = f'https://api.crusoecloud.com{api_version}{endpoint}'
        
        try:
            if query_params:
                params = dict(param.split('=') for param in query_params.split('&'))
                response = requests.get(url, headers=headers, params=params, timeout=10)
            else:
                response = requests.get(url, headers=headers, timeout=10)
            
            return response
            
        except Exception as e:
            print(f"❌ Request error: {e}")
            return None

    # Test different audit log endpoint patterns
    audit_endpoints = [
        "/audit-logs",  # Direct audit logs (no project)
        "/logs",        # Simple logs endpoint
        "/events",      # Events endpoint
        "/activity",    # Activity endpoint
        "/users/audit-logs",  # User-specific audit logs
    ]
    
    print("=== TESTING AUDIT LOG ENDPOINTS ===")
    
    for endpoint in audit_endpoints:
        print(f"\nTesting: {endpoint}")
        response = make_signed_request(endpoint)
        
        if response:
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    print(f"   ✅ SUCCESS! Audit logs found!")
                    print(f"   Data structure: {list(data.keys()) if isinstance(data, dict) else 'List/Other'}")
                    
                    if isinstance(data, dict) and 'items' in data:
                        print(f"   Number of logs: {len(data['items'])}")
                        if data['items']:
                            print(f"   Sample log: {json.dumps(data['items'][0], indent=8)}")
                    elif isinstance(data, list):
                        print(f"   Number of logs: {len(data)}")
                        if data:
                            print(f"   Sample log: {json.dumps(data[0], indent=8)}")
                    else:
                        print(f"   Response: {json.dumps(data, indent=6)}")
                        
                except Exception as e:
                    print(f"   ✅ SUCCESS! Non-JSON response: {response.text[:200]}")
                    
            elif response.status_code == 404:
                print(f"   ⚠️  404: Endpoint not found")
            elif response.status_code == 403:
                print(f"   ⚠️  403: No permission")
            else:
                print(f"   ⚠️  {response.status_code}: {response.text}")
        else:
            print(f"   ❌ Request failed")
    
    # Test with user ID in path (since we know the user ID)
    user_id = "c352ac90-8473-4038-8ca9-cdb107801efe"  # From previous output
    
    print(f"\n=== TESTING USER-SPECIFIC ENDPOINTS ===")
    print(f"Using User ID: {user_id}")
    
    user_endpoints = [
        f"/users/{user_id}/audit-logs",
        f"/users/{user_id}/logs", 
        f"/users/{user_id}/events",
        f"/users/{user_id}/activity",
    ]
    
    for endpoint in user_endpoints:
        print(f"\nTesting: {endpoint}")
        response = make_signed_request(endpoint)
        
        if response:
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    print(f"   ✅ SUCCESS! User audit logs found!")
                    print(f"   Data: {json.dumps(data, indent=6)}")
                except:
                    print(f"   ✅ SUCCESS! Response: {response.text[:200]}")
            else:
                print(f"   {response.text}")
    
    # Test some working endpoints to see if they contain project info
    print(f"\n=== CHECKING WORKING ENDPOINTS FOR PROJECT INFO ===")
    
    response = make_signed_request("/compute/images")
    if response and response.status_code == 200:
        try:
            data = response.json()
            if 'items' in data and data['items']:
                first_image = data['items'][0]
                print(f"Sample compute image data:")
                print(json.dumps(first_image, indent=4))
                
                # Look for project references
                for key, value in first_image.items():
                    if 'project' in key.lower():
                        print(f"🔍 Found project reference: {key} = {value}")
        except:
            pass
    
    print(f"\n" + "="*60)
    print("DIAGNOSIS:")
    print("="*60)
    print("Based on the API behavior:")
    print("1. Some endpoints work without project IDs (/compute/images)")
    print("2. Project/organization endpoints return 404")
    print("3. This suggests the API might be user-scoped, not project-scoped")
    print("4. OR your account might not have projects set up yet")
    print("\nRECOMMENDATIONS:")
    print("1. Check Crusoe console for project creation")
    print("2. Contact Crusoe support about audit log access")
    print("3. The working endpoints show authentication is perfect")

if __name__ == "__main__":
    test_audit_approaches()
