import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Application configuration"""

    # eBay API credentials
    EBAY_APP_ID = os.getenv('EBAY_APP_ID', '')
    EBAY_CERT_ID = os.getenv('EBAY_CERT_ID', '')
    EBAY_DEV_ID = os.getenv('EBAY_DEV_ID', '')

    # OpenAI (optional)
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')

    # eBay settings
    EBAY_MARKETPLACE = os.getenv('EBAY_MARKETPLACE', 'EBAY_GB')
    EBAY_CURRENCY = os.getenv('EBAY_CURRENCY', 'GBP')

    # API endpoints
    EBAY_API_BASE_URL = 'https://api.ebay.com'
    EBAY_OAUTH_URL = 'https://api.ebay.com/identity/v1/oauth2/token'

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
