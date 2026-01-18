#!/usr/bin/env python3
"""
PowerTrader AI - Volume Analysis Module
=====================================
Volume-based trade entry confirmation, analysis, and filtering.

Usage:
    # As module - integrate with pt_thinker.py and pt_trader.py
    from pt_volume import VolumeAnalyzer, VolumeFilter, add_volume_to_prediction

    # CLI for volume backtesting
    python pt_volume.py backtest BTC 2024-01-01 2024-12-31
    python pt_volume.py analyze BTC --days 30
    python pt_volume.py profile BTC
"""

import sqlite3
import json
import argparse
import sys
from datetime import datetime, timedelta
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional, Tuple, Any
from pathlib import Path
from contextlib import contextmanager
import math
from collections import deque

try:
    from kucoin.client import Market

    KUCOIN_AVAILABLE = True
except ImportError:
    KUCOIN_AVAILABLE = False
    print("[pt_volume] kucoin-python not installed. Volume data fetching limited.")

try:
    from pt_analytics import TradeJournal

    ANALYTICS_AVAILABLE = True
except ImportError:
    ANALYTICS_AVAILABLE = False
    print(
        "[pt_volume] pt_analytics module not available - volume decision logging disabled."
    )

DB_PATH = Path("hub_data/volume.db")


@dataclass
class CandleVolumeData:
    """OHLCV candle data with volume metrics."""

    timestamp: int
    open: float
    high: float
    low: float
    close: float
    volume: float

    @property
    def datetime(self) -> datetime:
        return datetime.fromtimestamp(self.timestamp)


@dataclass
class VolumeMetrics:
    """Volume metrics for a single candle."""

    timestamp: int
    volume: float
    volume_sma: float = 0.0
    volume_ema: float = 0.0
    vwap: float = 0.0
    volume_ratio: float = 1.0  # Current volume / average volume
    z_score: float = 0.0
    trend: str = "stable"  # 'increasing', 'decreasing', 'stable'
    anomaly: bool = False
    anomaly_type: str = ""  # 'high_volume', 'low_volume'


@dataclass
class VolumeProfile:
    """Volume profile over a period."""

    period: str
    avg_volume: float
    median_volume: float
    p25_volume: float
    p50_volume: float
    p75_volume: float
    p90_volume: float
    std_volume: float
    total_volume: float
    candle_count: int


@dataclass
class VolumeDecision:
    """Volume-based trade entry decision."""

    timestamp: datetime
    coin: str
    price: float
    volume: float
    metrics: VolumeMetrics
    decision: (
        str  # 'allow', 'reject_low_volume', 'reject_high_volume', 'reject_no_trend'
    )
    reason: str
    confidence: float  # 0.0 to 1.0


@dataclass
class VolumeBacktestConfig:
    """Configuration for volume-based backtesting."""

    # Volume thresholds
    min_volume_ratio: float = 0.5  # Require volume >= 50% of average
    max_volume_ratio: float = 3.0  # Reject volume > 300% of average (anomaly)

    # Z-score thresholds for anomaly detection
    high_volume_zscore: float = 2.0  # Above this = high volume anomaly
    low_volume_zscore: float = -2.0  # Below this = low volume anomaly

    # Trend requirements
    require_increasing_volume: bool = False  # Require volume to be increasing

    # VWAP confirmation
    vwap_distance_pct: float = 0.5  # Allow price within 0.5% of VWAP


class VolumeAnalyzer:
    """
    Calculates volume metrics on historical candle data.
    Supports SMA, EMA, VWAP, anomaly detection, and trend analysis.
    """

    def __init__(self, sma_periods: int = 20, ema_periods: int = 20):
        self.sma_periods = sma_periods
        self.ema_periods = ema_periods
        self.volume_history: deque = deque(maxlen=max(sma_periods, ema_periods) * 2)
        self.price_volume_history: List[Tuple[float, float]] = []

    def calculate_sma(self, values: List[float], period: int) -> float:
        """Calculate Simple Moving Average."""
        if len(values) < period:
            return sum(values) / len(values) if values else 0.0
        return sum(values[-period:]) / period

    def calculate_ema(
        self, current: float, prev_ema: Optional[float], period: int
    ) -> float:
        """Calculate Exponential Moving Average."""
        if prev_ema is None:
            return current
        multiplier = 2 / (period + 1)
        return (current * multiplier) + (prev_ema * (1 - multiplier))

    def calculate_vwap(self, prices: List[float], volumes: List[float]) -> float:
        """
        Calculate Volume-Weighted Average Price.
        VWAP = Sum(price * volume) / Sum(volume)
        """
        if not prices or not volumes or len(prices) != len(volumes):
            return 0.0

        total_pv = sum(p * v for p, v in zip(prices, volumes))
        total_volume = sum(volumes)

        return total_pv / total_volume if total_volume > 0 else 0.0

    def calculate_z_score(self, value: float, mean: float, std: float) -> float:
        """Calculate z-score for anomaly detection."""
        if std == 0:
            return 0.0
        return (value - mean) / std

    def detect_trend(self, volumes: List[float], min_periods: int = 5) -> str:
        """
        Detect volume trend direction.
        Returns: 'increasing', 'decreasing', or 'stable'
        """
        if len(volumes) < min_periods:
            return "stable"

        recent = volumes[-min_periods:]
        avg_first_half = sum(recent[: min_periods // 2]) / (min_periods // 2)
        avg_second_half = sum(recent[min_periods // 2 :]) / (
            min_periods - min_periods // 2
        )

        change_pct = (
            ((avg_second_half - avg_first_half) / avg_first_half) * 100
            if avg_first_half > 0
            else 0
        )

        if change_pct > 10:
            return "increasing"
        elif change_pct < -10:
            return "decreasing"
        return "stable"

    def analyze_candle(
        self, candle: CandleVolumeData, prev_ema: Optional[float] = None
    ) -> VolumeMetrics:
        """
        Calculate all volume metrics for a single candle.
        """
        self.volume_history.append(candle.volume)
        self.price_volume_history.append((candle.close, candle.volume))

        # Calculate SMA
        volume_sma = self.calculate_sma(list(self.volume_history), self.sma_periods)

        # Calculate EMA
        volume_ema = self.calculate_ema(candle.volume, prev_ema, self.ema_periods)

        # Calculate VWAP (using last 50 candles for VWAP window)
        vwap_window = min(50, len(self.price_volume_history))
        recent_prices = [p for p, v in self.price_volume_history[-vwap_window:]]
        recent_volumes = [v for p, v in self.price_volume_history[-vwap_window:]]
        vwap = self.calculate_vwap(recent_prices, recent_volumes)

        # Calculate volume ratio (current / SMA)
        volume_ratio = (candle.volume / volume_sma) if volume_sma > 0 else 1.0

        # Calculate z-score for anomaly detection
        volume_list = list(self.volume_history)
        if len(volume_list) >= 10:
            mean_vol = sum(volume_list) / len(volume_list)
            std_vol = math.sqrt(
                sum((v - mean_vol) ** 2 for v in volume_list) / len(volume_list)
            )
            z_score = self.calculate_z_score(candle.volume, mean_vol, std_vol)
        else:
            z_score = 0.0

        # Detect trend
        trend = self.detect_trend(volume_list)

        # Detect anomaly
        anomaly = False
        anomaly_type = ""
        if z_score > 2.5:
            anomaly = True
            anomaly_type = "high_volume"
        elif z_score < -2.5:
            anomaly = True
            anomaly_type = "low_volume"

        return VolumeMetrics(
            timestamp=candle.timestamp,
            volume=candle.volume,
            volume_sma=volume_sma,
            volume_ema=volume_ema,
            vwap=vwap,
            volume_ratio=volume_ratio,
            z_score=z_score,
            trend=trend,
            anomaly=anomaly,
            anomaly_type=anomaly_type,
        )

    def calculate_profile(self, candles: List[CandleVolumeData]) -> VolumeProfile:
        """
        Calculate volume profile statistics over a period.
        """
        if not candles:
            return VolumeProfile(
                period="unknown",
                avg_volume=0.0,
                median_volume=0.0,
                p25_volume=0.0,
                p50_volume=0.0,
                p75_volume=0.0,
                p90_volume=0.0,
                std_volume=0.0,
                total_volume=0.0,
                candle_count=0,
            )

        volumes = [c.volume for c in candles]
        volumes_sorted = sorted(volumes)
        count = len(volumes)

        avg = sum(volumes) / count
        median = volumes_sorted[count // 2]

        total = sum(volumes)
        std = (
            math.sqrt(sum((v - avg) ** 2 for v in volumes) / count)
            if count > 0
            else 0.0
        )

        p25 = volumes_sorted[int(count * 0.25)] if count >= 4 else volumes_sorted[0]
        p50 = volumes_sorted[int(count * 0.50)] if count >= 2 else volumes_sorted[0]
        p75 = volumes_sorted[int(count * 0.75)] if count >= 4 else volumes_sorted[-1]
        p90 = volumes_sorted[int(count * 0.90)] if count >= 10 else volumes_sorted[-1]

        period = f"{candles[0].datetime.date()} to {candles[-1].datetime.date()}"

        return VolumeProfile(
            period=period,
            avg_volume=avg,
            median_volume=median,
            p25_volume=p25,
            p50_volume=p50,
            p75_volume=p75,
            p90_volume=p90,
            std_volume=std,
            total_volume=total,
            candle_count=count,
        )


class VolumeFilter:
    """
    Filters trade entries based on volume confirmation.
    Only allows entries when volume confirms the price move.
    """

    def __init__(self, config: Optional[VolumeBacktestConfig] = None):
        self.config = config or VolumeBacktestConfig()

    def should_allow_entry(
        self, metrics: VolumeMetrics, price: float
    ) -> Tuple[bool, str, float]:
        """
        Determine if volume confirms the trade entry.

        Returns:
            (allow, reason, confidence)
        """
        confidence = 1.0

        # Check volume ratio
        if metrics.volume_ratio < self.config.min_volume_ratio:
            reason = f"Volume too low: {metrics.volume_ratio:.2f}x average (min: {self.config.min_volume_ratio}x)"
            confidence *= 0.3
            return False, reason, confidence

        if metrics.volume_ratio > self.config.max_volume_ratio:
            reason = f"Volume spike anomaly: {metrics.volume_ratio:.2f}x average (max: {self.config.max_volume_ratio}x)"
            confidence *= 0.2
            return False, reason, confidence

        # Check z-score anomaly
        if metrics.z_score > self.config.high_volume_zscore:
            reason = f"High volume anomaly: z-score {metrics.z_score:.2f} (threshold: {self.config.high_volume_zscore})"
            confidence *= 0.4
            return False, reason, confidence

        if metrics.z_score < self.config.low_volume_zscore:
            reason = f"Low volume anomaly: z-score {metrics.z_score:.2f} (threshold: {self.config.low_volume_zscore})"
            confidence *= 0.3
            return False, reason, confidence

        # Check trend if required
        if self.config.require_increasing_volume and metrics.trend != "increasing":
            reason = f"Volume trend not increasing: {metrics.trend}"
            confidence *= 0.6
            return False, reason, confidence

        # Check VWAP distance
        if metrics.vwap > 0:
            vwap_distance_pct = abs((price - metrics.vwap) / metrics.vwap) * 100
            if vwap_distance_pct > self.config.vwap_distance_pct:
                reason = f"Price too far from VWAP: {vwap_distance_pct:.2f}% (max: {self.config.vwap_distance_pct}%)"
                confidence *= 0.7
                return False, reason, confidence
            else:
                # Price close to VWAP is a positive signal
                confidence *= 1.2

        # All checks passed
        reason = f"Volume confirms entry: {metrics.volume_ratio:.2f}x average, trend: {metrics.trend}"
        return True, reason, min(confidence, 1.0)

    def make_decision(
        self, candle: CandleVolumeData, metrics: VolumeMetrics, coin: str
    ) -> VolumeDecision:
        """
        Make a complete volume-based entry decision.
        """
        allow, reason, confidence = self.should_allow_entry(metrics, candle.close)

        decision = "allow" if allow else "reject"
        if not allow:
            if "too low" in reason:
                decision = "reject_low_volume"
            elif "spike anomaly" in reason or "High volume anomaly" in reason:
                decision = "reject_high_volume"
            elif "trend not" in reason:
                decision = "reject_no_trend"

        return VolumeDecision(
            timestamp=datetime.now(),
            coin=coin,
            price=candle.close,
            volume=candle.volume,
            metrics=metrics,
            decision=decision,
            reason=reason,
            confidence=confidence,
        )


class VolumeDecisionLogger:
    """Logs volume-based trading decisions to database."""

    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    @contextmanager
    def _get_conn(self):
        conn = sqlite3.connect(self.db_path, detect_types=sqlite3.PARSE_DECLTYPES)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def _init_db(self):
        with self._get_conn() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS volume_decisions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TIMESTAMP NOT NULL,
                    coin TEXT NOT NULL,
                    price REAL NOT NULL,
                    volume REAL NOT NULL,
                    volume_sma REAL,
                    volume_ema REAL,
                    vwap REAL,
                    volume_ratio REAL,
                    z_score REAL,
                    trend TEXT,
                    anomaly INTEGER,
                    anomaly_type TEXT,
                    decision TEXT NOT NULL,
                    reason TEXT,
                    confidence REAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS volume_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TIMESTAMP NOT NULL,
                    coin TEXT NOT NULL,
                    timeframe TEXT NOT NULL,
                    avg_volume REAL,
                    median_volume REAL,
                    p25_volume REAL,
                    p75_volume REAL,
                    p90_volume REAL,
                    std_volume REAL,
                    total_volume REAL,
                    candle_count INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_decisions_coin ON volume_decisions(coin)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_decisions_timestamp ON volume_decisions(timestamp)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_metrics_coin ON volume_metrics(coin)"
            )

    def log_decision(self, decision: VolumeDecision) -> int:
        """Log a volume decision to database."""
        with self._get_conn() as conn:
            cursor = conn.execute(
                """
                INSERT INTO volume_decisions (
                    timestamp, coin, price, volume, volume_sma, volume_ema,
                    vwap, volume_ratio, z_score, trend, anomaly,
                    anomaly_type, decision, reason, confidence
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    decision.timestamp,
                    decision.coin,
                    decision.price,
                    decision.volume,
                    decision.metrics.volume_sma,
                    decision.metrics.volume_ema,
                    decision.metrics.vwap,
                    decision.metrics.volume_ratio,
                    decision.metrics.z_score,
                    decision.metrics.trend,
                    1 if decision.metrics.anomaly else 0,
                    decision.metrics.anomaly_type,
                    decision.decision,
                    decision.reason,
                    decision.confidence,
                ),
            )
            return cursor.lastrowid

    def log_profile(self, coin: str, timeframe: str, profile: VolumeProfile):
        """Log volume profile metrics."""
        with self._get_conn() as conn:
            conn.execute(
                """
                INSERT INTO volume_metrics (
                    timestamp, coin, timeframe, avg_volume, median_volume,
                    p25_volume, p75_volume, p90_volume, std_volume,
                    total_volume, candle_count
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    datetime.now(),
                    coin,
                    timeframe,
                    profile.avg_volume,
                    profile.median_volume,
                    profile.p25_volume,
                    profile.p75_volume,
                    profile.p90_volume,
                    profile.std_volume,
                    profile.total_volume,
                    profile.candle_count,
                ),
            )

    def get_decisions(
        self, coin: Optional[str] = None, limit: int = 100
    ) -> List[VolumeDecision]:
        """Retrieve volume decision history."""
        query = "SELECT * FROM volume_decisions WHERE 1=1"
        params = []

        if coin:
            query += " AND coin = ?"
            params.append(coin)

        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)

        with self._get_conn() as conn:
            rows = conn.execute(query, params).fetchall()

        return [
            VolumeDecision(
                timestamp=datetime.fromisoformat(r["timestamp"]),
                coin=r["coin"],
                price=r["price"],
                volume=r["volume"],
                metrics=VolumeMetrics(
                    timestamp=int(datetime.fromisoformat(r["timestamp"]).timestamp()),
                    volume=r["volume"],
                    volume_sma=r["volume_sma"] or 0.0,
                    volume_ema=r["volume_ema"] or 0.0,
                    vwap=r["vwap"] or 0.0,
                    volume_ratio=r["volume_ratio"] or 1.0,
                    z_score=r["z_score"] or 0.0,
                    trend=r["trend"] or "stable",
                    anomaly=bool(r["anomaly"]),
                    anomaly_type=r["anomaly_type"] or "",
                ),
                decision=r["decision"],
                reason=r["reason"] or "",
                confidence=r["confidence"] or 0.0,
            )
            for r in rows
        ]


# =============================================================================
# INTEGRATION HELPERS
# =============================================================================


def add_volume_to_prediction(
    coin: str, current_price: float, volume_metrics: VolumeMetrics
) -> Dict[str, Any]:
    """
    Integration helper for pt_thinker.py.
    Adds volume data to prediction output.

    Usage in pt_thinker.py:
        from pt_volume import add_volume_to_prediction

        volume_data = add_volume_to_prediction(sym, current, metrics)
        print(f"VOLUME CONFIRMATION: {volume_data['decision']}")
    """
    return {
        "coin": coin,
        "price": current_price,
        "volume": volume_metrics.volume,
        "volume_sma": volume_metrics.volume_sma,
        "volume_ema": volume_metrics.volume_ema,
        "vwap": volume_metrics.vwap,
        "volume_ratio": volume_metrics.volume_ratio,
        "z_score": volume_metrics.z_score,
        "trend": volume_metrics.trend,
        "anomaly": volume_metrics.anomaly,
        "anomaly_type": volume_metrics.anomaly_type,
        "volume_confirms": volume_metrics.volume_ratio >= 0.5
        and not volume_metrics.anomaly,
    }


def log_volume_decision_to_analytics(
    journal: TradeJournal, decision: VolumeDecision, trade_group_id: str
):
    """
    Integration helper for pt_analytics.py.
    Logs volume-based decision as a trade note.

    Usage:
        from pt_analytics import TradeJournal
        from pt_volume import log_volume_decision_to_analytics

        journal = TradeJournal()
        log_volume_decision_to_analytics(journal, decision, trade_group_id)
    """
    if not ANALYTICS_AVAILABLE:
        return

    notes = (
        f"Volume Decision: {decision.decision}\n"
        f"Reason: {decision.reason}\n"
        f"Confidence: {decision.confidence:.2f}\n"
        f"Volume Ratio: {decision.metrics.volume_ratio:.2f}x\n"
        f"Trend: {decision.metrics.trend}\n"
        f"Z-Score: {decision.metrics.z_score:.2f}"
    )

    # Log as a note on the trade
    try:
        # This would require extending TradeJournal to support notes
        # For now, we'll store in our volume database
        logger = VolumeDecisionLogger()
        logger.log_decision(decision)
    except Exception as e:
        print(f"[pt_volume] Failed to log to analytics: {e}")


# =============================================================================
# DATA FETCHING
# =============================================================================


class VolumeDataFetcher:
    """Fetches OHLCV data with volume from exchange."""

    def __init__(self):
        self.market = Market(url="https://api.kucoin.com") if KUCOIN_AVAILABLE else None

    def fetch_candles(
        self,
        coin: str,
        start_date: datetime,
        end_date: datetime,
        timeframe: str = "1hour",
    ) -> List[CandleVolumeData]:
        """
        Fetch historical candles with volume data.

        Args:
            coin: Coin symbol (e.g., 'BTC', 'ETH')
            start_date: Start of period
            end_date: End of period
            timeframe: Candle interval

        Returns:
            List of CandleVolumeData objects
        """
        if not KUCOIN_AVAILABLE:
            raise RuntimeError("kucoin-python not installed. Cannot fetch volume data.")

        symbol = f"{coin}-USDT"
        all_candles = []

        # KuCoin returns max 1500 candles per request
        tf_minutes = {
            "1hour": 60,
            "4hour": 240,
            "1day": 1440,
        }

        minutes = tf_minutes.get(timeframe, 60)
        chunk_seconds = 1500 * minutes * 60

        current_start = int(start_date.timestamp())
        end_ts = int(end_date.timestamp())

        while current_start < end_ts:
            chunk_end = min(current_start + chunk_seconds, end_ts)

            try:
                data = self.market.get_kline(
                    symbol, timeframe, startAt=current_start, endAt=chunk_end
                )

                if data:
                    for candle_data in data:
                        # KuCoin format: [timestamp, open, close, high, low, volume, turnover]
                        candle = CandleVolumeData(
                            timestamp=int(candle_data[0]),
                            open=float(candle_data[1]),
                            close=float(candle_data[2]),
                            high=float(candle_data[3]),
                            low=float(candle_data[4]),
                            volume=float(candle_data[5]),
                        )
                        all_candles.append(candle)

            except Exception as e:
                print(f"Error fetching volume data: {e}")

            current_start = chunk_end

        all_candles.sort(key=lambda c: c.timestamp)
        return all_candles


# =============================================================================
# CLI TOOLS
# =============================================================================


def analyze_volume(args):
    """Analyze volume for a coin."""
    if not KUCOIN_AVAILABLE:
        print("ERROR: kucoin-python not installed")
        return

    coin = args.coin.upper()
    end_date = datetime.now()
    start_date = end_date - timedelta(days=args.days)

    fetcher = VolumeDataFetcher()
    candles = fetcher.fetch_candles(coin, start_date, end_date, args.timeframe)

    if not candles:
        print(f"No volume data found for {coin}")
        return

    analyzer = VolumeAnalyzer(sma_periods=args.sma, ema_periods=args.ema)
    metrics_list = []

    for candle in candles:
        prev_ema = metrics_list[-1].volume_ema if metrics_list else None
        metrics = analyzer.analyze_candle(candle, prev_ema)
        metrics_list.append(metrics)

    profile = analyzer.calculate_profile(candles)

    print("\n" + "=" * 60)
    print(f"VOLUME ANALYSIS: {coin}")
    print("=" * 60)
    print(f"\nPeriod: {profile.period}")
    print(f"Candles: {profile.candle_count}")

    print(f"\n{'─' * 40}")
    print("VOLUME PROFILE")
    print(f"{'─' * 40}")
    print(f"Average Volume:     {profile.avg_volume:,.2f}")
    print(f"Median Volume:      {profile.median_volume:,.2f}")
    print(f"P25 Volume:         {profile.p25_volume:,.2f}")
    print(f"P50 Volume:         {profile.p50_volume:,.2f}")
    print(f"P75 Volume:         {profile.p75_volume:,.2f}")
    print(f"P90 Volume:         {profile.p90_volume:,.2f}")
    print(f"Std Dev:           {profile.std_volume:,.2f}")
    print(f"Total Volume:       {profile.total_volume:,.2f}")

    print(f"\n{'─' * 40}")
    print("RECENT VOLUME METRICS (Last 10 candles)")
    print(f"{'─' * 40}")
    for m in metrics_list[-10:]:
        dt = datetime.fromtimestamp(m.timestamp)
        print(
            f"  {dt.strftime('%Y-%m-%d %H:%M')} | "
            f"Vol: {m.volume:,.0f} | "
            f"Ratio: {m.volume_ratio:.2f}x | "
            f"Z-Score: {m.z_score:.2f} | "
            f"Trend: {m.trend}"
        )

    print("\n" + "=" * 60)


def backtest_volume(args):
    """Backtest volume-based entry filtering."""
    if not KUCOIN_AVAILABLE:
        print("ERROR: kucoin-python not installed")
        return

    coin = args.coin.upper()
    start_date = datetime.strptime(args.start_date, "%Y-%m-%d")
    end_date = datetime.strptime(args.end_date, "%Y-%m-%d")

    config = VolumeBacktestConfig(
        min_volume_ratio=args.min_volume_ratio,
        max_volume_ratio=args.max_volume_ratio,
        high_volume_zscore=args.high_zscore,
        low_volume_zscore=args.low_zscore,
        require_increasing_volume=args.require_increasing,
        vwap_distance_pct=args.vwap_distance,
    )

    fetcher = VolumeDataFetcher()
    candles = fetcher.fetch_candles(coin, start_date, end_date, args.timeframe)

    if not candles:
        print(f"No volume data found for {coin}")
        return

    analyzer = VolumeAnalyzer(sma_periods=args.sma, ema_periods=args.ema)
    volume_filter = VolumeFilter(config)

    total_entries = 0
    allowed_entries = 0
    rejected_entries = 0
    decisions = []

    for candle in candles[args.warmup :]:
        prev_ema = decisions[-1].metrics.volume_ema if decisions else None
        metrics = analyzer.analyze_candle(candle, prev_ema)
        decision = volume_filter.make_decision(candle, metrics, coin)
        decisions.append(decision)

        total_entries += 1
        if decision.decision == "allow":
            allowed_entries += 1
        else:
            rejected_entries += 1

    print("\n" + "=" * 60)
    print(f"VOLUME BACKTEST RESULTS: {coin}")
    print("=" * 60)
    print(f"\nPeriod: {start_date.date()} to {end_date.date()}")
    print(f"Timeframe: {args.timeframe}")

    print(f"\n{'─' * 40}")
    print("CONFIGURATION")
    print(f"{'─' * 40}")
    print(f"Min Volume Ratio:   {config.min_volume_ratio}x")
    print(f"Max Volume Ratio:   {config.max_volume_ratio}x")
    print(f"High Z-Score:       {config.high_volume_zscore}")
    print(f"Low Z-Score:        {config.low_volume_zscore}")
    print(f"Require Increasing:  {config.require_increasing_volume}")
    print(f"VWAP Distance:      {config.vwap_distance_pct}%")

    print(f"\n{'─' * 40}")
    print("RESULTS")
    print(f"{'─' * 40}")
    print(f"Total Entries:      {total_entries}")
    print(
        f"Allowed Entries:    {allowed_entries} ({allowed_entries / total_entries * 100:.1f}%)"
    )
    print(
        f"Rejected Entries:   {rejected_entries} ({rejected_entries / total_entries * 100:.1f}%)"
    )

    rejection_reasons = {}
    for d in decisions:
        if d.decision != "allow":
            reason = d.decision
            rejection_reasons[reason] = rejection_reasons.get(reason, 0) + 1

    if rejection_reasons:
        print(f"\n{'─' * 40}")
        print("REJECTION BREAKDOWN")
        print(f"{'─' * 40}")
        for reason, count in rejection_reasons.items():
            print(f"  {reason}: {count} ({count / rejected_entries * 100:.1f}%)")

    print("\n" + "=" * 60)


def profile_volume(args):
    """Generate volume profile for a coin."""
    if not KUCOIN_AVAILABLE:
        print("ERROR: kucoin-python not installed")
        return

    coin = args.coin.upper()
    end_date = datetime.now()
    start_date = end_date - timedelta(days=args.days)

    fetcher = VolumeDataFetcher()
    candles = fetcher.fetch_candles(coin, start_date, end_date, args.timeframe)

    if not candles:
        print(f"No volume data found for {coin}")
        return

    analyzer = VolumeAnalyzer()
    profile = analyzer.calculate_profile(candles)

    logger = VolumeDecisionLogger()
    logger.log_profile(coin, args.timeframe, profile)

    print("\n" + "=" * 60)
    print(f"VOLUME PROFILE: {coin} ({args.timeframe})")
    print("=" * 60)
    print(f"\nPeriod: {profile.period}")

    print(f"\n{'─' * 40}")
    print("STATISTICS")
    print(f"{'─' * 40}")
    print(f"Average:    {profile.avg_volume:,.2f}")
    print(f"Median:     {profile.median_volume:,.2f}")
    print(f"Std Dev:    {profile.std_volume:,.2f}")
    print(f"Total:      {profile.total_volume:,.2f}")

    print(f"\n{'─' * 40}")
    print("PERCENTILES")
    print(f"{'─' * 40}")
    print(f"P25 (25th): {profile.p25_volume:,.2f}")
    print(f"P50 (50th): {profile.p50_volume:,.2f}")
    print(f"P75 (75th): {profile.p75_volume:,.2f}")
    print(f"P90 (90th): {profile.p90_volume:,.2f}")

    print("\n" + "=" * 60)
    print("Volume profile saved to database")
    print("=" * 60 + "\n")


def main():
    parser = argparse.ArgumentParser(
        description="PowerTrader AI Volume Analysis",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python pt_volume.py analyze BTC --days 30
  python pt_volume.py backtest BTC 2024-01-01 2024-12-31
  python pt_volume.py profile ETH --timeframe 4hour
        """,
    )

    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Analyze command
    analyze_parser = subparsers.add_parser("analyze", help="Analyze volume for a coin")
    analyze_parser.add_argument("coin", help="Coin symbol (e.g., BTC, ETH)")
    analyze_parser.add_argument(
        "--days", type=int, default=30, help="Days to analyze (default: 30)"
    )
    analyze_parser.add_argument(
        "--timeframe", default="1hour", help="Timeframe (default: 1hour)"
    )
    analyze_parser.add_argument(
        "--sma", type=int, default=20, help="SMA period (default: 20)"
    )
    analyze_parser.add_argument(
        "--ema", type=int, default=20, help="EMA period (default: 20)"
    )

    # Backtest command
    backtest_parser = subparsers.add_parser(
        "backtest", help="Backtest volume filtering"
    )
    backtest_parser.add_argument("coin", help="Coin symbol (e.g., BTC, ETH)")
    backtest_parser.add_argument("start_date", help="Start date (YYYY-MM-DD)")
    backtest_parser.add_argument("end_date", help="End date (YYYY-MM-DD)")
    backtest_parser.add_argument(
        "--timeframe", default="1hour", help="Timeframe (default: 1hour)"
    )
    backtest_parser.add_argument(
        "--sma", type=int, default=20, help="SMA period (default: 20)"
    )
    backtest_parser.add_argument(
        "--ema", type=int, default=20, help="EMA period (default: 20)"
    )
    backtest_parser.add_argument(
        "--warmup", type=int, default=50, help="Warmup candles (default: 50)"
    )
    backtest_parser.add_argument(
        "--min-volume-ratio", type=float, default=0.5, help="Min volume ratio"
    )
    backtest_parser.add_argument(
        "--max-volume-ratio", type=float, default=3.0, help="Max volume ratio"
    )
    backtest_parser.add_argument(
        "--high-zscore", type=float, default=2.0, help="High z-score threshold"
    )
    backtest_parser.add_argument(
        "--low-zscore", type=float, default=-2.0, help="Low z-score threshold"
    )
    backtest_parser.add_argument(
        "--require-increasing", action="store_true", help="Require increasing volume"
    )
    backtest_parser.add_argument(
        "--vwap-distance", type=float, default=0.5, help="Max VWAP distance %"
    )

    # Profile command
    profile_parser = subparsers.add_parser("profile", help="Generate volume profile")
    profile_parser.add_argument("coin", help="Coin symbol (e.g., BTC, ETH)")
    profile_parser.add_argument(
        "--days", type=int, default=30, help="Days to analyze (default: 30)"
    )
    profile_parser.add_argument(
        "--timeframe", default="1hour", help="Timeframe (default: 1hour)"
    )

    args = parser.parse_args()

    if args.command == "analyze":
        analyze_volume(args)
    elif args.command == "backtest":
        backtest_volume(args)
    elif args.command == "profile":
        profile_volume(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
