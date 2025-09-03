#!/usr/bin/env python3
"""Test Crusoe audit logs API with correct project-based endpoint."""

import os
import hmac
import hashlib
import base64
import datetime
import requests
import json
from dotenv import load_dotenv

def test_project_audit_logs():
    """Test the project-based audit logs endpoint."""
    load_dotenv()
    
    access_key = os.getenv('CRUSOE_ACCESS_KEY_ID')
    secret_key = os.getenv('CRUSOE_SECRET_ACCESS_KEY')
    project_id = os.getenv('CRUSOE_PROJECT_ID', 'robc')  # Default to 'robc' as mentioned
    
    if not access_key or not secret_key:
        print("❌ Missing CRUSOE_ACCESS_KEY_ID or CRUSOE_SECRET_ACCESS_KEY")
        return
    
    print("=== TESTING PROJECT-BASED AUDIT LOGS ENDPOINT ===")
    print(f"Access Key: {access_key}")
    print(f"Secret Key: {secret_key}")
    print(f"Project ID: {project_id}")
    
    # Test the correct audit logs endpoint format
    api_version = "/v1alpha5"
    request_path = f"/projects/{project_id}/audit-logs"
    request_verb = "GET"
    query_params_str = ""  # No query params for basic test
    
    # Create timestamp
    dt = str(datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0))
    dt = dt.replace(" ", "T")
    
    print(f"\nRequest details:")
    print(f"Full path: {api_version + request_path}")
    print(f"Method: {request_verb}")
    print(f"Timestamp: {dt}")
    
    # Build payload for signing
    payload = api_version + request_path + "\n" + query_params_str + "\n" + request_verb + "\n{0}\n".format(dt)
    
    print(f"\nPayload for signing:")
    print(repr(payload))
    
    # Generate signature
    try:
        decoded = base64.urlsafe_b64decode(secret_key + '=' * (-len(secret_key) % 4))
        signature = base64.urlsafe_b64encode(
            hmac.new(decoded, msg=bytes(payload, 'ascii'), digestmod=hashlib.sha256).digest()
        ).decode('ascii').rstrip("=")
        
        print(f"Generated signature: {signature}")
        
        # Make request
        full_url = f'https://api.crusoecloud.com{api_version}{request_path}'
        headers = {
            'X-Crusoe-Timestamp': dt, 
            'Authorization': f'Bearer 1.0:{access_key}:{signature}',
            'Content-Type': 'application/json'
        }
        
        print(f"\nRequest URL: {full_url}")
        print(f"Headers: {headers}")
        
        response = requests.get(full_url, headers=headers, timeout=10)
        
        print(f"\nResponse Status: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                print(f"✅ SUCCESS! Audit logs retrieved:")
                print(json.dumps(data, indent=2))
            except:
                print(f"✅ SUCCESS! Response: {response.text}")
        
        elif response.status_code == 401:
            print(f"❌ 401 Unauthorized: {response.text}")
            print("   This suggests the API credentials are still invalid.")
        
        elif response.status_code == 403:
            print(f"⚠️  403 Forbidden: {response.text}")
            print("   Authentication worked but no permission for this project/endpoint.")
        
        elif response.status_code == 404:
            print(f"⚠️  404 Not Found: {response.text}")
            print(f"   The project '{project_id}' might not exist or the endpoint is wrong.")
        
        else:
            print(f"⚠️  {response.status_code}: {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

    # Also test if we can access any project-level endpoints
    print(f"\n" + "="*60)
    print("=== TESTING OTHER PROJECT ENDPOINTS ===")
    
    # Test endpoints that should work with valid credentials
    test_endpoints = [
        f"/projects/{project_id}/compute/instances",
        f"/projects/{project_id}/storage/disks", 
        f"/projects/{project_id}/compute/images",
    ]
    
    for endpoint in test_endpoints:
        print(f"\nTesting: {endpoint}")
        
        payload = api_version + endpoint + "\n\nGET\n{0}\n".format(dt)
        signature = base64.urlsafe_b64encode(
            hmac.new(decoded, msg=bytes(payload, 'ascii'), digestmod=hashlib.sha256).digest()
        ).decode('ascii').rstrip("=")
        
        headers = {
            'X-Crusoe-Timestamp': dt, 
            'Authorization': f'Bearer 1.0:{access_key}:{signature}',
            'Content-Type': 'application/json'
        }
        
        try:
            response = requests.get(f'https://api.crusoecloud.com{api_version}{endpoint}', headers=headers, timeout=10)
            print(f"  Status: {response.status_code}")
            
            if response.status_code == 200:
                print(f"  ✅ Success!")
            elif response.status_code == 401:
                print(f"  ❌ 401 - Authentication failed")
            elif response.status_code == 403:
                print(f"  ⚠️  403 - No permission (but auth worked)")
            elif response.status_code == 404:
                print(f"  ⚠️  404 - Endpoint not found")
            else:
                print(f"  ⚠️  {response.status_code} - {response.text[:100]}")
                
        except Exception as e:
            print(f"  ❌ Error: {e}")

if __name__ == "__main__":
    test_project_audit_logs()
