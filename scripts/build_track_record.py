"""
Build track_record.json and performance.json from Telegram export + yfinance.

Usage:
    python scripts/build_track_record.py --telegram path/to/result.json
    python scripts/build_track_record.py --update   # refresh prices for open positions
"""

import argparse
import json
import os
import re
import sys
from collections import defaultdict
from datetime import datetime, date, timedelta

import yfinance as yf

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TRACK_RECORD_PATH = os.path.join(BASE_DIR, "data", "track_record.json")
PERFORMANCE_PATH = os.path.join(BASE_DIR, "data", "performance.json")
INITIAL_CAPITAL = 50_000.0


# ── Text helpers ───────────────────────────────────────────────────────────────

def get_text(msg: dict) -> str:
    t = msg.get("text", "")
    if isinstance(t, str):
        return t
    return "".join(item["text"] if isinstance(item, dict) else item for item in t)


def unescape_md(txt: str) -> str:
    """Remove MarkdownV2 backslash escapes."""
    return re.sub(r"\\(.)", r"\1", txt)


# ── Parse a single portfolio snapshot from message text ───────────────────────

def parse_portfolio_snapshot(raw: str, date_str: str) -> dict | None:
    txt = unescape_md(raw)

    # detect format
    if "Worth Today" not in txt and "Current Value" not in txt:
        return None

    snap = {"date": date_str, "positions": {}}

    # total value — handle *$X* bold markers from MarkdownV2
    m = re.search(r"Worth Today:\s*\*?\$?([\d,]+\.?\d*)\*?", txt)
    if not m:
        m = re.search(r"Current Value:\s*\*?\$?([\d,]+\.?\d*)\*?", txt)
    if m:
        snap["total_value"] = float(m.group(1).replace(",", ""))

    # cash
    m = re.search(r"Cash(?:\s*on\s*Hand)?:\s*\*?\$?([\d,]+\.?\d*)\*?", txt)
    if m:
        snap["cash"] = float(m.group(1).replace(",", ""))

    # return — handle bold markers and emoji before the sign
    m = re.search(r"(?:Your Gain/Loss|Return):[^\d%+-]{0,30}([+-]?\d+\.?\d*)%", txt)
    if m:
        snap["return_pct"] = float(m.group(1))

    # SPY
    m = re.search(r"(?:Market Benchmark|S&P 500 Return)[^\d%+-]{0,30}([+-]?\d+\.?\d*)%", txt)
    if m:
        snap["spy_return"] = float(m.group(1))

    # alpha
    m = re.search(r"(?:You vs Market|Alpha):[^\d%+-]{0,30}([+-]?\d+\.?\d*)%", txt)
    if m:
        snap["alpha"] = float(m.group(1))

    # positions — new format: "Company (TICKER): N shares | Cost: $X.XX -> Now: $Y.YY [emoji] Z%"
    # The -> may be a unicode arrow; after unescape it stays as the unicode char or "->"
    for pm in re.finditer(
        r"\(([A-Z0-9\-\.]+)\):\s*(\d+)\s*shares\s*\|\s*Cost:\s*\$?([\d.]+)"
        r"[^$\n]{0,30}Now:\s*\$?([\d.]+)[^\d-]{0,10}([+-]?[\d.]+)%",
        txt,
    ):
        ticker = pm.group(1)
        snap["positions"][ticker] = {
            "shares": int(pm.group(2)),
            "avg_cost": float(pm.group(3)),
            "current_price": float(pm.group(4)),
            "pct_change": float(pm.group(5)),
        }

    # positions — old format: "TICKER: N shares @ $X -> $Y (Z%)"
    if not snap["positions"]:
        for pm in re.finditer(
            r"\b([A-Z][A-Z0-9\-\.]{1,9}):\s*(\d+)\s*shares\s*@\s*\$?([\d.]+)"
            r"[^$\n]{0,20}\$?([\d.]+)\s*\(([+-]?[\d.]+)%\)",
            txt,
        ):
            ticker = pm.group(1)
            if ticker in ("S&P",):
                continue
            snap["positions"][ticker] = {
                "shares": int(pm.group(2)),
                "avg_cost": float(pm.group(3)),
                "current_price": float(pm.group(4)),
                "pct_change": float(pm.group(5)),
            }

    if "total_value" not in snap:
        return None
    return snap


# ── Parse all snapshots from Telegram export ──────────────────────────────────

def parse_telegram_export(path: str) -> list[dict]:
    with open(path, encoding="utf-8") as f:
        data = json.load(f)

    bot_name = data.get("name", "")
    msgs = data["messages"]
    # Keep only bot outgoing messages
    bot_id = None
    for m in msgs:
        if m.get("from") == "Alpha Investor":
            bot_id = m.get("from_id")
            break

    bot_msgs = [m for m in msgs if m.get("from_id") == bot_id and m.get("type") == "message"]

    snapshots = []
    for m in bot_msgs:
        raw = get_text(m)
        date_str = m["date"][:10]
        snap = parse_portfolio_snapshot(raw, date_str)
        if snap:
            snapshots.append(snap)

    # de-duplicate: one snapshot per day (prefer the one with the highest total_value)
    by_date: dict[str, dict] = {}
    for s in snapshots:
        d = s["date"]
        if d not in by_date or s.get("total_value", 0) > by_date[d].get("total_value", 0):
            by_date[d] = s

    return sorted(by_date.values(), key=lambda x: x["date"])


# ── Derive trades from position changes between snapshots ─────────────────────

def derive_trades(snapshots: list[dict]) -> list[dict]:
    trades = []
    prev_positions: dict = {}

    for snap in snapshots:
        curr = snap["positions"]
        date_str = snap["date"]

        # New tickers = BUY
        for ticker, pos in curr.items():
            if ticker not in prev_positions:
                trades.append({
                    "date": date_str,
                    "action": "BUY",
                    "ticker": ticker,
                    "shares": pos["shares"],
                    "price": pos["avg_cost"],
                    "total": round(pos["shares"] * pos["avg_cost"], 2),
                })

        # Disappeared tickers = SELL (use last known price from current snap or prev)
        for ticker, pos in prev_positions.items():
            if ticker not in curr:
                sell_price = pos.get("current_price", pos["avg_cost"])
                trades.append({
                    "date": date_str,
                    "action": "SELL",
                    "ticker": ticker,
                    "shares": pos["shares"],
                    "price": sell_price,
                    "total": round(pos["shares"] * sell_price, 2),
                    "cost_basis": pos["avg_cost"],
                    "pnl": round(pos["shares"] * (sell_price - pos["avg_cost"]), 2),
                    "pnl_pct": round((sell_price - pos["avg_cost"]) / pos["avg_cost"] * 100, 2),
                })

        prev_positions = curr

    return trades


# ── Fetch SPY history ──────────────────────────────────────────────────────────

def fetch_spy_series(start: str, end: str) -> dict[str, float]:
    spy = yf.Ticker("SPY")
    hist = spy.history(start=start, end=end)
    result = {}
    for idx, row in hist.iterrows():
        result[idx.strftime("%Y-%m-%d")] = float(row["Close"])
    return result


# ── Compute daily portfolio value using yfinance historical prices ─────────────

def compute_daily_values(
    snapshots: list[dict],
    start_date: str,
    end_date: str,
) -> list[dict]:
    """
    For dates with a real snapshot: use the recorded total_value.
    For gaps: use last known positions × historical prices from yfinance.
    """
    known: dict[str, dict] = {s["date"]: s for s in snapshots}
    last_snap = snapshots[-1] if snapshots else None

    # collect all tickers ever held
    all_tickers = set()
    for s in snapshots:
        all_tickers.update(s["positions"].keys())

    # fetch price history for all tickers at once
    print(f"Fetching price history for {len(all_tickers)} tickers + SPY ...")
    tickers_list = sorted(all_tickers) + ["SPY"]
    price_cache: dict[str, dict[str, float]] = {}  # ticker -> date -> price
    try:
        hist_df = yf.download(tickers_list, start=start_date, end=end_date, progress=False, auto_adjust=True)
        # yf.download returns MultiIndex columns when multiple tickers
        if hasattr(hist_df.columns, "levels"):
            close_df = hist_df["Close"]
        else:
            close_df = hist_df["Close"] if "Close" in hist_df.columns else hist_df
        for ticker in tickers_list:
            if ticker in close_df.columns:
                ser = close_df[ticker].dropna()
                price_cache[ticker] = {
                    idx.strftime("%Y-%m-%d"): float(val)
                    for idx, val in ser.items()
                }
    except Exception as e:
        print(f"  Warning: yfinance download failed: {e}")

    def get_price(ticker: str, date_str: str) -> float | None:
        series = price_cache.get(ticker, {})
        # exact date or nearest prior trading day (look back up to 5 days)
        if date_str in series:
            return series[date_str]
        d = datetime.strptime(date_str, "%Y-%m-%d").date()
        for offset in range(1, 6):
            prev = (d - timedelta(days=offset)).strftime("%Y-%m-%d")
            if prev in series:
                return series[prev]
        return None

    # Build date range
    current = datetime.strptime(start_date, "%Y-%m-%d").date()
    end = datetime.strptime(end_date, "%Y-%m-%d").date()

    daily = []
    prev_positions: dict = {}
    prev_cash = INITIAL_CAPITAL
    spy_start_price: float | None = None
    spy_start_date: str | None = None

    while current <= end:
        d = current.strftime("%Y-%m-%d")
        current += timedelta(days=1)

        if d in known:
            snap = known[d]
            total = snap.get("total_value", 0)
            ret = snap.get("return_pct", 0)
            spy_ret = snap.get("spy_return", 0)
            alpha = snap.get("alpha", 0)
            prev_positions = snap["positions"]
            prev_cash = snap.get("cash", prev_cash)
        elif prev_positions:
            # Reconstruct from last positions × today's prices
            positions_value = 0.0
            for ticker, pos in prev_positions.items():
                p = get_price(ticker, d)
                if p is None:
                    p = pos.get("current_price", pos["avg_cost"])
                positions_value += pos["shares"] * p
            total = prev_cash + positions_value
            ret = round((total - INITIAL_CAPITAL) / INITIAL_CAPITAL * 100, 2)

            # SPY return
            spy_today = get_price("SPY", d)
            if spy_today and spy_start_price:
                spy_ret = round((spy_today - spy_start_price) / spy_start_price * 100, 2)
            else:
                spy_ret = 0.0
            alpha = round(ret - spy_ret, 2)
        else:
            # no data yet
            total = INITIAL_CAPITAL
            ret = 0.0
            spy_ret = 0.0
            alpha = 0.0

        # track SPY baseline
        spy_price = get_price("SPY", d)
        if spy_price and spy_start_price is None:
            spy_start_price = spy_price
            spy_start_date = d

        # only include trading days (skip weekends with no data and no snapshot)
        if total == 0:
            continue

        daily.append({
            "date": d,
            "total_value": round(total, 2),
            "return_pct": round(ret, 2),
            "spy_return": round(spy_ret, 2),
            "alpha": round(alpha, 2),
        })

    return daily, price_cache


# ── Compute KPIs from trades ────────────────────────────────────────────────────

def compute_kpis(
    trades: list[dict],
    daily_values: list[dict],
    snapshots: list[dict],
    price_cache: dict | None = None,
) -> dict:
    sells = [t for t in trades if t["action"] == "SELL" and "pnl_pct" in t]
    wins = [t for t in sells if t["pnl_pct"] >= 0]
    losses = [t for t in sells if t["pnl_pct"] < 0]

    last = daily_values[-1] if daily_values else {}

    # open positions from last snapshot — refresh pct_change with today's prices
    open_positions = []
    if snapshots:
        last_snap = snapshots[-1]
        today = date.today()
        for ticker, pos in last_snap["positions"].items():
            current_price = pos["current_price"]
            pct_change = pos["pct_change"]
            if price_cache and ticker in price_cache:
                series = price_cache[ticker]
                for offset in range(0, 10):
                    ds = (today - timedelta(days=offset)).strftime("%Y-%m-%d")
                    if ds in series:
                        current_price = series[ds]
                        pct_change = round(
                            (current_price - pos["avg_cost"]) / pos["avg_cost"] * 100, 2
                        )
                        break
            try:
                info = yf.Ticker(ticker).info
                company_name = info.get("shortName") or info.get("longName") or ticker
            except Exception:
                company_name = ticker
            open_positions.append({
                "ticker": ticker,
                "company_name": company_name,
                "shares": pos["shares"],
                "avg_cost": pos["avg_cost"],
                "current_price": current_price,
                "pct_change": pct_change,
            })

    return {
        "start_date": daily_values[0]["date"] if daily_values else "",
        "end_date": daily_values[-1]["date"] if daily_values else "",
        "initial_capital": INITIAL_CAPITAL,
        "current_value": last.get("total_value", INITIAL_CAPITAL),
        "total_return_pct": last.get("return_pct", 0),
        "spy_return_pct": last.get("spy_return", 0),
        "alpha_pct": last.get("alpha", 0),
        "total_trades": len(trades),
        "closed_trades": len(sells),
        "win_rate": round(len(wins) / len(sells) * 100, 1) if sells else 0,
        "avg_gain_pct": round(sum(t["pnl_pct"] for t in wins) / len(wins), 2) if wins else 0,
        "avg_loss_pct": round(sum(t["pnl_pct"] for t in losses) / len(losses), 2) if losses else 0,
        "open_positions": open_positions,
        "days_active": (
            (datetime.strptime(daily_values[-1]["date"], "%Y-%m-%d") -
             datetime.strptime(daily_values[0]["date"], "%Y-%m-%d")).days
            if len(daily_values) >= 2 else 0
        ),
    }


# ── Main ────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--telegram", help="Path to Telegram result.json export")
    parser.add_argument("--update", action="store_true", help="Refresh prices only (no Telegram needed)")
    args = parser.parse_args()

    os.makedirs(os.path.join(BASE_DIR, "data"), exist_ok=True)

    # Load existing track record if available
    existing: dict = {}
    if os.path.exists(TRACK_RECORD_PATH):
        with open(TRACK_RECORD_PATH, encoding="utf-8") as f:
            existing = json.load(f)

    if args.telegram:
        print(f"Parsing Telegram export: {args.telegram}")
        snapshots = parse_telegram_export(args.telegram)
        print(f"  Found {len(snapshots)} daily snapshots: {snapshots[0]['date']} to {snapshots[-1]['date']}")
        trades = derive_trades(snapshots)
        print(f"  Derived {len(trades)} trades ({sum(1 for t in trades if t['action']=='BUY')} buys, {sum(1 for t in trades if t['action']=='SELL')} sells)")
        existing["snapshots"] = [dict(s, positions={k: v for k, v in s["positions"].items()}) for s in snapshots]
        existing["trades"] = trades
    else:
        snapshots = existing.get("snapshots", [])
        trades = existing.get("trades", [])

    if not snapshots:
        print("No snapshots found. Run with --telegram to import history.")
        sys.exit(1)

    start_date = snapshots[0]["date"]
    end_date = date.today().strftime("%Y-%m-%d")

    print(f"Computing daily portfolio values: {start_date} -> {end_date}")
    daily_values, price_cache = compute_daily_values(snapshots, start_date, end_date)
    print(f"  Generated {len(daily_values)} daily data points")

    kpis = compute_kpis(trades, daily_values, snapshots, price_cache=price_cache)

    # Save track_record.json (full history)
    track_record = {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "initial_capital": INITIAL_CAPITAL,
        "snapshots": [dict(s, positions={k: v for k, v in s["positions"].items()}) for s in snapshots],
        "trades": trades,
        "daily_values": daily_values,
        "kpis": kpis,
    }
    with open(TRACK_RECORD_PATH, "w", encoding="utf-8") as f:
        json.dump(track_record, f, indent=2)
    print(f"Saved: {TRACK_RECORD_PATH}")

    # Save performance.json (lightweight, for website)
    performance = {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "kpis": kpis,
        "chart": {
            "labels": [d["date"] for d in daily_values],
            "portfolio": [d["total_value"] for d in daily_values],
            "spy_benchmark": [
                round(INITIAL_CAPITAL * (1 + d["spy_return"] / 100), 2)
                for d in daily_values
            ],
        },
        "recent_trades": sorted(trades, key=lambda t: t["date"], reverse=True)[:20],
    }
    with open(PERFORMANCE_PATH, "w", encoding="utf-8") as f:
        json.dump(performance, f, indent=2)
    print(f"Saved: {PERFORMANCE_PATH}")

    print("\n── Summary ──────────────────────────────")
    print(f"  Period:      {kpis['start_date']} -> {kpis['end_date']} ({kpis['days_active']} days)")
    print(f"  Portfolio:   ${kpis['current_value']:,.2f}  ({kpis['total_return_pct']:+.2f}%)")
    print(f"  S&P 500:     {kpis['spy_return_pct']:+.2f}%")
    print(f"  Alpha:       {kpis['alpha_pct']:+.2f}%")
    print(f"  Win rate:    {kpis['win_rate']}% ({kpis['closed_trades']} closed trades)")
    print(f"  Open pos:    {len(kpis['open_positions'])}")


if __name__ == "__main__":
    main()
