#!/usr/bin/env python3
"""
eBay API Credentials Test Utility

This script helps you verify that your eBay API credentials are properly configured
and working correctly with the sandbox or production environment.

Usage:
    python test_credentials.py
"""

import sys
from config import Config
from ebay_api import EbayAPIClient


def print_separator():
    print("\n" + "=" * 70 + "\n")


def main():
    print_separator()
    print("🔍 eBay API Credentials Test Utility")
    print_separator()

    # Check configuration
    print("📋 Configuration Status:")
    print(f"   Environment: {Config.EBAY_ENVIRONMENT.upper()}")
    print(f"   OAuth URL: {Config.get_oauth_url()}")
    print(f"   API Base URL: {Config.get_api_base_url()}")
    print(f"   Marketplace: {Config.EBAY_MARKETPLACE}")
    print(f"   Currency: {Config.EBAY_CURRENCY}")

    # Check if credentials are configured
    is_valid, missing = Config.validate()

    print_separator()
    print("🔑 Credentials Check:")

    if Config.EBAY_APP_ID:
        # Mask the credentials for security
        masked_app_id = Config.EBAY_APP_ID[:8] + "..." + Config.EBAY_APP_ID[-4:] if len(Config.EBAY_APP_ID) > 12 else "***"
        print(f"   ✅ EBAY_APP_ID: {masked_app_id} (length: {len(Config.EBAY_APP_ID)})")
    else:
        print("   ❌ EBAY_APP_ID: Not set")

    if Config.EBAY_CERT_ID:
        masked_cert_id = Config.EBAY_CERT_ID[:8] + "..." + Config.EBAY_CERT_ID[-4:] if len(Config.EBAY_CERT_ID) > 12 else "***"
        print(f"   ✅ EBAY_CERT_ID: {masked_cert_id} (length: {len(Config.EBAY_CERT_ID)})")
    else:
        print("   ❌ EBAY_CERT_ID: Not set")

    if Config.EBAY_DEV_ID:
        print(f"   ✅ EBAY_DEV_ID: Set (length: {len(Config.EBAY_DEV_ID)})")
    else:
        print("   ⚠️  EBAY_DEV_ID: Not set (optional for Browse API)")

    # Check for Anthropic API
    if Config.ANTHROPIC_API_KEY and not Config.ANTHROPIC_API_KEY.startswith('your_'):
        print(f"   ✅ ANTHROPIC_API_KEY: Set (AI features enabled)")
    else:
        print("   ⚠️  ANTHROPIC_API_KEY: Not set (AI features disabled)")

    if not is_valid:
        print_separator()
        print("❌ CONFIGURATION ERROR:")
        print(f"   Missing required credentials: {', '.join(missing)}")
        print("\n📝 Setup Instructions:")
        print("   1. Copy .env.example to .env")
        print("   2. Go to https://developer.ebay.com/my/keys")

        if Config.EBAY_ENVIRONMENT == 'sandbox':
            print("   3. Copy your SANDBOX credentials (Application Keys - Sandbox section)")
            print("      - App ID (Client ID)")
            print("      - Cert ID (Client Secret)")
        else:
            print("   3. Copy your PRODUCTION credentials (Application Keys - Production section)")
            print("      - App ID (Client ID)")
            print("      - Cert ID (Client Secret)")

        print("   4. Update the .env file with your credentials")
        print("   5. Run this test again")
        print_separator()
        return 1

    # Test API connection
    print_separator()
    print("🌐 Testing API Connection...")
    print("   This may take a few seconds...")

    try:
        client = EbayAPIClient()
        test_result = client.test_credentials()

        print_separator()

        if test_result['success']:
            print("✅ SUCCESS!")
            print(f"\n{test_result['message']}")
            print(f"\n   Token obtained: Yes")
            print(f"   Token length: {test_result.get('token_length', 'N/A')} characters")
            print("\n🎉 Your eBay API credentials are working correctly!")
            print("\nYou can now run the main application:")
            print("   streamlit run app.py")
            print_separator()
            return 0
        else:
            print("❌ AUTHENTICATION FAILED")
            print(f"\n{test_result['message']}")

            if test_result.get('error'):
                print("\n📋 Detailed Error:")
                print(f"   {test_result['error']}")

            print_separator()
            return 1

    except Exception as e:
        print_separator()
        print("❌ TEST FAILED")
        print(f"\nError: {str(e)}")
        print_separator()
        return 1


if __name__ == "__main__":
    sys.exit(main())
