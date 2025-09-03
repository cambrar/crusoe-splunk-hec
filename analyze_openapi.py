#!/usr/bin/env python3
"""Download and analyze Crusoe OpenAPI specification to find audit logs endpoint."""

import requests
import json
import os
from dotenv import load_dotenv

load_dotenv()

def download_and_analyze_openapi():
    """Download the OpenAPI spec and find audit-related endpoints."""
    print("=== Analyzing Crusoe OpenAPI Specification ===")
    
    try:
        # Download the OpenAPI spec
        response = requests.get("https://api.crusoecloud.com/v1alpha5/openapi.json")
        if response.status_code != 200:
            print(f"❌ Failed to download OpenAPI spec: {response.status_code}")
            return
        
        spec = response.json()
        print("✅ Successfully downloaded OpenAPI specification")
        
        # Extract all paths
        paths = spec.get('paths', {})
        print(f"📊 Total endpoints found: {len(paths)}")
        
        # Look for audit-related endpoints
        print("\\n🔍 Looking for audit-related endpoints...")
        audit_paths = []
        
        for path, methods in paths.items():
            if 'audit' in path.lower():
                audit_paths.append(path)
                print(f"  ✅ Found: {path}")
                
                # Show available methods for this path
                for method, details in methods.items():
                    if method in ['get', 'post', 'put', 'delete', 'patch']:
                        summary = details.get('summary', 'No description')
                        print(f"    {method.upper()}: {summary}")
        
        if not audit_paths:
            print("  ❌ No audit-related endpoints found")
            
            # Look for organization-related endpoints
            print("\\n🏢 Looking for organization-related endpoints...")
            org_paths = []
            
            for path in paths.keys():
                if 'organization' in path.lower():
                    org_paths.append(path)
                    print(f"  📋 Found: {path}")
            
            # Look for any paths that might contain logs
            print("\\n📝 Looking for log-related endpoints...")
            log_paths = []
            
            for path in paths.keys():
                if any(keyword in path.lower() for keyword in ['log', 'event', 'activity', 'history']):
                    log_paths.append(path)
                    print(f"  📜 Found: {path}")
            
            if not org_paths and not log_paths:
                print("\\n📋 All available endpoints:")
                for i, path in enumerate(sorted(paths.keys())):
                    print(f"  {i+1:2d}. {path}")
                    if i >= 50:  # Limit output
                        print(f"  ... and {len(paths) - 51} more")
                        break
        
        # Check if audit logs might be under a different structure
        print("\\n🔍 Checking endpoint details for audit log clues...")
        
        for path, methods in paths.items():
            for method, details in methods.items():
                if method in ['get', 'post', 'put', 'delete', 'patch']:
                    summary = details.get('summary', '').lower()
                    description = details.get('description', '').lower()
                    
                    if any(keyword in summary + description for keyword in ['audit', 'log', 'activity', 'event']):
                        print(f"  💡 {path} ({method.upper()}): {details.get('summary', 'No summary')}")
        
        # Check if there are parameters that might indicate organization-specific endpoints
        print("\\n🏗️ Checking for organization parameters...")
        
        for path, methods in paths.items():
            if '{' in path:  # Path has parameters
                for method, details in methods.items():
                    if method in ['get', 'post', 'put', 'delete', 'patch']:
                        params = details.get('parameters', [])
                        for param in params:
                            param_name = param.get('name', '').lower()
                            if 'org' in param_name or 'organization' in param_name:
                                print(f"  🎯 {path} ({method.upper()}) has org parameter: {param.get('name')}")
        
        return audit_paths
        
    except Exception as e:
        print(f"❌ Error analyzing OpenAPI spec: {e}")
        return []

def test_discovered_endpoints():
    """Test any discovered audit endpoints with proper authentication."""
    print("\\n=== Testing Discovered Endpoints ===")
    
    access_key = os.getenv('CRUSOE_ACCESS_KEY_ID')
    secret_key = os.getenv('CRUSOE_SECRET_ACCESS_KEY')
    org_id = os.getenv('CRUSOE_ORG_ID')
    
    if not access_key or not secret_key:
        print("❌ No credentials available for testing")
        return
    
    # Test some common patterns based on what we know
    test_endpoints = [
        f"/organizations/entities",
        f"/organizations/projects", 
        f"/organizations/entities/{org_id}",
        f"/organizations/projects/{org_id}",
    ]
    
    from botocore.auth import SigV4Auth
    from botocore.awsrequest import AWSRequest
    from botocore.credentials import Credentials
    
    base_url = "https://api.crusoecloud.com/v1alpha5"
    
    for endpoint in test_endpoints:
        url = f"{base_url}{endpoint}"
        print(f"\\n🧪 Testing: {endpoint}")
        
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
            
            signer = SigV4Auth(credentials, "crusoe", "us-east-1")
            signer.add_auth(aws_request)
            
            response = requests.get(url, headers=dict(aws_request.headers))
            print(f"  Status: {response.status_code}")
            
            if response.status_code == 200:
                print(f"  ✅ SUCCESS!")
                try:
                    data = response.json()
                    print(f"  📊 Response preview: {json.dumps(data, indent=2)[:400]}...")
                    
                    # Look for organization info that might help us find the right org ID
                    if isinstance(data, list):
                        print(f"  📋 Found {len(data)} items")
                        for item in data[:3]:  # Show first 3 items
                            if isinstance(item, dict):
                                org_info = {}
                                for key, value in item.items():
                                    if any(keyword in key.lower() for keyword in ['id', 'name', 'org']):
                                        org_info[key] = value
                                if org_info:
                                    print(f"    📌 Item: {org_info}")
                    elif isinstance(data, dict):
                        # Look for organization-related fields
                        org_fields = {}
                        for key, value in data.items():
                            if any(keyword in key.lower() for keyword in ['id', 'name', 'org']):
                                org_fields[key] = value
                        if org_fields:
                            print(f"    📌 Org fields: {org_fields}")
                            
                except Exception as e:
                    print(f"  📄 Raw response: {response.text[:300]}...")
            elif response.status_code == 401:
                print(f"  🔐 Authentication failed")
            elif response.status_code == 403:
                print(f"  🚫 Access forbidden - check permissions")
            elif response.status_code == 404:
                print(f"  📭 Endpoint not found")
            else:
                try:
                    error_data = response.json()
                    print(f"  ❌ Error: {error_data}")
                except:
                    print(f"  ❌ Error response: {response.text[:200]}...")
                    
        except Exception as e:
            print(f"  💥 Exception: {e}")

def main():
    """Run OpenAPI analysis."""
    print("Crusoe OpenAPI Analysis")
    print("=" * 40)
    
    # Download and analyze the OpenAPI spec
    audit_paths = download_and_analyze_openapi()
    
    # Test discovered endpoints
    test_discovered_endpoints()
    
    print("\\n" + "=" * 40)
    print("📋 Summary:")
    if audit_paths:
        print(f"✅ Found {len(audit_paths)} audit-related endpoints")
        for path in audit_paths:
            print(f"  - {path}")
    else:
        print("❌ No direct audit endpoints found")
        print("💡 Next steps:")
        print("  1. Check if audit logs are under projects instead of organizations")
        print("  2. Look for audit logs in organization/project details")
        print("  3. Check if audit feature needs to be enabled")
        print("  4. Contact Crusoe support for audit logs API guidance")

if __name__ == "__main__":
    main()
