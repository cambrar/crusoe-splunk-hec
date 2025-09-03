#!/usr/bin/env python3
"""Check environment variable loading."""

import os
from dotenv import load_dotenv
from config import CrusoeConfig

def check_env_loading():
    """Check if environment variables are loading correctly."""
    
    print("=== ENVIRONMENT VARIABLE CHECK ===")
    
    # Load .env file
    load_dotenv()
    
    # Check raw environment variables
    print("Raw environment variables:")
    env_vars = [
        'CRUSOE_ACCESS_KEY_ID',
        'CRUSOE_SECRET_ACCESS_KEY', 
        'CRUSOE_ORG_ID',
        'CRUSOE_PROJECT_ID',
        'CRUSOE_BASE_URL'
    ]
    
    for var in env_vars:
        value = os.getenv(var)
        if value:
            if 'SECRET' in var:
                print(f"  {var}: {value[:10]}...")
            else:
                print(f"  {var}: {value}")
        else:
            print(f"  {var}: ❌ NOT SET")
    
    print(f"\n=== CONFIG OBJECT TEST ===")
    
    try:
        config = CrusoeConfig.from_env()
        print(f"✅ Config created successfully")
        print(f"  access_key_id: {config.access_key_id}")
        print(f"  secret_access_key: {config.secret_access_key[:10] if config.secret_access_key else 'None'}...")
        print(f"  organization_id: '{config.organization_id}'")
        print(f"  base_url: {config.base_url}")
        
        # Check if organization_id is empty string vs None
        if config.organization_id == "":
            print(f"⚠️  organization_id is empty string")
        elif config.organization_id is None:
            print(f"⚠️  organization_id is None")
        else:
            print(f"✅ organization_id is set")
            
    except Exception as e:
        print(f"❌ Config creation failed: {e}")
    
    print(f"\n=== EXPECTED VALUES ===")
    print(f"Should have:")
    print(f"  CRUSOE_ACCESS_KEY_ID=n4Cm1VYRTGeipLsQFG1jqg")
    print(f"  CRUSOE_SECRET_ACCESS_KEY=VQSKaxlVqAuB0yD9Sab6lA")
    print(f"  CRUSOE_ORG_ID=c594a031-5041-45ff-a72c-ba127c9884d1")
    
    print(f"\n=== RECOMMENDATIONS ===")
    print(f"1. Check your .env file exists in current directory")
    print(f"2. Make sure .env file has the correct variable names")
    print(f"3. No spaces around the = sign in .env file")
    print(f"4. No quotes around values unless they contain spaces")

if __name__ == "__main__":
    check_env_loading()
