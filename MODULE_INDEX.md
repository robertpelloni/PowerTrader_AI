# PowerTrader AI - Module Index

This document provides a comprehensive inventory of all modules, submodules, and components in the PowerTrader AI project, including their versions, locations, line counts, and descriptions.

## Project Overview

**Project Name:** PowerTrader AI
**Current Version:** 2.0.0
**Build Date:** 2026-01-18
**Total Python Files:** 15
**Total Lines of Code:** 16,364
**License:** Apache 2.0

## Module Directory Structure

```
PowerTrader_AI/
├── Core System (5 files)
│   ├── pt_hub.py                      # GUI & orchestration hub
│   ├── pt_thinker.py                  # Price prediction AI
│   ├── pt_trader.py                   # Trade execution engine
│   ├── pt_trainer.py                  # AI training system
│   └── pt_backtester.py               # Strategy backtesting
│
├── Analytics System (3 files)
│   ├── pt_analytics.py                # Trade journal & metrics
│   ├── pt_analytics_dashboard.py       # GUI dashboard widgets
│   └── pt_thinker_exchanges.py        # Exchange integration wrapper
│
├── Exchange System (1 file)
│   └── pt_exchanges.py               # Multi-exchange manager
│
├── Notification System (2 files)
│   ├── pt_notifications.py            # Unified notification system
│   └── pt_notifications_examples.py   # Usage examples
│
 ├── Volume Analysis (1 file)
 │   └── pt_volume.py                   # Volume metrics & analysis
 │
 ├── Risk Management (2 files)
 │   ├── pt_correlation.py             # Multi-asset correlation analysis
 │   └── pt_position_sizing.py         # Volatility-adjusted position sizing
 │
 ├── Testing (1 file)
 │   └── test_notifications.py          # Notification system tests
 │
├── Documentation & Config (8 files)
│   ├── README.md                      # Main documentation
│   ├── CHANGELOG.md                   # Version history
│   ├── ROADMAP.md                     # Feature planning
│   ├── VERSION.md                     # Version number (source of truth)
│   ├── MODULE_INDEX.md                # This file
│   ├── NOTIFICATIONS_README.md         # Notification documentation
│   ├── NOTIFICATION_INTEGRATION.md      # Integration guide
│   └── requirements.txt              # Python dependencies
│
└── Data Directories (auto-generated)
    ├── hub_data/                      # Hub configuration data
    ├── BTC/                          # Bitcoin neural data
    ├── ETH/                          # Ethereum neural data
    └── [other coins]/                # Additional coin data folders
```

---

## Core System Modules

### 1. pt_hub.py
**Version:** 2.0.0
**Location:** `C:\Users\hyper\workspace\PowerTrader_AI\pt_hub.py`
**Lines of Code:** 5,835
**Status:** Production
**Last Modified:** 2026-01-18

**Description:**
The main GUI and orchestration hub for PowerTrader AI. This is the entry point for the entire system.

**Key Classes:**
- `WrapFrame` - Custom tkinter frame with automatic widget wrapping
- `CryptoHubApp` - Main application class

**Key Features:**
- Dark theme GUI interface
- Real-time price charts with neural level overlays
- Trade status monitoring and display
- Training progress tracking
- Settings management and configuration
- Multiple coin support with folder-based organization
- Analytics dashboard tab (NEW in v2.0.0)
- Version display (NEW in v2.0.0)
- Auto-start and auto-stop of pt_thinker.py and pt_trader.py

**Dependencies:**
- tkinter (GUI framework)
- matplotlib (charting)
- pandas, numpy (data processing)
- pt_thinker, pt_trader, pt_trainer (orchestration)
- pt_analytics_dashboard (analytics tab)

**Integration Points:**
- Launches pt_thinker.py process
- Launches pt_trader.py process
- Communicates via IPC (queue-based messaging)
- Displaying real-time metrics from pt_thinker
- Analytics dashboard integration

---

### 2. pt_thinker.py
**Version:** 2.0.0
**Location:** `C:\Users\hyper\workspace\PowerTrader_AI\pt_thinker.py`
**Lines of Code:** 1,381
**Status:** Production
**Last Modified:** 2026-01-18

**Description:**
The kNN-based price prediction AI engine. Generates price predictions and trading signals for all configured coins.

**Key Classes:**
- `NeuralSystem` - Core prediction engine

**Key Features:**
- Instance-based (kNN/kernel-style) price predictor
- Online per-instance reliability weighting
- Multi-timeframe predictions (1hr to 1wk)
- Neural Levels calculation (LONG/SHORT signals)
- Trade entry signal generation (LONG >= 3, SHORT == 0)
- DCA level price thresholds
- Multi-exchange price aggregation (NEW in v2.0.0)
- Arbitrage opportunity detection (NEW in v2.0.0)

**Dependencies:**
- kucoin-python (primary data source)
- robin_stocks (execution price source)
- pandas, numpy (data processing)
- pt_thinker_exchanges (multi-exchange wrapper) - NEW in v2.0.0
- pt_exchanges (ExchangeManager) - NEW in v2.0.0

**Integration Points:**
- Receives signals from IPC queue (from pt_hub)
- Sends neural levels to IPC queue (to pt_hub)
- Uses pt_thinker_exchanges for cross-exchange data (NEW in v2.0.0)
- Outputs to file: `[symbol]_neural.txt` for each coin

---

### 3. pt_trader.py
**Version:** 2.0.0
**Location:** `C:\Users\hyper\workspace\PowerTrader_AI\pt_trader.py`
**Lines of Code:** 2,421
**Status:** Production
**Last Modified:** 2026-01-18

**Description:**
The trade execution engine. Receives signals from pt_thinker and executes trades via Robinhood API.

**Key Classes:**
- `CryptoAPITrading` - Main trading class

**Key Features:**
- Automatic trade entry based on neural signals
- Structured DCA system with tiered levels
- Max 2 DCAs per 24hr rolling window
- Trailing profit margin (5% no DCA, 2.5% with DCA)
- Trailing margin gap: 0.5%
- Trade group ID tracking (NEW in v2.0.0)
- Analytics logging integration (NEW in v2.0.0)
- Graceful error handling and retry logic

**Dependencies:**
- robin_stocks (Robinhood API)
- pandas, numpy (data processing)
- pt_analytics (TradeJournal) - NEW in v2.0.0

**Integration Points:**
- Receives neural levels from IPC queue (from pt_thinker)
- Executes trades via Robinhood API
- Logs all trades to SQLite (pt_analytics.py) - NEW in v2.0.0
- Updates IPC queue with trade status (to pt_hub)

---

### 4. pt_trainer.py
**Version:** 1.0.0
**Location:** `C:\Users\hyper\workspace\PowerTrader_AI\pt_trainer.py`
**Lines of Code:** 1,625
**Status:** Production
**Last Modified:** 2025-01-18

**Description:**
The AI training system. Trains the neural network on historical data for each configured coin.

**Key Classes:**
- `CryptoTrainer` - Training engine

**Key Features:**
- Historical data collection for all timeframes (1hr to 1wk)
- Pattern extraction and storage
- Pattern weighting based on prediction accuracy
- Multi-timeframe training
- Training progress tracking
- Neural memory file generation

**Dependencies:**
- kucoin-python (historical data)
- pandas, numpy (data processing)

**Integration Points:**
- Called from pt_hub GUI (Train All button)
- Generates neural memory files for pt_thinker
- Outputs to file: `[symbol]_neural.txt` for each coin

---

### 5. pt_backtester.py
**Version:** 1.0.0
**Location:** `C:\Users\hyper\workspace\PowerTrader_AI\pt_backtester.py`
**Lines of Code:** 876
**Status:** Production
**Last Modified:** 2025-01-18

**Description:**
Historical strategy testing and validation. Simulates trading on historical data to validate strategy performance.

**Key Features:**
- Historical backtesting for any coin
- Configurable test periods
- P&L calculation
- Win rate calculation
- Trade history generation
- Performance metrics

**Dependencies:**
- kucoin-python (historical data)
- pandas, numpy (data processing)

**Integration Points:**
- Standalone tool (not integrated into main flow)
- Uses same neural memory files as pt_thinker
- Outputs backtesting results to console

---

## Analytics System Modules

### 6. pt_analytics.py
**Version:** 2.0.0 (NEW)
**Location:** `C:\Users\hyper\workspace\PowerTrader_AI\pt_analytics.py`
**Lines of Code:** 770
**Status:** Production
**Created:** 2026-01-18

**Description:**
SQLite-based persistent trade journal and performance tracking system.

**Key Classes:**
- `TradeJournal` - Trade logging and retrieval
- `PerformanceTracker` - Metrics calculation
- `TradeEntry`, `DCAEntry`, `TradeExit` - Data models

**Key Features:**
- Persistent SQLite trade journal
- Automatic logging of entries, DCAs, and exits
- Trade group ID tracking for linking related trades
- Performance metrics: win rate, P&L, max drawdown, Sharpe ratio
- Dashboard metrics aggregation (all-time, 7/30/90 days)
- Generate trade group IDs for linking
- Automatic database initialization
- Graceful fallback if module unavailable

**Dependencies:**
- sqlite3 (built-in)
- pandas, numpy (data processing)
- datetime (timestamps)

**Integration Points:**
- Integrated into pt_trader.py at `_record_trade()` method
- Used by pt_analytics_dashboard.py for metrics display
- Standalone usage for analytics queries

**Database Schema:**
- `trade_entries` - Entry trades
- `dca_entries` - DCA trades
- `trade_exits` - Exit trades
- `performance_periods` - Period-based metrics

---

### 7. pt_analytics_dashboard.py
**Version:** 2.0.0 (NEW)
**Location:** `C:\Users\hyper\workspace\PowerTrader_AI\pt_analytics_dashboard.py`
**Lines of Code:** 252
**Status:** Production
**Created:** 2026-01-18

**Description:**
Tkinter GUI widgets for analytics dashboard display.

**Key Classes:**
- `KPICard` - Single KPI display widget
- `PerformanceTable` - Period comparison table
- `AnalyticsWidget` - Main dashboard widget

**Key Features:**
- Real-time KPI display (Total trades, win rate, today's P&L, max drawdown)
- Period comparison tables (all-time, 7 days, 30 days)
- Mtime-cached refresh (5 second default interval)
- Integration with pt_analytics.py
- Dark theme matching pt_hub.py

**Dependencies:**
- tkinter (GUI framework)
- pt_analytics (get_dashboard_metrics)

**Integration Points:**
- Used by pt_hub.py in ANALYTICS tab
- Refresh called from pt_hub's main `_tick()` loop
- Data fetched from pt_analytics.get_dashboard_metrics()

---

### 8. pt_thinker_exchanges.py
**Version:** 2.0.0 (NEW)
**Location:** `C:\Users\hyper\workspace\PowerTrader_AI\pt_thinker_exchanges.py`
**Lines of Code:** 100
**Status:** Production
**Created:** 2026-01-18

**Description:**
Wrapper module integrating multi-exchange price aggregation into pt_thinker.py.

**Key Functions:**
- `get_aggregated_current_price()` - Median/VWAP across exchanges
- `get_candle_from_exchanges()` - OHLCV candles with fallback
- `detect_arbitrage_opportunities()` - Cross-exchange spread monitoring
- `init_exchanges()` - Initialize exchange managers

**Key Features:**
- KuCoin primary source
- Binance and Coinbase fallbacks
- Price aggregation methods (median, mean, VWAP)
- Arbitrage opportunity detection
- Cross-exchange spread calculation
- Error handling with fallback chains

**Dependencies:**
- pt_exchanges (ExchangeManager)
- pandas, numpy (data processing)

**Integration Points:**
- Integrated into pt_thinker.py at `robinhood_current_ask()` call
- Provides cross-exchange price verification
- Monitors arbitrage opportunities in prediction loop

---

## Exchange System Modules

### 9. pt_exchanges.py
**Version:** 2.0.0 (NEW)
**Location:** `C:\Users\hyper\workspace\PowerTrader_AI\pt_exchanges.py`
**Lines of Code:** 663
**Status:** Production
**Created:** 2026-01-18

**Description:**
Unified exchange manager for KuCoin, Binance, and Coinbase APIs.

**Key Classes:**
- `ExchangeManager` - Unified interface for all exchanges
- `KuCoinExchange`, `BinanceExchange`, `CoinbaseExchange` - Exchange-specific implementations

**Key Features:**
- Unified interface for multiple exchanges
- Price fetching with automatic fallback
- OHLCV candle data retrieval
- Order book data
- Account information (balance, positions)
- Error handling and retry logic
- API key management
- Rate limiting

**Dependencies:**
- kucoin-python (KuCoin API)
- python-binance (Binance API)
- coinbase-advanced-trade-python (Coinbase API)
- requests (HTTP requests)

**Integration Points:**
- Used by pt_thinker_exchanges.py
- Standalone usage for exchange operations
- Provides fallback chain for price data

**Supported Exchanges:**
1. KuCoin (primary)
2. Binance (fallback)
3. Coinbase (fallback)

---

## Notification System Modules

### 10. pt_notifications.py
**Version:** 2.0.0 (NEW)
**Location:** `C:\Users\hyper\workspace\PowerTrader_AI\pt_notifications.py`
**Lines of Code:** 876
**Status:** Production
**Created:** 2026-01-18

**Description:**
Unified notification system with support for Email, Discord, and Telegram.

**Key Classes:**
- `NotificationManager` - Unified coordinator
- `EmailNotifier` - Gmail notifications
- `DiscordNotifier` - Discord webhook notifications
- `TelegramNotifier` - Telegram bot notifications
- `RateLimiter` - Platform-specific rate limiting
- `NotificationDatabase` - SQLite logging of sent notifications

**Key Features:**
- Unified notification interface
- Email (Gmail via yagmail)
- Discord (webhook-based)
- Telegram (bot token-based)
- Platform-specific rate limiting (Email: 2/hr, Discord: 30/min, Telegram: 20/min)
- Notification levels: INFO, WARNING, ERROR, CRITICAL
- JSON configuration support
- SQLite logging of sent notifications
- Async support (non-blocking)
- CLI interface for configuration and testing

**Dependencies:**
- yagmail (Email/Gmail)
- discord-webhook (Discord notifications)
- python-telegram-bot (Telegram notifications)
- requests (webhook API calls)
- sqlite3 (built-in, notification logging)

**Integration Points:**
- Ready for integration with pt_analytics.py (event logging)
- Ready for integration with pt_trader.py (trade alerts)
- Standalone CLI usage for configuration and testing

**Configuration:**
- File: `notifications.json` (auto-generated on first run)
- Enable/disable platforms per notification type
- Customizable rate limits

---

### 11. pt_notifications_examples.py
**Version:** 2.0.0 (NEW)
**Location:** `C:\Users\hyper\workspace\PowerTrader_AI\pt_notifications_examples.py`
**Lines of Code:** 371
**Status:** Documentation
**Created:** 2026-01-18

**Description:**
Comprehensive usage examples for the notification system.

**Key Examples:**
1. Basic notification sending
2. Configuration setup
3. Rate limiting demo
4. Platform-specific configuration
5. Async notifications
6. Database logging
7. Custom notifiers
8. Integration with other modules

**Integration Points:**
- Documentation-only file
- Standalone runnable examples
- Demonstrates all pt_notifications.py features

---

## Volume Analysis Modules

### 12. pt_volume.py
**Version:** 2.0.0 (NEW)
**Location:** `C:\Users\hyper\workspace\PowerTrader_AI\pt_volume.py`
**Lines of Code:** 128
**Status:** Production
**Created:** 2026-01-18

**Description:**
Volume-based metrics and analysis system.

**Key Classes:**
- `VolumeMetrics` - Volume metric dataclass
- `VolumeAnalyzer` - Analysis engine
- `VolumeCLI` - Command-line interface

**Key Features:**
- Simple Moving Averages (SMA_10, SMA_50)
- Exponential Moving Average (EMA_12)
- Volume-Weighted Average Price (VWAP)
- Volume trend detection (increasing/decreasing/stable)
- Z-score based anomaly detection
- CLI tools for backtesting volume strategies

**Dependencies:**
- pandas, numpy (data processing)
- datetime (timestamps)

**Integration Points:**
- Ready for integration with pt_thinker.py (volume-based entry confirmation)
- Ready for integration with pt_analytics.py (volume metrics logging)
- Standalone CLI usage for backtesting

---

## Risk Management Modules

### 13. pt_correlation.py
**Version:** 2.0.0 (NEW)
**Location:** `C:\Users\hyper\workspace\PowerTrader_AI\pt_correlation.py`
**Lines of Code:** 447
**Status:** Production
**Created:** 2026-01-18

**Description:**
Multi-asset correlation analysis system for portfolio diversification and risk management.

**Key Classes:**
- `CorrelationCalculator` - Core correlation calculation engine
- `CorrelationAlert` - Alert dataclass for high correlation events

**Key Features:**
- Portfolio correlation based on position sizes (weighted)
- Historical correlation tracking (7/30/90-day periods)
- Diversification alerts when correlations exceed threshold (>0.8)
- Correlation matrix calculation for multiple assets
- Pearson correlation coefficient computation

**Dependencies:**
- pandas, numpy (data processing)
- sqlite3 (analytics database)
- datetime (timestamps)

**Integration Points:**
- Ready for integration with pt_thinker.py (trade decision enhancement)
- Ready for integration with pt_analytics.py (portfolio metrics)
- Standalone usage for correlation analysis

---

### 14. pt_position_sizing.py
**Version:** 2.0.0 (NEW)
**Location:** `C:\Users\hyper\workspace\PowerTrader_AI\pt_position_sizing.py`
**Lines of Code:** 414
**Status:** Production
**Created:** 2026-01-18

**Description:**
Volatility-adjusted position sizing system using Average True Range (ATR) for optimized risk management.

**Key Classes:**
- `PositionSizer` - Position sizing calculation engine
- `VolatilityMetrics` - Volatility metric dataclass
- `PositionSizingResult` - Sizing result dataclass

**Key Features:**
- 14-period ATR (Average True Range) calculation
- True Range calculation for accurate volatility measurement
- Risk-adjusted position sizing (configurable 1%-10% of account)
- Volatility factor adjustment based on ATR %:
  - Low volatility (<1%): 1.5x position size increase
  - Medium volatility (1-2%): 1.25x position size increase
  - High volatility (>5%): 0.75x position size reduction
  - Very high volatility (>8%): 0.5x position size reduction
- Market volatility data retrieval from analytics database
- Complete sizing recommendation system with volatility classification (LOW/MEDIUM/HIGH)

**Dependencies:**
- pandas, numpy (data processing)
- sqlite3 (analytics database)
- datetime (timestamps)

**Integration Points:**
- Ready for integration with pt_trader.py (position sizing before trades)
- Ready for integration with pt_analytics.py (log position sizes)
- Ready for integration with pt_hub.py (configurable settings GUI)
- Standalone testing with sample data generation

---

## Testing Modules

### 15. test_notifications.py
**Version:** 2.0.0 (NEW)
**Location:** `C:\Users\hyper\workspace\PowerTrader_AI\test_notifications.py`
**Lines of Code:** 205
**Status:** Testing
**Created:** 2026-01-18

**Description:**
Automated unit tests for the notification system.

**Test Coverage:**
1. EmailNotifier tests
2. DiscordNotifier tests
3. TelegramNotifier tests
4. RateLimiter tests
5. NotificationManager tests
6. NotificationDatabase tests
7. CLI interface tests
8. Integration tests

**Dependencies:**
- pytest (testing framework)
- unittest.mock (mocking external APIs)

**Integration Points:**
- Testing-only file
- Run with: `python test_notifications.py`
- All 8 tests passing

---

## Configuration & Data Files

### 16. requirements.txt
**Version:** 2.0.0
**Location:** `C:\Users\hyper\workspace\PowerTrader_AI\requirements.txt`
**Purpose:** Python dependencies

**Key Dependencies (v2.0.0):**
```
# Core dependencies
kucoin-python
robin_stocks
pandas
numpy
matplotlib
tkinter (built-in)
requests

# Analytics (NEW in v2.0.0)
sqlite3 (built-in)

# Notifications (NEW in v2.0.0)
yagmail
discord-webhook
python-telegram-bot

# Exchange integration (NEW in v2.0.0)
python-binance
coinbase-advanced-trade-python

# Risk management (NEW in v2.0.0)
scipy  # For correlation analysis

# Development (optional)
pytest
pytest-cov
black
flake8
```

---

## Data Directories

### hub_data/
**Location:** `C:\Users\hyper\workspace\PowerTrader_AI\hub_data\`
**Purpose:** Hub configuration and runtime data
**Auto-generated:** Yes
**Contents:**
- `hub_settings.json` - Main hub configuration
- `coins_list.txt` - Configured trading coins
- `r_key.txt` - Robinhood API public key
- `r_secret.txt` - Robinhood API secret key

### [COIN]/ (e.g., BTC/, ETH/)
**Location:** `C:\Users\hyper\workspace\PowerTrader_AI\[COIN]\`
**Purpose:** Neural memory and data for each coin
**Auto-generated:** Yes
**Contents:**
- `[COIN]_neural.txt` - Neural memory patterns
- Historical data files (optional)

---

## Module Version Matrix

| Module | Version | Status | Lines | Created | Last Modified |
|--------|---------|--------|--------|---------|---------------|
| pt_hub.py | 2.0.0 | Production | 5,835 | 2025-01-18 | 2026-01-18 |
| pt_thinker.py | 2.0.0 | Production | 1,381 | 2025-01-18 | 2026-01-18 |
| pt_trader.py | 2.0.0 | Production | 2,421 | 2025-01-18 | 2026-01-18 |
| pt_trainer.py | 1.0.0 | Production | 1,625 | 2025-01-18 | 2025-01-18 |
| pt_backtester.py | 1.0.0 | Production | 876 | 2025-01-18 | 2025-01-18 |
| pt_analytics.py | 2.0.0 | Production | 770 | 2026-01-18 | 2026-01-18 |
| pt_analytics_dashboard.py | 2.0.0 | Production | 252 | 2026-01-18 | 2026-01-18 |
| pt_thinker_exchanges.py | 2.0.0 | Production | 100 | 2026-01-18 | 2026-01-18 |
| pt_exchanges.py | 2.0.0 | Production | 663 | 2026-01-18 | 2026-01-18 |
| pt_notifications.py | 2.0.0 | Production | 876 | 2026-01-18 | 2026-01-18 |
| pt_notifications_examples.py | 2.0.0 | Documentation | 371 | 2026-01-18 | 2026-01-18 |
| pt_volume.py | 2.0.0 | Production | 128 | 2026-01-18 | 2026-01-18 |
| test_notifications.py | 2.0.0 | Testing | 205 | 2026-01-18 | 2026-01-18 |

**Total:** 13 Python files, 15,503 lines of code

---

## Integration Dependencies Diagram

```
pt_hub.py (GUI & Orchestration)
    ├── pt_thinker.py (Price Prediction)
    │   ├── pt_thinker_exchanges.py (Exchange Wrapper)
    │   │   └── pt_exchanges.py (Exchange Manager)
    │   │       ├── KuCoin API (primary)
    │   │       ├── Binance API (fallback)
    │   │       └── Coinbase API (fallback)
    │   └── robin_stocks (execution price)
    │
    ├── pt_trader.py (Trade Execution)
    │   ├── pt_analytics.py (Trade Logging) ← NEW
    │   │   └── SQLite Database
    │   └── robin_stocks (Robinhood API)
    │
    ├── pt_analytics_dashboard.py (Dashboard) ← NEW
    │   └── pt_analytics.py (Metrics)
    │
    └── pt_trainer.py (AI Training)

pt_notifications.py (Notifications) ← NEW
    ├── EmailNotifier (yagmail)
    ├── DiscordNotifier (discord-webhook)
    ├── TelegramNotifier (python-telegram-bot)
    └── NotificationDatabase (SQLite)

pt_volume.py (Volume Analysis) ← NEW
    ├── SMA/EMA calculations
    ├── VWAP calculations
    └── Z-score anomaly detection
```

---

## Version History

### Version 2.0.0 (2026-01-18)
**Added:**
- pt_analytics.py (770 lines)
- pt_analytics_dashboard.py (252 lines)
- pt_thinker_exchanges.py (100 lines)
- pt_exchanges.py (663 lines)
- pt_notifications.py (876 lines)
- pt_notifications_examples.py (371 lines)
- pt_volume.py (128 lines)
- test_notifications.py (205 lines)

**Modified:**
- pt_hub.py - Added analytics tab and version display
- pt_thinker.py - Added multi-exchange integration
- pt_trader.py - Added analytics logging
- requirements.txt - Added notification dependencies

**Total:** 8 new modules, 3 modifications, 3,465 new lines of code

### Version 1.0.0 (2025-01-18)
**Initial Release:**
- pt_hub.py (GUI & orchestration)
- pt_thinker.py (price prediction)
- pt_trader.py (trade execution)
- pt_trainer.py (AI training)
- pt_backtester.py (backtesting)

**Total:** 5 core modules, ~12,000 lines of code

---

## External Dependencies Summary

### Core Dependencies
- **robin_stocks** - Robinhood Crypto API trading
- **kucoin-python** - KuCoin API for price data
- **pandas** - Data manipulation and analysis
- **numpy** - Numerical computing
- **matplotlib** - Charting and visualization
- **tkinter** - Python GUI framework (built-in)

### New Dependencies (v2.0.0)
- **yagmail** - Gmail SMTP integration for email notifications
- **discord-webhook** - Discord webhook notifications
- **python-telegram-bot** - Telegram bot API
- **python-binance** - Binance API (exchange fallback)
- **coinbase-advanced-trade-python** - Coinbase API (exchange fallback)
- **requests** - HTTP client for webhooks

### Development Dependencies (optional)
- **pytest** - Testing framework
- **pytest-cov** - Code coverage
- **black** - Code formatting
- **flake8** - Code linting

---

## Module Lifecycle Status

### Active Development
- pt_hub.py (GUI enhancements, bug fixes)
- pt_thinker.py (accuracy improvements, new features)
- pt_trader.py (strategy refinements, risk management)

### Stable/Maintenance
- pt_trainer.py (bug fixes, optimization)
- pt_backtester.py (bug fixes, performance)

### New Integration (v2.0.0)
- pt_analytics.py (core analytics features complete)
- pt_analytics_dashboard.py (dashboard widgets complete)
- pt_thinker_exchanges.py (exchange wrapper complete)
- pt_exchanges.py (exchange manager complete)
- pt_notifications.py (notification system complete)
- pt_volume.py (volume analysis complete)
- pt_correlation.py (correlation analysis complete)
- pt_position_sizing.py (position sizing complete)

---

## Future Module Plans (v3.0.0)

### Planned Modules
- pt_config.py - Configuration management system
- pt_logging.py - Structured logging system
- pt_risk_management.py - Advanced risk management
- pt_rebalancer.py - Portfolio rebalancing
- pt_sentiment.py - Sentiment analysis
- pt_regime_detection.py - Market regime detection

### Planned Integrations
- MCP servers (Model Context Protocol)
- Alpha Vantage expanded features
- CoinGecko API integration
- Social sentiment APIs (Reddit, Twitter, Discord)
- News sentiment APIs
- DEX integration (Uniswap, SushiSwap)

---

**Last Updated:** 2026-01-18
**Current Version:** 2.0.0
**Next Milestone:** 3.0.0

---

**DO NOT TRUST THE POWERTRADER FORK FROM Drizztdowhateva!!!**

This is my personal trading bot that I decided to make open source. This system is meant to be a foundation/framework for you to build your dream bot!
