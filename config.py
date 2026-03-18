"""Central configuration for Project Alpha: Advisory."""

import os

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "data", "alpha.db")
LOG_PATH = os.path.join(BASE_DIR, "logs", "alpha.log")

# ---------------------------------------------------------------------------
# Portfolio
# ---------------------------------------------------------------------------
INITIAL_CAPITAL = 50_000.0
MAX_POSITION_PCT = 0.10  # max 10% of portfolio per position
STOP_LOSS_PCT = 0.08     # 8% below entry low

# ---------------------------------------------------------------------------
# Watchlist — diversified across sectors and geographies
# ---------------------------------------------------------------------------
WATCHLIST = [
    # US Tech
    "AAPL", "MSFT", "GOOGL", "NVDA", "META", "AMZN", "TSM",
    # US Financials / Industrial
    "JPM", "V", "UNH", "CAT",
    # US Energy / Materials
    "XOM", "LIN",
    # Europe
    "ASML", "SAP", "NVO",
    # Consumer / Other
    "COST", "PG", "KO",
    # China / EM
    "BABA",
]

# ---------------------------------------------------------------------------
# Value Hunter — scoring thresholds
# ---------------------------------------------------------------------------
PE_LOW = 15       # P/E below this = 2 pts
PE_MID = 25       # P/E below this = 1 pt
FCF_LOW = 15      # price-to-FCF below this = 2 pts
FCF_MID = 25      # price-to-FCF below this = 1 pt
BUY_THRESHOLD = 6   # score >= this → Buy
SELL_THRESHOLD = 3   # score <= this + existing position → Sell

# ---------------------------------------------------------------------------
# RSS Feeds for Macro Scout
# ---------------------------------------------------------------------------
MACRO_RSS_FEEDS = {
    "MarketWatch": "http://feeds.marketwatch.com/marketwatch/topstories/",
    "Google_Macro": "https://news.google.com/rss/search?q=federal+reserve+OR+inflation+OR+GDP&hl=en",
    "BBC_Business": "http://feeds.bbci.co.uk/news/business/rss.xml",
}

# ---------------------------------------------------------------------------
# Sentiment keywords
# ---------------------------------------------------------------------------
HAWKISH_KEYWORDS = [
    "rate hike", "tightening", "inflation concern", "restrictive",
    "hawkish", "higher rates", "quantitative tightening",
]
DOVISH_KEYWORDS = [
    "rate cut", "easing", "stimulus", "accommodative",
    "dovish", "lower rates", "quantitative easing",
]
SUPPLY_CHAIN_KEYWORDS = [
    "shortage", "disruption", "delay", "tariff", "sanctions",
    "supply chain", "chip shortage", "port congestion",
]

# ---------------------------------------------------------------------------
# FRED Series (optional — requires FRED_API_KEY in .env)
# ---------------------------------------------------------------------------
FRED_SERIES = {
    "10Y_YIELD": "DGS10",
    "VIX": "VIXCLS",
    "UNEMPLOYMENT": "UNRATE",
}
