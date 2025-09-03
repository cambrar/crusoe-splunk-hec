#!/usr/bin/env python3
"""Test API token authentication and find correct organization ID."""

import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

def test_token_on_simple_endpoints():
    """Test the token on endpoints that should work."""
    token = os.getenv('CRUSOE_API_TOKEN')
    
    if not token:
        print("❌ No API token found")
        return
    
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    print(f"🔑 Testing token: {token[:8]}...")
    print("=" * 50)
    
    # Test endpoints that should work with basic permissions
    test_endpoints = [
        ("User Identity", "https://api.crusoecloud.com/v1alpha5/users/identities"),
        ("Organizations", "https://api.crusoecloud.com/v1alpha5/organizations/entities"),
        ("Projects", "https://api.crusoecloud.com/v1alpha5/organizations/projects"),
        ("Locations", "https://api.crusoecloud.com/v1alpha5/locations"),
    ]
    
    working_endpoints = []
    
    for name, url in test_endpoints:
        print(f"\\n🧪 Testing {name}: {url}")
        
        try:
            response = requests.get(url, headers=headers, timeout=10)
            print(f"  Status: {response.status_code}")
            
            if response.status_code == 200:
                print(f"  ✅ SUCCESS!")
                try:
                    data = response.json()
                    print(f"  📊 Data type: {type(data)}")
                    
                    if isinstance(data, list):
                        print(f"  📋 Found {len(data)} items")
                        if data and len(data) > 0:
                            print(f"  📄 First item keys: {list(data[0].keys()) if isinstance(data[0], dict) else 'Not a dict'}")
                            # Look for organization info
                            for item in data[:3]:
                                if isinstance(item, dict):
                                    org_fields = {k: v for k, v in item.items() if any(keyword in k.lower() for keyword in ['id', 'name', 'org'])}
                                    if org_fields:
                                        print(f"    🏢 Org info: {org_fields}")
                    elif isinstance(data, dict):
                        print(f"  📄 Dict keys: {list(data.keys())}")
                        org_fields = {k: v for k, v in data.items() if any(keyword in k.lower() for keyword in ['id', 'name', 'org'])}
                        if org_fields:
                            print(f"    🏢 Org info: {org_fields}")
                    
                    # Show a preview of the response
                    print(f"  📄 Response preview: {json.dumps(data, indent=2)[:300]}...")
                    working_endpoints.append((name, url, data))
                    
                except Exception as e:
                    print(f"  📄 Response text: {response.text[:200]}...")
                    working_endpoints.append((name, url, response.text))
                    
            elif response.status_code == 401:
                try:
                    error_data = response.json()
                    print(f"  ❌ Unauthorized: {error_data.get('message', 'Authentication failed')}")
                except:
                    print(f"  ❌ Unauthorized: {response.text[:100]}...")
                    
            elif response.status_code == 403:
                print(f"  🚫 Forbidden: Insufficient permissions")
                try:
                    error_data = response.json()
                    print(f"    Details: {error_data.get('message', 'No details')}")
                except:
                    pass
                    
            else:
                print(f"  ⚠️  Unexpected status: {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"    Error: {error_data}")
                except:
                    print(f"    Response: {response.text[:200]}...")
                    
        except Exception as e:
            print(f"  💥 Exception: {e}")
    
    return working_endpoints

def test_audit_logs_with_different_org_ids(working_endpoints):
    """If we have working endpoints, try to find the correct org ID format."""
    token = os.getenv('CRUSOE_API_TOKEN')
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    print("\\n" + "=" * 50)
    print("🔍 Looking for correct organization ID")
    print("=" * 50)
    
    # Extract potential org IDs from working endpoints
    potential_org_ids = ['robc']  # Start with the current one
    
    for name, url, data in working_endpoints:
        if isinstance(data, list):
            for item in data:
                if isinstance(item, dict):
                    for key, value in item.items():
                        if 'id' in key.lower() and isinstance(value, str):
                            if value not in potential_org_ids:
                                potential_org_ids.append(value)
                                print(f"  📋 Found potential ID from {name}: {value}")
        elif isinstance(data, dict):
            for key, value in data.items():
                if 'id' in key.lower() and isinstance(value, str):
                    if value not in potential_org_ids:
                        potential_org_ids.append(value)
                        print(f"  📋 Found potential ID from {name}: {value}")
    
    print(f"\\n🧪 Testing audit logs with {len(potential_org_ids)} potential org IDs...")
    
    for org_id in potential_org_ids:
        print(f"\\n  Testing org ID: {org_id}")
        audit_url = f"https://api.crusoecloud.com/v1alpha5/organizations/{org_id}/audit-logs"
        
        try:
            response = requests.get(audit_url, headers=headers, params={'limit': 1}, timeout=10)
            print(f"    Status: {response.status_code}")
            
            if response.status_code == 200:
                print(f"    ✅ SUCCESS! Correct org ID: {org_id}")
                try:
                    data = response.json()
                    print(f"    📊 Response: {json.dumps(data, indent=2)[:300]}...")
                except:
                    print(f"    📄 Response: {response.text[:200]}...")
                return org_id
            elif response.status_code == 401:
                print(f"    ❌ Still unauthorized")
            elif response.status_code == 403:
                print(f"    🚫 Forbidden (org exists but no audit permissions)")
            elif response.status_code == 404:
                print(f"    📭 Not found (wrong org ID)")
            else:
                try:
                    error_data = response.json()
                    print(f"    ⚠️  {response.status_code}: {error_data}")
                except:
                    print(f"    ⚠️  {response.status_code}: {response.text[:100]}...")
                    
        except Exception as e:
            print(f"    💥 Exception: {e}")
    
    return None

def main():
    """Test token authentication and find issues."""
    print("Crusoe API Token Authentication Test")
    print("=" * 50)
    
    # Test basic endpoints first
    working_endpoints = test_token_on_simple_endpoints()
    
    if not working_endpoints:
        print("\\n❌ No endpoints worked - token might be invalid or expired")
        print("\\nCheck in Crusoe console:")
        print("  1. Is the token active/not expired?")
        print("  2. Does the token have the right permissions?")
        print("  3. Are there any IP restrictions?")
        return
    
    print(f"\\n✅ {len(working_endpoints)} endpoints worked - token is valid!")
    
    # Try to find the correct org ID for audit logs
    correct_org_id = test_audit_logs_with_different_org_ids(working_endpoints)
    
    if correct_org_id:
        print(f"\\n🎉 Found working audit logs with org ID: {correct_org_id}")
        if correct_org_id != os.getenv('CRUSOE_ORG_ID'):
            print(f"\\n💡 Update your .env file:")
            print(f"   CRUSOE_ORG_ID={correct_org_id}")
    else:
        print("\\n❌ Audit logs still not accessible")
        print("\\nPossible issues:")
        print("  1. Audit logs feature not enabled for your organization")
        print("  2. Token doesn't have audit log permissions")
        print("  3. You're not a member of the organization")
        print("  4. Audit logs require a different endpoint or format")

if __name__ == "__main__":
    main()
