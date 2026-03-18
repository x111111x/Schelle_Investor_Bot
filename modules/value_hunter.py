"""Value Hunter — fundamental stock screening using yfinance."""

import time

import yfinance as yf

from config import (
    PE_LOW, PE_MID, FCF_LOW, FCF_MID,
    BUY_THRESHOLD, SELL_THRESHOLD, STOP_LOSS_PCT,
)
from utils.logger import get_logger

logger = get_logger("value_hunter")


class ValueHunter:
    def scan(self, watchlist: list[str]) -> list[dict]:
        """Screen each ticker and return scored recommendations."""
        logger.info("Scanning %d tickers", len(watchlist))
        results = []

        for ticker in watchlist:
            try:
                pick = self._analyze_ticker(ticker)
                if pick:
                    results.append(pick)
            except Exception as e:
                logger.warning("Failed to analyze %s: %s", ticker, e)
            time.sleep(0.5)  # rate limit

        # Sort by confidence descending
        results.sort(key=lambda x: x["confidence"], reverse=True)
        logger.info("Scan complete — %d recommendations generated", len(results))
        return results

    def _analyze_ticker(self, ticker: str) -> dict | None:
        """Analyze a single ticker and return a recommendation dict."""
        stock = yf.Ticker(ticker)
        info = stock.info
        if not info or not info.get("currentPrice") and not info.get("regularMarketPrice"):
            logger.debug("No price data for %s", ticker)
            return None

        current = float(info.get("currentPrice") or info.get("regularMarketPrice", 0))
        if current <= 0:
            return None

        # Extract fundamentals (with safe defaults)
        trailing_pe = self._safe_float(info.get("trailingPE"))
        forward_pe = self._safe_float(info.get("forwardPE"))
        fcf = self._safe_float(info.get("freeCashflow"))
        market_cap = self._safe_float(info.get("marketCap"))
        debt_equity = self._safe_float(info.get("debtToEquity"))
        dividend_yield = self._safe_float(info.get("dividendYield"))
        week52_low = self._safe_float(info.get("fiftyTwoWeekLow"))
        week52_high = self._safe_float(info.get("fiftyTwoWeekHigh"))
        earnings_growth = self._safe_float(info.get("earningsGrowth"))
        exchange = info.get("exchange", "")
        name = info.get("longName") or info.get("shortName") or ticker
        sector = info.get("sector", "Unknown")

        # Calculate derived metrics
        price_to_fcf = (market_cap / fcf) if fcf and fcf > 0 and market_cap else None

        # ------------------------------------------------------------------
        # Scoring (0-10)
        # ------------------------------------------------------------------
        score = 0
        rationale_parts = []

        # P/E scoring (0-2)
        if trailing_pe and trailing_pe > 0:
            if trailing_pe < PE_LOW:
                score += 2
                rationale_parts.append(f"Attractive P/E of {trailing_pe:.1f}")
            elif trailing_pe < PE_MID:
                score += 1
                rationale_parts.append(f"Moderate P/E of {trailing_pe:.1f}")
            else:
                rationale_parts.append(f"High P/E of {trailing_pe:.1f}")

        # Forward P/E improving (0-1)
        if forward_pe and trailing_pe and forward_pe < trailing_pe:
            score += 1
            rationale_parts.append("Forward P/E improving")

        # Price-to-FCF scoring (0-2)
        if price_to_fcf and price_to_fcf > 0:
            if price_to_fcf < FCF_LOW:
                score += 2
                rationale_parts.append(f"Strong FCF yield (P/FCF: {price_to_fcf:.1f})")
            elif price_to_fcf < FCF_MID:
                score += 1
                rationale_parts.append(f"Decent FCF yield (P/FCF: {price_to_fcf:.1f})")

        # Earnings/EBITDA growth (0-1)
        if earnings_growth and earnings_growth > 0:
            score += 1
            rationale_parts.append(f"Positive earnings growth ({earnings_growth:.1%})")

        # Debt/Equity (0-1)
        if debt_equity is not None and debt_equity < 100:  # yfinance reports as %
            score += 1
            rationale_parts.append(f"Manageable debt (D/E: {debt_equity:.0f}%)")

        # 52-week range position (0-2)
        if week52_low and week52_high and week52_high > week52_low:
            range_pct = (current - week52_low) / (week52_high - week52_low)
            if range_pct < 0.4:
                score += 2
                rationale_parts.append(f"Trading in lower 40% of 52-wk range")
            elif range_pct < 0.6:
                score += 1
                rationale_parts.append(f"Mid-range of 52-week band")

        # Dividend bonus (0-1)
        if dividend_yield and dividend_yield > 0:
            score += 1
            rationale_parts.append(f"Dividend yield: {dividend_yield:.2%}")

        # Cap at 10
        score = min(score, 10)

        # Determine action
        if score >= BUY_THRESHOLD:
            action = "Buy"
        elif score <= SELL_THRESHOLD:
            action = "Sell"
        else:
            action = "Hold"

        # Entry & stop-loss
        entry_low = round(current * 0.97, 2)
        entry_high = round(current * 1.01, 2)
        stop_loss = round(entry_low * (1 - STOP_LOSS_PCT), 2)

        rationale = ". ".join(rationale_parts) if rationale_parts else "Insufficient data for detailed analysis"

        return {
            "ticker": ticker,
            "exchange": exchange,
            "company_name": name,
            "sector": sector,
            "action": action,
            "current_price": current,
            "entry_price_low": entry_low,
            "entry_price_high": entry_high,
            "stop_loss": stop_loss,
            "confidence": score,
            "rationale": rationale,
            "metrics": {
                "trailing_pe": trailing_pe,
                "forward_pe": forward_pe,
                "price_to_fcf": round(price_to_fcf, 2) if price_to_fcf else None,
                "debt_equity": debt_equity,
                "earnings_growth": earnings_growth,
                "dividend_yield": dividend_yield,
                "week52_low": week52_low,
                "week52_high": week52_high,
            },
        }

    @staticmethod
    def _safe_float(val) -> float | None:
        """Safely convert to float, returning None on failure."""
        if val is None:
            return None
        try:
            result = float(val)
            return result if result == result else None  # NaN check
        except (ValueError, TypeError):
            return None
