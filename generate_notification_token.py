#!/usr/bin/env python3
"""
Generate eBay Notification Verification Token

This script generates a secure random verification token for use with eBay
marketplace account deletion/closure notifications.

Requirements:
- Token must be 32-80 characters
- Allowed characters: alphanumeric (a-z, A-Z, 0-9), underscore (_), hyphen (-)
- Should be cryptographically secure (random)

Usage:
    python3 generate_notification_token.py [--length LENGTH]

Example:
    python3 generate_notification_token.py
    python3 generate_notification_token.py --length 64
"""

import secrets
import string
import argparse
import sys


def generate_token(length: int = 64) -> str:
    """
    Generate a cryptographically secure random token

    Args:
        length: Length of the token (must be 32-80)

    Returns:
        Random token string

    Raises:
        ValueError: If length is not between 32 and 80
    """
    # Validate length
    if length < 32 or length > 80:
        raise ValueError("Token length must be between 32 and 80 characters")

    # Allowed characters: alphanumeric + underscore + hyphen
    # eBay specification: alphanumeric, underscore (_), and hyphen (-)
    allowed_chars = string.ascii_letters + string.digits + '_-'

    # Generate cryptographically secure random token
    token = ''.join(secrets.choice(allowed_chars) for _ in range(length))

    return token


def main():
    """Main function"""
    parser = argparse.ArgumentParser(
        description='Generate eBay notification verification token',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  Generate token with default length (64):
    python3 generate_notification_token.py

  Generate token with custom length:
    python3 generate_notification_token.py --length 80

The generated token should be added to your .env file:
    EBAY_NOTIFICATION_VERIFICATION_TOKEN=<generated_token>
        """
    )

    parser.add_argument(
        '--length',
        type=int,
        default=64,
        help='Token length (32-80 characters, default: 64)'
    )

    args = parser.parse_args()

    try:
        # Generate token
        token = generate_token(args.length)

        # Display results
        print("=" * 80)
        print("eBay Notification Verification Token Generator")
        print("=" * 80)
        print()
        print(f"Generated Token (length: {len(token)}):")
        print()
        print(f"  {token}")
        print()
        print("=" * 80)
        print()
        print("Next Steps:")
        print()
        print("1. Copy the token above")
        print("2. Add it to your .env file:")
        print(f"   EBAY_NOTIFICATION_VERIFICATION_TOKEN={token}")
        print()
        print("3. Deploy your notification server to an HTTPS endpoint")
        print()
        print("4. In eBay Developer Portal (https://developer.ebay.com/my/subscriptions):")
        print("   - Set Notification Endpoint URL: https://yourdomain.com/ebay/notifications")
        print(f"   - Set Verification Token: {token}")
        print("   - Click Save")
        print()
        print("5. eBay will send a challenge code to validate your endpoint")
        print()
        print("6. Once validated, test with 'Send Test Notification' button")
        print()
        print("=" * 80)
        print()
        print("IMPORTANT:")
        print("- Keep this token SECRET and secure")
        print("- Do NOT commit it to version control")
        print("- Use the same token in both your .env file and eBay Developer Portal")
        print("- The endpoint MUST be HTTPS (not HTTP)")
        print("=" * 80)

        return 0

    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
