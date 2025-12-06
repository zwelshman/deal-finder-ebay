# eBay Smart Deal Finder

A Streamlit web application that helps you find underpriced items on eBay using intelligent scoring and market price analysis.

## Features

- **Smart Deal Scoring**: Multi-factor scoring system that evaluates:
  - Price discount vs market average (40% weight)
  - Seller reputation and feedback (30% weight)
  - Shipping costs (15% weight)
  - Listing quality (15% weight)

- **Market Price Analysis**: Automatically calculates market prices from similar listings

- **Flexible Search**: Configure searches with:
  - Custom keywords
  - Price ranges
  - Minimum seller feedback scores
  - Target discount thresholds

- **Visual Dashboard**: Clean interface showing:
  - Deal cards with images and details
  - Score breakdowns
  - Profit estimates
  - Direct links to eBay listings

- **Export Functionality**: Download results as CSV for offline analysis

- **AI-Enhanced Scoring** (Optional): Use Anthropic's Claude to provide intelligent deal analysis with:
  - Contextual deal reasoning
  - Risk assessment (Low/Medium/High)
  - Buy/Consider/Pass recommendations

- **Sandbox Support**: Test with eBay sandbox environment before using production credentials

## Setup

### 1. eBay API Credentials

You'll need to register for eBay API access:

1. Go to [eBay Developer Portal](https://developer.ebay.com/)
2. Sign in or create an account
3. Navigate to "My Account" → "Keys"
4. Create a keyset:
   - **Sandbox keys** for testing (limited test data)
   - **Production keys** for live eBay data
5. Note down your:
   - App ID (Client ID)
   - Cert ID (Client Secret)
   - Dev ID

### 2. Installation

```bash
# Clone or download this repository
cd deal-finder-ebay

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
cp .env.example .env
# Edit .env and add your eBay API credentials
```

### 3. Configuration

Edit `.env` file with your credentials:

```bash
# eBay API Credentials
EBAY_APP_ID=your_app_id_here
EBAY_CERT_ID=your_cert_id_here
EBAY_DEV_ID=your_dev_id_here

# Environment: 'sandbox' for testing, 'production' for live data
# IMPORTANT: Use sandbox credentials with sandbox, production credentials with production
EBAY_ENVIRONMENT=sandbox

# Optional: For AI-enhanced deal analysis with Claude
# Get your key from: https://console.anthropic.com/
ANTHROPIC_API_KEY=your_anthropic_key_here

# Marketplace (default: eBay UK)
EBAY_MARKETPLACE=EBAY_GB
EBAY_CURRENCY=GBP
```

### 4. Test Your Credentials (Recommended)

Before running the main app, test your eBay API credentials:

```bash
python test_credentials.py
```

This will verify your credentials are working and provide helpful diagnostic information if there are any issues.

### 5. Run the App

```bash
streamlit run app.py
```

The app will open in your browser at `http://localhost:8501`

## Usage

### Quick Start

1. **Enter Keywords**: Type what you're looking for (e.g., "Seiko SKX", "iPhone 15", "vintage camera")

2. **Set Price Range**: Define min/max prices to filter results

3. **Configure Seller Requirements**: Set minimum feedback score for seller credibility

4. **Set Target Discount**: Choose the minimum discount percentage you're looking for

5. **Click "Find Deals"**: The app will search, analyze, and score all matching listings

6. **Review Results**: Browse deals sorted by score, with detailed breakdowns

7. **Export**: Download results as CSV for further analysis

### Understanding Deal Scores

The overall deal score (0-100) combines:

- **Price Score**: How much below market price
- **Seller Score**: Seller reputation and feedback
- **Shipping Score**: Shipping cost relative to item price
- **Quality Score**: Listing completeness and returns policy

**Score Ranges:**
- 80-100: Excellent deal
- 60-79: Good deal
- 40-59: Fair deal
- 0-39: Not recommended

### Example Use Cases

**Watches & Collectibles**
```
Keywords: "Seiko SKX"
Price Range: £100-£400
Min Feedback: 100
Target Discount: 20%
```

**Electronics**
```
Keywords: "iPhone 15 Pro unlocked"
Price Range: £400-£800
Min Feedback: 500
Target Discount: 15%
```

**General Bargain Hunting**
```
Keywords: "vintage camera"
Price Range: £0-£200
Min Feedback: 50
Target Discount: 25%
```

## eBay Notification Server

This project includes a notification server for handling eBay marketplace account deletion/closure notifications (required for GDPR/CCPA compliance).

### Quick Setup

```bash
# 1. Generate verification token
python3 generate_notification_token.py

# 2. Add to .env file
EBAY_NOTIFICATION_VERIFICATION_TOKEN=your_generated_token

# 3. Run notification server
python3 notification_server.py
```

### Features

- **Challenge/Response Validation**: Automatically validates endpoint ownership
- **Notification Processing**: Handles account deletion notifications
- **HTTPS Support**: Works with nginx/caddy reverse proxy
- **Logging**: Records all notifications for compliance
- **Health Checks**: Monitor server status

### Full Documentation

See **[NOTIFICATION_SETUP.md](NOTIFICATION_SETUP.md)** for complete setup instructions including:
- Production deployment with systemd
- HTTPS configuration with nginx/Let's Encrypt
- eBay Developer Portal configuration
- Troubleshooting guide

## Architecture

### Project Structure

```
deal-finder-ebay/
├── app.py                          # Main Streamlit application
├── ebay_api.py                     # eBay Browse API client
├── scorer.py                       # Deal scoring algorithms
├── ai_scorer.py                    # AI-enhanced scoring with Anthropic Claude
├── config.py                       # Configuration management
├── notification_server.py          # eBay notification webhook server
├── generate_notification_token.py  # Token generator utility
├── test_credentials.py             # Credential testing utility
├── requirements.txt                # Python dependencies
├── .env.example                    # Example environment variables
├── nginx.conf.example              # Nginx configuration template
├── ebay-notifications.service      # systemd service file
├── NOTIFICATION_SETUP.md           # Notification server setup guide
└── README.md                       # This file
```

### How It Works

1. **Search Phase**:
   - App calls eBay Browse API `item_summary/search` endpoint
   - Retrieves active fixed-price listings matching your criteria
   - Also searches for similar sold items to establish market price

2. **Analysis Phase**:
   - Calculates median market price from similar items
   - Scores each listing across 4 dimensions
   - Generates human-readable reasoning
   - Optionally enhances top deals with AI insights from Claude

3. **Display Phase**:
   - Ranks results by overall score
   - Shows detailed breakdowns
   - Provides export and filtering options

### Scoring Algorithm

The scorer uses a weighted combination of factors:

```python
overall_score = (
    price_score × 0.4 +
    seller_score × 0.3 +
    shipping_score × 0.15 +
    quality_score × 0.15
)
```

**Price Score**: Based on discount vs market price
- Uses median price of similar items to reduce outlier impact
- Scales from 0 (overpriced) to 100 (deeply discounted)

**Seller Score**: Based on reputation
- Feedback count (experience)
- Positive feedback percentage (reliability)
- Top-rated seller status

**Shipping Score**: Based on cost efficiency
- Free shipping = 100
- Cost as % of item price (lower is better)

**Quality Score**: Based on listing completeness
- Images present
- Detailed condition description
- Returns accepted
- Seller type (business vs individual)

## API Rate Limits

eBay Browse API has rate limits:
- **Free tier**: 5,000 calls/day
- Each search uses ~1-2 API calls

Tips to stay within limits:
- Use specific keywords to reduce result count
- Set reasonable price ranges
- Limit results per search (default: 50)

### AI-Enhanced Scoring

When you provide an Anthropic API key, the app automatically enhances the top 5 deals with AI insights:

- **Contextual Reasoning**: Claude analyzes the full context of each deal
- **Risk Assessment**: Identifies potential red flags or concerns
- **Actionable Recommendations**: Clear Buy/Consider/Pass guidance

The AI enhancement is optional - the app works perfectly fine without it using rule-based scoring.

## Future Enhancements

Planned features for v2:

- **Background Monitoring**: Save watch rules and get periodic email alerts
- **Multiple Marketplaces**: Support eBay US, DE, AU, etc.
- **Push Notifications**: Real-time alerts via mobile app/PWA
- **Historical Tracking**: Track price trends over time
- **Category Specialization**: Custom scoring for different item types
- **Profit Calculator**: Include eBay fees, PayPal fees, shipping costs

## Troubleshooting

### "Failed to get access token" / 401 Authentication Error

This is the most common issue with eBay API setup. Follow these steps:

1. **Run the test utility first**:
   ```bash
   python test_credentials.py
   ```
   This will help diagnose the exact issue.

2. **Verify you're using the correct credentials for your environment**:
   - **Sandbox**: Use credentials from "Application Keys (Sandbox)" section at https://developer.ebay.com/my/keys
   - **Production**: Use credentials from "Application Keys (Production)" section
   - ⚠️ **DO NOT** use production credentials with `EBAY_ENVIRONMENT=sandbox` or vice versa!

3. **Check your .env file**:
   - Copy `.env.example` to `.env` if you haven't already
   - Ensure no extra spaces or newlines in credentials
   - Make sure credentials are not wrapped in quotes
   - Verify credentials don't contain placeholder text like "your_app_id_here"

4. **Common sandbox issues**:
   - Sandbox credentials expire if not used regularly - try regenerating them
   - Make sure you've accepted the sandbox user agreement on eBay Developer Portal
   - Verify your eBay developer account is active and in good standing

5. **If still failing**:
   - Try regenerating your keyset on eBay Developer Portal
   - Wait a few minutes after generating new keys before testing
   - Clear any cached tokens by restarting the application

### "No items found"

- Try broader keywords
- Expand price range
- Lower minimum feedback score
- Check eBay website to confirm items exist

### Low scores for legitimate deals

- Adjust score weights in `scorer.py`
- Lower target discount percentage
- Review component scores to see which factor is low

## Contributing

Feel free to submit issues or pull requests for:
- Bug fixes
- New features
- Documentation improvements
- Additional marketplaces

## License

MIT License - feel free to use and modify for your needs

## Disclaimer

This tool is for personal use and educational purposes. Always verify listings on eBay before making purchases. The app provides estimates and scores based on available data, but cannot guarantee accuracy or profitability.

Not affiliated with eBay Inc.
