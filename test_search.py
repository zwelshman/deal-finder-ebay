#!/usr/bin/env python3
"""
Test script to diagnose eBay search issues
This will test the search functionality with various queries and show detailed results
"""

from ebay_api import EbayAPIClient
from config import Config
import sys


def test_search():
    """Test basic search functionality"""
    print("=" * 60)
    print("eBay Search Diagnostic Test")
    print("=" * 60)

    # Initialize client
    try:
        client = EbayAPIClient()
        config = Config()

        print(f"\n✓ API Client initialized")
        print(f"  Environment: {config.EBAY_ENVIRONMENT}")
        print(f"  API Base URL: {config.get_api_base_url()}")
        print(f"  Marketplace: {config.EBAY_MARKETPLACE}")

    except Exception as e:
        print(f"\n✗ Failed to initialize API client: {e}")
        return False

    # Test authentication
    print("\n" + "-" * 60)
    print("Testing Authentication...")
    print("-" * 60)

    try:
        token = client._get_access_token()
        print(f"✓ Authentication successful")
        print(f"  Token length: {len(token)} characters")
    except Exception as e:
        print(f"✗ Authentication failed: {e}")
        return False

    # Test searches with various keywords
    test_queries = [
        {"keywords": "laptop", "description": "Common item (laptop)"},
        {"keywords": "iphone", "description": "Popular item (iPhone)"},
        {"keywords": "test", "description": "Simple keyword (test)"},
    ]

    print("\n" + "-" * 60)
    print("Testing Search Queries...")
    print("-" * 60)

    for test in test_queries:
        print(f"\nSearching for: '{test['keywords']}' ({test['description']})")
        print("-" * 40)

        try:
            # The debug output will be printed from the search_items method
            items = client.search_items(
                keywords=test['keywords'],
                limit=10
            )

            if items:
                print(f"✓ Found {len(items)} items")
                print(f"\nFirst item details:")
                first_item = items[0]
                print(f"  Title: {first_item.get('title', 'N/A')[:60]}...")
                print(f"  Price: {first_item.get('price', {}).get('value', 'N/A')} {first_item.get('price', {}).get('currency', '')}")
                print(f"  Condition: {first_item.get('condition', 'N/A')}")
                print(f"  Item URL: {first_item.get('itemWebUrl', 'N/A')[:60]}...")
            else:
                print(f"✗ No items found")

        except Exception as e:
            print(f"✗ Search failed: {e}")

    # Test with filters
    print("\n" + "-" * 60)
    print("Testing Search with Filters...")
    print("-" * 60)

    print(f"\nSearching for 'laptop' with price range £100-£500")
    print("-" * 40)

    try:
        items = client.search_items(
            keywords="laptop",
            min_price=100,
            max_price=500,
            limit=10
        )

        if items:
            print(f"✓ Found {len(items)} items with filters")
        else:
            print(f"✗ No items found with filters")
            print(f"\nTIP: If using sandbox, filters may reduce already limited results to zero.")
            print(f"     Try searching without price filters.")

    except Exception as e:
        print(f"✗ Search with filters failed: {e}")

    print("\n" + "=" * 60)
    print("Test Complete")
    print("=" * 60)

    if config.EBAY_ENVIRONMENT == 'sandbox':
        print(f"\n⚠️  SANDBOX ENVIRONMENT NOTES:")
        print(f"   - Sandbox has very limited test data")
        print(f"   - Only specific test items may be available")
        print(f"   - Try very generic searches like 'test', 'laptop', 'phone'")
        print(f"   - For real listings, switch to production environment")
        print(f"   - Update EBAY_ENVIRONMENT=production in your .env file")

    print("\nCheck the debug output above for detailed API response information.")

    return True


if __name__ == "__main__":
    try:
        success = test_search()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nUnexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
