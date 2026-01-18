# PowerTrader AI Notification System - Integration Guide

## Files Created

1. **pt_notifications.py** (29K) - Main notification module
   - Complete implementation with Email, Discord, and Telegram support
   - Rate limiting, async support, database logging
   - CLI interface for configuration and testing

2. **pt_notifications_examples.py** (11K) - Usage examples
   - 13 comprehensive examples covering all features
   - Integration examples with pt_analytics.py
   - Trade event notifications

3. **test_notifications.py** (4.9K) - Unit tests
   - 8 automated tests for core functionality
   - Tests configuration, database, rate limiting, etc.

4. **NOTIFICATIONS_README.md** (11K) - Complete documentation
   - Setup instructions for all platforms
   - Usage examples and API reference
   - Troubleshooting guide

5. **requirements.txt** - Updated with notification dependencies
   - yagmail (Email/Gmail)
   - discord-webhook (Discord notifications)
   - python-telegram-bot (Telegram notifications)

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Test the System

```bash
# Run automated tests
python test_notifications.py

# View statistics (no config needed)
python pt_notifications.py stats

# View current configuration
python pt_notifications.py config
```

### 3. Configure Platforms

#### Email (Gmail)

```bash
python pt_notifications.py config --email your.email@gmail.com
```

Then edit `hub_data/notification_config.json` to add your app password:
```json
{
  "email_address": "your.email@gmail.com",
  "email_app_password": "your-app-password"
}
```

#### Discord

```bash
python pt_notifications.py config --discord https://discord.com/api/webhooks/YOUR_WEBHOOK
```

#### Telegram

```bash
python pt_notifications.py config --telegram-token YOUR_BOT_TOKEN
python pt_notifications.py config --telegram-chat YOUR_CHAT_ID
```

### 4. Test Notifications

```bash
python pt_notifications.py test
```

## Integration with pt_analytics.py

### Basic Integration

```python
from pt_notifications import NotificationManager
from pt_analytics import TradeJournal, PerformanceTracker

manager = NotificationManager()
journal = TradeJournal()
tracker = PerformanceTracker(journal)

# Get performance metrics
snapshot = tracker.calculate_snapshot()

# Send notifications based on performance
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
# Log trade and notify
trade_id = journal.log_entry(
    coin="BTC",
    price=50000,
    quantity=0.01,
    cost_usd=500
)

await manager.send_info(
    f"Trade started: BTC entry at $50,000\n"
    f"Trade ID: {trade_id}"
)

# On trade completion
journal.log_exit(trade_id, coin="BTC", price=52000, ...)

await manager.send_info(
    f"Trade completed: BTC\n"
    f"Profit: +4.0% ($40.00)"
)
```

## Key Features

### 1. Notification Levels

- **INFO**: Routine updates (trade executed, system status)
- **WARNING**: Alerts requiring attention (low balance, approaching limits)
- **ERROR**: Failures needing immediate action (API errors, connection issues)
- **CRITICAL**: Critical failures requiring intervention (account issues, security alerts)

### 2. Platform-Specific Routing

Configure which platforms receive which levels:

```python
config.level_platforms = {
    "info": {"email": False, "discord": True, "telegram": True},
    "warning": {"email": False, "discord": True, "telegram": True},
    "error": {"email": True, "discord": True, "telegram": True},
    "critical": {"email": True, "discord": True, "telegram": True}
}
```

### 3. Rate Limiting

Prevents API bans and spam:

```python
config = NotificationConfig(
    rate_limit_emails_per_minute=5,
    rate_limit_discord_per_minute=10,
    rate_limit_telegram_per_minute=10
)
```

### 4. Async/Non-Blocking

```python
# Send notification without blocking main logic
async def main_task():
    await manager.send_info("Processing started...")
    # Do work
    await manager.send_info("Processing completed!")

# Run with other async tasks
await asyncio.gather(
    main_task(),
    notification_task()
)
```

## Common Use Cases

### 1. Daily Reports

```python
report = f"""
📊 Daily Report
📅 {datetime.now().strftime('%Y-%m-%d')}

📈 Total Trades: {snapshot.total_trades}
✅ Winning: {snapshot.winning_trades}
❌ Losing: {snapshot.losing_trades}
📊 Win Rate: {snapshot.win_rate:.1f}%
💰 P&L: ${snapshot.total_pnl:.2f}
"""

await manager.send_info(report, platforms=["discord", "telegram"])
```

### 2. Trade Alerts

```python
# Entry
await manager.send_info(
    f"🚀 New Trade Started\n"
    f"Coin: {coin}\n"
    f"Price: ${price}\n"
    f"Quantity: {quantity}\n"
    f"Trigger: {trigger_reason}"
)

# DCA
await manager.send_info(
    f"📊 DCA Executed\n"
    f"Coin: {coin}\n"
    f"Level: {dca_level}%\n"
    f"Price: ${price}"
)

# Exit
await manager.send_info(
    f"✅ Trade Completed\n"
    f"Coin: {coin}\n"
    f"Profit: {pnl_pct:.1f}% (${pnl:.2f})\n"
    f"Holding: {holding_hours:.1f}h"
)
```

### 3. System Alerts

```python
try:
    # Trading logic
    pass
except APIConnectionError as e:
    await manager.send_error(f"API connection failed: {e}")
except InsufficientFundsError as e:
    await manager.send_critical(f"Insufficient funds: {e}")
except Exception as e:
    await manager.send_error(f"Unexpected error: {e}")
```

## Monitoring and Analytics

### View Statistics

```bash
# All time
python pt_notifications.py stats

# Last 7 days
python pt_notifications.py stats --days 7

# Last 30 days
python pt_notifications.py stats --days 30
```

### List Recent Notifications

```bash
# List 20 most recent
python pt_notifications.py list

# Filter by level
python pt_notifications.py list --level error

# Filter by platform
python pt_notifications.py list --platform discord

# Custom limit
python pt_notifications.py list --limit 50
```

### Programmatic Access

```python
manager = NotificationManager()

# Get statistics
stats = manager.get_statistics()
print(f"Success rate: {stats['success_rate']:.1f}%")

# Get recent notifications
notifications = manager.get_notifications(limit=10)
for n in notifications:
    print(f"{n.timestamp} - {n.level}: {n.message}")
```

## Configuration File

Location: `hub_data/notification_config.json`

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

## Security Notes

1. **Never commit** `hub_data/notification_config.json` to version control
2. **Use app passwords** for Gmail instead of regular passwords
3. **Rotate credentials** regularly
4. **Monitor logs** for unusual activity
5. **Limit permissions** on Discord webhooks and Telegram bots

## Troubleshooting

### Notifications Not Sending

1. Check configuration: `python pt_notifications.py config`
2. Verify credentials are correct
3. Check rate limits in config
4. Review notification logs: `python pt_notifications.py list --level error`

### Email Issues

- Ensure 2FA is enabled on Gmail
- Generate a new App Password
- Check network connectivity

### Discord Issues

- Verify webhook URL is correct
- Check webhook has message permissions
- Ensure server/channel exists

### Telegram Issues

- Verify bot token is correct
- Check bot is started
- Ensure chat ID is correct
- Check bot isn't blocked

## API Reference

See `NOTIFICATIONS_README.md` for complete API documentation and `pt_notifications_examples.py` for usage examples.

## Testing

Run automated tests to verify installation:

```bash
python test_notifications.py
```

Expected output:
```
============================================================
PowerTrader AI - Notification System Tests
============================================================
Testing configuration loading...
PASS Configuration loading works

Testing database operations...
PASS Database operations work

Testing rate limiter...
PASS Rate limiter works

Testing notification manager...
PASS Notification manager works

Testing notification levels...
PASS Notification levels work

Testing notification record...
PASS Notification record works

Testing statistics...
PASS Statistics work

Testing platform availability...
PASS Platform availability checks work

============================================================
Test Results: 8 passed, 0 failed
============================================================

PASS All tests passed!
```

## Next Steps

1. Configure at least one notification platform
2. Test notifications with `python pt_notifications.py test`
3. Integrate with your trading logic using examples from `pt_notifications_examples.py`
4. Set up daily reports and trade alerts
5. Monitor statistics regularly to ensure reliability

## Support

For issues or questions:
1. Check `NOTIFICATIONS_README.md` troubleshooting section
2. Review `pt_notifications_examples.py` for usage patterns
3. Check notification logs: `python pt_notifications.py list`
4. Verify configuration: `python pt_notifications.py config`
