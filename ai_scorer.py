from typing import Dict, List, Optional
import json
from config import Config


class AIEnhancedScorer:
    """Use Anthropic Claude to provide AI-enhanced deal scoring and insights"""

    def __init__(self):
        self.config = Config()
        self.client = None

        # Initialize Anthropic client if API key is available
        if self.config.ANTHROPIC_API_KEY:
            try:
                import anthropic
                self.client = anthropic.Anthropic(api_key=self.config.ANTHROPIC_API_KEY)
            except ImportError:
                print("Warning: anthropic package not installed. Run: pip install anthropic")
                self.client = None
            except Exception as e:
                print(f"Warning: Failed to initialize Anthropic client: {e}")
                self.client = None

    def is_available(self) -> bool:
        """Check if AI scoring is available"""
        return self.client is not None

    def enhance_deal_analysis(
        self,
        item: Dict,
        scores: Dict,
        market_price: Optional[float] = None
    ) -> Dict:
        """
        Use Claude to provide enhanced analysis of a deal

        Args:
            item: Item dictionary from eBay
            scores: Scores from the standard scorer
            market_price: Estimated market price

        Returns:
            Dictionary with AI-enhanced insights
        """
        if not self.is_available():
            return {
                'enhanced': False,
                'reasoning': scores.get('reasoning', 'Standard scoring only'),
                'risk_assessment': 'N/A',
                'recommendation': 'N/A'
            }

        # Prepare item data for Claude
        item_summary = {
            'title': item.get('title', 'Unknown'),
            'current_price': scores['current_price'],
            'market_price': market_price,
            'condition': item.get('condition', 'N/A'),
            'seller': {
                'username': item.get('seller', {}).get('username', 'Unknown'),
                'feedback_score': item.get('seller', {}).get('feedbackScore', 0),
                'feedback_percentage': item.get('seller', {}).get('feedbackPercentage', 0)
            },
            'scores': {
                'overall': scores['overall_score'],
                'price': scores['price_score'],
                'seller': scores['seller_score'],
                'shipping': scores['shipping_score'],
                'quality': scores['quality_score']
            },
            'shipping': 'Free' if self._has_free_shipping(item) else 'Paid',
            'returns': 'Yes' if item.get('returnsAccepted', False) else 'No'
        }

        prompt = f"""Analyze this eBay listing and provide a concise deal assessment:

{json.dumps(item_summary, indent=2)}

Provide:
1. A 1-2 sentence deal reasoning (why this is or isn't a good deal)
2. Risk assessment (Low/Medium/High) with brief explanation
3. Recommendation (Buy/Consider/Pass) with one key reason

Keep your response concise and focused on the most important factors."""

        try:
            message = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=300,
                temperature=0.3,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )

            ai_response = message.content[0].text

            # Parse response into components
            result = self._parse_ai_response(ai_response)
            result['enhanced'] = True
            result['full_analysis'] = ai_response

            return result

        except Exception as e:
            print(f"AI enhancement failed: {e}")
            return {
                'enhanced': False,
                'reasoning': 'AI analysis unavailable',
                'risk_assessment': 'N/A',
                'recommendation': 'N/A'
            }

    def batch_rank_deals(
        self,
        deals: List[Dict],
        user_preferences: Optional[Dict] = None
    ) -> List[Dict]:
        """
        Use Claude to re-rank deals based on user preferences and context

        Args:
            deals: List of scored deals
            user_preferences: Optional user preferences (budget, risk tolerance, etc.)

        Returns:
            Re-ranked list of deals with AI insights
        """
        if not self.is_available() or len(deals) == 0:
            return deals

        # For now, enhance each deal individually
        # In production, you might batch this more efficiently
        enhanced_deals = []

        for deal in deals[:10]:  # Limit to top 10 to save API calls
            item = deal['item']
            scores = deal['scores']
            market_price = scores.get('market_price')

            enhancement = self.enhance_deal_analysis(item, scores, market_price)
            deal['ai_enhancement'] = enhancement

            enhanced_deals.append(deal)

        # Add unenhanced deals
        enhanced_deals.extend(deals[10:])

        return enhanced_deals

    def _has_free_shipping(self, item: Dict) -> bool:
        """Check if item has free shipping"""
        shipping_options = item.get('shippingOptions', [])
        for option in shipping_options:
            cost = option.get('shippingCost', {})
            if cost and cost.get('value') == '0':
                return True
        return False

    def _parse_ai_response(self, response: str) -> Dict:
        """
        Parse Claude's response into structured components

        Args:
            response: Raw text response from Claude

        Returns:
            Structured dictionary
        """
        lines = response.strip().split('\n')

        result = {
            'reasoning': '',
            'risk_assessment': 'Medium',
            'recommendation': 'Consider'
        }

        current_section = None
        for line in lines:
            line = line.strip()
            if not line:
                continue

            lower_line = line.lower()

            # Detect sections
            if 'reasoning' in lower_line or 'deal assessment' in lower_line:
                current_section = 'reasoning'
                continue
            elif 'risk' in lower_line:
                current_section = 'risk'
                # Extract risk level
                if 'low' in lower_line:
                    result['risk_assessment'] = 'Low'
                elif 'high' in lower_line:
                    result['risk_assessment'] = 'High'
                else:
                    result['risk_assessment'] = 'Medium'
                continue
            elif 'recommendation' in lower_line:
                current_section = 'recommendation'
                # Extract recommendation
                if 'buy' in lower_line and 'consider' not in lower_line:
                    result['recommendation'] = 'Buy'
                elif 'pass' in lower_line:
                    result['recommendation'] = 'Pass'
                else:
                    result['recommendation'] = 'Consider'
                continue

            # Add content to current section
            if current_section == 'reasoning':
                result['reasoning'] += line + ' '
            elif current_section == 'risk' and ':' in line:
                # Extract explanation after colon
                result['risk_assessment'] += ': ' + line.split(':', 1)[1].strip()
            elif current_section == 'recommendation' and ':' in line:
                # Extract explanation after colon
                result['recommendation'] += ': ' + line.split(':', 1)[1].strip()

        # Fallback: if parsing failed, use entire response as reasoning
        if not result['reasoning'].strip():
            result['reasoning'] = response[:200]  # First 200 chars

        result['reasoning'] = result['reasoning'].strip()

        return result
