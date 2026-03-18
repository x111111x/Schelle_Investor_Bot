"""Sentiment Engine — news sentiment and supply chain monitoring."""

import time
from datetime import datetime, timedelta

import feedparser
import pytz

from config import SUPPLY_CHAIN_KEYWORDS
from utils.logger import get_logger

logger = get_logger("sentiment_engine")

# Try to import VADER; fall back to simple keyword-based if unavailable
try:
    from nltk.sentiment.vader import SentimentIntensityAnalyzer
    _SID = SentimentIntensityAnalyzer()
    _HAS_VADER = True
except Exception:
    _HAS_VADER = False
    logger.warning("VADER not available — using keyword fallback for sentiment")


def _simple_sentiment(text: str) -> float:
    """Keyword-based fallback sentiment scorer (-1 to 1)."""
    positive = ["surge", "gain", "rally", "beat", "strong", "growth", "profit",
                "upgrade", "bullish", "record", "soar", "outperform"]
    negative = ["drop", "fall", "crash", "miss", "weak", "loss", "decline",
                "downgrade", "bearish", "plunge", "cut", "risk", "fear"]
    text_lower = text.lower()
    pos = sum(1 for w in positive if w in text_lower)
    neg = sum(1 for w in negative if w in text_lower)
    total = pos + neg
    if total == 0:
        return 0.0
    return (pos - neg) / total


class SentimentEngine:
    def analyze(self, watchlist: list[str]) -> dict:
        """Analyze sentiment for each ticker and detect supply chain issues."""
        logger.info("Starting sentiment analysis for %d tickers", len(watchlist))

        ticker_sentiments = {}
        all_headlines = []

        for ticker in watchlist:
            try:
                sentiment_data = self._analyze_ticker(ticker)
                ticker_sentiments[ticker] = sentiment_data
                all_headlines.extend(sentiment_data.get("headlines", []))
            except Exception as e:
                logger.warning("Sentiment failed for %s: %s", ticker, e)
                ticker_sentiments[ticker] = {"score": 0, "trend": "neutral", "headlines": []}
            time.sleep(0.3)  # rate limit

        supply_chain_alerts = self._scan_supply_chain(all_headlines)
        overall_mood = self._compute_overall_mood(ticker_sentiments)

        result = {
            "ticker_sentiments": ticker_sentiments,
            "supply_chain_alerts": supply_chain_alerts,
            "overall_market_mood": overall_mood,
        }
        logger.info("Sentiment analysis complete — mood: %s", overall_mood)
        return result

    def _analyze_ticker(self, ticker: str) -> dict:
        """Fetch Google News RSS for a ticker and compute sentiment."""
        url = f"https://news.google.com/rss/search?q={ticker}+stock&hl=en"
        feed = feedparser.parse(url)

        headlines = []
        scores = []
        cutoff = datetime.now(pytz.UTC) - timedelta(hours=48)

        for entry in feed.entries[:10]:
            title = entry.get("title", "").strip()
            if not title:
                continue

            # Filter by recency if date available
            pub = entry.get("published_parsed")
            if pub:
                pub_dt = datetime(*pub[:6], tzinfo=pytz.UTC)
                if pub_dt < cutoff:
                    continue

            headlines.append(title)

            if _HAS_VADER:
                score = _SID.polarity_scores(title)["compound"]
            else:
                score = _simple_sentiment(title)
            scores.append(score)

        avg = sum(scores) / len(scores) if scores else 0.0

        if avg > 0.15:
            trend = "Bullish"
        elif avg < -0.15:
            trend = "Bearish"
        else:
            trend = "Neutral"

        return {
            "score": round(avg, 3),
            "trend": trend,
            "headlines": headlines[:3],
        }

    def _scan_supply_chain(self, headlines: list[str]) -> list[str]:
        """Scan headlines for supply chain disruption signals."""
        alerts = set()
        for headline in headlines:
            lower = headline.lower()
            for kw in SUPPLY_CHAIN_KEYWORDS:
                if kw in lower:
                    alerts.add(headline)
                    break
        return list(alerts)[:5]

    def _compute_overall_mood(self, sentiments: dict) -> str:
        """Compute aggregate market mood across all tickers."""
        scores = [s["score"] for s in sentiments.values() if s.get("score") is not None]
        if not scores:
            return "Neutral"
        avg = sum(scores) / len(scores)
        if avg > 0.1:
            return "Bullish"
        if avg < -0.1:
            return "Bearish"
        return "Neutral"
