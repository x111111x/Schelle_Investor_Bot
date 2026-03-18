"""Paper portfolio manager backed by SQLite."""

import os
import sqlite3
from datetime import datetime

import yfinance as yf

from config import DB_PATH, INITIAL_CAPITAL, MAX_POSITION_PCT
from utils.helpers import now_china
from utils.logger import get_logger

logger = get_logger("portfolio")


class PortfolioManager:
    def __init__(self, db_path: str = DB_PATH):
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row

    # ------------------------------------------------------------------
    # Schema
    # ------------------------------------------------------------------
    def init_db(self):
        """Create tables and seed initial cash if needed."""
        cur = self.conn.cursor()
        cur.executescript("""
            CREATE TABLE IF NOT EXISTS positions (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                ticker      TEXT NOT NULL,
                shares      REAL NOT NULL,
                avg_cost    REAL NOT NULL,
                opened_at   TEXT NOT NULL,
                last_updated TEXT NOT NULL,
                status      TEXT NOT NULL DEFAULT 'open',
                UNIQUE(ticker, status)
            );

            CREATE TABLE IF NOT EXISTS trades (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                ticker      TEXT NOT NULL,
                action      TEXT NOT NULL,
                shares      REAL NOT NULL,
                price       REAL NOT NULL,
                total_value REAL NOT NULL,
                rationale   TEXT,
                confidence  INTEGER,
                executed_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS cash (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                balance     REAL NOT NULL,
                updated_at  TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS daily_snapshots (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                date            TEXT NOT NULL UNIQUE,
                total_value     REAL NOT NULL,
                cash_balance    REAL NOT NULL,
                positions_value REAL NOT NULL,
                spy_value       REAL NOT NULL,
                created_at      TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS recommendations (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                date        TEXT NOT NULL,
                ticker      TEXT NOT NULL,
                action      TEXT NOT NULL,
                entry_low   REAL,
                entry_high  REAL,
                stop_loss   REAL,
                confidence  INTEGER,
                rationale   TEXT,
                was_executed INTEGER DEFAULT 0,
                created_at  TEXT NOT NULL
            );
        """)
        # Seed cash if table is empty
        row = cur.execute("SELECT COUNT(*) FROM cash").fetchone()
        if row[0] == 0:
            cur.execute(
                "INSERT INTO cash (balance, updated_at) VALUES (?, ?)",
                (INITIAL_CAPITAL, now_china().isoformat()),
            )
        self.conn.commit()
        logger.info("Database initialized")

    # ------------------------------------------------------------------
    # Cash helpers
    # ------------------------------------------------------------------
    def _get_cash(self) -> float:
        row = self.conn.execute(
            "SELECT balance FROM cash ORDER BY id DESC LIMIT 1"
        ).fetchone()
        return float(row["balance"]) if row else 0.0

    def _set_cash(self, balance: float):
        self.conn.execute(
            "INSERT INTO cash (balance, updated_at) VALUES (?, ?)",
            (balance, now_china().isoformat()),
        )
        self.conn.commit()

    # ------------------------------------------------------------------
    # Position helpers
    # ------------------------------------------------------------------
    def _get_open_position(self, ticker: str):
        return self.conn.execute(
            "SELECT * FROM positions WHERE ticker = ? AND status = 'open'",
            (ticker,),
        ).fetchone()

    def _get_all_open_positions(self) -> list[dict]:
        rows = self.conn.execute(
            "SELECT * FROM positions WHERE status = 'open'"
        ).fetchall()
        return [dict(r) for r in rows]

    # ------------------------------------------------------------------
    # Trade execution (paper)
    # ------------------------------------------------------------------
    def apply_recommendations(self, picks: list[dict]):
        """Process recommendations and execute paper trades."""
        now = now_china().isoformat()
        cash = self._get_cash()
        total_value = self._calculate_total_value(cash)

        for pick in picks:
            ticker = pick["ticker"]
            action = pick["action"]
            price = pick.get("current_price", 0)
            if price <= 0:
                continue

            # Log recommendation
            self.conn.execute(
                """INSERT INTO recommendations
                   (date, ticker, action, entry_low, entry_high, stop_loss,
                    confidence, rationale, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    now_china().strftime("%Y-%m-%d"),
                    ticker,
                    action,
                    pick.get("entry_price_low"),
                    pick.get("entry_price_high"),
                    pick.get("stop_loss"),
                    pick.get("confidence"),
                    pick.get("rationale"),
                    now,
                ),
            )

            existing = self._get_open_position(ticker)

            if action == "Buy" and not existing:
                # Allocate up to MAX_POSITION_PCT of portfolio
                max_alloc = total_value * MAX_POSITION_PCT
                alloc = min(max_alloc, cash)
                if alloc < price:
                    continue  # not enough cash for even 1 share
                shares = int(alloc / price)
                if shares <= 0:
                    continue
                cost = shares * price
                cash -= cost
                self.conn.execute(
                    """INSERT INTO positions
                       (ticker, shares, avg_cost, opened_at, last_updated, status)
                       VALUES (?, ?, ?, ?, ?, 'open')""",
                    (ticker, shares, price, now, now),
                )
                self.conn.execute(
                    """INSERT INTO trades
                       (ticker, action, shares, price, total_value,
                        rationale, confidence, executed_at)
                       VALUES (?, 'BUY', ?, ?, ?, ?, ?, ?)""",
                    (ticker, shares, price, cost, pick.get("rationale"),
                     pick.get("confidence"), now),
                )
                # Mark recommendation as executed
                self.conn.execute(
                    """UPDATE recommendations SET was_executed = 1
                       WHERE ticker = ? AND date = ? AND action = 'Buy'""",
                    (ticker, now_china().strftime("%Y-%m-%d")),
                )
                logger.info("BUY %s: %d shares @ $%.2f ($%.2f)", ticker, shares, price, cost)

            elif action == "Sell" and existing:
                shares = float(existing["shares"])
                proceeds = shares * price
                cash += proceeds
                self.conn.execute(
                    "UPDATE positions SET status = 'closed', last_updated = ? WHERE id = ?",
                    (now, existing["id"]),
                )
                self.conn.execute(
                    """INSERT INTO trades
                       (ticker, action, shares, price, total_value,
                        rationale, confidence, executed_at)
                       VALUES (?, 'SELL', ?, ?, ?, ?, ?, ?)""",
                    (ticker, shares, price, proceeds, pick.get("rationale"),
                     pick.get("confidence"), now),
                )
                logger.info("SELL %s: %d shares @ $%.2f ($%.2f)", ticker, int(shares), price, proceeds)

        self._set_cash(cash)

    # ------------------------------------------------------------------
    # Snapshot & performance
    # ------------------------------------------------------------------
    def _calculate_total_value(self, cash: float) -> float:
        positions = self._get_all_open_positions()
        positions_value = 0.0
        for pos in positions:
            try:
                info = yf.Ticker(pos["ticker"]).info
                current = info.get("currentPrice") or info.get("regularMarketPrice", 0)
                positions_value += float(pos["shares"]) * float(current or 0)
            except Exception:
                positions_value += float(pos["shares"]) * float(pos["avg_cost"])
        return cash + positions_value

    def get_snapshot(self) -> dict:
        """Return current portfolio state."""
        cash = self._get_cash()
        positions = self._get_all_open_positions()
        enriched = []
        positions_value = 0.0

        for pos in positions:
            try:
                info = yf.Ticker(pos["ticker"]).info
                current = float(info.get("currentPrice") or info.get("regularMarketPrice", 0))
            except Exception:
                current = float(pos["avg_cost"])
            market_val = float(pos["shares"]) * current
            positions_value += market_val
            pct = ((current - float(pos["avg_cost"])) / float(pos["avg_cost"])) * 100 if pos["avg_cost"] else 0
            enriched.append({
                "ticker": pos["ticker"],
                "shares": pos["shares"],
                "avg_cost": pos["avg_cost"],
                "current_price": current,
                "market_value": market_val,
                "pct_change": round(pct, 2),
            })

        total = cash + positions_value
        return {
            "cash": cash,
            "positions_value": positions_value,
            "total_value": total,
            "return_pct": round(((total - INITIAL_CAPITAL) / INITIAL_CAPITAL) * 100, 2),
            "positions": enriched,
        }

    def get_performance_vs_spy(self) -> dict:
        """Compare portfolio return to SPY since inception."""
        # Find first snapshot date or use today
        first = self.conn.execute(
            "SELECT date FROM daily_snapshots ORDER BY date ASC LIMIT 1"
        ).fetchone()

        if first:
            start_date = first["date"]
        else:
            start_date = now_china().strftime("%Y-%m-%d")

        try:
            spy = yf.Ticker("SPY")
            hist = spy.history(start=start_date)
            if len(hist) >= 2:
                spy_start = float(hist.iloc[0]["Close"])
                spy_now = float(hist.iloc[-1]["Close"])
                spy_return = ((spy_now - spy_start) / spy_start) * 100
            else:
                spy_return = 0.0
        except Exception:
            spy_return = 0.0

        snapshot = self.get_snapshot()
        return {
            "portfolio_return": snapshot["return_pct"],
            "spy_return": round(spy_return, 2),
            "alpha": round(snapshot["return_pct"] - spy_return, 2),
            "since": start_date,
        }

    def save_daily_snapshot(self):
        """Persist today's snapshot for historical tracking."""
        snapshot = self.get_snapshot()
        today = now_china().strftime("%Y-%m-%d")
        now = now_china().isoformat()

        try:
            spy = yf.Ticker("SPY")
            spy_price = float(spy.info.get("currentPrice") or spy.info.get("regularMarketPrice", 0))
        except Exception:
            spy_price = 0.0

        # Calculate SPY benchmark value (same start capital)
        try:
            first = self.conn.execute(
                "SELECT spy_value FROM daily_snapshots ORDER BY date ASC LIMIT 1"
            ).fetchone()
            if first:
                spy_value = float(first["spy_value"])  # keep tracking from first entry
            else:
                spy_value = INITIAL_CAPITAL  # first day benchmark
        except Exception:
            spy_value = INITIAL_CAPITAL

        try:
            self.conn.execute(
                """INSERT OR REPLACE INTO daily_snapshots
                   (date, total_value, cash_balance, positions_value, spy_value, created_at)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (today, snapshot["total_value"], snapshot["cash"],
                 snapshot["positions_value"], spy_value, now),
            )
            self.conn.commit()
            logger.info("Daily snapshot saved: $%.2f", snapshot["total_value"])
        except Exception as e:
            logger.error("Failed to save snapshot: %s", e)
