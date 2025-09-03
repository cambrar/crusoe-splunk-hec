#!/usr/bin/env python3
"""Test the updated implementation with working credentials and organization ID."""

import os
from dotenv import load_dotenv
from config import AppConfig
from crusoe_client import CrusoeClient

def test_working_implementation():
    """Test the updated implementation with working organization-based audit logs."""
    
    print("=== TESTING UPDATED IMPLEMENTATION ===")
    print("Using organization-based audit logs endpoint")
    print("With working credentials and organization ID")
    
    # Load configuration
    try:
        config = AppConfig.from_env()
        print(f"\nConfiguration loaded:")
        print(f"  Base URL: {config.crusoe.base_url}")
        print(f"  Organization ID: {config.crusoe.organization_id}")
        print(f"  Access Key: {config.crusoe.access_key_id}")
        print(f"  Secret Key: {config.crusoe.secret_access_key[:10]}...")
        
        # Create client
        client = CrusoeClient(config.crusoe)
        
        # Test health check
        print(f"\n=== TESTING HEALTH CHECK ===")
        is_healthy = client.health_check()
        print(f"Health check result: {'✅ Healthy' if is_healthy else '❌ Unhealthy'}")
        
        # Test audit logs fetch
        print(f"\n=== TESTING AUDIT LOGS FETCH ===")
        try:
            logs = client.get_audit_logs(limit=5)
            print(f"✅ Successfully fetched {len(logs)} audit logs!")
            
            if logs:
                print(f"\nSample audit log:")
                import json
                print(json.dumps(logs[0], indent=4))
            else:
                print("No audit logs found (empty result)")
                
        except Exception as e:
            print(f"❌ Failed to fetch audit logs: {e}")
        
        # Test paginated fetch
        print(f"\n=== TESTING PAGINATED FETCH ===")
        try:
            all_logs = client.get_audit_logs_paginated(page_size=10, max_pages=2)
            print(f"✅ Successfully fetched {len(all_logs)} audit logs via pagination!")
            
        except Exception as e:
            print(f"❌ Failed to fetch paginated audit logs: {e}")
        
    except Exception as e:
        print(f"❌ Configuration or client error: {e}")
        print("\nMake sure your .env file contains:")
        print("CRUSOE_ACCESS_KEY_ID=n4Cm1VYRTGeipLsQFG1jqg")
        print("CRUSOE_SECRET_ACCESS_KEY=VQSKaxlVqAuB0yD9Sab6lA")
        print("CRUSOE_ORG_ID=c594a031-5041-45ff-a72c-ba127c9884d1")

if __name__ == "__main__":
    test_working_implementation()
