#!/usr/bin/env python3
"""Find the correct project ID for your Crusoe account."""

import os
import hmac
import hashlib
import base64
import datetime
import requests
import json
from dotenv import load_dotenv

def find_project_id():
    """Find available projects and their correct IDs."""
    load_dotenv()
    
    access_key = os.getenv('CRUSOE_ACCESS_KEY_ID')
    secret_key = os.getenv('CRUSOE_SECRET_ACCESS_KEY')
    
    if not access_key or not secret_key:
        print("❌ Missing credentials")
        return
    
    print("=== FINDING YOUR CORRECT PROJECT ID ===")
    print(f"Access Key: {access_key}")
    
    # Create signature helper function
    def make_signed_request(endpoint, query_params=""):
        api_version = "/v1alpha5"
        request_verb = "GET"
        
        dt = str(datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0))
        dt = dt.replace(" ", "T")
        
        payload = api_version + endpoint + "\n" + query_params + "\n" + request_verb + "\n{0}\n".format(dt)
        
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
                # Parse query params for requests
                params = dict(param.split('=') for param in query_params.split('&'))
                response = requests.get(url, headers=headers, params=params, timeout=10)
            else:
                response = requests.get(url, headers=headers, timeout=10)
            
            return response
            
        except Exception as e:
            print(f"❌ Request error: {e}")
            return None

    # Try to find projects using different approaches
    print("\n=== TRYING TO FIND PROJECTS ===")
    
    # Approach 1: Try organizations endpoint (might list projects)
    print("\n1. Testing organizations endpoint...")
    response = make_signed_request("/organizations")
    if response:
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            try:
                data = response.json()
                print(f"   ✅ Organizations: {json.dumps(data, indent=4)}")
            except:
                print(f"   ✅ Response: {response.text}")
        else:
            print(f"   Response: {response.text}")
    
    # Approach 2: Try to list projects directly
    print("\n2. Testing projects list endpoint...")
    response = make_signed_request("/projects")
    if response:
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            try:
                data = response.json()
                print(f"   ✅ Projects: {json.dumps(data, indent=4)}")
                
                # Extract project IDs if available
                if 'items' in data:
                    for project in data['items']:
                        if 'id' in project:
                            print(f"   📝 Found Project ID: {project['id']}")
                        if 'name' in project:
                            print(f"      Project Name: {project['name']}")
                            
            except:
                print(f"   ✅ Response: {response.text}")
        else:
            print(f"   Response: {response.text}")
    
    # Approach 3: Try user identity endpoint (might show associated projects)
    print("\n3. Testing user identity endpoint...")
    response = make_signed_request("/users/identities")
    if response:
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            try:
                data = response.json()
                print(f"   ✅ User info: {json.dumps(data, indent=4)}")
            except:
                print(f"   ✅ Response: {response.text}")
        else:
            print(f"   Response: {response.text}")
    
    # Approach 4: Check what public endpoints work to confirm auth
    print("\n4. Testing public endpoints...")
    
    public_endpoints = [
        ("/locations", "Locations"),
        ("/capacities", "Capacities"),
    ]
    
    for endpoint, name in public_endpoints:
        print(f"\n   Testing {name}: {endpoint}")
        response = make_signed_request(endpoint)
        if response:
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                print(f"   ✅ {name} endpoint works - authentication confirmed!")
                try:
                    data = response.json()
                    if 'items' in data and len(data['items']) > 0:
                        print(f"   Sample data: {data['items'][0]}")
                except:
                    pass
            else:
                print(f"   {response.text[:100]}")
    
    print(f"\n" + "="*60)
    print("NEXT STEPS:")
    print("="*60)
    print("1. If you see project IDs above, use one of those UUIDs")
    print("2. If no projects found, you may need to:")
    print("   - Create a project in the Crusoe console first")
    print("   - Check if your account has access to existing projects")
    print("   - Verify you're using the right organization/account")
    print("3. Project IDs should be UUIDs like: ab4a6b00-aa5f-408e-a9fb-ac6de5eb45ab")

if __name__ == "__main__":
    find_project_id()
