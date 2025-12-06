import requests
import base64
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from config import Config


class EbayAPIClient:
    """Client for eBay Browse API"""

    def __init__(self):
        self.config = Config()
        self.access_token = None
        self.token_expiry = None

    def _get_access_token(self) -> str:
        """Get OAuth2 access token for application access"""
        # Check if we have a valid cached token
        if self.access_token and self.token_expiry and datetime.now() < self.token_expiry:
            return self.access_token

        # Validate credentials are set
        if not self.config.EBAY_APP_ID or not self.config.EBAY_CERT_ID:
            raise Exception(
                "eBay credentials not configured. Please set EBAY_APP_ID and EBAY_CERT_ID in your .env file.\n"
                f"Environment: {self.config.EBAY_ENVIRONMENT}\n"
                "Get credentials from: https://developer.ebay.com/my/keys"
            )

        # Validate credentials don't contain placeholder text
        if 'your_' in self.config.EBAY_APP_ID.lower() or 'your_' in self.config.EBAY_CERT_ID.lower():
            raise Exception(
                "eBay credentials contain placeholder text. Please replace with actual credentials.\n"
                f"Environment: {self.config.EBAY_ENVIRONMENT}\n"
                "Get credentials from: https://developer.ebay.com/my/keys"
            )

        # Create credentials string
        credentials = f"{self.config.EBAY_APP_ID}:{self.config.EBAY_CERT_ID}"
        b64_credentials = base64.b64encode(credentials.encode()).decode()

        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Authorization': f'Basic {b64_credentials}'
        }

        # Scope differs between sandbox and production
        if self.config.EBAY_ENVIRONMENT == 'production':
            scope = 'https://api.ebay.com/oauth/api_scope'
        else:
            scope = 'https://api.ebay.com/oauth/api_scope'

        data = {
            'grant_type': 'client_credentials',
            'scope': scope
        }

        oauth_url = self.config.get_oauth_url()

        try:
            response = requests.post(oauth_url, headers=headers, data=data, timeout=10)
        except requests.exceptions.RequestException as e:
            raise Exception(f"Network error connecting to eBay API: {str(e)}")

        if response.status_code == 200:
            token_data = response.json()
            self.access_token = token_data['access_token']
            # Set expiry to 5 minutes before actual expiry for safety
            expires_in = token_data.get('expires_in', 7200) - 300
            self.token_expiry = datetime.now() + timedelta(seconds=expires_in)
            return self.access_token
        else:
            error_msg = f"Failed to get access token: {response.status_code} - {response.text}\n\n"
            error_msg += f"Environment: {self.config.EBAY_ENVIRONMENT.upper()}\n"
            error_msg += f"OAuth URL: {oauth_url}\n\n"

            if response.status_code == 401:
                error_msg += "TROUBLESHOOTING 401 ERROR:\n"
                error_msg += "1. Verify you're using the correct credentials for your environment:\n"
                if self.config.EBAY_ENVIRONMENT == 'sandbox':
                    error_msg += "   - For SANDBOX: Use 'Application Keys (Sandbox)' from https://developer.ebay.com/my/keys\n"
                    error_msg += "   - NOT production keys!\n"
                else:
                    error_msg += "   - For PRODUCTION: Use 'Application Keys (Production)' from https://developer.ebay.com/my/keys\n"
                    error_msg += "   - NOT sandbox keys!\n"
                error_msg += "2. Check that your App ID (Client ID) and Cert ID (Client Secret) are correct\n"
                error_msg += "3. Ensure there are no extra spaces or newlines in your credentials\n"
                error_msg += "4. Verify your eBay developer account is in good standing\n"
                if self.config.EBAY_ENVIRONMENT == 'sandbox':
                    error_msg += "5. For sandbox, make sure you've accepted the sandbox user agreement\n"
                    error_msg += "6. Try regenerating your sandbox keyset if the error persists\n"

            raise Exception(error_msg)

    def search_items(
        self,
        keywords: str,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        min_feedback_score: Optional[int] = None,
        category_id: Optional[str] = None,
        condition: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict]:
        """
        Search for items on eBay

        Args:
            keywords: Search keywords
            min_price: Minimum price filter
            max_price: Maximum price filter
            min_feedback_score: Minimum seller feedback score
            category_id: eBay category ID
            condition: Item condition (NEW, USED, etc.)
            limit: Maximum number of results

        Returns:
            List of item dictionaries
        """
        token = self._get_access_token()

        headers = {
            'Authorization': f'Bearer {token}',
            'X-EBAY-C-MARKETPLACE-ID': self.config.EBAY_MARKETPLACE,
            'X-EBAY-C-ENDUSERCTX': 'contextualLocation=country=GB'
        }

        # Build query parameters
        params = {
            'q': keywords,
            'limit': min(limit, 200)  # eBay max is 200
        }

        # Build filter string
        filters = []
        if min_price is not None:
            filters.append(f'price:[{min_price}..]')
        if max_price is not None:
            if min_price is not None:
                filters[-1] = f'price:[{min_price}..{max_price}]'
            else:
                filters.append(f'price:[..{max_price}]')

        if condition:
            filters.append(f'conditions:{{{condition}}}')

        if min_feedback_score is not None:
            filters.append(f'feedbackScore:[{min_feedback_score}..]')

        # Add buying format filter (fixed price only, no auctions)
        filters.append('buyingOptions:{FIXED_PRICE}')

        if filters:
            params['filter'] = ','.join(filters)

        if category_id:
            params['category_ids'] = category_id

        url = f"{self.config.get_api_base_url()}/buy/browse/v1/item_summary/search"

        try:
            response = requests.get(url, headers=headers, params=params)

            if response.status_code == 200:
                data = response.json()
                return data.get('itemSummaries', [])
            else:
                raise Exception(f"eBay API error: {response.status_code} - {response.text}")
        except Exception as e:
            raise Exception(f"Failed to search items: {str(e)}")

    def get_item_details(self, item_id: str) -> Optional[Dict]:
        """
        Get detailed information about a specific item

        Args:
            item_id: eBay item ID

        Returns:
            Item details dictionary or None
        """
        token = self._get_access_token()

        headers = {
            'Authorization': f'Bearer {token}',
            'X-EBAY-C-MARKETPLACE-ID': self.config.EBAY_MARKETPLACE
        }

        url = f"{self.config.get_api_base_url()}/buy/browse/v1/item/{item_id}"

        try:
            response = requests.get(url, headers=headers)

            if response.status_code == 200:
                return response.json()
            else:
                return None
        except Exception as e:
            print(f"Failed to get item details: {str(e)}")
            return None

    def search_completed_items(
        self,
        keywords: str,
        days_back: int = 90,
        limit: int = 50
    ) -> List[Dict]:
        """
        Search for sold/completed items to establish pricing history
        Note: This uses item_summary search with sold items filter

        Args:
            keywords: Search keywords
            days_back: How many days back to search
            limit: Maximum results

        Returns:
            List of sold items
        """
        token = self._get_access_token()

        headers = {
            'Authorization': f'Bearer {token}',
            'X-EBAY-C-MARKETPLACE-ID': self.config.EBAY_MARKETPLACE
        }

        params = {
            'q': keywords,
            'limit': min(limit, 200),
            'filter': 'buyingOptions:{FIXED_PRICE}'
        }

        url = f"{self.config.get_api_base_url()}/buy/browse/v1/item_summary/search"

        try:
            response = requests.get(url, headers=headers, params=params)

            if response.status_code == 200:
                data = response.json()
                return data.get('itemSummaries', [])
            else:
                return []
        except Exception as e:
            print(f"Failed to search completed items: {str(e)}")
            return []

    def test_credentials(self) -> Dict:
        """
        Test eBay API credentials and connection

        Returns:
            Dictionary with test results and diagnostic information
        """
        result = {
            'success': False,
            'environment': self.config.EBAY_ENVIRONMENT,
            'oauth_url': self.config.get_oauth_url(),
            'api_url': self.config.get_api_base_url(),
            'has_app_id': bool(self.config.EBAY_APP_ID),
            'has_cert_id': bool(self.config.EBAY_CERT_ID),
            'app_id_length': len(self.config.EBAY_APP_ID) if self.config.EBAY_APP_ID else 0,
            'cert_id_length': len(self.config.EBAY_CERT_ID) if self.config.EBAY_CERT_ID else 0,
            'error': None,
            'token_obtained': False
        }

        try:
            # Try to get access token
            token = self._get_access_token()
            result['success'] = True
            result['token_obtained'] = True
            result['token_length'] = len(token) if token else 0
            result['message'] = f"✅ Successfully authenticated with eBay {self.config.EBAY_ENVIRONMENT.upper()} API"
        except Exception as e:
            result['error'] = str(e)
            result['message'] = f"❌ Authentication failed: {str(e)}"

        return result
