import streamlit as st
import pandas as pd
from datetime import datetime
from typing import List, Dict
import json
import os

from config import Config
from ebay_api import EbayAPIClient
from scorer import DealScorer

# Page configuration
st.set_page_config(
    page_title="eBay Smart Deal Finder",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'watch_rules' not in st.session_state:
    st.session_state.watch_rules = []
if 'search_results' not in st.session_state:
    st.session_state.search_results = []
if 'api_client' not in st.session_state:
    st.session_state.api_client = None
if 'scorer' not in st.session_state:
    st.session_state.scorer = DealScorer()


def check_credentials():
    """Check if eBay API credentials are configured"""
    is_valid, missing = Config.validate()
    return is_valid, missing


def initialize_api_client():
    """Initialize the eBay API client"""
    if st.session_state.api_client is None:
        try:
            st.session_state.api_client = EbayAPIClient()
        except Exception as e:
            st.error(f"Failed to initialize API client: {str(e)}")
            return False
    return True


def search_deals(
    keywords: str,
    min_price: float = None,
    max_price: float = None,
    min_feedback: int = None,
    target_discount: float = 0.20,
    limit: int = 50
) -> List[Dict]:
    """
    Search for deals and score them

    Args:
        keywords: Search keywords
        min_price: Minimum price
        max_price: Maximum price
        min_feedback: Minimum seller feedback score
        target_discount: Target discount percentage (0-1)
        limit: Maximum results

    Returns:
        List of scored deals
    """
    if not initialize_api_client():
        return []

    try:
        # Search current listings
        with st.spinner("Searching eBay listings..."):
            items = st.session_state.api_client.search_items(
                keywords=keywords,
                min_price=min_price,
                max_price=max_price,
                min_feedback_score=min_feedback,
                limit=limit
            )

        if not items:
            st.warning("No items found matching your criteria.")
            return []

        # Get market price from similar items
        with st.spinner("Analyzing market prices..."):
            market_items = st.session_state.api_client.search_completed_items(
                keywords=keywords,
                limit=100
            )
            market_price = st.session_state.scorer.calculate_market_price(market_items)

        # Score each item
        scored_deals = []
        with st.spinner("Scoring deals..."):
            for item in items:
                scores = st.session_state.scorer.score_item(
                    item,
                    market_price=market_price,
                    target_discount=target_discount
                )

                reasoning = st.session_state.scorer.generate_reasoning(item, scores)

                deal = {
                    'item': item,
                    'scores': scores,
                    'reasoning': reasoning
                }

                scored_deals.append(deal)

        # Sort by overall score (descending)
        scored_deals.sort(key=lambda x: x['scores']['overall_score'], reverse=True)

        return scored_deals

    except Exception as e:
        st.error(f"Error searching for deals: {str(e)}")
        return []


def display_deal_card(deal: Dict, index: int):
    """Display a single deal in a card format"""
    item = deal['item']
    scores = deal['scores']
    reasoning = deal['reasoning']

    # Extract item details
    title = item.get('title', 'Unknown Item')
    price = item.get('price', {})
    current_price = price.get('value', 'N/A')
    currency = price.get('currency', '')

    image = item.get('image', {})
    image_url = image.get('imageUrl') if image else None

    item_url = item.get('itemWebUrl', '#')
    condition = item.get('condition', 'N/A')

    seller = item.get('seller', {})
    seller_name = seller.get('username', 'Unknown')
    feedback_score = seller.get('feedbackScore', 0)
    feedback_pct = seller.get('feedbackPercentage', 0)

    # Determine score color
    score = scores['overall_score']
    if score >= 80:
        score_color = "🟢"
    elif score >= 60:
        score_color = "🟡"
    else:
        score_color = "🔴"

    # Create expandable card
    with st.expander(f"#{index + 1} - {title[:80]}... - Score: {score_color} {score}/100", expanded=(index < 3)):
        col1, col2 = st.columns([1, 2])

        with col1:
            if image_url:
                st.image(image_url, use_container_width=True)
            else:
                st.info("No image available")

        with col2:
            st.markdown(f"### {title}")

            # Price information
            price_col1, price_col2, price_col3 = st.columns(3)
            with price_col1:
                st.metric("Current Price", f"{currency} {current_price}")
            with price_col2:
                if scores['market_price']:
                    st.metric("Market Price", f"{currency} {scores['market_price']:.2f}")
            with price_col3:
                if scores['estimated_profit']:
                    st.metric(
                        "Est. Profit",
                        f"{currency} {scores['estimated_profit']:.2f}",
                        delta=f"{scores['estimated_profit_pct']:.1f}%"
                    )

            # Item details
            st.markdown(f"**Condition:** {condition}")
            st.markdown(f"**Seller:** {seller_name} ({feedback_score} feedback, {feedback_pct}% positive)")

            # Reasoning
            st.markdown("**Deal Analysis:**")
            st.info(reasoning)

            # Detailed scores
            score_col1, score_col2, score_col3, score_col4 = st.columns(4)
            with score_col1:
                st.metric("Price Score", f"{scores['price_score']}/100")
            with score_col2:
                st.metric("Seller Score", f"{scores['seller_score']}/100")
            with score_col3:
                st.metric("Shipping Score", f"{scores['shipping_score']}/100")
            with score_col4:
                st.metric("Quality Score", f"{scores['quality_score']}/100")

            # Link to item
            st.link_button("View on eBay", item_url, use_container_width=True)


def main():
    """Main application"""

    # Header
    st.title("🔍 eBay Smart Deal Finder")
    st.markdown("Find underpriced items on eBay using intelligent scoring and market analysis")

    # Check credentials
    is_valid, missing = check_credentials()

    if not is_valid:
        st.error("⚠️ eBay API credentials not configured!")
        st.markdown("""
        ### Setup Instructions:

        1. Get your eBay API credentials from [eBay Developer Portal](https://developer.ebay.com/my/keys)
        2. Copy `.env.example` to `.env`
        3. Add your credentials to the `.env` file:
           - `EBAY_APP_ID`
           - `EBAY_CERT_ID`
           - `EBAY_DEV_ID`
        4. Restart the application

        **Missing credentials:** {missing}
        """.format(missing=", ".join(missing)))
        return

    # Sidebar - Search Configuration
    with st.sidebar:
        st.header("Search Configuration")

        # Keywords
        keywords = st.text_input(
            "Keywords",
            placeholder="e.g., Seiko SKX, iPhone 15, vintage watch",
            help="Search terms for items you're looking for"
        )

        # Price range
        st.subheader("Price Range")
        col1, col2 = st.columns(2)
        with col1:
            min_price = st.number_input(
                "Min Price (£)",
                min_value=0.0,
                value=0.0,
                step=10.0
            )
        with col2:
            max_price = st.number_input(
                "Max Price (£)",
                min_value=0.0,
                value=500.0,
                step=10.0
            )

        # Seller requirements
        st.subheader("Seller Requirements")
        min_feedback = st.number_input(
            "Min Feedback Score",
            min_value=0,
            value=10,
            step=10,
            help="Minimum seller feedback score for credibility"
        )

        # Deal parameters
        st.subheader("Deal Parameters")
        target_discount = st.slider(
            "Target Discount (%)",
            min_value=5,
            max_value=50,
            value=20,
            step=5,
            help="Minimum discount vs market price to consider it a 'deal'"
        ) / 100.0

        result_limit = st.slider(
            "Max Results",
            min_value=10,
            max_value=100,
            value=50,
            step=10
        )

        # Search button
        search_button = st.button("🔍 Find Deals", type="primary", use_container_width=True)

        st.divider()

        # Display filter
        st.subheader("Display Filters")
        min_score = st.slider(
            "Minimum Deal Score",
            min_value=0,
            max_value=100,
            value=50,
            step=5,
            help="Only show deals with score above this threshold"
        )

    # Main content area
    if search_button:
        if not keywords:
            st.warning("Please enter search keywords")
        else:
            st.session_state.search_results = search_deals(
                keywords=keywords,
                min_price=min_price if min_price > 0 else None,
                max_price=max_price if max_price > 0 else None,
                min_feedback=min_feedback if min_feedback > 0 else None,
                target_discount=target_discount,
                limit=result_limit
            )

    # Display results
    if st.session_state.search_results:
        # Filter by minimum score
        filtered_results = [
            deal for deal in st.session_state.search_results
            if deal['scores']['overall_score'] >= min_score
        ]

        # Summary statistics
        st.header(f"Found {len(filtered_results)} Deals")

        if filtered_results:
            # Stats
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                avg_score = sum(d['scores']['overall_score'] for d in filtered_results) / len(filtered_results)
                st.metric("Avg Deal Score", f"{avg_score:.1f}/100")

            with col2:
                avg_discount = [d['scores']['estimated_profit_pct'] for d in filtered_results if d['scores']['estimated_profit_pct']]
                if avg_discount:
                    st.metric("Avg Discount", f"{sum(avg_discount) / len(avg_discount):.1f}%")

            with col3:
                top_deal = filtered_results[0]
                st.metric("Top Deal Score", f"{top_deal['scores']['overall_score']}/100")

            with col4:
                great_deals = sum(1 for d in filtered_results if d['scores']['overall_score'] >= 80)
                st.metric("Great Deals (80+)", great_deals)

            st.divider()

            # Display deals
            for idx, deal in enumerate(filtered_results):
                display_deal_card(deal, idx)

            # Export option
            st.divider()
            if st.button("📥 Export to CSV"):
                # Prepare data for export
                export_data = []
                for deal in filtered_results:
                    item = deal['item']
                    scores = deal['scores']

                    export_data.append({
                        'Title': item.get('title', ''),
                        'Price': scores['current_price'],
                        'Market Price': scores['market_price'],
                        'Profit': scores['estimated_profit'],
                        'Profit %': scores['estimated_profit_pct'],
                        'Overall Score': scores['overall_score'],
                        'Seller': item.get('seller', {}).get('username', ''),
                        'Feedback Score': item.get('seller', {}).get('feedbackScore', 0),
                        'URL': item.get('itemWebUrl', ''),
                        'Reasoning': deal['reasoning']
                    })

                df = pd.DataFrame(export_data)
                csv = df.to_csv(index=False)

                st.download_button(
                    label="Download CSV",
                    data=csv,
                    file_name=f"ebay_deals_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )
        else:
            st.info(f"No deals found with score >= {min_score}. Try lowering the minimum score filter.")

    else:
        # Welcome message
        st.info("👈 Configure your search parameters in the sidebar and click 'Find Deals' to get started!")

        # Features
        st.markdown("### Features")
        col1, col2, col3 = st.columns(3)

        with col1:
            st.markdown("""
            **Smart Scoring**
            - Price vs market analysis
            - Seller reputation check
            - Shipping cost evaluation
            - Listing quality assessment
            """)

        with col2:
            st.markdown("""
            **Flexible Filters**
            - Custom price ranges
            - Seller feedback requirements
            - Target discount thresholds
            - Result limits
            """)

        with col3:
            st.markdown("""
            **Easy Export**
            - Download deals as CSV
            - Direct links to items
            - Detailed scoring breakdown
            - Deal reasoning included
            """)


if __name__ == "__main__":
    main()
