# eBay Marketplace Account Deletion/Closure Notification Setup

This guide walks you through setting up eBay marketplace account deletion and closure notifications for your application.

## Table of Contents

- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Detailed Setup](#detailed-setup)
  - [1. Generate Verification Token](#1-generate-verification-token)
  - [2. Configure Environment](#2-configure-environment)
  - [3. Deploy Notification Server](#3-deploy-notification-server)
  - [4. Set Up HTTPS](#4-set-up-https)
  - [5. Configure eBay Developer Portal](#5-configure-ebay-developer-portal)
  - [6. Test the Setup](#6-test-the-setup)
- [Production Deployment](#production-deployment)
- [Troubleshooting](#troubleshooting)

## Overview

eBay requires applications to handle marketplace account deletion and closure notifications to comply with data protection regulations (GDPR, CCPA, etc.). This implementation provides:

- **Challenge/Response Validation**: Validates endpoint ownership
- **Notification Processing**: Handles account deletion notifications
- **Secure Token Verification**: Uses SHA256 hashing for security
- **Logging**: Records all notifications for compliance
- **Health Checks**: Monitors server status

## Prerequisites

- Python 3.8 or higher
- Access to a server with a public IP or domain
- SSL/TLS certificate for HTTPS
- eBay Developer Account
- Required Python packages (see `requirements.txt`)

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Generate verification token
python3 generate_notification_token.py

# 3. Configure .env file
cp .env.example .env
# Edit .env and add your verification token

# 4. Test locally
python3 notification_server.py

# 5. Test the endpoint
curl http://localhost:5000/health
```

## Detailed Setup

### 1. Generate Verification Token

eBay requires a verification token (32-80 characters) containing only alphanumeric characters, underscores, and hyphens.

```bash
python3 generate_notification_token.py
```

This will output a secure random token. Copy it for the next step.

**Example output:**
```
Generated Token (length: 64):

  aB3dEf9hIjKlMn0pQrStUv-WxYz1234567890_AbCdEfGhIjKlMnOpQrStU

Next Steps:
1. Copy the token above
2. Add it to your .env file
...
```

**Optional: Custom token length**
```bash
python3 generate_notification_token.py --length 80
```

### 2. Configure Environment

Copy the example environment file and add your configuration:

```bash
cp .env.example .env
```

Edit `.env` and set:

```bash
# eBay Notification Configuration
EBAY_NOTIFICATION_VERIFICATION_TOKEN=your_generated_token_here
NOTIFICATION_SERVER_PORT=5000
NOTIFICATION_LOG_FILE=ebay_notifications.log
FLASK_DEBUG=false
```

**Important:**
- Keep the token SECRET
- Use the same token in both your `.env` file and eBay Developer Portal
- Never commit the `.env` file to version control

### 3. Deploy Notification Server

The notification server can run standalone or alongside your main application.

#### Option A: Run Directly (Development)

```bash
python3 notification_server.py
```

The server will start on `http://localhost:5000`

#### Option B: Use Gunicorn (Production)

```bash
gunicorn -w 4 -b 0.0.0.0:5000 notification_server:app
```

#### Option C: Use systemd (Production - Recommended)

See [Production Deployment](#production-deployment) section below.

### 4. Set Up HTTPS

**eBay requires HTTPS endpoints.** HTTP endpoints will be rejected.

#### Option A: Use Nginx as Reverse Proxy (Recommended)

1. Install Nginx:
```bash
sudo apt update
sudo apt install nginx
```

2. Install Certbot for SSL:
```bash
sudo apt install certbot python3-certbot-nginx
```

3. Configure Nginx (`/etc/nginx/sites-available/ebay-notifications`):
```nginx
server {
    listen 80;
    server_name yourdomain.com;

    location /.well-known/acme-challenge/ {
        root /var/www/html;
    }

    location / {
        return 301 https://$server_name$request_uri;
    }
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;

    location /ebay/notifications {
        proxy_pass http://localhost:5000/ebay/notifications;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /health {
        proxy_pass http://localhost:5000/health;
    }
}
```

4. Get SSL certificate:
```bash
sudo certbot --nginx -d yourdomain.com
```

5. Enable the site:
```bash
sudo ln -s /etc/nginx/sites-available/ebay-notifications /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

#### Option B: Use Caddy (Automatic HTTPS)

1. Install Caddy:
```bash
sudo apt install -y debian-keyring debian-archive-keyring apt-transport-https
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' | sudo gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' | sudo tee /etc/apt/sources.list.d/caddy-stable.list
sudo apt update
sudo apt install caddy
```

2. Configure Caddy (`/etc/caddy/Caddyfile`):
```
yourdomain.com {
    reverse_proxy /ebay/notifications localhost:5000
    reverse_proxy /health localhost:5000
}
```

3. Reload Caddy:
```bash
sudo systemctl reload caddy
```

Caddy automatically obtains and renews SSL certificates from Let's Encrypt.

### 5. Configure eBay Developer Portal

1. Log in to [eBay Developer Portal](https://developer.ebay.com)

2. Navigate to **My Account** → **Subscriptions** or visit:
   ```
   https://developer.ebay.com/my/subscriptions
   ```

3. Find the **Marketplace Account Deletion/Closure Notifications** section

4. Enter your configuration:
   - **Notification Endpoint URL**: `https://yourdomain.com/ebay/notifications`
   - **Verification Token**: Your generated token (same as in `.env`)

5. Click **Save**

6. eBay will immediately send a **challenge code** to your endpoint

   Your notification server will:
   - Receive the challenge code
   - Compute SHA256 hash of: `challengeCode + verificationToken + endpointUrl`
   - Return the hash in a `challengeResponse` field

7. If validation succeeds, your endpoint is now configured!

**Validation Flow:**
```
eBay → GET https://yourdomain.com/ebay/notifications?challenge_code=ABC123
Your Server → Computes: SHA256(ABC123 + your_token + https://yourdomain.com/ebay/notifications)
Your Server → Returns: {"challengeResponse": "computed_hash"}
eBay → Validates hash and confirms endpoint
```

### 6. Test the Setup

#### Test with eBay's Test Notification

1. In eBay Developer Portal, click **Send Test Notification**
2. Check your server logs:
   ```bash
   tail -f ebay_notifications.log
   ```
3. Verify the notification was received and processed

#### Test Locally

Use the built-in test endpoint:

```bash
curl -X POST http://localhost:5000/test/notification \
  -H "Content-Type: application/json" \
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
```

Check the response and logs.

## Production Deployment

### Using systemd (Recommended for Linux)

1. Create a systemd service file (`/etc/systemd/system/ebay-notifications.service`):

```ini
[Unit]
Description=eBay Marketplace Notification Server
After=network.target

[Service]
Type=notify
User=www-data
Group=www-data
WorkingDirectory=/path/to/deal-finder-ebay
Environment="PATH=/path/to/deal-finder-ebay/venv/bin"
ExecStart=/path/to/deal-finder-ebay/venv/bin/gunicorn \
    --workers 4 \
    --bind 127.0.0.1:5000 \
    --timeout 30 \
    --access-logfile /var/log/ebay-notifications/access.log \
    --error-logfile /var/log/ebay-notifications/error.log \
    notification_server:app
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

2. Create log directory:
```bash
sudo mkdir -p /var/log/ebay-notifications
sudo chown www-data:www-data /var/log/ebay-notifications
```

3. Enable and start the service:
```bash
sudo systemctl daemon-reload
sudo systemctl enable ebay-notifications
sudo systemctl start ebay-notifications
```

4. Check status:
```bash
sudo systemctl status ebay-notifications
```

5. View logs:
```bash
sudo journalctl -u ebay-notifications -f
```

### Using Docker

1. Create `Dockerfile`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY notification_server.py .
COPY .env .

EXPOSE 5000

CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "notification_server:app"]
```

2. Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  ebay-notifications:
    build: .
    ports:
      - "5000:5000"
    environment:
      - EBAY_NOTIFICATION_VERIFICATION_TOKEN=${EBAY_NOTIFICATION_VERIFICATION_TOKEN}
    volumes:
      - ./ebay_notifications.log:/app/ebay_notifications.log
    restart: unless-stopped
```

3. Build and run:
```bash
docker-compose up -d
```

### Security Considerations

1. **HTTPS Only**: Never use HTTP in production
2. **Firewall**: Only allow traffic on ports 80 and 443
3. **Token Security**: Keep verification token secret
4. **Log Rotation**: Set up log rotation to prevent disk space issues
5. **Monitoring**: Monitor server health and notification logs
6. **Rate Limiting**: Consider adding rate limiting with nginx/caddy

## Troubleshooting

### Issue: Challenge validation fails

**Symptoms:**
- eBay shows "Endpoint validation failed"
- Server receives challenge but eBay rejects response

**Solutions:**
1. Verify endpoint URL matches exactly (including `/ebay/notifications`)
2. Check verification token is identical in both `.env` and eBay portal
3. Ensure HTTPS is working (not HTTP)
4. Check server logs for errors:
   ```bash
   tail -f /var/log/ebay-notifications/error.log
   ```

### Issue: Server not accessible from internet

**Symptoms:**
- Local tests work, but eBay can't reach endpoint
- Connection timeout errors

**Solutions:**
1. Check firewall settings:
   ```bash
   sudo ufw status
   sudo ufw allow 80/tcp
   sudo ufw allow 443/tcp
   ```
2. Verify DNS is configured correctly
3. Test from external server:
   ```bash
   curl https://yourdomain.com/health
   ```

### Issue: Notifications not being logged

**Symptoms:**
- Server runs but no logs appear in `ebay_notifications.log`

**Solutions:**
1. Check file permissions:
   ```bash
   ls -la ebay_notifications.log
   sudo chown www-data:www-data ebay_notifications.log
   ```
2. Check disk space:
   ```bash
   df -h
   ```

### Issue: SSL certificate errors

**Symptoms:**
- "SSL certificate problem" or "certificate verify failed"

**Solutions:**
1. Verify certificate is valid:
   ```bash
   sudo certbot certificates
   ```
2. Renew certificate if expired:
   ```bash
   sudo certbot renew
   ```
3. Check nginx/caddy configuration

### Debugging Tips

1. **Enable debug logging**:
   ```bash
   # In .env
   FLASK_DEBUG=true
   ```

2. **Monitor logs in real-time**:
   ```bash
   # Server logs
   sudo journalctl -u ebay-notifications -f

   # Notification logs
   tail -f ebay_notifications.log

   # Nginx logs
   sudo tail -f /var/log/nginx/error.log
   ```

3. **Test endpoint manually**:
   ```bash
   # Test challenge
   curl "https://yourdomain.com/ebay/notifications?challenge_code=test123"

   # Test health
   curl https://yourdomain.com/health
   ```

4. **Check service status**:
   ```bash
   sudo systemctl status ebay-notifications
   sudo systemctl status nginx
   ```

## Notification Processing

When you receive a notification, the server:

1. Logs the full notification to `ebay_notifications.log`
2. Calls `process_marketplace_account_deletion()` function
3. Returns a 200 OK response to eBay

**Customize processing** by editing the `process_marketplace_account_deletion()` function in `notification_server.py`:

```python
def process_marketplace_account_deletion(notification: dict):
    """
    Process account deletion notification

    Implement your business logic here:
    - Delete user data from database
    - Remove stored credentials
    - Send confirmation emails
    - Update records
    """
    # Your custom logic here
    pass
```

## Support

For issues or questions:
- eBay API Documentation: https://developer.ebay.com/api-docs/
- eBay Developer Support: https://developer.ebay.com/support
- Project Issues: [Create an issue in your repository]

## References

- [eBay Marketplace Account Deletion Notifications](https://developer.ebay.com/api-docs/sell/account/resources/subscription/methods/createSubscription)
- [eBay Developer Portal](https://developer.ebay.com)
- [GDPR Compliance](https://gdpr.eu/)
- [Flask Documentation](https://flask.palletsprojects.com/)
- [Gunicorn Documentation](https://docs.gunicorn.org/)
- [Let's Encrypt](https://letsencrypt.org/)
