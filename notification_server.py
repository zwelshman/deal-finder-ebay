#!/usr/bin/env python3
"""
eBay Marketplace Account Deletion/Closure Notification Server

This server handles notifications from eBay about marketplace account deletions
and closures. It implements the required challenge/response validation and
processes incoming notifications.

eBay Notification Flow:
1. Initial Setup: eBay sends a challenge code to validate the endpoint
2. Validation: Endpoint must respond with challengeResponse containing the hash
3. Notifications: eBay sends account deletion/closure notifications to this endpoint

For more information, see:
https://developer.ebay.com/api-docs/sell/account/resources/subscription/methods/createSubscription
"""

import os
import json
import hashlib
import hmac
import logging
from datetime import datetime
from flask import Flask, request, jsonify
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)

# Configuration
VERIFICATION_TOKEN = os.getenv('EBAY_NOTIFICATION_VERIFICATION_TOKEN', '')
NOTIFICATION_LOG_FILE = os.getenv('NOTIFICATION_LOG_FILE', 'ebay_notifications.log')

# Validate configuration
if not VERIFICATION_TOKEN:
    logger.warning("EBAY_NOTIFICATION_VERIFICATION_TOKEN not set! This is required for production.")
elif len(VERIFICATION_TOKEN) < 32 or len(VERIFICATION_TOKEN) > 80:
    logger.error(f"Verification token must be 32-80 characters. Current length: {len(VERIFICATION_TOKEN)}")
else:
    logger.info(f"Verification token configured (length: {len(VERIFICATION_TOKEN)})")


def validate_verification_token(token: str) -> bool:
    """
    Validate that the provided token matches our configured verification token

    Args:
        token: The verification token from the request

    Returns:
        True if token is valid, False otherwise
    """
    if not VERIFICATION_TOKEN:
        logger.warning("No verification token configured - accepting all requests (INSECURE!)")
        return True

    return hmac.compare_digest(token, VERIFICATION_TOKEN)


def create_challenge_response(challenge_code: str, verification_token: str, endpoint_url: str) -> str:
    """
    Create the challenge response hash as required by eBay

    eBay requires: SHA256 hash of challengeCode + verificationToken + endpoint URL

    Args:
        challenge_code: The challenge code sent by eBay
        verification_token: Your verification token
        endpoint_url: The notification endpoint URL

    Returns:
        Hex digest of the SHA256 hash
    """
    # Concatenate the three values
    hash_input = challenge_code + verification_token + endpoint_url

    # Create SHA256 hash
    hash_object = hashlib.sha256(hash_input.encode('utf-8'))
    challenge_response = hash_object.hexdigest()

    logger.info(f"Created challenge response for challenge code: {challenge_code[:10]}...")

    return challenge_response


def log_notification(notification_data: dict):
    """
    Log notification data to a file for record-keeping

    Args:
        notification_data: The notification payload from eBay
    """
    try:
        with open(NOTIFICATION_LOG_FILE, 'a') as f:
            log_entry = {
                'timestamp': datetime.utcnow().isoformat(),
                'notification': notification_data
            }
            f.write(json.dumps(log_entry) + '\n')
        logger.info(f"Logged notification to {NOTIFICATION_LOG_FILE}")
    except Exception as e:
        logger.error(f"Failed to log notification: {e}")


def process_marketplace_account_deletion(notification: dict):
    """
    Process a marketplace account deletion/closure notification

    This is where you implement your business logic for handling account deletions.
    For example:
    - Remove user data from your database
    - Send confirmation emails
    - Update your records
    - Trigger cleanup jobs

    Args:
        notification: The notification payload from eBay
    """
    try:
        # Extract notification details
        notification_id = notification.get('notificationId', 'N/A')
        event_date = notification.get('eventDate', 'N/A')

        # Extract metadata
        metadata = notification.get('metadata', {})
        topic = metadata.get('topic', 'UNKNOWN')

        # Extract notification data
        data = notification.get('data', {})
        user_id = data.get('userId', 'N/A')
        username = data.get('username', 'N/A')
        marketplace_account_id = data.get('marketplaceAccountId', 'N/A')

        logger.info(f"Processing marketplace account deletion:")
        logger.info(f"  Notification ID: {notification_id}")
        logger.info(f"  Event Date: {event_date}")
        logger.info(f"  Topic: {topic}")
        logger.info(f"  User ID: {user_id}")
        logger.info(f"  Username: {username}")
        logger.info(f"  Marketplace Account ID: {marketplace_account_id}")

        # TODO: Implement your business logic here
        # Examples:
        # - Delete user data from database
        # - Remove stored credentials
        # - Cancel any active operations
        # - Send confirmation notifications

        logger.info("Marketplace account deletion processed successfully")

    except Exception as e:
        logger.error(f"Error processing marketplace account deletion: {e}")
        raise


@app.route('/health', methods=['GET'])
def health_check():
    """
    Health check endpoint

    Returns:
        200 OK if the server is running
    """
    return jsonify({
        'status': 'healthy',
        'service': 'eBay Notification Server',
        'timestamp': datetime.utcnow().isoformat(),
        'verification_token_configured': bool(VERIFICATION_TOKEN)
    }), 200


@app.route('/ebay/notifications', methods=['GET', 'POST'])
def ebay_notification_endpoint():
    """
    eBay Notification Endpoint

    This endpoint handles both:
    1. GET requests with challenge codes (for initial validation)
    2. POST requests with notification payloads (for actual notifications)

    Returns:
        For GET: challengeResponse object
        For POST: 200 OK acknowledgment
    """

    # Handle GET request (Challenge validation)
    if request.method == 'GET':
        logger.info("Received challenge request from eBay")

        # Extract query parameters
        challenge_code = request.args.get('challenge_code', '')

        if not challenge_code:
            logger.error("No challenge_code provided in GET request")
            return jsonify({'error': 'Missing challenge_code parameter'}), 400

        # Get the endpoint URL (reconstructed from request)
        endpoint_url = request.url_root.rstrip('/') + '/ebay/notifications'

        logger.info(f"Challenge Code: {challenge_code}")
        logger.info(f"Endpoint URL: {endpoint_url}")
        logger.info(f"Verification Token: {'*' * len(VERIFICATION_TOKEN)}")

        # Create challenge response
        challenge_response = create_challenge_response(
            challenge_code,
            VERIFICATION_TOKEN,
            endpoint_url
        )

        # Return the challenge response
        response = {
            'challengeResponse': challenge_response
        }

        logger.info("Sending challenge response back to eBay")
        return jsonify(response), 200

    # Handle POST request (Actual notification)
    elif request.method == 'POST':
        logger.info("Received notification from eBay")

        try:
            # Get the notification payload
            notification = request.get_json()

            if not notification:
                logger.error("Empty notification payload")
                return jsonify({'error': 'Empty payload'}), 400

            logger.info(f"Notification received: {json.dumps(notification, indent=2)}")

            # Extract and validate verification token from headers
            # eBay sends the verification token in the X-EBAY-SIGNATURE header
            ebay_signature = request.headers.get('X-EBAY-SIGNATURE', '')

            # Log notification
            log_notification(notification)

            # Determine notification type and process accordingly
            metadata = notification.get('metadata', {})
            topic = metadata.get('topic', '')

            if 'MARKETPLACE_ACCOUNT_DELETION' in topic:
                logger.info("Processing MARKETPLACE_ACCOUNT_DELETION notification")
                process_marketplace_account_deletion(notification)
            else:
                logger.warning(f"Unknown notification topic: {topic}")

            # Return success response
            return jsonify({
                'status': 'success',
                'message': 'Notification received and processed',
                'notificationId': notification.get('notificationId', 'N/A')
            }), 200

        except Exception as e:
            logger.error(f"Error processing notification: {e}")
            # Still return 200 to acknowledge receipt
            # (eBay will retry if we return an error)
            return jsonify({
                'status': 'error',
                'message': str(e)
            }), 200


@app.route('/test/notification', methods=['POST'])
def test_notification():
    """
    Test endpoint for sending test notifications

    Use this to test your notification handling logic without relying on eBay

    Example request:
    curl -X POST http://localhost:5000/test/notification \\
      -H "Content-Type: application/json" \\
      -d '{
        "notificationId": "test-123",
        "eventDate": "2024-01-01T12:00:00.000Z",
        "metadata": {"topic": "MARKETPLACE_ACCOUNT_DELETION"},
        "data": {
          "userId": "test_user_123",
          "username": "testuser",
          "marketplaceAccountId": "test_account_456"
        }
      }'
    """
    try:
        notification = request.get_json()

        if not notification:
            return jsonify({'error': 'Empty payload'}), 400

        logger.info("Received test notification")

        # Process the test notification
        log_notification(notification)
        process_marketplace_account_deletion(notification)

        return jsonify({
            'status': 'success',
            'message': 'Test notification processed'
        }), 200

    except Exception as e:
        logger.error(f"Error processing test notification: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


if __name__ == '__main__':
    # Print startup information
    logger.info("=" * 60)
    logger.info("eBay Marketplace Notification Server")
    logger.info("=" * 60)
    logger.info(f"Verification Token Configured: {bool(VERIFICATION_TOKEN)}")
    if VERIFICATION_TOKEN:
        logger.info(f"Verification Token Length: {len(VERIFICATION_TOKEN)}")
    logger.info(f"Notification Log File: {NOTIFICATION_LOG_FILE}")
    logger.info("=" * 60)
    logger.info("")
    logger.info("Endpoints:")
    logger.info("  GET  /health                  - Health check")
    logger.info("  GET  /ebay/notifications      - Challenge validation")
    logger.info("  POST /ebay/notifications      - Receive notifications")
    logger.info("  POST /test/notification       - Test endpoint")
    logger.info("")
    logger.info("=" * 60)

    # Run the Flask app
    # Note: For production, use a production WSGI server like gunicorn
    # Example: gunicorn -w 4 -b 0.0.0.0:5000 notification_server:app
    port = int(os.getenv('NOTIFICATION_SERVER_PORT', 5000))
    app.run(
        host='0.0.0.0',
        port=port,
        debug=os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    )
