"""Report Builder — aggregates all module data into Telegram HTML."""

import html as _html

from utils.helpers import escape_html, now_china
from utils.logger import get_logger

logger = get_logger("report_builder")

# Telegram message limit
MAX_MSG_LEN = 4000  # leave some buffer under 4096

# Stock ticker to company name mapping
TICKER_TO_COMPANY = {
    # US Technology (Mega Cap)
    "AAPL": "Apple", "MSFT": "Microsoft", "GOOGL": "Alphabet (Google)",
    "AMZN": "Amazon", "NVDA": "NVIDIA", "META": "Meta (Facebook)",
    "AVGO": "Broadcom", "ORCL": "Oracle", "CRM": "Salesforce",
    "ADBE": "Adobe", "AMD": "AMD", "INTC": "Intel",
    "CSCO": "Cisco", "IBM": "IBM", "TXN": "Texas Instruments",
    "QCOM": "Qualcomm", "NOW": "ServiceNow", "INTU": "Intuit",
    "AMAT": "Applied Materials", "MU": "Micron", "LRCX": "Lam Research",
    "ADI": "Analog Devices", "KLAC": "KLA Corp", "SNPS": "Synopsys",
    "CDNS": "Cadence Design", "MRVL": "Marvell Technology",
    "PANW": "Palo Alto Networks", "CRWD": "CrowdStrike",
    "FTNT": "Fortinet", "WDAY": "Workday", "TEAM": "Atlassian",
    "DDOG": "Datadog", "ZS": "Zscaler", "SNOW": "Snowflake",
    "PLTR": "Palantir", "NET": "Cloudflare", "MNST": "Monster Beverage",
    "MSTR": "MicroStrategy", "SHOP": "Shopify",
    # US Technology (Mid Cap / Growth)
    "HUBS": "HubSpot", "TTD": "The Trade Desk", "OKTA": "Okta",
    "ZM": "Zoom", "DOCU": "DocuSign", "PINS": "Pinterest",
    "SNAP": "Snap", "U": "Unity Software", "TWLO": "Twilio",
    "BILL": "Bill.com", "PAYC": "Paycom", "PCTY": "Paylocity",
    "MANH": "Manhattan Associates", "ANSS": "Ansys", "PTC": "PTC",
    "EPAM": "EPAM Systems", "GLOB": "Globant", "FIVN": "Five9",
    "CFLT": "Confluent", "MDB": "MongoDB", "ESTC": "Elastic",
    "PATH": "UiPath", "SMCI": "Super Micro Computer",
    "ON": "ON Semiconductor", "MPWR": "Monolithic Power",
    "SWKS": "Skyworks", "QRVO": "Qorvo", "NXPI": "NXP Semiconductors",
    "MCHP": "Microchip Technology", "GFS": "GlobalFoundries",
    # US Financials (Banks)
    "JPM": "JPMorgan Chase", "BAC": "Bank of America",
    "WFC": "Wells Fargo", "C": "Citigroup", "GS": "Goldman Sachs",
    "MS": "Morgan Stanley", "USB": "U.S. Bancorp", "PNC": "PNC Financial",
    "TFC": "Truist", "SCHW": "Charles Schwab", "BK": "Bank of New York Mellon",
    "STT": "State Street", "CFG": "Citizens Financial",
    "KEY": "KeyCorp", "HBAN": "Huntington Bancshares",
    "RF": "Regions Financial", "FITB": "Fifth Third Bancorp",
    "NTRS": "Northern Trust", "ZION": "Zions Bancorp",
    "CMA": "Comerica",
    # US Financials (Insurance)
    "BRK-B": "Berkshire Hathaway", "AIG": "AIG",
    "MET": "MetLife", "PRU": "Prudential", "AFL": "Aflac",
    "TRV": "Travelers", "ALL": "Allstate", "PGR": "Progressive",
    "CB": "Chubb", "HIG": "Hartford Financial",
    "CINF": "Cincinnati Financial", "GL": "Globe Life",
    "LNC": "Lincoln National",
    # US Financials (Payments & Fintech)
    "V": "Visa", "MA": "Mastercard", "PYPL": "PayPal",
    "SQ": "Block (Square)", "FIS": "Fidelity National Info",
    "FISV": "Fiserv", "GPN": "Global Payments",
    "AXP": "American Express", "DFS": "Discover Financial",
    "COF": "Capital One", "SYF": "Synchrony Financial",
    "WU": "Western Union",
    # US Financials (Asset Managers / Exchanges)
    "BLK": "BlackRock", "SPGI": "S&P Global", "MCO": "Moody's",
    "MSCI": "MSCI", "ICE": "Intercontinental Exchange",
    "CME": "CME Group", "NDAQ": "Nasdaq Inc", "CBOE": "Cboe Global Markets",
    "AMG": "Affiliated Managers", "TROW": "T. Rowe Price",
    "BEN": "Franklin Templeton", "IVZ": "Invesco",
    "RJF": "Raymond James", "LPL": "LPL Financial",
    # US Healthcare / Pharma / Biotech
    "UNH": "UnitedHealth", "JNJ": "Johnson & Johnson",
    "LLY": "Eli Lilly", "ABBV": "AbbVie", "MRK": "Merck",
    "PFE": "Pfizer", "TMO": "Thermo Fisher", "ABT": "Abbott Labs",
    "DHR": "Danaher", "BMY": "Bristol-Myers Squibb",
    "AMGN": "Amgen", "GILD": "Gilead Sciences",
    "ISRG": "Intuitive Surgical", "MDT": "Medtronic",
    "SYK": "Stryker", "BSX": "Boston Scientific",
    "VRTX": "Vertex Pharma", "REGN": "Regeneron",
    "ZTS": "Zoetis", "CI": "Cigna", "ELV": "Elevance Health",
    "HCA": "HCA Healthcare", "IDXX": "IDEXX Labs",
    "EW": "Edwards Lifesciences", "DXCM": "DexCom",
    "IQV": "IQVIA", "MTD": "Mettler-Toledo", "A": "Agilent",
    "BDX": "Becton Dickinson", "BAX": "Baxter",
    "HOLX": "Hologic", "ALGN": "Align Technology",
    "BIIB": "Biogen", "MRNA": "Moderna", "ILMN": "Illumina",
    "TECH": "Bio-Techne", "CRL": "Charles River Labs",
    "XRAY": "Dentsply Sirona", "HSIC": "Henry Schein",
    "MOH": "Molina Healthcare", "CNC": "Centene",
    "HUM": "Humana", "CVS": "CVS Health",
    # US Consumer Discretionary (Retail)
    "HD": "Home Depot", "LOW": "Lowe's", "TJX": "TJX Companies",
    "ROST": "Ross Stores", "DG": "Dollar General",
    "DLTR": "Dollar Tree", "ORLY": "O'Reilly Automotive",
    "AZO": "AutoZone", "TSCO": "Tractor Supply",
    "BBY": "Best Buy", "EBAY": "eBay", "ETSY": "Etsy",
    "W": "Wayfair",
    # US Consumer Discretionary (Auto)
    "TSLA": "Tesla", "F": "Ford", "GM": "General Motors",
    "RIVN": "Rivian", "LCID": "Lucid Group",
    # US Consumer Discretionary (Luxury / Apparel)
    "NKE": "Nike", "LULU": "Lululemon", "TPR": "Tapestry",
    "RL": "Ralph Lauren", "PVH": "PVH Corp",
    "HAS": "Hasbro", "MAT": "Mattel",
    # US Consumer Discretionary (Media / Entertainment)
    "DIS": "Walt Disney", "NFLX": "Netflix", "CMCSA": "Comcast",
    "WBD": "Warner Bros Discovery", "PARA": "Paramount",
    "LYV": "Live Nation", "CHTR": "Charter Communications",
    # US Consumer Discretionary (Travel / Leisure / Restaurants)
    "BKNG": "Booking Holdings", "ABNB": "Airbnb",
    "MAR": "Marriott", "HLT": "Hilton", "EXPE": "Expedia",
    "RCL": "Royal Caribbean", "CCL": "Carnival",
    "WYNN": "Wynn Resorts", "LVS": "Las Vegas Sands",
    "MGM": "MGM Resorts", "YUM": "Yum! Brands",
    "MCD": "McDonald's", "SBUX": "Starbucks",
    "CMG": "Chipotle", "DPZ": "Domino's", "QSR": "Restaurant Brands Intl",
    # US Consumer Staples
    "PG": "Procter & Gamble", "KO": "Coca-Cola", "PEP": "PepsiCo",
    "COST": "Costco", "WMT": "Walmart", "PM": "Philip Morris",
    "MO": "Altria", "CL": "Colgate-Palmolive",
    "KMB": "Kimberly-Clark", "GIS": "General Mills",
    "K": "Kellanova", "SJM": "J.M. Smucker",
    "HSY": "Hershey", "MDLZ": "Mondelez", "KHC": "Kraft Heinz",
    "CAG": "Conagra", "CPB": "Campbell Soup", "HRL": "Hormel",
    "TSN": "Tyson Foods", "BG": "Bunge", "ADM": "Archer-Daniels-Midland",
    "STZ": "Constellation Brands", "TAP": "Molson Coors",
    "SAM": "Boston Beer", "EL": "Estee Lauder",
    "CHD": "Church & Dwight", "CLX": "Clorox",
    "KR": "Kroger", "SYY": "Sysco", "WBA": "Walgreens Boots Alliance",
    # US Industrials (Defense / Aerospace)
    "RTX": "RTX Corp (Raytheon)", "LMT": "Lockheed Martin",
    "BA": "Boeing", "NOC": "Northrop Grumman",
    "GD": "General Dynamics", "LHX": "L3Harris",
    "HII": "Huntington Ingalls", "TXT": "Textron",
    "HWM": "Howmet Aerospace", "TDG": "TransDigm",
    # US Industrials (Machinery / Equipment)
    "CAT": "Caterpillar", "DE": "John Deere", "HON": "Honeywell",
    "MMM": "3M", "EMR": "Emerson Electric", "ETN": "Eaton",
    "ROK": "Rockwell Automation", "IR": "Ingersoll Rand",
    "PH": "Parker-Hannifin", "DOV": "Dover Corp",
    "ITW": "Illinois Tool Works", "SWK": "Stanley Black & Decker",
    "GWW": "W.W. Grainger", "FAST": "Fastenal",
    # US Industrials (Logistics / Transport)
    "UPS": "UPS", "FDX": "FedEx", "UNP": "Union Pacific",
    "NSC": "Norfolk Southern", "CSX": "CSX Corp",
    "DAL": "Delta Air Lines", "UAL": "United Airlines",
    "LUV": "Southwest Airlines", "JBHT": "J.B. Hunt",
    "XPO": "XPO Inc", "CHRW": "C.H. Robinson", "EXPD": "Expeditors Intl",
    # US Industrials (Other)
    "GE": "GE Aerospace", "WM": "Waste Management",
    "RSG": "Republic Services", "VRSK": "Verisk Analytics",
    "CTAS": "Cintas", "CPRT": "Copart",
    "CARR": "Carrier Global", "OTIS": "Otis Worldwide",
    "AME": "Ametek", "NDSN": "Nordson", "AOS": "A.O. Smith",
    "SNA": "Snap-on",
    # US Energy
    "XOM": "ExxonMobil", "CVX": "Chevron", "COP": "ConocoPhillips",
    "EOG": "EOG Resources", "SLB": "Schlumberger",
    "MPC": "Marathon Petroleum", "PSX": "Phillips 66",
    "VLO": "Valero Energy", "PXD": "Pioneer Natural Resources",
    "DVN": "Devon Energy", "HES": "Hess Corp",
    "OXY": "Occidental Petroleum", "FANG": "Diamondback Energy",
    "HAL": "Halliburton", "BKR": "Baker Hughes",
    "KMI": "Kinder Morgan", "WMB": "Williams Companies",
    "OKE": "ONEOK", "TRGP": "Targa Resources",
    "ET": "Energy Transfer",
    # US Renewables / Clean Energy
    "NEE": "NextEra Energy", "ENPH": "Enphase Energy",
    "SEDG": "SolarEdge", "FSLR": "First Solar",
    "RUN": "Sunrun", "PLUG": "Plug Power", "BE": "Bloom Energy",
    # US Materials
    "LIN": "Linde", "APD": "Air Products", "SHW": "Sherwin-Williams",
    "ECL": "Ecolab", "DD": "DuPont", "DOW": "Dow Inc",
    "PPG": "PPG Industries", "NEM": "Newmont Mining",
    "FCX": "Freeport-McMoRan", "NUE": "Nucor",
    "STLD": "Steel Dynamics", "CF": "CF Industries",
    "MOS": "Mosaic", "ALB": "Albemarle", "CE": "Celanese",
    "EMN": "Eastman Chemical", "IP": "International Paper",
    "PKG": "Packaging Corp", "AVY": "Avery Dennison",
    "VMC": "Vulcan Materials", "MLM": "Martin Marietta",
    "CRH": "CRH plc",
    # US Real Estate (REITs)
    "AMT": "American Tower", "PLD": "Prologis",
    "CCI": "Crown Castle", "EQIX": "Equinix",
    "PSA": "Public Storage", "SPG": "Simon Property Group",
    "O": "Realty Income", "DLR": "Digital Realty",
    "WELL": "Welltower", "AVB": "AvalonBay",
    "EQR": "Equity Residential", "VTR": "Ventas",
    "ARE": "Alexandria Real Estate", "MAA": "Mid-America Apartment",
    "UDR": "UDR Inc", "ESS": "Essex Property",
    "CPT": "Camden Property", "SBAC": "SBA Communications",
    "VICI": "VICI Properties", "INVH": "Invitation Homes",
    "GLPI": "Gaming & Leisure Properties", "MPW": "Medical Properties Trust",
    # US Utilities
    "DUK": "Duke Energy", "SO": "Southern Company",
    "D": "Dominion Energy", "AEP": "American Electric Power",
    "SRE": "Sempra Energy", "EXC": "Exelon",
    "XEL": "Xcel Energy", "ED": "Consolidated Edison",
    "WEC": "WEC Energy", "ES": "Eversource Energy",
    "DTE": "DTE Energy", "PPL": "PPL Corp",
    "FE": "FirstEnergy", "AEE": "Ameren",
    "CMS": "CMS Energy", "EVRG": "Evergy",
    "ATO": "Atmos Energy", "NI": "NiSource",
    "PNW": "Pinnacle West",
    # US Communication Services
    "GOOG": "Alphabet (Google)", "T": "AT&T", "VZ": "Verizon",
    "TMUS": "T-Mobile", "EA": "Electronic Arts",
    "TTWO": "Take-Two Interactive", "RBLX": "Roblox",
    "MTCH": "Match Group", "ZG": "Zillow", "YELP": "Yelp",
    "SPOT": "Spotify", "ROKU": "Roku", "IMAX": "IMAX Corp",
    "FOXA": "Fox Corp", "NWSA": "News Corp",
    # Europe — United Kingdom
    "SHEL": "Shell", "BP": "BP", "AZN": "AstraZeneca",
    "GSK": "GSK plc", "HSBC": "HSBC", "RIO": "Rio Tinto",
    "BHP": "BHP Group", "UL": "Unilever", "BTI": "British American Tobacco",
    "DEO": "Diageo", "LYG": "Lloyds Banking Group",
    "BCS": "Barclays", "NWG": "NatWest Group",
    "VOD": "Vodafone", "WPP": "WPP plc",
    "LSXMK": "Liberty Media", "RELX": "RELX Group",
    "ARM": "ARM Holdings", "GLEN.L": "Glencore",
    "LSEG.L": "London Stock Exchange Group", "BARC.L": "Barclays (London)",
    # Europe — Germany
    "SIE.DE": "Siemens", "ALV.DE": "Allianz",
    "DTE.DE": "Deutsche Telekom", "BAS.DE": "BASF",
    "MBG.DE": "Mercedes-Benz", "BMW.DE": "BMW",
    "VOW3.DE": "Volkswagen", "MUV2.DE": "Munich Re",
    "ADS.DE": "Adidas", "DB": "Deutsche Bank",
    "IFX.DE": "Infineon", "HEN3.DE": "Henkel",
    "RWE.DE": "RWE", "DHL.DE": "DHL Group",
    # Europe — France
    "TTE": "TotalEnergies", "SNY": "Sanofi", "STLA": "Stellantis",
    "MC.PA": "LVMH", "OR.PA": "L'Oreal", "AIR.PA": "Airbus",
    "SU.PA": "Schneider Electric", "BNP.PA": "BNP Paribas",
    "SAN.PA": "Sanofi (Paris)", "AI.PA": "Air Liquide",
    "CS.PA": "AXA", "DSY.PA": "Dassault Systemes",
    "KER.PA": "Kering", "RI.PA": "Pernod Ricard",
    # Europe — Netherlands
    "ASML": "ASML", "ING": "ING Group", "QGEN": "Qiagen",
    "PHG": "Philips", "WKL.AS": "Wolters Kluwer",
    "UNA.AS": "Unilever (Amsterdam)", "HEIA.AS": "Heineken",
    # Europe — Switzerland
    "NESN.SW": "Nestle", "ROG.SW": "Roche",
    "NOVN.SW": "Novartis", "UBSG.SW": "UBS",
    "ZURN.SW": "Zurich Insurance", "ABB": "ABB Ltd",
    "LONN.SW": "Lonza", "SREN.SW": "Swiss Re",
    "GIVN.SW": "Givaudan",
    # Europe — Spain
    "TEF": "Telefonica", "SAN": "Banco Santander",
    "BBVA": "BBVA", "IBE.MC": "Iberdrola", "ITX.MC": "Inditex (Zara)",
    # Europe — Italy
    "ENEL.MI": "Enel", "ENI.MI": "Eni", "ISP.MI": "Intesa Sanpaolo",
    "UCG.MI": "UniCredit", "RACE": "Ferrari",
    # Europe — Nordics
    "NVO": "Novo Nordisk", "ERIC": "Ericsson",
    "VOLV-B.ST": "Volvo", "SAND.ST": "Sandvik",
    "TELIA.ST": "Telia", "NESTE.HE": "Neste",
    "ORSTED.CO": "Orsted", "MAERSK-B.CO": "Maersk",
    "NOKIA": "Nokia", "DANSKE.CO": "Danske Bank",
    "SWED-A.ST": "Swedbank", "SHB-A.ST": "Handelsbanken",
    # Europe — Other
    "WIX": "Wix.com",
    # Japan
    "TM": "Toyota", "SONY": "Sony", "MUFG": "Mitsubishi UFJ Financial",
    "SMFG": "Sumitomo Mitsui Financial", "MFG": "Mizuho Financial",
    "NMR": "Nomura", "HMC": "Honda",
    "NTDOY": "Nintendo", "IX": "Orix Corp", "OTCM": "OTC Markets",
    "7203.T": "Toyota (Tokyo)", "6758.T": "Sony (Tokyo)",
    "9984.T": "SoftBank", "6861.T": "Keyence",
    "8035.T": "Tokyo Electron", "6902.T": "Denso",
    "4063.T": "Shin-Etsu Chemical", "6501.T": "Hitachi",
    "7741.T": "HOYA",
    # China / Hong Kong
    "BABA": "Alibaba", "TCEHY": "Tencent (OTC)",
    "JD": "JD.com", "PDD": "PDD Holdings (Pinduoduo)",
    "BIDU": "Baidu", "NIO": "NIO", "XPEV": "XPeng",
    "LI": "Li Auto", "BEKE": "KE Holdings",
    "ZTO": "ZTO Express", "BILI": "Bilibili",
    "TME": "Tencent Music", "VNET": "VNET Group",
    "YMM": "Full Truck Alliance", "MNSO": "Miniso",
    "0700.HK": "Tencent (HK)", "0941.HK": "China Mobile",
    "1299.HK": "AIA Group", "2318.HK": "Ping An Insurance",
    "3690.HK": "Meituan", "9618.HK": "JD.com (HK)",
    "9988.HK": "Alibaba (HK)", "1810.HK": "Xiaomi",
    "0005.HK": "HSBC (HK)", "1398.HK": "ICBC",
    # South Korea
    "005930.KS": "Samsung Electronics", "000660.KS": "SK Hynix",
    "035420.KS": "Naver", "PKX": "POSCO",
    "KB": "KB Financial Group", "SHG": "Shinhan Financial",
    # India (ADRs)
    "INFY": "Infosys", "WIT": "Wipro", "HDB": "HDFC Bank",
    "IBN": "ICICI Bank", "RDY": "Dr. Reddy's Labs",
    "SIFY": "Sify Technologies", "TTM": "Tata Motors",
    "WNS": "WNS Holdings", "MMYT": "MakeMyTrip",
    # Australia
    "CBA.AX": "Commonwealth Bank", "CSL.AX": "CSL Limited",
    "WES.AX": "Wesfarmers", "WBC.AX": "Westpac",
    "ANZ.AX": "ANZ Group", "NAB.AX": "National Australia Bank",
    "MQG.AX": "Macquarie Group", "FMG.AX": "Fortescue Metals",
    "WDS.AX": "Woodside Energy", "ALL.AX": "Aristocrat Leisure",
    # Canada
    "RY": "Royal Bank of Canada", "TD": "Toronto-Dominion Bank",
    "ENB": "Enbridge", "CNQ": "Canadian Natural Resources",
    "BN": "Brookfield Corp", "BMO": "Bank of Montreal",
    "CP": "Canadian Pacific Kansas City", "CNI": "Canadian National Railway",
    "TRP": "TC Energy", "SU": "Suncor Energy",
    "MFC": "Manulife Financial", "CM": "CIBC",
    "BAM": "Brookfield Asset Management", "OTEX": "OpenText",
    "NTR": "Nutrien", "FNV": "Franco-Nevada", "WFG": "West Fraser Timber",
    "ATD.TO": "Alimentation Couche-Tard", "L.TO": "Loblaw",
    # Latin America — Brazil
    "VALE": "Vale", "PBR": "Petrobras", "ITUB": "Itau Unibanco",
    "BBD": "Banco Bradesco", "ABEV": "Ambev",
    "SBS": "SABESP", "EWZ": "iShares MSCI Brazil ETF",
    "NU": "Nu Holdings", "XP": "XP Inc",
    "STNE": "StoneCo", "PAGS": "PagSeguro",
    "BRBR3.SA": "BRF SA", "RENT3.SA": "Localiza",
    "WEGE3.SA": "WEG SA",
    # Latin America — Mexico
    "AMX": "America Movil", "FMX": "FEMSA",
    "CEMEX": "Cemex", "BSMX": "Banco Santander Mexico",
    "GFNORTEO.MX": "Banorte", "WALMEX.MX": "Walmart Mexico",
    # Southeast Asia
    "SE": "Sea Limited", "GRAB": "Grab Holdings",
    "D05.SI": "DBS Group", "O39.SI": "OCBC Bank",
    "U11.SI": "United Overseas Bank",
    "BBCA.JK": "Bank Central Asia", "TLKM.JK": "Telkom Indonesia",
    # Middle East
    "2222.SR": "Saudi Aramco", "EMAAR.AE": "Emaar Properties",
    "CIB": "Commercial Intl Bank (Egypt)",
    "QNB.QA": "Qatar National Bank", "FAB.AE": "First Abu Dhabi Bank",
    # Taiwan
    "TSM": "Taiwan Semiconductor", "2330.TW": "TSMC (Taipei)",
    "2454.TW": "MediaTek", "2317.TW": "Hon Hai (Foxconn)",
    "3711.TW": "ASE Technology",
    # Additional US Large Caps — Semiconductors / Hardware
    "HPQ": "HP Inc", "HPE": "Hewlett Packard Enterprise",
    "DELL": "Dell Technologies", "WDC": "Western Digital",
    "STX": "Seagate", "KEYS": "Keysight Technologies",
    "TER": "Teradyne", "ENTG": "Entegris",
    # Additional US — Software / Internet
    "FICO": "Fair Isaac (FICO)", "GDDY": "GoDaddy",
    "GEN": "Gen Digital", "AKAM": "Akamai",
    "JNPR": "Juniper Networks", "FFIV": "F5 Networks",
    "RPD": "Rapid7",
    # Additional US — Biotech / Specialty Pharma
    "ALNY": "Alnylam Pharma", "BMRN": "BioMarin",
    "EXAS": "Exact Sciences", "INCY": "Incyte",
    "IONS": "Ionis Pharma", "NBIX": "Neurocrine Biosciences",
    "PCVX": "Vaxcyte", "SRPT": "Sarepta Therapeutics",
    "UTHR": "United Therapeutics", "RARE": "Ultragenyx Pharma",
    # Additional US — Financials
    "ALLY": "Ally Financial", "EWBC": "East West Bancorp",
    "WAL": "Western Alliance", "FRC": "First Republic Bank",
    "SIVB": "SVB Financial", "IBKR": "Interactive Brokers",
    "LPLA": "LPL Financial Holdings",
    "MKTX": "MarketAxess", "VIRT": "Virtu Financial",
    "HOOD": "Robinhood",
    # Additional US — Industrials
    "PCAR": "PACCAR", "GNRC": "Generac",
    "TT": "Trane Technologies", "AXON": "Axon Enterprise",
    "LDOS": "Leidos", "BAH": "Booz Allen Hamilton",
    "CSGP": "CoStar Group", "HUBB": "Hubbell",
    "WCC": "WESCO International", "RBC": "RBC Bearings",
    # Additional US — Consumer
    "DECK": "Deckers Outdoor", "CROX": "Crocs",
    "BIRK": "Birkenstock", "GRMN": "Garmin",
    "POOL": "Pool Corp", "WSM": "Williams-Sonoma",
    "RH": "RH (Restoration Hardware)", "ULTA": "Ulta Beauty",
    "FIVE": "Five Below", "OLLI": "Ollie's Bargain Outlet",
}


class ReportBuilder:
    def build(
        self,
        macro: dict,
        picks: list[dict],
        sentiment: dict,
        snapshot: dict,
        performance: dict,
    ) -> list[str]:
        """Build the full Executive Alpha Briefing and return as list of message strings."""
        sections = []

        # Header
        date_str = now_china().strftime("%Y-%m-%d %H:%M CST")
        sections.append(self._build_header(date_str))

        # Executive Summary
        sections.append(self._build_executive_summary(macro, sentiment))

        # Macro Outlook
        sections.append(self._build_macro_section(macro))

        # Stock Recommendations (each as its own section to allow splitting)
        rec_sections = self._build_recommendations(picks, sentiment)
        sections.extend(rec_sections)

        # Join and split into Telegram-safe messages
        return self._split_messages(sections)

    def _build_header(self, date_str: str) -> str:
        d = escape_html(date_str)
        return f"<b>📊 DAILY INVESTMENT BRIEF</b>\n<i>{d}</i>"

    def _build_executive_summary(self, macro: dict, sentiment: dict) -> str:
        mood = sentiment.get("overall_market_mood", "Neutral")
        mood_emoji = self._mood_to_emoji(mood)
        summary = escape_html(macro.get("macro_summary", "Data unavailable"))
        return (
            f"\n<b>🎯 QUICK SUMMARY</b>\n"
            f"Market Feeling: <b>{mood_emoji} {escape_html(mood)}</b>\n"
            f"{summary}"
        )

    @staticmethod
    def _mood_to_emoji(mood: str) -> str:
        """Convert mood to emoji."""
        mood_lower = mood.lower()
        if "bullish" in mood_lower or "positive" in mood_lower:
            return "😊"
        elif "bearish" in mood_lower or "negative" in mood_lower:
            return "😟"
        else:
            return "😐"

    def _build_macro_section(self, macro: dict) -> str:
        risk = escape_html(macro.get("risk_level", "N/A"))
        fed = escape_html(macro.get("fed_sentiment", "N/A"))
        fed_detail = escape_html(macro.get("fed_detail", ""))

        lines = [
            f"\n<b>🌍 BIG PICTURE OUTLOOK</b>",
            f"Overall Market Risk: <b>{risk}</b>",
            f"What the Fed Is Doing: <b>{fed}</b>",
            f"<i>{fed_detail}</i>",
        ]

        events = macro.get("key_events", [])
        if events:
            lines.append("\nImportant News:")
            for evt in events[:5]:
                title = escape_html(evt["title"][:100])
                link = evt.get("link", "")
                if link:
                    safe_url = _html.escape(link, quote=True)
                    lines.append(f'  • <a href="{safe_url}">{title}</a>')
                else:
                    lines.append(f"  • {title}")

        fred = macro.get("fred_data", {})
        if fred:
            parts = []
            if "10Y_YIELD" in fred:
                yield_val = fred['10Y_YIELD']
                parts.append(f"10-Year Bond Yield: {escape_html(str(yield_val))}%")
            if "VIX" in fred:
                vix_val = fred['VIX']
                vix_status = "High Fear" if float(vix_val) > 25 else "Normal"
                parts.append(f"Fear Index: {escape_html(str(vix_val))} ({vix_status})")
            if parts:
                lines.append("\nKey Numbers:")
                for part in parts:
                    lines.append(f"  • {part}")

        return "\n".join(lines)

    def _build_recommendations(self, picks: list[dict], sentiment: dict) -> list[str]:
        sections = ["\n<b>📈 WHAT TO BUY OR SELL TODAY</b>"]

        actionable = [p for p in picks if p["action"] in ("Buy", "Sell")]
        if not actionable:
            sections.append("<i>No changes recommended today. Hold steady.</i>")
            return sections

        for pick in actionable[:8]:
            ticker = pick["ticker"]
            company = TICKER_TO_COMPANY.get(ticker, ticker)
            action = pick["action"]
            action_emoji = "🟢 BUY" if action == "Buy" else "🔴 SELL"

            tick_sent = sentiment.get("ticker_sentiments", {}).get(ticker, {})
            trend = escape_html(tick_sent.get("trend", "Neutral"))

            current = f"${pick.get('current_price', 0):.2f}"
            entry_low = f"${pick.get('entry_price_low', 0):.2f}"
            entry_high = f"${pick.get('entry_price_high', 0):.2f}"
            stop = f"${pick.get('stop_loss', 0):.2f}"
            conf = pick.get("confidence", 0)
            rationale = escape_html(pick.get("rationale", "")[:150])

            block = (
                f"\n<b>{escape_html(company)}</b> ({escape_html(ticker)}) — <b>{action_emoji}</b>\n"
                f"  Current Price: <b>{escape_html(current)}</b>\n"
                f"  Good Price to Buy: {escape_html(entry_low)} - {escape_html(entry_high)}\n"
                f"  Exit Point (If Loss): {escape_html(stop)}\n"
                f"  Confidence: <b>{conf}/10</b> (higher is better)\n"
                f"  Market Outlook: {trend}\n"
                f"  Why: <i>{rationale}</i>"
            )
            sections.append(block)

        return sections

    def _build_portfolio_section(self, snapshot: dict, performance: dict) -> str:
        total = f"${snapshot.get('total_value', 0):,.2f}"
        cash = f"${snapshot.get('cash', 0):,.2f}"
        ret = f"{snapshot.get('return_pct', 0):.2f}%"
        spy_ret = f"{performance.get('spy_return', 0):.2f}%"
        alpha = f"{performance.get('alpha', 0):.2f}%"
        capital = "$50,000"

        ret_color = "📈" if float(ret.rstrip('%')) >= 0 else "📉"
        alpha_color = "✅" if float(alpha.rstrip('%')) >= 0 else "⚠️"

        lines = [
            f"\n<b>💼 YOUR PAPER PORTFOLIO</b>",
            f"Started With: {escape_html(capital)}",
            f"Worth Today: <b>{escape_html(total)}</b>",
            f"Cash on Hand: {escape_html(cash)}",
            f"Your Gain/Loss: <b>{ret_color} {escape_html(ret)}</b>",
            f"Market Benchmark (S&amp;P 500): {escape_html(spy_ret)}",
            f"You vs Market: <b>{alpha_color} {escape_html(alpha)}</b>",
        ]

        positions = snapshot.get("positions", [])
        if positions:
            lines.append("\nStocks You Own:")
            for pos in positions:
                ticker = pos["ticker"]
                company = TICKER_TO_COMPANY.get(ticker, ticker)
                sh = int(pos["shares"])
                avg = f"${pos['avg_cost']:.2f}"
                cur = f"${pos['current_price']:.2f}"
                pct = f"{pos['pct_change']:.1f}%"
                pct_emoji = "📈" if pos['pct_change'] >= 0 else "📉"
                lines.append(
                    f"  • {escape_html(company)} ({escape_html(ticker)}): "
                    f"{sh} shares | "
                    f"Cost: {escape_html(avg)} → Now: {escape_html(cur)} "
                    f"{pct_emoji} {escape_html(pct)}"
                )
        else:
            lines.append("\n<i>No stocks owned yet.</i>")

        return "\n".join(lines)

    def _build_footer(self) -> str:
        return (
            f"\n<i>⚠️ This is a practice portfolio (no real money invested)</i>\n"
            f"<i>Project Alpha • Automated Daily Report</i>"
        )

    def _split_messages(self, sections: list[str]) -> list[str]:
        """Split sections into messages that fit Telegram's limit."""
        messages = []
        current = ""

        for section in sections:
            if len(current) + len(section) + 1 > MAX_MSG_LEN:
                if current:
                    messages.append(current)
                current = section
            else:
                current = current + "\n" + section if current else section

        if current:
            messages.append(current)

        return messages if messages else ["<i>No data available for today's report.</i>"]
