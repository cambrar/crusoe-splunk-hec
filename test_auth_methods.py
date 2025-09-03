#!/usr/bin/env python3
"""Test different authentication methods for the known audit logs endpoint."""

import os
import requests
import json
import base64
from dotenv import load_dotenv
from botocore.auth import SigV4Auth
from botocore.awsrequest import AWSRequest
from botocore.credentials import Credentials

load_dotenv()

def test_all_auth_methods():
    """Test every possible authentication method for the audit logs endpoint."""
    access_key = os.getenv('CRUSOE_ACCESS_KEY_ID')
    secret_key = os.getenv('CRUSOE_SECRET_ACCESS_KEY')
    org_id = os.getenv('CRUSOE_ORG_ID')
    
    if not all([access_key, secret_key, org_id]):
        print("❌ Missing required credentials")
        return
    
    # The correct endpoint path from OpenAPI analysis
    url = f"https://api.crusoecloud.com/v1alpha5/organizations/{org_id}/audit-logs"
    params = {"limit": 1}  # Small test request
    
    print(f"🎯 Testing endpoint: {url}")
    print(f"📋 Organization ID: {org_id}")
    print(f"🔑 Access Key: {access_key[:8]}...")
    print("=" * 60)
    
    auth_methods = [
        ("AWS SigV4 with 'crusoe' service", lambda: test_aws_sigv4(url, params, access_key, secret_key, "crusoe", "us-east-1")),
        ("AWS SigV4 with 'execute-api' service", lambda: test_aws_sigv4(url, params, access_key, secret_key, "execute-api", "us-east-1")),
        ("AWS SigV4 with 's3' service", lambda: test_aws_sigv4(url, params, access_key, secret_key, "s3", "us-east-1")),
        ("AWS SigV4 with different region us-west-2", lambda: test_aws_sigv4(url, params, access_key, secret_key, "crusoe", "us-west-2")),
        ("Bearer token (access key)", lambda: test_bearer_token(url, params, access_key)),
        ("API Key header", lambda: test_api_key_header(url, params, access_key)),
        ("Basic Auth", lambda: test_basic_auth(url, params, access_key, secret_key)),
        ("Custom headers", lambda: test_custom_headers(url, params, access_key, secret_key)),
    ]
    
    for method_name, test_func in auth_methods:
        print(f"\\n🧪 Testing: {method_name}")
        try:
            result = test_func()
            if result:
                print(f"  ✅ SUCCESS! This method works!")
                return method_name
        except Exception as e:
            print(f"  💥 Exception: {e}")
    
    print("\\n❌ All authentication methods failed")
    return None

def test_aws_sigv4(url, params, access_key, secret_key, service, region):
    """Test AWS SigV4 authentication."""
    credentials = Credentials(access_key=access_key, secret_key=secret_key)
    
    aws_request = AWSRequest(
        method='GET',
        url=url,
        params=params,
        headers={'Content-Type': 'application/json'}
    )
    
    signer = SigV4Auth(credentials, service, region)
    signer.add_auth(aws_request)
    
    response = requests.get(url, params=params, headers=dict(aws_request.headers))
    
    print(f"    Status: {response.status_code}")
    print(f"    Service: {service}, Region: {region}")
    
    if response.status_code == 200:
        print(f"    Response: {response.text[:200]}...")
        return True
    elif response.status_code == 401:
        try:
            error_data = response.json()
            print(f"    Error: {error_data.get('message', 'Authentication failed')}")
        except:
            print(f"    Error: {response.text[:100]}...")
    elif response.status_code == 403:
        print(f"    Forbidden: Check permissions")
    else:
        print(f"    Unexpected status: {response.text[:100]}...")
    
    return False

def test_bearer_token(url, params, access_key):
    """Test Bearer token authentication."""
    headers = {
        'Authorization': f'Bearer {access_key}',
        'Content-Type': 'application/json'
    }
    
    response = requests.get(url, params=params, headers=headers)
    print(f"    Status: {response.status_code}")
    
    if response.status_code == 200:
        print(f"    Response: {response.text[:200]}...")
        return True
    else:
        try:
            error_data = response.json()
            print(f"    Error: {error_data.get('message', 'Failed')}")
        except:
            print(f"    Error: {response.text[:100]}...")
    
    return False

def test_api_key_header(url, params, access_key):
    """Test API key in various header formats."""
    header_formats = [
        {'X-API-Key': access_key},
        {'X-API-Token': access_key},
        {'API-Key': access_key},
        {'Authorization': f'API-Key {access_key}'},
        {'Authorization': f'Token {access_key}'},
    ]
    
    for headers in header_formats:
        response = requests.get(url, params=params, headers=headers)
        if response.status_code == 200:
            print(f"    ✅ Success with headers: {list(headers.keys())}")
            print(f"    Response: {response.text[:200]}...")
            return True
    
    print(f"    Status: 401 (tried {len(header_formats)} header formats)")
    return False

def test_basic_auth(url, params, access_key, secret_key):
    """Test HTTP Basic authentication."""
    auth = (access_key, secret_key)
    response = requests.get(url, params=params, auth=auth)
    
    print(f"    Status: {response.status_code}")
    
    if response.status_code == 200:
        print(f"    Response: {response.text[:200]}...")
        return True
    else:
        try:
            error_data = response.json()
            print(f"    Error: {error_data.get('message', 'Failed')}")
        except:
            print(f"    Error: {response.text[:100]}...")
    
    return False

def test_custom_headers(url, params, access_key, secret_key):
    """Test custom header combinations."""
    header_combinations = [
        {'X-Access-Key': access_key, 'X-Secret-Key': secret_key},
        {'Access-Key-Id': access_key, 'Secret-Access-Key': secret_key},
        {'Crusoe-Access-Key': access_key, 'Crusoe-Secret-Key': secret_key},
        {'Authorization': f'{access_key}:{secret_key}'},
        {'Authorization': f'Crusoe {access_key}:{secret_key}'},
    ]
    
    for headers in header_combinations:
        response = requests.get(url, params=params, headers=headers)
        if response.status_code == 200:
            print(f"    ✅ Success with custom headers: {list(headers.keys())}")
            print(f"    Response: {response.text[:200]}...")
            return True
    
    print(f"    Status: 401 (tried {len(header_combinations)} custom formats)")
    return False

def check_organization_id():
    """Check if we can find the correct organization ID."""
    print("\\n" + "=" * 60)
    print("🏢 Checking Organization ID")
    print("=" * 60)
    
    access_key = os.getenv('CRUSOE_ACCESS_KEY_ID')
    secret_key = os.getenv('CRUSOE_SECRET_ACCESS_KEY')
    
    # Try to get organizations list with bearer token (simplest method)
    headers = {'Authorization': f'Bearer {access_key}', 'Content-Type': 'application/json'}
    
    endpoints_to_try = [
        "https://api.crusoecloud.com/v1alpha5/organizations/entities",
        "https://api.crusoecloud.com/v1alpha5/organizations/projects",
        "https://api.crusoecloud.com/v1alpha5/users/identities",
    ]
    
    for endpoint in endpoints_to_try:
        print(f"\\n🧪 Trying: {endpoint}")
        response = requests.get(endpoint, headers=headers)
        print(f"  Status: {response.status_code}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                print(f"  ✅ Success! Data structure:")
                if isinstance(data, list) and data:
                    print(f"    📋 Found {len(data)} items")
                    for i, item in enumerate(data[:3]):
                        if isinstance(item, dict):
                            # Look for ID fields
                            id_fields = {k: v for k, v in item.items() if 'id' in k.lower()}
                            print(f"    {i+1}. ID fields: {id_fields}")
                elif isinstance(data, dict):
                    id_fields = {k: v for k, v in data.items() if 'id' in k.lower()}
                    print(f"    📌 ID fields: {id_fields}")
                
                print(f"    📄 Raw response: {json.dumps(data, indent=2)[:400]}...")
                
            except Exception as e:
                print(f"    📄 Raw response: {response.text[:300]}...")
        else:
            try:
                error_data = response.json()
                print(f"    ❌ Error: {error_data.get('message', 'Failed')}")
            except:
                print(f"    ❌ Error: {response.text[:100]}...")

def main():
    """Run comprehensive authentication testing."""
    print("Crusoe Authentication Method Testing")
    print("=" * 60)
    
    # Test all authentication methods
    working_method = test_all_auth_methods()
    
    if working_method:
        print(f"\\n🎉 Found working authentication method: {working_method}")
    else:
        print("\\n😔 No working authentication method found")
        
        # Check if we can find the correct organization ID
        check_organization_id()
        
        print("\\n💡 Next steps:")
        print("1. Verify your access key and secret key are exactly correct")
        print("2. Check if your keys have audit log permissions in Crusoe console")
        print("3. Try a different organization ID format")
        print("4. Contact Crusoe support with these test results")

if __name__ == "__main__":
    main()
