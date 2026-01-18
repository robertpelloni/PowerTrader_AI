"""
Structured Logging System for PowerTrader AI

This module provides structured JSON logging across all modules with
log rotation, retention policies, and integration with notification system.

Author: PowerTrader AI Team
Version: 2.0.0
Created: 2026-01-18
License: Apache 2.0
"""

import logging
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
from logging.handlers import RotatingFileHandler, QueueHandler
import threading


@dataclass
class LogEntry:
    timestamp: str
    level: str
    module: str
    function: str
    message: str
    extra: Optional[Dict[str, Any]] = None


@dataclass
class LogConfig:
    log_level: str = "INFO"
    log_file: str = "hub_data/powertrader.log"
    max_log_size_mb: int = 10
    backup_log_count: int = 5
    enable_console: bool = True
    enable_json: bool = True
    log_to_database: bool = False
    critical_notification: bool = True


class StructuredFormatter(logging.Formatter):
    """Custom formatter for structured JSON logging."""

    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "module": record.name,
            "function": record.funcName,
            "line": record.lineno,
            "message": record.getMessage(),
        }

        if hasattr(record, "extra"):
            log_entry["extra"] = record.extra

        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_entry)


class ConsoleFormatter(logging.Formatter):
    """Human-readable formatter for console output."""

    def format(self, record: logging.LogRecord) -> str:
        timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        level = record.levelname
        module = record.name
        function = record.funcName
        message = record.getMessage()

        color_map = {
            "DEBUG": "\033[36m",
            "INFO": "\033[32m",
            "WARNING": "\033[33m",
            "ERROR": "\033[31m",
            "CRITICAL": "\033[35m",
        }
        reset = "\033[0m"

        level_color = color_map.get(level, "")

        log_str = (
            f"{timestamp} {level_color}[{level}]{reset} [{module}.{function}] {message}"
        )

        if record.exc_info:
            log_str += f"\n{self.formatException(record.exc_info)}"

        return log_str


class CriticalLogHandler(logging.Handler):
    """Handler that triggers notifications for critical logs."""

    def __init__(self, callback=None):
        super().__init__()
        self.callback = callback

    def emit(self, record: logging.LogRecord):
        if record.levelno >= logging.CRITICAL and self.callback:
            log_entry = {
                "timestamp": datetime.utcnow().isoformat(),
                "level": record.levelname,
                "module": record.name,
                "message": record.getMessage(),
            }
            self.callback(log_entry)


class StructuredLogger:
    """Structured JSON logger with rotation and retention policies."""

    _instances = {}
    _lock = threading.Lock()

    def __new__(cls, name: str, *args, **kwargs):
        with cls._lock:
            if name not in cls._instances:
                cls._instances[name] = super(StructuredLogger, cls).__new__(cls)
            return cls._instances[name]

    def __init__(self, name: str, config: Optional[LogConfig] = None):
        self.name = name
        self.config = config or LogConfig()
        self.logger = logging.getLogger(name)
        self.logger.setLevel(
            getattr(logging, self.config.log_level.upper(), logging.INFO)
        )
        self.logger.propagate = False

        self._setup_handlers()

    def _setup_handlers(self) -> None:
        """Setup all handlers for the logger."""
        self.logger.handlers.clear()

        log_path = Path(self.config.log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        if self.config.enable_json:
            file_handler = RotatingFileHandler(
                log_path,
                maxBytes=self.config.max_log_size_mb * 1024 * 1024,
                backupCount=self.config.backup_log_count,
            )
            file_handler.setFormatter(StructuredFormatter())
            self.logger.addHandler(file_handler)

        if self.config.enable_console:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setFormatter(ConsoleFormatter())
            self.logger.addHandler(console_handler)

    def _critical_callback(self, log_entry: Dict[str, Any]) -> None:
        """Callback for critical log notifications."""
        if self.config.critical_notification:
            try:
                from pt_notifications import (
                    NotificationManager,
                    NotificationConfig,
                    NotificationLevel,
                )

                notification_config = NotificationConfig()
                manager = NotificationManager(notification_config)

                message = f"[CRITICAL] [{log_entry['module']}] {log_entry['message']}"

                manager.send_notification(
                    message=message, level=NotificationLevel.CRITICAL
                )
            except Exception as e:
                pass

    def enable_critical_notifications(self, callback=None) -> None:
        """Enable critical log notifications."""
        self._remove_critical_handler()

        if callback is None:
            callback = self._critical_callback

        handler = CriticalLogHandler(callback)
        handler.setLevel(logging.CRITICAL)
        self.logger.addHandler(handler)

    def disable_critical_notifications(self) -> None:
        """Disable critical log notifications."""
        self._remove_critical_handler()

    def _remove_critical_handler(self) -> None:
        """Remove critical log handler if exists."""
        for handler in self.logger.handlers[:]:
            if isinstance(handler, CriticalLogHandler):
                self.logger.removeHandler(handler)
                break

    def debug(self, msg: str, *args, extra: Optional[Dict[str, Any]] = None) -> None:
        """Log debug message."""
        self.logger.debug(msg, *args, extra={"extra": extra})

    def info(self, msg: str, *args, extra: Optional[Dict[str, Any]] = None) -> None:
        """Log info message."""
        self.logger.info(msg, *args, extra={"extra": extra})

    def warning(self, msg: str, *args, extra: Optional[Dict[str, Any]] = None) -> None:
        """Log warning message."""
        self.logger.warning(msg, *args, extra={"extra": extra})

    def error(
        self, msg: str, *args, extra: Optional[Dict[str, Any]] = None, exc_info=None
    ) -> None:
        """Log error message."""
        self.logger.error(msg, *args, extra={"extra": extra}, exc_info=exc_info)

    def critical(
        self, msg: str, *args, extra: Optional[Dict[str, Any]] = None, exc_info=None
    ) -> None:
        """Log critical message."""
        self.logger.critical(msg, *args, extra={"extra": extra}, exc_info=exc_info)

    def trade(
        self, symbol: str, action: str, details: Optional[Dict[str, Any]] = None
    ) -> None:
        """Log trade event."""
        log_entry = {
            "type": "trade",
            "symbol": symbol,
            "action": action,
            "details": details or {},
        }
        self.info(f"Trade: {action} for {symbol}", extra=log_entry)

    def prediction(
        self,
        symbol: str,
        timeframe: str,
        signal: str,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Log prediction event."""
        log_entry = {
            "type": "prediction",
            "symbol": symbol,
            "timeframe": timeframe,
            "signal": signal,
            "details": details or {},
        }
        self.info(f"Prediction: {signal} for {symbol} ({timeframe})", extra=log_entry)

    def api_call(
        self,
        api_name: str,
        endpoint: str,
        status: str,
        response_time_ms: Optional[float] = None,
    ) -> None:
        """Log API call."""
        log_entry = {
            "type": "api_call",
            "api": api_name,
            "endpoint": endpoint,
            "status": status,
            "response_time_ms": response_time_ms,
        }
        self.info(f"API: {api_name} {endpoint} - {status}", extra=log_entry)

    def set_level(self, level: str) -> None:
        """Change log level."""
        try:
            new_level = getattr(logging, level.upper(), logging.INFO)
            self.logger.setLevel(new_level)
            self.config.log_level = level.upper()
        except AttributeError:
            self.warning(f"Invalid log level: {level}")

    def get_level(self) -> str:
        """Get current log level."""
        return self.config.log_level

    def get_recent_logs(self, count: int = 100) -> List[LogEntry]:
        """Get recent log entries from file."""
        log_path = Path(self.config.log_file)
        if not log_path.exists():
            return []

        entries = []

        try:
            with open(log_path, "r", encoding="utf-8") as f:
                lines = f.readlines()[-count:]

                for line in lines:
                    try:
                        data = json.loads(line.strip())
                        entries.append(LogEntry(**data))
                    except json.JSONDecodeError:
                        continue
        except Exception as e:
            self.error(f"Error reading log file: {e}")

        return entries

    def search_logs(
        self, query: str, level: Optional[str] = None, module: Optional[str] = None
    ) -> List[LogEntry]:
        """Search logs by query."""
        log_path = Path(self.config.log_file)
        if not log_path.exists():
            return []

        entries = []

        try:
            with open(log_path, "r", encoding="utf-8") as f:
                for line in f:
                    try:
                        data = json.loads(line.strip())

                        if level and data.get("level") != level.upper():
                            continue
                        if (
                            module
                            and module.lower() not in data.get("module", "").lower()
                        ):
                            continue
                        if query.lower() not in json.dumps(data).lower():
                            continue

                        entries.append(LogEntry(**data))
                    except json.JSONDecodeError:
                        continue
        except Exception as e:
            self.error(f"Error searching log file: {e}")

        return entries[-100:]

    @staticmethod
    def get_all_loggers() -> List[str]:
        """Get all active logger names."""
        return list(StructuredLogger._instances.keys())

    @staticmethod
    def cleanup_old_logs(config: LogConfig) -> int:
        """Clean up old log files beyond retention policy."""
        log_path = Path(config.log_file)
        if not log_path.exists():
            return 0

        try:
            backup_files = sorted(
                log_path.parent.glob(f"{log_path.name}.*"),
                key=lambda x: x.stat().st_mtime,
            )

            files_to_delete = backup_files[: -config.backup_log_count]
            deleted_count = 0

            for file in files_to_delete:
                file.unlink()
                deleted_count += 1

            return deleted_count
        except Exception as e:
            print(f"Error cleaning up old logs: {e}")
            return 0


class LogViewer:
    """Log viewer for dashboard integration."""

    @staticmethod
    def get_log_summary(count: int = 50) -> Dict[str, Any]:
        """Get summary of recent logs."""
        all_entries = []

        for logger_name in StructuredLogger.get_all_loggers():
            logger_instance = StructuredLogger._instances[logger_name]
            if isinstance(logger_instance, StructuredLogger):
                entries = logger_instance.get_recent_logs(count)
                all_entries.extend(entries)

        all_entries.sort(key=lambda x: x.timestamp, reverse=True)

        summary = {
            "total_entries": len(all_entries),
            "by_level": {},
            "by_module": {},
            "recent_critical": [],
            "recent_errors": [],
        }

        for entry in all_entries:
            level = entry.level
            summary["by_level"][level] = summary["by_level"].get(level, 0) + 1

            module = entry.module
            summary["by_module"][module] = summary["by_module"].get(module, 0) + 1

            if level == "CRITICAL":
                if len(summary["recent_critical"]) < 10:
                    summary["recent_critical"].append(entry)

            if level == "ERROR":
                if len(summary["recent_errors"]) < 10:
                    summary["recent_errors"].append(entry)

        return summary

    @staticmethod
    def get_log_entries(
        count: int = 100, level: Optional[str] = None, module: Optional[str] = None
    ) -> List[LogEntry]:
        """Get log entries for display."""
        all_entries = []

        for logger_name in StructuredLogger.get_all_loggers():
            logger_instance = StructuredLogger._instances[logger_name]
            if isinstance(logger_instance, StructuredLogger):
                if level or module:
                    entries = logger_instance.search_logs(
                        query="", level=level, module=module
                    )
                    all_entries.extend(entries[:count])
                else:
                    entries = logger_instance.get_recent_logs(count)
                    all_entries.extend(entries)

        all_entries.sort(key=lambda x: x.timestamp, reverse=True)

        return all_entries[:count]


def setup_logging(config: LogConfig) -> None:
    """Setup structured logging for the application."""
    log_path = Path(config.log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    StructuredLogger.cleanup_old_logs(config)

    main_logger = StructuredLogger("main", config)
    trader_logger = StructuredLogger("trader", config)
    thinker_logger = StructuredLogger("thinker", config)
    analytics_logger = StructuredLogger("analytics", config)
    notifications_logger = StructuredLogger("notifications", config)
    exchanges_logger = StructuredLogger("exchanges", config)
    volume_logger = StructuredLogger("volume", config)
    correlation_logger = StructuredLogger("correlation", config)
    position_sizing_logger = StructuredLogger("position_sizing", config)

    main_logger.enable_critical_notifications()


def get_logger(name: str) -> StructuredLogger:
    """Get or create a logger by name."""
    if name in StructuredLogger._instances:
        return StructuredLogger._instances[name]

    from pt_config import get_config

    config = get_config()
    log_config = LogConfig(
        log_level=config.get().system.log_level,
        log_file=config.get().system.log_file,
        max_log_size_mb=config.get().system.max_log_size_mb,
        backup_log_count=config.get().system.backup_log_count,
        enable_console=config.get().system.debug_mode,
        enable_json=True,
        critical_notification=config.get().system.log_level.upper() == "CRITICAL",
    )

    return StructuredLogger(name, log_config)


def main():
    """Main function for testing structured logging system."""
    import tempfile
    import time

    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        tmpdir.mkdir(exist_ok=True)

        log_file = tmpdir / "test.log"
        config = LogConfig(
            log_level="DEBUG",
            log_file=str(log_file),
            max_log_size_mb=1,
            backup_log_count=3,
            enable_console=True,
            enable_json=True,
            critical_notification=False,
        )

        setup_logging(config)

        main_logger = StructuredLogger("main", config)
        trader_logger = StructuredLogger("trader", config)
        api_logger = StructuredLogger("api", config)

        print("Testing Structured Logging System...")

        print("\n--- Basic Logging ---")
        main_logger.debug("Debug message test")
        main_logger.info("Info message test")
        main_logger.warning("Warning message test")
        main_logger.error("Error message test")

        print("\n--- Trade Logging ---")
        main_logger.trade(
            "BTC", "BUY", {"price": 50000, "quantity": 0.001, "total": 50.0}
        )
        main_logger.trade("ETH", "SELL", {"price": 3000, "quantity": 0.01, "pnl": 25.0})

        print("\n--- Prediction Logging ---")
        main_logger.prediction(
            "BTC", "1hour", "LONG", {"long_level": 3, "short_level": 0}
        )
        main_logger.prediction(
            "ETH", "4hour", "SHORT", {"long_level": 1, "short_level": 2}
        )

        print("\n--- API Call Logging ---")
        main_logger.api_call("KuCoin", "/api/v1/market/stats", "SUCCESS", 250.5)
        main_logger.api_call("Binance", "/api/v3/klines", "ERROR", 1200.0)

        print("\n--- Extra Data Logging ---")
        main_logger.info(
            "Trade executed with extra data",
            extra={"trade_id": "T001", "timestamp": "2026-01-18T12:00:00Z"},
        )

        print("\n--- Critical Log Notification Test ---")
        print("Enabling critical notifications (no real notification will be sent)...")
        main_logger.critical("Critical error occurred!", exc_info=True)

        time.sleep(1)

        print("\n--- Log Search ---")
        api_logger.api_call("KuCoin", "/api/v1/market/stats", "SUCCESS")
        api_logger.api_call("KuCoin", "/api/v1/orders", "ERROR")

        search_results = main_logger.search_logs(query="api")
        print(f"\nFound {len(search_results)} entries matching 'api':")
        for entry in search_results[:5]:
            print(f"  [{entry.level}] {entry.module}: {entry.message}")

        print("\n--- Recent Logs ---")
        recent_logs = main_logger.get_recent_logs(count=5)
        print(f"\nRecent 5 log entries:")
        for entry in recent_logs:
            print(f"  [{entry.level}] {entry.module}: {entry.message}")

        print("\n--- Log Summary ---")
        summary = LogViewer.get_log_summary(count=20)
        print(f"\nTotal entries: {summary['total_entries']}")
        print(f"Entries by level: {summary['by_level']}")
        print(f"Entries by module: {summary['by_module']}")

        print("\n--- Log File Check ---")
        if log_file.exists():
            with open(log_file, "r") as f:
                lines = f.readlines()
                print(f"\nLog file has {len(lines)} lines")
                print(f"\nLast 3 log entries:")
                for line in lines[-3:]:
                    print(f"  {line.strip()}")
        else:
            print(f"\nLog file does not exist: {log_file}")

        print("\n--- Structured Logging System Test Complete ---")


if __name__ == "__main__":
    main()
