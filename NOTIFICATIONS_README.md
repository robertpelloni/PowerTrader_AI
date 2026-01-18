# PowerTrader AI Notification System

A comprehensive multi-platform notification system for PowerTrader AI with Email, Discord, and Telegram support.

## Features

- **Multiple Platforms**: Email (Gmail), Discord (webhooks), Telegram (bot)
- **Rate Limiting**: Prevent spam with configurable rate limits per platform
- **Notification Levels**: INFO, WARNING, ERROR, CRITICAL with color coding
- **Async Support**: Non-blocking notifications using asyncio
- **Analytics Integration**: Log all notifications to SQLite database
- **Flexible Configuration**: Enable/disable platforms per notification type
- **Error Handling**: Graceful fallbacks and detailed error logging
- **Statistics**: Track notification success rates and performance

## Installation

The notification dependencies are already included in `requirements.txt`:

```
yagmail
discord-webhook
python-telegram-bot
```

Install them:

```bash
pip install -r requirements.txt
```

## Quick Setup

### Email (Gmail)

1. Enable 2-factor authentication on your Gmail account
2. Generate an App Password:
   - Go to Google Account > Security
   - 2-Step Verification > App passwords
   - Generate a new app password (name it "PowerTrader AI")
3. Configure:

```python
python pt_notifications.py config --email your.email@gmail.com
```

You'll need to set your app password separately in the config file or programmatically.

### Discord

1. Go to your Discord server settings
2. Integrations > Webhooks > New Webhook
3. Copy the webhook URL
4. Configure:

```python
python pt_notifications.py config --discord https://discord.com/api/webhooks/YOUR_WEBHOOK
```

### Telegram

1. Create a bot via @BotFather on Telegram
2. Copy the bot token
3. Get your chat ID:
   - Message @userinfobot or use the Telegram API
4. Configure:

```python
python pt_notifications.py config --telegram-token YOUR_BOT_TOKEN
python pt_notifications.py config --telegram-chat YOUR_CHAT_ID
```

## Usage

### Basic Usage

```python
from pt_notifications import NotificationManager

manager = NotificationManager()

# Send notifications
await manager.send_info("System started")
await manager.send_warning("Low balance warning")
await manager.send_error("API connection failed")
await manager.send_critical("Critical error!")
```

### With Specific Platforms

```python
await manager.send(
    "Trade executed",
    level="info",
    platforms=["discord", "telegram"]
)
```

### Programmatic Configuration

```python
from pt_notifications import create_notification_manager

manager = create_notification_manager(
    email_address="your.email@gmail.com",
    email_app_password="your-app-password",
    discord_webhook_url="https://discord.com/api/webhooks/...",
    telegram_bot_token="your-bot-token",
    telegram_chat_id="your-chat-id"
)
```

### Integration with pt_analytics.py

```python
from pt_notifications import NotificationManager
from pt_analytics import TradeJournal, PerformanceTracker

manager = NotificationManager()
journal = TradeJournal()
tracker = PerformanceTracker(journal)

# Check performance and send notifications
snapshot = tracker.calculate_snapshot()

if snapshot.win_rate < 40:
    await manager.send_warning(
        f"Low win rate: {snapshot.win_rate:.1f}% - Review strategy"
    )

if snapshot.max_drawdown_pct > 20:
    await manager.send_error(
        f"High drawdown: {snapshot.max_drawdown_pct:.1f}% - Check risk"
    )
```

### Trade Event Notifications

```python
# Trade started
await manager.send_info(
    "🚀 New Trade Started\n"
    f"Coin: BTC\n"
    f"Entry: $50,000\n"
    f"Quantity: 0.01 BTC"
)

# DCA executed
await manager.send_info(
    "📊 DCA Executed\n"
    f"Coin: BTC\n"
    f"Level: -5%\n"
    f"Price: $47,500"
)

# Trade completed
await manager.send_info(
    "✅ Trade Completed\n"
    f"Coin: BTC\n"
    f"Profit: +4.0% ($40.00)"
)

# Margin alert
await manager.send_critical(
    "🚨 Margin Alert\n"
    f"Coin: ETH\n"
    f"Loss: -15%\n"
    f"Warning: Approaching max loss"
)
```

## Configuration

### Configuration File

Configuration is stored in `hub_data/notification_config.json`:

```json
{
  "enabled": true,
  "platforms": {
    "email": true,
    "discord": true,
    "telegram": true
  },
  "email_address": "your.email@gmail.com",
  "email_app_password": "your-app-password",
  "discord_webhook_url": "https://discord.com/api/webhooks/...",
  "telegram_bot_token": "your-bot-token",
  "telegram_chat_id": "your-chat-id",
  "rate_limit_emails_per_minute": 5,
  "rate_limit_discord_per_minute": 10,
  "rate_limit_telegram_per_minute": 10,
  "level_platforms": {
    "info": {
      "email": true,
      "discord": true,
      "telegram": true
    },
    "warning": {
      "email": true,
      "discord": true,
      "telegram": true
    },
    "error": {
      "email": true,
      "discord": true,
      "telegram": true
    },
    "critical": {
      "email": true,
      "discord": true,
      "telegram": true
    }
  }
}
```

### Platform-Specific Settings

Configure which platforms receive which notification levels:

```python
config = NotificationConfig()
config.level_platforms = {
    "info": {"email": False, "discord": True, "telegram": True},
    "warning": {"email": False, "discord": True, "telegram": True},
    "error": {"email": True, "discord": True, "telegram": True},
    "critical": {"email": True, "discord": True, "telegram": True}
}
manager = NotificationManager(config)
```

### Rate Limiting

Adjust rate limits per platform:

```python
config = NotificationConfig(
    rate_limit_emails_per_minute=5,
    rate_limit_discord_per_minute=10,
    rate_limit_telegram_per_minute=10
)
manager = NotificationManager(config)
```

## CLI Commands

### Test Notifications

```bash
python pt_notifications.py test
```

### View Statistics

```bash
# All time statistics
python pt_notifications.py stats

# Last 7 days
python pt_notifications.py stats --days 7

# Last 30 days
python pt_notifications.py stats --days 30
```

### List Recent Notifications

```bash
# List 20 most recent notifications
python pt_notifications.py list

# Filter by level
python pt_notifications.py list --level error

# Filter by platform
python pt_notifications.py list --platform discord

# Custom limit
python pt_notifications.py list --limit 50
```

### Configure

```bash
# Show current configuration
python pt_notifications.py config

# Set email
python pt_notifications.py config --email your@email.com

# Set Discord webhook
python pt_notifications.py config --discord https://discord.com/api/webhooks/...

# Set Telegram
python pt_notifications.py config --telegram-token YOUR_TOKEN
python pt_notifications.py config --telegram-chat YOUR_CHAT_ID
```

## Statistics and Analytics

All notifications are logged to `hub_data/notifications.db`.

### Access Statistics Programmatically

```python
manager = NotificationManager()

# Get statistics
stats = manager.get_statistics()
print(f"Total: {stats['total']}")
print(f"Success Rate: {stats['success_rate']:.1f}%")

# Print formatted statistics
manager.print_statistics()

# Get recent notifications
notifications = manager.get_notifications(limit=10)
for n in notifications:
    print(f"{n.timestamp} - {n.level}: {n.message}")
```

### Statistics Output

```
============================================================
POWERTRADER AI - NOTIFICATION STATISTICS
============================================================

Period: All time
----------------------------------------
Total Notifications:           156
Successful:                    148
Failed:                          8
Success Rate:                  94.9%

BY LEVEL
----------------------------------------
INFO           85 sent   97.6% success
WARNING        42 sent   95.2% success
ERROR          20 send   90.0% success
CRITICAL        9 sent   88.9% success

BY PLATFORM
----------------------------------------
EMAIL          50 sent   92.0% success
DISCORD        58 sent   96.6% success
TELEGRAM       48 sent   95.8% success

============================================================
```

## Notification Levels

| Level | Email | Discord | Telegram | Color |
|-------|-------|---------|----------|-------|
| INFO | ✓ | ✓ | ✓ | Blue |
| WARNING | ✓ | ✓ | ✓ | Orange |
| ERROR | ✓ | ✓ | ✓ | Red |
| CRITICAL | ✓ | ✓ | ✓ | Dark Red |

## Error Handling

The notification system includes comprehensive error handling:

- Failed notifications are logged with error details
- Graceful fallback to configured platforms
- Rate limit protection
- Platform availability checks

```python
results = await manager.send("Test message")
# Returns: {"email": True, "discord": True, "telegram": False}

# Check for failures
for platform, success in results.items():
    if not success:
        print(f"Failed to send to {platform}")
```

## Examples

See `pt_notifications_examples.py` for comprehensive examples:

1. Basic Usage
2. Specific Platforms
3. Rate Limiting
4. Custom Configuration
5. Platform-Specific Levels
6. Notifications with Metadata
7. Statistics and History
8. Error Handling
9. Non-Blocking Notifications
10. Synchronous Wrapper
11. Integration with pt_analytics.py
12. Trade Event Notifications
13. Daily Trading Report

Run examples:

```python
python pt_notifications_examples.py
```

## Security Best Practices

1. **Never commit credentials** to version control
2. **Use app passwords** instead of regular passwords for email
3. **Rotate API keys** regularly
4. **Limit webhook permissions** in Discord
5. **Restrict bot permissions** in Telegram
6. **Monitor notification logs** for unusual activity

## Troubleshooting

### Email Not Working

- Ensure 2FA is enabled on Gmail account
- Generate a new App Password (old ones may expire)
- Check network connectivity
- Verify email address format

### Discord Not Working

- Verify webhook URL is correct
- Check webhook has message permissions
- Ensure server/channel still exists
- Check rate limits

### Telegram Not Working

- Verify bot token is correct
- Check bot is started and has proper permissions
- Ensure chat ID is correct
- Check bot is not blocked by user

### Notifications Not Sending

- Check global `enabled` setting in config
- Verify platform-specific `enabled` settings
- Check rate limits (may be temporarily blocked)
- Review notification logs in database

## Performance Considerations

- Notifications are sent asynchronously to avoid blocking
- Rate limiting prevents API bans
- Database operations use context managers for proper cleanup
- Failed notifications are logged but don't crash the system

## API Reference

See the full API documentation in `pt_notifications.py` for all available methods and parameters.

## Contributing

When adding new notification platforms or features:

1. Follow the existing `BaseNotifier` pattern
2. Implement `is_available()` and `send()` methods
3. Add rate limiting support
4. Log all attempts to the database
5. Update configuration schema
6. Add examples to `pt_notifications_examples.py`

## License

This notification system is part of PowerTrader AI, released under the Apache 2.0 license.
