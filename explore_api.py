#!/usr/bin/env python3
"""Explore Crusoe API structure and find correct endpoints."""

import os
import requests
import json
from dotenv import load_dotenv
from botocore.auth import SigV4Auth
from botocore.awsrequest import AWSRequest
from botocore.credentials import Credentials

load_dotenv()

def test_base_endpoints():
    """Test what the base API returns."""
    print("=== Base API Responses ===")
    
    base_urls = [
        "https://api.crusoecloud.com/v1alpha5",
        "https://api.crusoecloud.com",
    ]
    
    for base_url in base_urls:
        print(f"\\nTesting: {base_url}")
        try:
            response = requests.get(base_url)
            print(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                print("Response content:")
                # Try to parse as JSON
                try:
                    data = response.json()
                    print(json.dumps(data, indent=2)[:500] + "...")
                except:
                    # If not JSON, show raw text
                    print(response.text[:500] + "...")
        except Exception as e:
            print(f"Error: {e}")

def test_with_proper_auth():
    """Test endpoints with proper AWS SigV4 auth but try different paths."""
    print("\\n=== Testing with AWS SigV4 Auth ===")
    
    access_key = os.getenv('CRUSOE_ACCESS_KEY_ID')
    secret_key = os.getenv('CRUSOE_SECRET_ACCESS_KEY')
    org_id = os.getenv('CRUSOE_ORG_ID')
    
    if not access_key or not secret_key:
        print("❌ No credentials available")
        return
    
    # Different endpoint patterns to try
    endpoints_to_try = [
        "/organizations",
        f"/organization/{org_id}",
        f"/organization/{org_id}/audit-logs",
        f"/organizations/{org_id}",
        f"/organizations/{org_id}/audit-logs",
        f"/projects",
        f"/user/organizations",
        f"/v1/organizations",
        f"/api/v1/organizations",
        "/audit-logs",
        f"/audit-logs?organization={org_id}",
    ]
    
    base_url = "https://api.crusoecloud.com/v1alpha5"
    
    for endpoint in endpoints_to_try:
        url = f"{base_url}{endpoint}"
        print(f"\\nTrying: {endpoint}")
        
        try:
            # Create AWS credentials
            credentials = Credentials(
                access_key=access_key,
                secret_key=secret_key
            )
            
            # Create signed request
            aws_request = AWSRequest(
                method='GET',
                url=url,
                headers={'Content-Type': 'application/json'}
            )
            
            signer = SigV4Auth(credentials, "crusoe", "us-east-1")
            signer.add_auth(aws_request)
            
            response = requests.get(url, headers=dict(aws_request.headers))
            print(f"  Status: {response.status_code}")
            
            if response.status_code == 200:
                print(f"  ✅ SUCCESS!")
                try:
                    data = response.json()
                    print(f"  Response: {json.dumps(data, indent=2)[:300]}...")
                except:
                    print(f"  Response: {response.text[:300]}...")
                return endpoint
            elif response.status_code != 404 and response.status_code != 401:
                print(f"  Response: {response.text[:200]}...")
                
        except Exception as e:
            print(f"  Error: {e}")
    
    return None

def check_openapi_spec():
    """Check if there's an OpenAPI/Swagger spec available."""
    print("\\n=== Checking for API Documentation ===")
    
    doc_endpoints = [
        "https://api.crusoecloud.com/v1alpha5/swagger.json",
        "https://api.crusoecloud.com/v1alpha5/openapi.json",
        "https://api.crusoecloud.com/v1alpha5/docs",
        "https://api.crusoecloud.com/v1alpha5/swagger",
        "https://api.crusoecloud.com/swagger.json",
        "https://api.crusoecloud.com/openapi.json",
        "https://api.crusoecloud.com/docs",
        "https://docs.crusoecloud.com/api.json",
        "https://docs.crusoecloud.com/openapi.json",
    ]
    
    for endpoint in doc_endpoints:
        print(f"\\nTrying: {endpoint}")
        try:
            response = requests.get(endpoint)
            if response.status_code == 200:
                print(f"  ✅ Found API docs!")
                try:
                    data = response.json()
                    # Look for paths in OpenAPI spec
                    if 'paths' in data:
                        print("  Available paths:")
                        for path in list(data['paths'].keys())[:10]:
                            print(f"    {path}")
                    else:
                        print(f"  Content: {response.text[:300]}...")
                except:
                    print(f"  Content: {response.text[:300]}...")
                return True
        except Exception as e:
            pass
    
    return False

def test_different_regions():
    """Test different regions in case that matters."""
    print("\\n=== Testing Different Regions ===")
    
    access_key = os.getenv('CRUSOE_ACCESS_KEY_ID')
    secret_key = os.getenv('CRUSOE_SECRET_ACCESS_KEY')
    org_id = os.getenv('CRUSOE_ORG_ID')
    
    if not access_key or not secret_key:
        return
    
    regions = ["us-east-1", "us-west-2", "eu-west-1", "ap-southeast-1"]
    url = f"https://api.crusoecloud.com/v1alpha5/organizations/{org_id}/audit-logs"
    
    for region in regions:
        print(f"\\nTrying region: {region}")
        
        try:
            credentials = Credentials(
                access_key=access_key,
                secret_key=secret_key
            )
            
            aws_request = AWSRequest(
                method='GET',
                url=url,
                headers={'Content-Type': 'application/json'}
            )
            
            signer = SigV4Auth(credentials, "crusoe", region)
            signer.add_auth(aws_request)
            
            response = requests.get(url, headers=dict(aws_request.headers))
            print(f"  Status: {response.status_code}")
            
            if response.status_code == 200:
                print(f"  ✅ SUCCESS with region: {region}")
                return region
            elif response.status_code != 401 and response.status_code != 404:
                try:
                    error_data = response.json()
                    print(f"  Response: {error_data}")
                except:
                    print(f"  Response: {response.text[:200]}...")
                    
        except Exception as e:
            print(f"  Error: {e}")
    
    return None

def main():
    """Run API exploration."""
    print("Crusoe API Exploration")
    print("=" * 40)
    
    # Check what the base API returns
    test_base_endpoints()
    
    # Check for API documentation
    if check_openapi_spec():
        print("\\n✅ Found API documentation - check the output above for available paths")
        return
    
    # Try different endpoints with authentication
    working_endpoint = test_with_proper_auth()
    if working_endpoint:
        print(f"\\n✅ Found working endpoint: {working_endpoint}")
        return
    
    # Try different regions
    working_region = test_different_regions()
    if working_region:
        print(f"\\n✅ Found working region: {working_region}")
        return
    
    print("\\n❌ Could not find working authentication or endpoints")
    print("\\nRecommendations:")
    print("1. Check Crusoe documentation for exact API endpoints")
    print("2. Verify organization ID is correct")
    print("3. Check if audit logs feature is enabled for your account")
    print("4. Contact Crusoe support with your findings")

if __name__ == "__main__":
    main()
