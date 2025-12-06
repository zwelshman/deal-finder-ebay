import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Application configuration"""

    # eBay API credentials
    EBAY_APP_ID = os.getenv('EBAY_APP_ID', '')
    EBAY_CERT_ID = os.getenv('EBAY_CERT_ID', '')
    EBAY_DEV_ID = os.getenv('EBAY_DEV_ID', '')

    # Environment: 'production' or 'sandbox'
    EBAY_ENVIRONMENT = os.getenv('EBAY_ENVIRONMENT', 'sandbox').lower()

    # Anthropic API (optional - for enhanced AI scoring)
    ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY', '')

    # eBay settings
    EBAY_MARKETPLACE = os.getenv('EBAY_MARKETPLACE', 'EBAY_GB')
    EBAY_CURRENCY = os.getenv('EBAY_CURRENCY', 'GBP')

    # API endpoints - dynamically set based on environment
    @classmethod
    def get_api_base_url(cls):
        if cls.EBAY_ENVIRONMENT == 'production':
            return 'https://api.ebay.com'
        else:
            return 'https://api.sandbox.ebay.com'

    @classmethod
    def get_oauth_url(cls):
        if cls.EBAY_ENVIRONMENT == 'production':
            return 'https://api.ebay.com/identity/v1/oauth2/token'
        else:
            return 'https://api.sandbox.ebay.com/identity/v1/oauth2/token'

    # Marketplace IDs
    MARKETPLACE_IDS = {
        'EBAY_GB': 'EBAY_GB',
        'EBAY_US': 'EBAY_US',
        'EBAY_DE': 'EBAY_DE',
    }

    @classmethod
    def validate(cls):
        """Check if required credentials are set"""
        missing = []
        if not cls.EBAY_APP_ID:
            missing.append('EBAY_APP_ID')
        if not cls.EBAY_CERT_ID:
            missing.append('EBAY_CERT_ID')

        return len(missing) == 0, missing
