#!/usr/bin/env python3
"""
PowerTrader AI - Notification System
========================================
Unified notification interface supporting Email, Discord, and Telegram.
Simplified for stability and ease of use.

Usage:
    import pt_notifications
    config = NotificationConfig.from_file("notifications.json")
    
    mgr = NotificationManager(config)
    
    # Send a notification
    mgr.notify(
        title="Trade Alert",
        message="BTC entry executed at $50000",
        level="info",
        platforms=["email"]
    )

if __name__ == "__main__":
    main()