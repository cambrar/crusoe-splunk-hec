#!/usr/bin/env python3
"""Debug script to test Crusoe API authentication methods."""

import os
import requests
from dotenv import load_dotenv
from botocore.auth import SigV4Auth
from botocore.awsrequest import AWSRequest
from botocore.credentials import Credentials
import json

# Load environment variables
load_dotenv()

def test_basic_auth():
    """Test if we can access any basic endpoint first."""
    access_key = os.getenv('CRUSOE_ACCESS_KEY_ID')
    secret_key = os.getenv('CRUSOE_SECRET_ACCESS_KEY')
    org_id = os.getenv('CRUSOE_ORG_ID')
    
    print("=== Testing Basic Authentication ===")
    print(f"Access Key: {'SET' if access_key else 'NOT SET'}")
    print(f"Secret Key: {'SET' if secret_key else 'NOT SET'}")
    print(f"Org ID: {org_id}")
    
    if not access_key or not secret_key:
        print("❌ Access key or secret key not set!")
        return False
    
    return True

def test_organizations_endpoint():
    """Test the organizations endpoint to see if basic auth works."""
    access_key = os.getenv('CRUSOE_ACCESS_KEY_ID')
    secret_key = os.getenv('CRUSOE_SECRET_ACCESS_KEY')
    base_url = os.getenv('CRUSOE_BASE_URL', 'https://api.crusoecloud.com/v1alpha5')
    
    print("\\n=== Testing Organizations Endpoint ===")
    
    # Test simple GET to organizations
    url = f"{base_url}/organizations"
    
    try:
        # Create AWS credentials
        credentials = Credentials(
            access_key=access_key,
            secret_key=secret_key
        )
        
        # Create AWS request
        aws_request = AWSRequest(
            method='GET',
            url=url,
            headers={'Content-Type': 'application/json'}
        )
        
        # Sign the request
        signer = SigV4Auth(credentials, "crusoe", "us-east-1")
        signer.add_auth(aws_request)
        
        # Make the request
        response = requests.get(url, headers=dict(aws_request.headers))
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text[:500]}...")
        
        if response.status_code == 200:
            print("✅ Organizations endpoint works!")
            return True
        else:
            print(f"❌ Organizations endpoint failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Exception: {str(e)}")
        return False

def test_different_service_names():
    """Test different service names for AWS signature."""
    access_key = os.getenv('CRUSOE_ACCESS_KEY_ID')
    secret_key = os.getenv('CRUSOE_SECRET_ACCESS_KEY')
    org_id = os.getenv('CRUSOE_ORG_ID')
    base_url = os.getenv('CRUSOE_BASE_URL', 'https://api.crusoecloud.com/v1alpha5')
    
    print("\\n=== Testing Different Service Names ===")
    
    url = f"{base_url}/organizations/{org_id}/audit-logs"
    params = {'limit': 1}
    
    service_names = ['crusoe', 'execute-api', 'ec2', 's3']
    
    for service_name in service_names:
        print(f"\\nTrying service name: {service_name}")
        
        try:
            credentials = Credentials(
                access_key=access_key,
                secret_key=secret_key
            )
            
            aws_request = AWSRequest(
                method='GET',
                url=url,
                params=params,
                headers={'Content-Type': 'application/json'}
            )
            
            signer = SigV4Auth(credentials, service_name, "us-east-1")
            signer.add_auth(aws_request)
            
            response = requests.get(url, params=params, headers=dict(aws_request.headers))
            
            print(f"  Status: {response.status_code}")
            if response.status_code != 401:
                print(f"  Response: {response.text[:200]}...")
                if response.status_code == 200:
                    print(f"  ✅ Success with service name: {service_name}")
                    return service_name
            else:
                error_data = response.json() if response.text else {}
                print(f"  ❌ 401 Unauthorized: {error_data.get('message', 'No message')}")
                
        except Exception as e:
            print(f"  ❌ Exception: {str(e)}")
    
    return None

def test_bearer_token_format():
    """Test if the API expects a different token format."""
    access_key = os.getenv('CRUSOE_ACCESS_KEY_ID')
    secret_key = os.getenv('CRUSOE_SECRET_ACCESS_KEY')
    org_id = os.getenv('CRUSOE_ORG_ID')
    base_url = os.getenv('CRUSOE_BASE_URL', 'https://api.crusoecloud.com/v1alpha5')
    
    print("\\n=== Testing Bearer Token Format ===")
    
    url = f"{base_url}/organizations/{org_id}/audit-logs"
    params = {'limit': 1}
    
    # Try using access key as bearer token
    headers = {
        'Authorization': f'Bearer {access_key}',
        'Content-Type': 'application/json'
    }
    
    try:
        response = requests.get(url, params=params, headers=headers)
        print(f"Bearer token test - Status: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ Bearer token format works!")
            return True
        else:
            error_data = response.json() if response.text else {}
            print(f"❌ Bearer token failed: {error_data.get('message', 'No message')}")
            
    except Exception as e:
        print(f"❌ Exception: {str(e)}")
    
    return False

def main():
    """Run all authentication tests."""
    print("Crusoe API Authentication Debug")
    print("=" * 40)
    
    if not test_basic_auth():
        return
    
    # Test different approaches
    if test_organizations_endpoint():
        print("\\n✅ Basic AWS SigV4 authentication works!")
    else:
        print("\\n❌ Basic AWS SigV4 authentication failed")
        
        # Try different service names
        working_service = test_different_service_names()
        if working_service:
            print(f"\\n✅ Found working service name: {working_service}")
        else:
            print("\\n❌ No working service name found")
            
            # Try bearer token format
            if test_bearer_token_format():
                print("\\n✅ Bearer token format works!")
            else:
                print("\\n❌ All authentication methods failed")
                print("\\nSuggestions:")
                print("1. Verify your access key and secret key are correct")
                print("2. Check if your keys have the right permissions")
                print("3. Contact Crusoe support for authentication details")

if __name__ == "__main__":
    main()
