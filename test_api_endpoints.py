#!/usr/bin/env python3
"""Test different Crusoe API endpoints to isolate authentication issues."""

import os
import requests
import hmac
import hashlib
import base64
import datetime
import json
from dotenv import load_dotenv

def test_crusoe_endpoints():
    """Test various Crusoe API endpoints to see if any work."""
    load_dotenv()
    
    access_key = os.getenv('CRUSOE_ACCESS_KEY_ID')
    secret_key = os.getenv('CRUSOE_SECRET_ACCESS_KEY')
    
    if not access_key or not secret_key:
        print("❌ Missing credentials")
        return
    
    print(f"Testing with Access Key: {access_key}")
    
    # Decode secret key (we know this works from verification)
    secret_padded = secret_key + '=' * (-len(secret_key) % 4)
    decoded_secret = base64.urlsafe_b64decode(secret_padded)
    
    # Test different endpoints with different permission levels
    endpoints_to_test = [
        # Public/basic endpoints
        ('/v1alpha5/locations', 'GET', 'Public locations endpoint'),
        ('/v1alpha5/capacities', 'GET', 'Public capacities endpoint'),
        
        # Organization-specific endpoints (require proper org access)
        ('/v1alpha5/organizations', 'GET', 'Organizations list'),
        ('/v1alpha5/projects', 'GET', 'Projects list'),
        
        # Compute endpoints (might require different permissions)
        ('/v1alpha5/compute/images', 'GET', 'Compute images'),
        ('/v1alpha5/compute/instances', 'GET', 'Compute instances'),
    ]
    
    successful_endpoints = []
    failed_endpoints = []
    
    for endpoint, method, description in endpoints_to_test:
        print(f"\n=== Testing: {description} ===")
        print(f"Endpoint: {method} {endpoint}")
        
        try:
            # Create timestamp
            dt = datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0)
            timestamp = dt.isoformat()
            
            # Create signature payload
            payload = f"{endpoint}\n\n{method}\n{timestamp}\n"
            
            # Generate signature
            signature_bytes = hmac.new(
                decoded_secret,
                payload.encode('ascii'),
                hashlib.sha256
            ).digest()
            
            signature = base64.urlsafe_b64encode(signature_bytes).decode('ascii').rstrip("=")
            auth_value = f"1.0:{access_key}:{signature}"
            
            # Make request
            headers = {
                'X-Crusoe-Timestamp': timestamp,
                'Authorization': f"Bearer {auth_value}",
                'Content-Type': 'application/json'
            }
            
            url = f"https://api.crusoecloud.com{endpoint}"
            response = requests.get(url, headers=headers, timeout=10)
            
            print(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                print(f"✅ SUCCESS!")
                try:
                    data = response.json()
                    print(f"Response preview: {json.dumps(data, indent=2)[:300]}...")
                    successful_endpoints.append((endpoint, description))
                except:
                    print(f"Response: {response.text[:200]}...")
                    successful_endpoints.append((endpoint, description))
            
            elif response.status_code == 401:
                print(f"❌ 401 Unauthorized: {response.text}")
                failed_endpoints.append((endpoint, description, "401 - Unauthorized"))
            
            elif response.status_code == 403:
                print(f"⚠️  403 Forbidden: {response.text}")
                failed_endpoints.append((endpoint, description, "403 - Forbidden (valid auth, no permission)"))
            
            elif response.status_code == 404:
                print(f"⚠️  404 Not Found: {response.text}")
                failed_endpoints.append((endpoint, description, "404 - Not Found"))
            
            else:
                print(f"⚠️  {response.status_code}: {response.text}")
                failed_endpoints.append((endpoint, description, f"{response.status_code} - {response.text[:100]}"))
                
        except Exception as e:
            print(f"❌ Error: {e}")
            failed_endpoints.append((endpoint, description, f"Exception: {e}"))
    
    print(f"\n" + "="*60)
    print(f"SUMMARY")
    print(f"="*60)
    
    if successful_endpoints:
        print(f"✅ Successful endpoints ({len(successful_endpoints)}):")
        for endpoint, desc in successful_endpoints:
            print(f"  - {endpoint}: {desc}")
    else:
        print(f"❌ No successful endpoints")
    
    if failed_endpoints:
        print(f"\n❌ Failed endpoints ({len(failed_endpoints)}):")
        for endpoint, desc, error in failed_endpoints:
            print(f"  - {endpoint}: {desc} - {error}")
    
    print(f"\n🔍 DIAGNOSIS:")
    
    if successful_endpoints:
        print(f"✅ Authentication is working! Your API keys are valid.")
        print(f"   The issue might be endpoint-specific permissions.")
    elif all("401" in error for _, _, error in failed_endpoints):
        print(f"❌ All endpoints return 401 - Authentication is failing.")
        print(f"   Possible issues:")
        print(f"   - API keys are expired or inactive")
        print(f"   - Keys are for wrong organization/environment")
        print(f"   - Account doesn't have API access enabled")
    elif any("403" in error for _, _, error in failed_endpoints):
        print(f"⚠️  Some endpoints return 403 - Authentication works but permissions are limited.")
        print(f"   Your API keys are valid but may have restricted access.")
    else:
        print(f"⚠️  Mixed results - check individual endpoint errors above.")

if __name__ == "__main__":
    test_crusoe_endpoints()
