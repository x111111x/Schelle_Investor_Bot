"""Macro Scout — global economic data, geopolitical news, central bank sentiment."""

import os
import time
from datetime import datetime, timedelta

import feedparser
import pytz

from config import MACRO_RSS_FEEDS, HAWKISH_KEYWORDS, DOVISH_KEYWORDS, FRED_SERIES
from utils.helpers import now_china
from utils.logger import get_logger

logger = get_logger("macro_scout")


class MacroScout:
    def analyze(self) -> dict:
        """Run full macro analysis and return structured results."""
        logger.info("Starting macro analysis")
        headlines = self._fetch_headlines()
        fed_sentiment, fed_detail = self._classify_fed_sentiment(headlines)
        key_events = self._extract_key_events(headlines)
        fred_data = self._fetch_fred_data()
        risk_level = self._assess_risk(fed_sentiment, fred_data)
        summary = self._build_summary(fed_sentiment, risk_level, key_events, fred_data)

        result = {
            "fed_sentiment": fed_sentiment,
            "fed_detail": fed_detail,
            "key_events": key_events[:5],
            "risk_level": risk_level,
            "macro_summary": summary,
            "fred_data": fred_data,
        }
        logger.info("Macro analysis complete — risk: %s, fed: %s", risk_level, fed_sentiment)
        return result

    def _fetch_headlines(self) -> list[dict]:
        """Fetch and filter RSS headlines from the last 24 hours."""
        cutoff = datetime.now(pytz.UTC) - timedelta(hours=24)
        headlines = []

        for name, url in MACRO_RSS_FEEDS.items():
            try:
                feed = feedparser.parse(url)
                for entry in feed.entries[:20]:
                    pub = entry.get("published_parsed")
                    if pub:
                        pub_dt = datetime(*pub[:6], tzinfo=pytz.UTC)
                        if pub_dt < cutoff:
                            continue
                    headlines.append({
                        "source": name,
                        "title": entry.get("title", ""),
                        "summary": entry.get("summary", "")[:200],
                        "link": entry.get("link", ""),
                    })
            except Exception as e:
                logger.warning("Failed to fetch %s: %s", name, e)

        logger.info("Fetched %d macro headlines", len(headlines))
        return headlines

    def _classify_fed_sentiment(self, headlines: list[dict]) -> tuple[str, str]:
        """Classify central bank sentiment from headline text."""
        text_blob = " ".join(h["title"].lower() + " " + h["summary"].lower() for h in headlines)

        hawk_count = sum(text_blob.count(kw) for kw in HAWKISH_KEYWORDS)
        dove_count = sum(text_blob.count(kw) for kw in DOVISH_KEYWORDS)

        if hawk_count > dove_count + 2:
            sentiment = "Hawkish"
            detail = f"Hawkish signals dominate ({hawk_count} hawkish vs {dove_count} dovish mentions)"
        elif dove_count > hawk_count + 2:
            sentiment = "Dovish"
            detail = f"Dovish signals dominate ({dove_count} dovish vs {hawk_count} hawkish mentions)"
        else:
            sentiment = "Neutral"
            detail = f"Mixed signals ({hawk_count} hawkish, {dove_count} dovish mentions)"

        return sentiment, detail

    # Keywords used to score headline relevance to markets/investing
    _MARKET_KEYWORDS = [
        "market", "stock", "shares", "equity", "equities", "index", "indices",
        "dow", "nasdaq", "s&p", "sp500", "fed", "federal reserve", "fomc",
        "inflation", "gdp", "economy", "economic", "recession", "rate", "rates",
        "yield", "bond", "treasury", "dollar", "currency", "trade", "tariff",
        "earnings", "revenue", "profit", "growth", "jobs", "unemployment",
        "oil", "energy", "commodity", "commodities", "crypto", "bitcoin",
        "bank", "banking", "debt", "deficit", "fiscal", "monetary",
        "china", "europe", "geopolit", "sanctions", "supply chain",
        "ipo", "merger", "acquisition", "buyback", "dividend",
    ]

    def _relevance_score(self, title: str) -> int:
        """Count how many market keywords appear in the headline."""
        title_lower = title.lower()
        return sum(1 for kw in self._MARKET_KEYWORDS if kw in title_lower)

    def _extract_key_events(self, headlines: list[dict]) -> list[dict]:
        """Score all headlines by relevance and return the top 5 across all sources."""
        seen = set()
        scored = []
        for h in headlines:
            title = h["title"].strip()
            if not title or title in seen:
                continue
            seen.add(title)
            score = self._relevance_score(title)
            if score > 0:
                scored.append((score, h))

        # Sort by relevance score descending; take top 5
        scored.sort(key=lambda x: x[0], reverse=True)
        return [{"title": h["title"], "link": h.get("link", "")} for _, h in scored[:5]]

    def _fetch_fred_data(self) -> dict:
        """Optionally fetch FRED economic data if API key is available."""
        api_key = os.environ.get("FRED_API_KEY", "").strip()
        if not api_key:
            return {}

        data = {}
        try:
            from fredapi import Fred
            fred = Fred(api_key=api_key)
            for label, series_id in FRED_SERIES.items():
                try:
                    series = fred.get_series_latest_release(series_id)
                    if len(series) > 0:
                        data[label] = round(float(series.iloc[-1]), 2)
                except Exception as e:
                    logger.warning("FRED %s fetch failed: %s", series_id, e)
        except ImportError:
            logger.warning("fredapi not installed, skipping FRED data")

        return data

    def _assess_risk(self, fed_sentiment: str, fred_data: dict) -> str:
        """Derive a risk level from available signals."""
        vix = fred_data.get("VIX", 0)
        if vix >= 35:
            return "High"
        if vix >= 25:
            return "Elevated"
        if fed_sentiment == "Hawkish":
            return "Elevated"
        if fed_sentiment == "Dovish":
            return "Low"
        return "Moderate"

    def _build_summary(self, fed: str, risk: str, events: list[str], fred: dict) -> str:
        """Create a 2-3 sentence executive macro summary."""
        parts = [f"Central bank stance is {fed.lower()} with market risk at {risk.lower()} levels."]

        if fred:
            metrics = []
            if "10Y_YIELD" in fred:
                metrics.append(f"10Y yield at {fred['10Y_YIELD']}%")
            if "VIX" in fred:
                metrics.append(f"VIX at {fred['VIX']}")
            if "UNEMPLOYMENT" in fred:
                metrics.append(f"unemployment at {fred['UNEMPLOYMENT']}%")
            if metrics:
                parts.append("Key metrics: " + ", ".join(metrics) + ".")

        if events:
            parts.append(f"Top headline: {events[0]['title'][:80]}.")

        return " ".join(parts)
