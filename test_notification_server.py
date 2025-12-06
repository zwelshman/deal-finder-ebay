#!/usr/bin/env python3
"""
Test eBay Notification Server

This script tests the notification server to ensure it's properly configured
and ready to receive eBay notifications.

Usage:
    python3 test_notification_server.py [--url URL] [--token TOKEN]

Examples:
    # Test local server
    python3 test_notification_server.py

    # Test production server
    python3 test_notification_server.py --url https://yourdomain.com

    # Test with custom token
    python3 test_notification_server.py --token your_token_here
"""

import sys
import argparse
import requests
import hashlib
import json
from datetime import datetime


def test_health_check(base_url: str) -> bool:
    """
    Test the health check endpoint

    Args:
        base_url: Base URL of the notification server

    Returns:
        True if health check passes, False otherwise
    """
    print("\n" + "=" * 60)
    print("TEST 1: Health Check")
    print("=" * 60)

    url = f"{base_url}/health"
    print(f"Testing: {url}")

    try:
        response = requests.get(url, timeout=10)

        if response.status_code == 200:
            data = response.json()
            print("✅ Health check passed!")
            print(f"   Status: {data.get('status')}")
            print(f"   Service: {data.get('service')}")
            print(f"   Token Configured: {data.get('verification_token_configured')}")
            return True
        else:
            print(f"❌ Health check failed with status code: {response.status_code}")
            print(f"   Response: {response.text}")
            return False

    except requests.exceptions.ConnectionError:
        print("❌ Connection failed - is the server running?")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_challenge_validation(base_url: str, verification_token: str) -> bool:
    """
    Test the challenge/response validation

    Args:
        base_url: Base URL of the notification server
        verification_token: The verification token to use

    Returns:
        True if challenge validation passes, False otherwise
    """
    print("\n" + "=" * 60)
    print("TEST 2: Challenge/Response Validation")
    print("=" * 60)

    # Generate test challenge code
    challenge_code = "test_challenge_123456"
    endpoint_url = f"{base_url}/ebay/notifications"

    print(f"Challenge Code: {challenge_code}")
    print(f"Endpoint URL: {endpoint_url}")
    print(f"Verification Token: {'*' * len(verification_token)}")

    # Calculate expected response
    hash_input = challenge_code + verification_token + endpoint_url
    expected_response = hashlib.sha256(hash_input.encode('utf-8')).hexdigest()

    print(f"\nExpected Challenge Response: {expected_response[:40]}...")

    # Send challenge request
    url = f"{endpoint_url}?challenge_code={challenge_code}"
    print(f"\nSending GET request to: {url}")

    try:
        response = requests.get(url, timeout=10)

        if response.status_code == 200:
            data = response.json()
            actual_response = data.get('challengeResponse', '')

            print(f"Actual Challenge Response: {actual_response[:40]}...")

            if actual_response == expected_response:
                print("\n✅ Challenge validation passed!")
                print("   The server correctly computed the challenge response.")
                return True
            else:
                print("\n❌ Challenge validation failed!")
                print("   The server returned an incorrect challenge response.")
                print(f"   Expected: {expected_response}")
                print(f"   Got: {actual_response}")
                return False
        else:
            print(f"\n❌ Request failed with status code: {response.status_code}")
            print(f"   Response: {response.text}")
            return False

    except Exception as e:
        print(f"\n❌ Error: {e}")
        return False


def test_notification_handling(base_url: str) -> bool:
    """
    Test notification handling by sending a test notification

    Args:
        base_url: Base URL of the notification server

    Returns:
        True if notification handling passes, False otherwise
    """
    print("\n" + "=" * 60)
    print("TEST 3: Notification Handling")
    print("=" * 60)

    url = f"{base_url}/test/notification"
    print(f"Testing: {url}")

    # Create test notification payload
    test_notification = {
        "notificationId": f"test-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
        "eventDate": datetime.utcnow().isoformat() + "Z",
        "metadata": {
            "topic": "MARKETPLACE_ACCOUNT_DELETION"
        },
        "data": {
            "userId": "test_user_12345",
            "username": "testuser",
            "marketplaceAccountId": "test_account_67890"
        }
    }

    print(f"\nSending test notification:")
    print(json.dumps(test_notification, indent=2))

    try:
        response = requests.post(
            url,
            json=test_notification,
            headers={'Content-Type': 'application/json'},
            timeout=10
        )

        if response.status_code == 200:
            data = response.json()
            print("\n✅ Notification handling passed!")
            print(f"   Status: {data.get('status')}")
            print(f"   Message: {data.get('message')}")
            print("\n   Check the notification log file (ebay_notifications.log)")
            print("   to verify the notification was recorded.")
            return True
        else:
            print(f"\n❌ Request failed with status code: {response.status_code}")
            print(f"   Response: {response.text}")
            return False

    except Exception as e:
        print(f"\n❌ Error: {e}")
        return False


def main():
    """Main function"""
    parser = argparse.ArgumentParser(
        description='Test eBay notification server',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  Test local server:
    python3 test_notification_server.py

  Test production server:
    python3 test_notification_server.py --url https://yourdomain.com

  Test with custom token:
    python3 test_notification_server.py --token your_verification_token
        """
    )

    parser.add_argument(
        '--url',
        default='http://localhost:5000',
        help='Base URL of notification server (default: http://localhost:5000)'
    )

    parser.add_argument(
        '--token',
        help='Verification token (reads from .env if not provided)'
    )

    args = parser.parse_args()

    # Get verification token
    verification_token = args.token
    if not verification_token:
        # Try to read from .env
        try:
            from dotenv import load_dotenv
            import os
            load_dotenv()
            verification_token = os.getenv('EBAY_NOTIFICATION_VERIFICATION_TOKEN', '')
        except:
            pass

    if not verification_token:
        print("⚠️  Warning: No verification token provided.")
        print("   Challenge validation test will be skipped.")
        print("   Use --token argument or set EBAY_NOTIFICATION_VERIFICATION_TOKEN in .env")

    # Print test configuration
    print("=" * 60)
    print("eBay Notification Server Test Suite")
    print("=" * 60)
    print(f"Server URL: {args.url}")
    print(f"Token Configured: {bool(verification_token)}")
    print("=" * 60)

    # Run tests
    results = []

    # Test 1: Health check
    results.append(("Health Check", test_health_check(args.url)))

    # Test 2: Challenge validation (only if token available)
    if verification_token:
        results.append(("Challenge Validation", test_challenge_validation(args.url, verification_token)))
    else:
        print("\n⏭️  Skipping challenge validation test (no token)")

    # Test 3: Notification handling
    results.append(("Notification Handling", test_notification_handling(args.url)))

    # Print summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    total_tests = len(results)
    passed_tests = sum(1 for _, result in results if result)

    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")

    print("=" * 60)
    print(f"Results: {passed_tests}/{total_tests} tests passed")
    print("=" * 60)

    if passed_tests == total_tests:
        print("\n🎉 All tests passed! Your notification server is ready.")
        print("\nNext steps:")
        print("1. Deploy the server to an HTTPS endpoint")
        print("2. Configure eBay Developer Portal:")
        print("   - URL: https://yourdomain.com/ebay/notifications")
        print(f"   - Token: {verification_token[:20]}..." if verification_token else "   - Token: [your token]")
        print("3. Test with eBay's 'Send Test Notification' button")
        return 0
    else:
        print("\n⚠️  Some tests failed. Please review the errors above.")
        print("\nTroubleshooting:")
        print("- Ensure the server is running: python3 notification_server.py")
        print("- Check the server logs for errors")
        print("- Verify the verification token is correct")
        print("- Make sure .env file is configured properly")
        return 1


if __name__ == '__main__':
    sys.exit(main())
