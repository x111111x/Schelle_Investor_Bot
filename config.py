"""Central configuration for Project Alpha: Advisory."""

import os

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "data", "alpha.db")
LOG_PATH = os.path.join(BASE_DIR, "logs", "alpha.log")
SUBSCRIBERS_PATH = os.path.join(BASE_DIR, "data", "subscribers.json")

# ---------------------------------------------------------------------------
# Portfolio
# ---------------------------------------------------------------------------
INITIAL_CAPITAL = 50_000.0
MAX_POSITION_PCT = 0.10  # max 10% of portfolio per position
STOP_LOSS_PCT = 0.08     # 8% below entry low

# ---------------------------------------------------------------------------
# Watchlist — 500+ stocks across all major sectors and geographies
# ---------------------------------------------------------------------------
WATCHLIST = [
    # ===== US TECHNOLOGY (Mega Cap) =====
    "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "AVGO", "ORCL",
    "CRM", "ADBE", "AMD", "INTC", "CSCO", "IBM", "TXN", "QCOM",
    "NOW", "INTU", "AMAT", "MU", "LRCX", "ADI", "KLAC", "SNPS",
    "CDNS", "MRVL", "PANW", "CRWD", "FTNT", "WDAY", "TEAM", "DDOG",
    "ZS", "SNOW", "PLTR", "NET", "MNST", "MSTR", "SHOP",
    # US Technology (Mid Cap / Growth)
    "HUBS", "TTD", "OKTA", "ZM", "DOCU", "PINS", "SNAP", "U",
    "TWLO", "BILL", "PAYC", "PCTY", "MANH", "PTC",
    "EPAM", "GLOB", "FIVN", "CFLT", "MDB", "ESTC", "PATH",
    "SMCI", "ON", "MPWR", "SWKS", "QRVO", "NXPI", "MCHP", "GFS",

    # ===== US FINANCIALS (Banks) =====
    "JPM", "BAC", "WFC", "C", "GS", "MS", "USB", "PNC",
    "TFC", "SCHW", "BK", "STT", "CFG", "KEY", "HBAN", "RF",
    "FITB", "NTRS", "ZION", "CMA",
    # US Financials (Insurance)
    "BRK-B", "AIG", "MET", "PRU", "AFL", "TRV", "ALL", "PGR",
    "CB", "HIG", "CINF", "GL", "LNC",
    # US Financials (Payments & Fintech)
    "V", "MA", "PYPL", "SQ", "FIS", "FISV", "GPN", "AXP",
    "DFS", "COF", "SYF", "WU",
    # US Financials (Asset Managers / Exchanges)
    "BLK", "SPGI", "MCO", "MSCI", "ICE", "CME", "NDAQ", "CBOE",
    "AMG", "TROW", "BEN", "IVZ", "RJF", "LPL",

    # ===== US HEALTHCARE / PHARMA / BIOTECH =====
    "UNH", "JNJ", "LLY", "ABBV", "MRK", "PFE", "TMO", "ABT",
    "DHR", "BMY", "AMGN", "GILD", "ISRG", "MDT", "SYK", "BSX",
    "VRTX", "REGN", "ZTS", "CI", "ELV", "HCA", "IDXX", "EW",
    "DXCM", "IQV", "MTD", "A", "BDX", "BAX", "HOLX", "ALGN",
    "BIIB", "MRNA", "ILMN", "TECH", "CRL", "XRAY", "HSIC",
    "MOH", "CNC", "HUM", "CVS",

    # ===== US CONSUMER DISCRETIONARY =====
    # Retail
    "HD", "LOW", "TJX", "ROST", "DG", "DLTR", "ORLY", "AZO",
    "TSCO", "BBY", "EBAY", "ETSY", "W",
    # Auto
    "TSLA", "F", "GM", "RIVN", "LCID",
    # Luxury / Apparel
    "NKE", "LULU", "TPR", "RL", "PVH", "HAS", "MAT",
    # Media / Entertainment
    "DIS", "NFLX", "CMCSA", "WBD", "LYV", "CHTR",
    # Travel / Leisure
    "BKNG", "ABNB", "MAR", "HLT", "EXPE", "RCL", "CCL", "WYNN",
    "LVS", "MGM", "YUM", "MCD", "SBUX", "CMG", "DPZ", "QSR",

    # ===== US CONSUMER STAPLES =====
    "PG", "KO", "PEP", "COST", "WMT", "PM", "MO", "CL",
    "KMB", "GIS", "SJM", "HSY", "MDLZ", "KHC", "CAG",
    "CPB", "HRL", "TSN", "BG", "ADM", "STZ", "TAP", "SAM",
    "EL", "CHD", "CLX", "KR", "SYY",

    # ===== US INDUSTRIALS =====
    # Defense / Aerospace
    "RTX", "LMT", "BA", "NOC", "GD", "LHX", "HII", "TXT",
    "HWM", "TDG",
    # Machinery / Equipment
    "CAT", "DE", "HON", "MMM", "EMR", "ETN", "ROK", "IR",
    "PH", "DOV", "ITW", "SWK", "GWW", "FAST",
    # Logistics / Transport
    "UPS", "FDX", "UNP", "NSC", "CSX", "DAL", "UAL", "LUV",
    "JBHT", "XPO", "CHRW", "EXPD",
    # Other Industrials
    "GE", "WM", "RSG", "VRSK", "CTAS", "CPRT", "CARR", "OTIS",
    "AME", "NDSN", "AOS", "SNA",

    # ===== US ENERGY =====
    "XOM", "CVX", "COP", "EOG", "SLB", "MPC", "PSX", "VLO",
    "PXD", "DVN", "OXY", "FANG", "HAL", "BKR", "KMI",
    "WMB", "OKE", "TRGP", "ET",
    # Renewables / Clean Energy
    "NEE", "ENPH", "SEDG", "FSLR", "RUN", "PLUG", "BE",

    # ===== US MATERIALS =====
    "LIN", "APD", "SHW", "ECL", "DD", "DOW", "PPG", "NEM",
    "FCX", "NUE", "STLD", "CF", "MOS", "ALB", "CE", "EMN",
    "IP", "PKG", "AVY", "VMC", "MLM", "CRH",

    # ===== US REAL ESTATE (REITs) =====
    "AMT", "PLD", "CCI", "EQIX", "PSA", "SPG", "O", "DLR",
    "WELL", "AVB", "EQR", "VTR", "ARE", "MAA", "UDR", "ESS",
    "CPT", "SBAC", "VICI", "INVH", "GLPI", "MPW",

    # ===== US UTILITIES =====
    "DUK", "SO", "D", "AEP", "SRE", "EXC", "XEL",
    "ED", "WEC", "ES", "DTE", "PPL", "FE", "AEE", "CMS",
    "EVRG", "ATO", "NI", "PNW",

    # ===== US COMMUNICATION SERVICES =====
    "GOOG", "T", "VZ", "TMUS", "EA", "TTWO", "RBLX", "MTCH",
    "ZG", "YELP", "SPOT", "ROKU", "IMAX", "FOXA", "NWSA",

    # ===== EUROPE — United Kingdom =====
    "SHEL", "BP", "AZN", "GSK", "HSBC", "RIO", "BHP", "UL",
    "BTI", "DEO", "LYG", "BCS", "NWG", "VOD", "WPP", "LSXMK",
    "RELX", "ARM", "GLEN.L", "LSEG.L", "BARC.L",

    # ===== EUROPE — Germany =====
    "SAP", "SIE.DE", "ALV.DE", "DTE.DE", "BAS.DE", "MBG.DE",
    "BMW.DE", "VOW3.DE", "MUV2.DE", "ADS.DE", "DB",
    "IFX.DE", "HEN3.DE", "RWE.DE", "DHL.DE",

    # ===== EUROPE — France =====
    "TTE", "SNY", "STLA",
    "MC.PA", "OR.PA", "AIR.PA", "SU.PA", "BNP.PA", "SAN.PA",
    "AI.PA", "CS.PA", "DSY.PA", "KER.PA", "RI.PA",

    # ===== EUROPE — Netherlands =====
    "ASML", "ING", "QGEN", "PHG", "WKL.AS", "UNA.AS", "HEIA.AS",

    # ===== EUROPE — Switzerland =====
    "NESN.SW", "ROG.SW", "NOVN.SW", "UBSG.SW", "ZURN.SW",
    "ABB", "LONN.SW", "SREN.SW", "GIVN.SW",

    # ===== EUROPE — Spain =====
    "SAN", "BBVA", "IBE.MC", "ITX.MC",

    # ===== EUROPE — Italy =====
    "ENEL.MI", "ENI.MI", "ISP.MI", "UCG.MI", "RACE",

    # ===== EUROPE — Nordics =====
    "NVO", "ERIC", "VOLV-B.ST", "SAND.ST",
    "TELIA.ST", "NESTE.HE", "ORSTED.CO", "MAERSK-B.CO",
    "DANSKE.CO", "SWED-A.ST", "SHB-A.ST",

    # ===== EUROPE — Other =====
    "WIX",

    # ===== JAPAN =====
    "TM", "SONY", "MUFG", "SMFG", "MFG", "NMR", "HMC",
    "NTDOY", "IX", "OTCM",
    "7203.T", "6758.T", "9984.T", "6861.T", "8035.T",
    "6902.T", "4063.T", "6501.T", "7741.T",

    # ===== CHINA / HONG KONG =====
    "BABA", "TCEHY", "JD", "PDD", "BIDU", "NIO", "XPEV", "LI",
    "BEKE", "ZTO", "BILI", "TME", "VNET", "YMM", "MNSO",
    "0700.HK", "0941.HK", "1299.HK", "2318.HK", "3690.HK",
    "9618.HK", "9988.HK", "1810.HK", "0005.HK", "1398.HK",

    # ===== SOUTH KOREA =====
    "005930.KS", "000660.KS", "035420.KS",
    "PKX", "KB", "SHG", "LPL",

    # ===== INDIA (ADRs) =====
    "INFY", "WIT", "HDB", "IBN", "RDY", "SIFY", "TTM",
    "MMYT",

    # ===== AUSTRALIA =====
    "CBA.AX", "CSL.AX", "WES.AX", "WBC.AX", "ANZ.AX",
    "NAB.AX", "MQG.AX", "FMG.AX", "WDS.AX", "ALL.AX",

    # ===== CANADA =====
    "RY", "TD", "ENB", "CNQ", "BN", "BMO", "CP", "CNI",
    "TRP", "SU", "MFC", "CM", "BAM", "OTEX",
    "NTR", "FNV", "WFG", "ATD.TO", "L.TO",

    # ===== LATIN AMERICA — Brazil =====
    "VALE", "PBR", "ITUB", "BBD", "ABEV", "SBS", "EWZ",
    "NU", "XP", "STNE", "PAGS",
    "RENT3.SA", "WEGE3.SA",

    # ===== LATIN AMERICA — Mexico =====
    "AMX", "FMX", "CEMEX", "BSMX",
    "GFNORTEO.MX", "WALMEX.MX",

    # ===== SOUTHEAST ASIA =====
    "SE", "GRAB",
    "D05.SI", "O39.SI", "U11.SI",
    "BBCA.JK", "TLKM.JK",

    # ===== MIDDLE EAST =====
    "2222.SR",  # Saudi Aramco
    "EMAAR.AE",
    "CIB",      # Commercial International Bank (Egypt)

    # ===== TAIWAN =====
    "TSM", "2330.TW", "2454.TW", "2317.TW", "3711.TW",

    # ===== ADDITIONAL US LARGE CAPS =====
    # Semiconductors / Hardware
    "HPQ", "HPE", "DELL", "WDC", "STX", "KEYS", "TER", "ENTG",
    # Software / Internet
    "FICO", "GDDY", "GEN", "AKAM", "JNPR", "FFIV", "RPD",
    # Biotech / Specialty Pharma
    "ALNY", "BMRN", "EXAS", "INCY", "IONS", "NBIX", "PCVX", "SRPT",
    "UTHR", "RARE",
    # Financials — additional
    "ALLY", "EWBC", "WAL", "FRC", "SIVB", "IBKR", "LPLA",
    "MKTX", "VIRT", "HOOD",
    # Industrials — additional
    "PCAR", "GNRC", "TT", "AXON", "LDOS", "BAH", "CSGP",
    "HUBB", "WCC", "RBC",
    # Consumer — additional
    "DECK", "CROX", "BIRK", "GRMN", "POOL", "WSM", "RH",
    "ULTA", "FIVE", "OLLI",
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
# RSS Feeds for Macro Scout — 20+ global financial news sources
# All feeds are tried; individual failures are silently skipped.
# ---------------------------------------------------------------------------
MACRO_RSS_FEEDS = {
    # US wire services
    "Reuters_Business":   "https://feeds.reuters.com/reuters/businessNews",
    "Reuters_Finance":    "https://feeds.reuters.com/reuters/financialNews",
    "AP_Business":        "https://feeds.apnews.com/apf-business",
    # US financial media
    "MarketWatch":        "http://feeds.marketwatch.com/marketwatch/topstories/",
    "CNBC_Finance":       "https://www.cnbc.com/id/10000664/device/rss/rss.html",
    "CNBC_Economy":       "https://www.cnbc.com/id/20910258/device/rss/rss.html",
    "WSJ_Markets":        "https://feeds.a.dj.com/rss/RSSMarketsMain.xml",
    "Barrons":            "https://www.barrons.com/feed/",
    "Seeking_Alpha":      "https://seekingalpha.com/market_currents.xml",
    "Yahoo_Finance":      "https://finance.yahoo.com/news/rssindex",
    "Forbes_Business":    "https://www.forbes.com/business/feed/",
    # UK / European media
    "BBC_Business":       "http://feeds.bbci.co.uk/news/business/rss.xml",
    "Guardian_Business":  "https://www.theguardian.com/business/rss",
    "FT_Economy":         "https://www.ft.com/world/economy?format=rss",
    "Economist_Finance":  "https://www.economist.com/finance-and-economics/rss.xml",
    # Asia / Global
    "SCMP_Business":      "https://www.scmp.com/rss/92/feed",
    "Nikkei_Asia":        "https://asia.nikkei.com/rss/feed/nar",
    # Google News — targeted searches for key macro themes
    "Google_Fed":         "https://news.google.com/rss/search?q=federal+reserve+OR+inflation+OR+GDP&hl=en",
    "Google_Markets":     "https://news.google.com/rss/search?q=stock+market+OR+S%26P+500+OR+Dow+Jones&hl=en",
    "Google_Trade":       "https://news.google.com/rss/search?q=trade+tariffs+OR+global+economy+OR+recession&hl=en",
    "Google_Rates":       "https://news.google.com/rss/search?q=interest+rates+OR+bond+yields+OR+central+bank&hl=en",
    # NPR / public interest
    "NPR_Business":       "https://feeds.npr.org/1006/rss.xml",
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
