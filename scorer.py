from typing import Dict, List, Optional
import statistics
from datetime import datetime


class DealScorer:
    """Score eBay listings to identify good deals"""

    def __init__(self):
        self.weights = {
            'price_discount': 0.4,     # 40% weight on price vs market
            'seller_quality': 0.3,     # 30% weight on seller reputation
            'shipping_cost': 0.15,     # 15% weight on shipping value
            'listing_quality': 0.15    # 15% weight on listing quality
        }

    def calculate_market_price(self, similar_items: List[Dict]) -> Optional[float]:
        """
        Calculate market price from similar items

        Args:
            similar_items: List of similar sold items

        Returns:
            Average market price or None
        """
        if not similar_items:
            return None

        prices = []
        for item in similar_items:
            price_obj = item.get('price', {})
            if price_obj and 'value' in price_obj:
                try:
                    prices.append(float(price_obj['value']))
                except (ValueError, TypeError):
                    continue

        if not prices:
            return None

        # Use median to reduce impact of outliers
        return statistics.median(prices)

    def score_price_discount(
        self,
        current_price: float,
        market_price: Optional[float],
        target_discount: float = 0.20
    ) -> float:
        """
        Score based on discount vs market price

        Args:
            current_price: Listed price
            market_price: Estimated market value
            target_discount: Target discount threshold (default 20%)

        Returns:
            Score 0-100
        """
        if not market_price or market_price <= 0:
            return 50.0  # Neutral score if no market data

        discount = (market_price - current_price) / market_price

        if discount <= 0:
            return 0.0  # Overpriced

        # Scale: 0% discount = 50, target discount = 100
        # Double the target gets max score
        score = 50 + (discount / (target_discount * 2)) * 50
        return min(100.0, max(0.0, score))

    def score_seller_quality(self, item: Dict) -> float:
        """
        Score seller based on feedback and other factors

        Args:
            item: Item dictionary from eBay

        Returns:
            Score 0-100
        """
        seller = item.get('seller', {})

        # Feedback score (number of ratings)
        feedback_score = seller.get('feedbackScore', 0)

        # Feedback percentage (positive %)
        feedback_pct = seller.get('feedbackPercentage', 0)

        # Score components
        score = 0.0

        # Feedback score component (0-50 points)
        if feedback_score >= 1000:
            score += 50
        elif feedback_score >= 500:
            score += 40
        elif feedback_score >= 100:
            score += 30
        elif feedback_score >= 50:
            score += 20
        elif feedback_score >= 10:
            score += 10

        # Feedback percentage component (0-50 points)
        if feedback_pct >= 99:
            score += 50
        elif feedback_pct >= 98:
            score += 40
        elif feedback_pct >= 95:
            score += 30
        elif feedback_pct >= 90:
            score += 20
        else:
            score += 10

        return score

    def score_shipping_cost(self, item: Dict, item_price: float) -> float:
        """
        Score based on shipping cost relative to item price

        Args:
            item: Item dictionary
            item_price: Item price

        Returns:
            Score 0-100
        """
        shipping_options = item.get('shippingOptions', [])

        if not shipping_options:
            return 50.0  # Neutral if no shipping info

        # Get cheapest shipping
        shipping_cost = float('inf')
        has_free_shipping = False

        for option in shipping_options:
            cost = option.get('shippingCost', {})
            if cost and 'value' in cost:
                try:
                    cost_value = float(cost['value'])
                    if cost_value == 0:
                        has_free_shipping = True
                        break
                    shipping_cost = min(shipping_cost, cost_value)
                except (ValueError, TypeError):
                    continue

        if has_free_shipping:
            return 100.0

        if shipping_cost == float('inf'):
            return 50.0  # No valid shipping cost

        # Score based on shipping cost as % of item price
        if item_price <= 0:
            return 50.0

        shipping_pct = shipping_cost / item_price

        if shipping_pct <= 0.05:  # 5% or less
            return 90.0
        elif shipping_pct <= 0.10:  # 10% or less
            return 70.0
        elif shipping_pct <= 0.15:  # 15% or less
            return 50.0
        elif shipping_pct <= 0.25:  # 25% or less
            return 30.0
        else:
            return 10.0

    def score_listing_quality(self, item: Dict) -> float:
        """
        Score based on listing quality indicators

        Args:
            item: Item dictionary

        Returns:
            Score 0-100
        """
        score = 0.0

        # Has images
        if item.get('image') or item.get('thumbnailImages'):
            score += 30

        # Has detailed condition description
        condition = item.get('condition', '')
        if condition:
            score += 20

        # Returns accepted
        if item.get('returnsAccepted', False):
            score += 25

        # Item location provided
        if item.get('itemLocation', {}).get('country'):
            score += 15

        # Top rated seller
        seller = item.get('seller', {})
        if seller.get('sellerAccountType') == 'BUSINESS':
            score += 10

        return min(100.0, score)

    def score_item(
        self,
        item: Dict,
        market_price: Optional[float] = None,
        target_discount: float = 0.20
    ) -> Dict:
        """
        Calculate comprehensive deal score for an item

        Args:
            item: Item dictionary from eBay
            market_price: Estimated market price (optional)
            target_discount: Target discount threshold

        Returns:
            Dictionary with overall score and component scores
        """
        # Extract current price
        price_obj = item.get('price', {})
        current_price = float(price_obj.get('value', 0))

        # Calculate component scores
        price_score = self.score_price_discount(current_price, market_price, target_discount)
        seller_score = self.score_seller_quality(item)
        shipping_score = self.score_shipping_cost(item, current_price)
        quality_score = self.score_listing_quality(item)

        # Calculate weighted overall score
        overall_score = (
            price_score * self.weights['price_discount'] +
            seller_score * self.weights['seller_quality'] +
            shipping_score * self.weights['shipping_cost'] +
            quality_score * self.weights['listing_quality']
        )

        # Calculate estimated profit
        profit_amount = (market_price - current_price) if market_price else None
        profit_pct = ((market_price - current_price) / market_price * 100) if market_price and market_price > 0 else None

        return {
            'overall_score': round(overall_score, 1),
            'price_score': round(price_score, 1),
            'seller_score': round(seller_score, 1),
            'shipping_score': round(shipping_score, 1),
            'quality_score': round(quality_score, 1),
            'current_price': current_price,
            'market_price': market_price,
            'estimated_profit': round(profit_amount, 2) if profit_amount else None,
            'estimated_profit_pct': round(profit_pct, 1) if profit_pct else None
        }

    def generate_reasoning(self, item: Dict, scores: Dict) -> str:
        """
        Generate human-readable reasoning for the deal score

        Args:
            item: Item dictionary
            scores: Scores dictionary from score_item()

        Returns:
            Reasoning string
        """
        reasons = []

        # Price reasoning
        if scores['estimated_profit_pct']:
            if scores['estimated_profit_pct'] >= 20:
                reasons.append(f"Priced {scores['estimated_profit_pct']:.0f}% below market average")
            elif scores['estimated_profit_pct'] >= 10:
                reasons.append(f"Moderate discount ({scores['estimated_profit_pct']:.0f}% below market)")
            else:
                reasons.append(f"Slight discount ({scores['estimated_profit_pct']:.0f}% below market)")

        # Seller reasoning
        seller = item.get('seller', {})
        feedback_score = seller.get('feedbackScore', 0)
        feedback_pct = seller.get('feedbackPercentage', 0)

        if feedback_score >= 1000 and feedback_pct >= 99:
            reasons.append(f"Excellent seller ({feedback_score} feedback, {feedback_pct}% positive)")
        elif feedback_score >= 100:
            reasons.append(f"Established seller ({feedback_score} feedback)")
        elif feedback_score < 10:
            reasons.append(f"New seller ({feedback_score} feedback) - higher risk")

        # Shipping
        shipping_options = item.get('shippingOptions', [])
        if shipping_options:
            for option in shipping_options:
                cost = option.get('shippingCost', {})
                if cost and cost.get('value') == '0':
                    reasons.append("Free shipping")
                    break

        # Returns
        if item.get('returnsAccepted'):
            reasons.append("Returns accepted")

        if not reasons:
            reasons.append("Standard listing")

        return "; ".join(reasons)
