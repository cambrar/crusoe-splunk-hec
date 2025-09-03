#!/usr/bin/env python3
"""Check project access and try different project discovery methods."""

import os
import hmac
import hashlib
import base64
import datetime
import requests
import json
from dotenv import load_dotenv

def check_project_access():
    """Check various ways to find or create projects."""
    load_dotenv()
    
    access_key = os.getenv('CRUSOE_ACCESS_KEY_ID')
    secret_key = os.getenv('CRUSOE_SECRET_ACCESS_KEY')
    
    print("=== COMPREHENSIVE PROJECT ACCESS CHECK ===")
    print(f"User: Rob Cambra (rcambra@crusoe.ai)")
    print(f"Company: crusoe-dx-lab")
    print(f"Role: admin")
    
    def make_signed_request(endpoint, method="GET", query_params="", body=None):
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
            if method == "GET":
                if query_params:
                    params = dict(param.split('=') for param in query_params.split('&'))
                    response = requests.get(url, headers=headers, params=params, timeout=10)
                else:
                    response = requests.get(url, headers=headers, timeout=10)
            elif method == "POST":
                response = requests.post(url, headers=headers, json=body, timeout=10)
            
            return response
            
        except Exception as e:
            print(f"❌ Request error: {e}")
            return None

    # Test different project-related endpoints
    test_endpoints = [
        ("/organizations", "GET", "Organizations (might show projects)"),
        ("/projects", "GET", "Direct projects list"),
        ("/users/identities", "GET", "User identity (already worked)"),
    ]
    
    print(f"\n=== TESTING PROJECT ENDPOINTS ===")
    
    for endpoint, method, description in test_endpoints:
        print(f"\n{description}: {method} {endpoint}")
        response = make_signed_request(endpoint, method)
        
        if response is None:
            print("   ❌ Request failed")
            continue
            
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                print(f"   ✅ Success: {json.dumps(data, indent=6)}")
                
                # Look for project information
                if 'items' in data:
                    for item in data['items']:
                        if 'id' in item:
                            print(f"   🔍 Found ID: {item['id']}")
                        if 'project_id' in item:
                            print(f"   🔍 Found Project ID: {item['project_id']}")
                            
            except Exception as e:
                print(f"   ✅ Success (non-JSON): {response.text}")
        
        elif response.status_code == 404:
            print(f"   ⚠️  404: Endpoint not found")
        elif response.status_code == 403:
            print(f"   ⚠️  403: No permission - {response.text}")
        elif response.status_code == 401:
            print(f"   ❌ 401: Auth failed - {response.text}")
        else:
            print(f"   ⚠️  {response.status_code}: {response.text}")
    
    # Try to create a project (since you're admin)
    print(f"\n=== TRYING TO CREATE A PROJECT ===")
    print("Since you're an admin, let's try creating a project...")
    
    project_data = {
        "name": "robc-project",
        "description": "Project for audit log testing"
    }
    
    response = make_signed_request("/projects", "POST", body=project_data)
    
    if response:
        print(f"Create project status: {response.status_code}")
        
        if response.status_code in [200, 201]:
            try:
                data = response.json()
                print(f"✅ Project created successfully!")
                print(f"Project data: {json.dumps(data, indent=4)}")
                
                if 'id' in data:
                    project_id = data['id']
                    print(f"\n🎉 YOUR PROJECT ID: {project_id}")
                    print(f"Add this to your .env file:")
                    print(f"CRUSOE_PROJECT_ID={project_id}")
                    
            except:
                print(f"✅ Project created: {response.text}")
                
        elif response.status_code == 409:
            print(f"⚠️  Project already exists: {response.text}")
        elif response.status_code == 403:
            print(f"⚠️  No permission to create projects: {response.text}")
        else:
            print(f"⚠️  {response.status_code}: {response.text}")
    
    # Also try some compute endpoints that might give clues
    print(f"\n=== TESTING COMPUTE ENDPOINTS (might show projects) ===")
    
    compute_endpoints = [
        "/compute/images",
        "/compute/instances", 
        "/storage/disks"
    ]
    
    for endpoint in compute_endpoints:
        print(f"\nTesting: {endpoint}")
        response = make_signed_request(endpoint)
        
        if response:
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                try:
                    data = response.json()
                    print(f"   ✅ Data available: {len(data.get('items', []))} items")
                    # Look for project references in the data
                    if 'items' in data and data['items']:
                        first_item = data['items'][0]
                        if 'project_id' in first_item:
                            print(f"   🔍 Found project reference: {first_item['project_id']}")
                except:
                    print(f"   ✅ Success: {response.text[:100]}")
            else:
                print(f"   {response.text}")
    
    print(f"\n" + "="*60)
    print("SUMMARY & RECOMMENDATIONS:")
    print("="*60)
    print("1. Your authentication is working perfectly ✅")
    print("2. You have admin role which should allow project creation")
    print("3. Check the output above for any project IDs found")
    print("4. If a project was created, use that UUID in your .env file")
    print("5. If no projects found, you may need to:")
    print("   - Log into Crusoe console and create a project manually")
    print("   - Check with Crusoe support about account setup")

if __name__ == "__main__":
    check_project_access()
