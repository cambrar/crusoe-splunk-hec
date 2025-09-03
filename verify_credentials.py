#!/usr/bin/env python3
"""Verify Crusoe API credentials and secret key decoding."""

import os
import base64
import binascii
from dotenv import load_dotenv

def verify_credentials():
    """Verify the format and validity of Crusoe API credentials."""
    load_dotenv()
    
    access_key = os.getenv('CRUSOE_ACCESS_KEY_ID')
    secret_key = os.getenv('CRUSOE_SECRET_ACCESS_KEY')
    
    print("=== Credential Verification ===")
    print(f"Access Key: {access_key}")
    print(f"Access Key Length: {len(access_key) if access_key else 'Not set'}")
    print(f"Secret Key: {secret_key}")
    print(f"Secret Key Length: {len(secret_key) if secret_key else 'Not set'}")
    
    if not access_key or not secret_key:
        print("❌ Missing credentials in environment variables")
        return False
    
    # Verify access key format (should be base64-like)
    print(f"\n=== Access Key Analysis ===")
    try:
        # Try to decode access key to see if it's valid base64
        access_decoded = base64.urlsafe_b64decode(access_key + '=' * (-len(access_key) % 4))
        print(f"✅ Access key appears to be valid base64 ({len(access_decoded)} bytes)")
    except Exception as e:
        print(f"⚠️  Access key might not be base64: {e}")
    
    # Verify secret key format and decoding
    print(f"\n=== Secret Key Analysis ===")
    print(f"Secret key characters: {set(secret_key)}")
    
    # Check if it looks like base64
    import string
    base64_chars = string.ascii_letters + string.digits + '-_='
    if all(c in base64_chars for c in secret_key):
        print("✅ Secret key contains only valid base64url characters")
    else:
        invalid_chars = [c for c in secret_key if c not in base64_chars]
        print(f"⚠️  Secret key contains invalid base64 characters: {invalid_chars}")
    
    # Try different decoding approaches
    decoding_results = {}
    
    # Approach 1: Direct decoding
    try:
        decoded1 = base64.urlsafe_b64decode(secret_key)
        decoding_results['direct'] = f"✅ Success: {len(decoded1)} bytes"
        print(f"Direct decode: {len(decoded1)} bytes")
    except Exception as e:
        decoding_results['direct'] = f"❌ Failed: {e}"
        print(f"Direct decode failed: {e}")
    
    # Approach 2: With padding
    try:
        padded = secret_key + '=' * (-len(secret_key) % 4)
        decoded2 = base64.urlsafe_b64decode(padded)
        decoding_results['padded'] = f"✅ Success: {len(decoded2)} bytes"
        print(f"Padded decode: {len(decoded2)} bytes")
    except Exception as e:
        decoding_results['padded'] = f"❌ Failed: {e}"
        print(f"Padded decode failed: {e}")
    
    # Approach 3: Standard base64 (not urlsafe)
    try:
        # Convert urlsafe to standard base64
        standard_key = secret_key.replace('-', '+').replace('_', '/')
        padded_standard = standard_key + '=' * (-len(standard_key) % 4)
        decoded3 = base64.b64decode(padded_standard)
        decoding_results['standard'] = f"✅ Success: {len(decoded3)} bytes"
        print(f"Standard base64 decode: {len(decoded3)} bytes")
    except Exception as e:
        decoding_results['standard'] = f"❌ Failed: {e}"
        print(f"Standard base64 decode failed: {e}")
    
    # Print hex representation of decoded secret (for debugging)
    for approach, result in decoding_results.items():
        if "Success" in result:
            try:
                if approach == 'direct':
                    decoded = base64.urlsafe_b64decode(secret_key)
                elif approach == 'padded':
                    padded = secret_key + '=' * (-len(secret_key) % 4)
                    decoded = base64.urlsafe_b64decode(padded)
                elif approach == 'standard':
                    standard_key = secret_key.replace('-', '+').replace('_', '/')
                    padded_standard = standard_key + '=' * (-len(standard_key) % 4)
                    decoded = base64.b64decode(padded_standard)
                
                hex_repr = binascii.hexlify(decoded).decode()
                print(f"{approach.capitalize()} decode hex: {hex_repr}")
            except:
                pass
    
    print(f"\n=== Recommendations ===")
    
    # Check key lengths
    if len(access_key) < 20:
        print("⚠️  Access key seems short - typical API keys are longer")
    
    if len(secret_key) != 22:
        print(f"⚠️  Secret key length is {len(secret_key)}, expected around 22 for base64url encoding")
    
    # Check if keys look like they're from the right service
    print("\n🔍 Key Validation Tips:")
    print("1. Ensure keys are copied correctly from Crusoe Cloud console")
    print("2. Check that keys haven't expired")
    print("3. Verify your account has API access permissions")
    print("4. Make sure keys are for the correct organization")
    
    return True

if __name__ == "__main__":
    verify_credentials()
