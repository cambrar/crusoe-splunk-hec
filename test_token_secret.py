#!/usr/bin/env python3
"""Test token + secret authentication combinations."""

import os
import requests
import base64
import hmac
import hashlib
from dotenv import load_dotenv

load_dotenv()

def test_token_secret_combinations():
    """Test different ways to use token + secret together."""
    token = os.getenv('CRUSOE_API_TOKEN')
    secret = os.getenv('CRUSOE_SECRET')  # You'll need to add this
    
    if not token:
        print("❌ No token found")
        return
    
    if not secret:
        print("❌ No secret found - please add CRUSOE_SECRET to your .env file")
        print("💡 Add this line to your .env file:")
        print("   CRUSOE_SECRET=your_secret_here")
        return
    
    print(f"🔑 Testing token: {token[:8]}...")
    print(f"🔐 Testing secret: {secret[:8]}...")
    print("=" * 60)
    
    # Test endpoint
    url = "https://api.crusoecloud.com/v1alpha5/locations"
    
    # Different authentication methods to try
    auth_methods = [
        ("Bearer token only", {
            'Authorization': f'Bearer {token}',
        }),
        ("Basic auth (token:secret)", None, (token, secret)),
        ("Token + Secret headers", {
            'X-API-Token': token,
            'X-API-Secret': secret,
        }),
        ("Authorization with both", {
            'Authorization': f'Bearer {token}:{secret}',
        }),
        ("Token as key, Secret as value", {
            'Authorization': f'{token} {secret}',
        }),
        ("Crusoe-specific headers", {
            'X-Crusoe-Token': token,
            'X-Crusoe-Secret': secret,
        }),
        ("API-Key style", {
            'X-API-Key': token,
            'X-API-Secret': secret,
        }),
        ("Token in header, Secret in auth", {
            'X-Token': token,
            'Authorization': f'Secret {secret}',
        }),
    ]
    
    for method_name, headers, auth in auth_methods:
        print(f"\\n🧪 Testing: {method_name}")
        
        try:
            if auth:  # Basic auth
                response = requests.get(url, auth=auth, timeout=10)
            else:  # Header auth
                response = requests.get(url, headers=headers, timeout=10)
            
            print(f"  Status: {response.status_code}")
            
            if response.status_code == 200:
                print(f"  ✅ SUCCESS!")
                try:
                    data = response.json()
                    print(f"  📊 Response: {data}")
                    return method_name, headers, auth
                except:
                    print(f"  📄 Response: {response.text[:200]}...")
                    return method_name, headers, auth
            elif response.status_code == 401:
                try:
                    error_data = response.json()
                    print(f"  ❌ Unauthorized: {error_data.get('message', 'Auth failed')}")
                except:
                    print(f"  ❌ Unauthorized")
            else:
                print(f"  ⚠️  Status {response.status_code}: {response.text[:100]}...")
                
        except Exception as e:
            print(f"  💥 Exception: {e}")
    
    return None

def test_signed_requests():
    """Test if we need to sign requests with HMAC."""
    token = os.getenv('CRUSOE_API_TOKEN')
    secret = os.getenv('CRUSOE_SECRET')
    
    if not token or not secret:
        return
    
    print(f"\\n" + "=" * 60)
    print("🔐 Testing HMAC signed requests")
    print("=" * 60)
    
    url = "https://api.crusoecloud.com/v1alpha5/locations"
    
    # Try HMAC-SHA256 signature
    try:
        import time
        timestamp = str(int(time.time()))
        
        # Different signature methods
        signature_methods = [
            ("Token + Timestamp", f"{token}{timestamp}"),
            ("Method + URL + Timestamp", f"GET{url}{timestamp}"),
            ("Token + URL", f"{token}{url}"),
        ]
        
        for method_name, message in signature_methods:
            print(f"\\n🔐 Testing HMAC: {method_name}")
            
            # Create HMAC signature
            signature = hmac.new(
                secret.encode('utf-8'),
                message.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            
            headers = {
                'Authorization': f'Bearer {token}',
                'X-Signature': signature,
                'X-Timestamp': timestamp,
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            print(f"  Status: {response.status_code}")
            
            if response.status_code == 200:
                print(f"  ✅ SUCCESS with HMAC!")
                return True
            elif response.status_code != 401:
                print(f"  Response: {response.text[:100]}...")
                
    except Exception as e:
        print(f"  💥 Exception: {e}")
    
    return False

def main():
    """Test token + secret authentication."""
    print("Crusoe Token + Secret Authentication Test")
    print("=" * 60)
    
    # Test different combinations
    result = test_token_secret_combinations()
    
    if result:
        method_name, headers, auth = result
        print(f"\\n🎉 Found working method: {method_name}")
        if headers:
            print(f"📋 Headers: {headers}")
        if auth:
            print(f"🔐 Auth: Basic auth with token:secret")
        return
    
    # If basic combinations don't work, try HMAC signing
    if test_signed_requests():
        print(f"\\n🎉 HMAC signing works!")
        return
    
    print(f"\\n❌ No token + secret combination worked")
    print(f"\\n💡 Please check:")
    print(f"  1. Is the secret correct and complete?")
    print(f"  2. Are both token and secret active?")
    print(f"  3. Is there documentation on how to use them together?")

if __name__ == "__main__":
    main()
