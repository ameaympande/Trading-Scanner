"""
Stock Universes for NSE Equities.

Provides predefined constituent lists for:
- NIFTY 50
- NIFTY NEXT 50
- NIFTY 100
- NIFTY 200
- NIFTY 500

Also includes sector mapping and liquidity metadata where available.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class UniverseStock:
    symbol: str
    company_name: str
    sector: str
    exchange: str = "NSE"


NIFTY_50_STOCKS: list[UniverseStock] = [
    UniverseStock("RELIANCE", "Reliance Industries Ltd.", "Energy"),
    UniverseStock("TCS", "Tata Consultancy Services Ltd.", "Information Technology"),
    UniverseStock("HDFCBANK", "HDFC Bank Ltd.", "Financial Services"),
    UniverseStock("ICICIBANK", "ICICI Bank Ltd.", "Financial Services"),
    UniverseStock("BHARTIARTL", "Bharti Airtel Ltd.", "Telecommunication"),
    UniverseStock("INFY", "Infosys Ltd.", "Information Technology"),
    UniverseStock("ITC", "ITC Ltd.", "Fast Moving Consumer Goods"),
    UniverseStock("SBIN", "State Bank of India", "Financial Services"),
    UniverseStock("LICI", "Life Insurance Corporation of India", "Financial Services"),
    UniverseStock("HINDUNILVR", "Hindustan Unilever Ltd.", "Fast Moving Consumer Goods"),
    UniverseStock("LT", "Larsen & Toubro Ltd.", "Construction"),
    UniverseStock("BAJFINANCE", "Bajaj Finance Ltd.", "Financial Services"),
    UniverseStock("HCLTECH", "HCL Technologies Ltd.", "Information Technology"),
    UniverseStock("MARUTI", "Maruti Suzuki India Ltd.", "Automobile and Auto Components"),
    UniverseStock("SUNPHARMA", "Sun Pharmaceutical Industries Ltd.", "Healthcare"),
    UniverseStock("ADANIENT", "Adani Enterprises Ltd.", "Metals & Mining"),
    UniverseStock("KOTAKBANK", "Kotak Mahindra Bank Ltd.", "Financial Services"),
    UniverseStock("TATAMOTORS", "Tata Motors Ltd.", "Automobile and Auto Components"),
    UniverseStock("AXISBANK", "Axis Bank Ltd.", "Financial Services"),
    UniverseStock("NTPC", "NTPC Ltd.", "Power"),
    UniverseStock("ONGC", "Oil & Natural Gas Corporation Ltd.", "Energy"),
    UniverseStock("TITAN", "Titan Company Ltd.", "Consumer Durables"),
    UniverseStock("POWERGRID", "Power Grid Corporation of India Ltd.", "Power"),
    UniverseStock("ADANIPORTS", "Adani Ports and Special Economic Zone Ltd.", "Services"),
    UniverseStock("WIPRO", "Wipro Ltd.", "Information Technology"),
    UniverseStock("ULTRACEMCO", "UltraTech Cement Ltd.", "Construction Materials"),
    UniverseStock("COALINDIA", "Coal India Ltd.", "Oil Gas & Consumable Fuels"),
    UniverseStock("BAJAJFINSV", "Bajaj Finserv Ltd.", "Financial Services"),
    UniverseStock("BAJAJ-AUTO", "Bajaj Auto Ltd.", "Automobile and Auto Components"),
    UniverseStock("NESTLEIND", "Nestle India Ltd.", "Fast Moving Consumer Goods"),
    UniverseStock("JSWSTEEL", "JSW Steel Ltd.", "Metals & Mining"),
    UniverseStock("GRASIM", "Grasim Industries Ltd.", "Construction Materials"),
    UniverseStock("M&M", "Mahindra & Mahindra Ltd.", "Automobile and Auto Components"),
    UniverseStock("TECHM", "Tech Mahindra Ltd.", "Information Technology"),
    UniverseStock("TATASTEEL", "Tata Steel Ltd.", "Metals & Mining"),
    UniverseStock("SBILIFE", "SBI Life Insurance Company Ltd.", "Financial Services"),
    UniverseStock("HDFCLIFE", "HDFC Life Insurance Company Ltd.", "Financial Services"),
    UniverseStock("BRITANNIA", "Britannia Industries Ltd.", "Fast Moving Consumer Goods"),
    UniverseStock("INDUSINDBK", "IndusInd Bank Ltd.", "Financial Services"),
    UniverseStock("HINDALCO", "Hindalco Industries Ltd.", "Metals & Mining"),
    UniverseStock("CIPLA", "Cipla Ltd.", "Healthcare"),
    UniverseStock("DRREDDY", "Dr. Reddy's Laboratories Ltd.", "Healthcare"),
    UniverseStock("EICHERMOT", "Eicher Motors Ltd.", "Automobile and Auto Components"),
    UniverseStock("DIVISLAB", "Divi's Laboratories Ltd.", "Healthcare"),
    UniverseStock("BPCL", "Bharat Petroleum Corporation Ltd.", "Energy"),
    UniverseStock("TATACONSUM", "Tata Consumer Products Ltd.", "Fast Moving Consumer Goods"),
    UniverseStock("APOLLOHOSP", "Apollo Hospitals Enterprise Ltd.", "Healthcare"),
    UniverseStock("ASIANPAINT", "Asian Paints Ltd.", "Consumer Durables"),
    UniverseStock("HEROMOTOCO", "Hero MotoCorp Ltd.", "Automobile and Auto Components"),
    UniverseStock("SHRIRAMFIN", "Shriram Finance Ltd.", "Financial Services"),
]

NIFTY_NEXT_50_STOCKS: list[UniverseStock] = [
    UniverseStock("ABB", "ABB India Ltd.", "Capital Goods"),
    UniverseStock("ADANIGREEN", "Adani Green Energy Ltd.", "Power"),
    UniverseStock("ADANIPOWER", "Adani Power Ltd.", "Power"),
    UniverseStock("ATGL", "Adani Total Gas Ltd.", "Oil Gas & Consumable Fuels"),
    UniverseStock("AMBUJACEM", "Ambuja Cements Ltd.", "Construction Materials"),
    UniverseStock("BANKBARODA", "Bank of Baroda", "Financial Services"),
    UniverseStock("BEL", "Bharat Electronics Ltd.", "Capital Goods"),
    UniverseStock("BOSCHLTD", "Bosch Ltd.", "Automobile and Auto Components"),
    UniverseStock("CANBK", "Canara Bank", "Financial Services"),
    UniverseStock("CHOLAFIN", "Cholamandalam Investment and Finance Company Ltd.", "Financial Services"),
    UniverseStock("COLPAL", "Colgate-Palmolive (India) Ltd.", "Fast Moving Consumer Goods"),
    UniverseStock("DLF", "DLF Ltd.", "Realty"),
    UniverseStock("DMART", "Avenue Supermarts Ltd.", "Consumer Services"),
    UniverseStock("GAIL", "GAIL (India) Ltd.", "Oil Gas & Consumable Fuels"),
    UniverseStock("GODREJCP", "Godrej Consumer Products Ltd.", "Fast Moving Consumer Goods"),
    UniverseStock("HAVELLS", "Havells India Ltd.", "Consumer Durables"),
    UniverseStock("HAL", "Hindustan Aeronautics Ltd.", "Capital Goods"),
    UniverseStock("ICICIGI", "ICICI Lombard General Insurance Co. Ltd.", "Financial Services"),
    UniverseStock("ICICIPRULI", "ICICI Prudential Life Insurance Co. Ltd.", "Financial Services"),
    UniverseStock("INDIGO", "InterGlobe Aviation Ltd.", "Services"),
    UniverseStock("IOC", "Indian Oil Corporation Ltd.", "Oil Gas & Consumable Fuels"),
    UniverseStock("IRCTC", "Indian Railway Catering and Tourism Corp. Ltd.", "Consumer Services"),
    UniverseStock("IRFC", "Indian Railway Finance Corporation Ltd.", "Financial Services"),
    UniverseStock("JINDALSTEL", "Jindal Steel & Power Ltd.", "Metals & Mining"),
    UniverseStock("JIOFIN", "Jio Financial Services Ltd.", "Financial Services"),
    UniverseStock("LTIM", "LTIMindtree Ltd.", "Information Technology"),
    UniverseStock("MARICO", "Marico Ltd.", "Fast Moving Consumer Goods"),
    UniverseStock("MOTHERSON", "Samvardhana Motherson International Ltd.", "Automobile and Auto Components"),
    UniverseStock("NAUKRI", "Info Edge (India) Ltd.", "Consumer Services"),
    UniverseStock("PIDILITIND", "Pidilite Industries Ltd.", "Chemicals"),
    UniverseStock("PFC", "Power Finance Corporation Ltd.", "Financial Services"),
    UniverseStock("PNB", "Punjab National Bank", "Financial Services"),
    UniverseStock("RECLTD", "REC Ltd.", "Financial Services"),
    UniverseStock("SIEMENS", "Siemens Ltd.", "Capital Goods"),
    UniverseStock("SRF", "SRF Ltd.", "Chemicals"),
    UniverseStock("TATAPOWER", "Tata Power Company Ltd.", "Power"),
    UniverseStock("TORNTPHARM", "Torrent Pharmaceuticals Ltd.", "Healthcare"),
    UniverseStock("TRENT", "Trent Ltd.", "Consumer Services"),
    UniverseStock("TVSHMOTOR", "TVS Motor Company Ltd.", "Automobile and Auto Components"),
    UniverseStock("UNITDSPR", "United Spirits Ltd.", "Fast Moving Consumer Goods"),
    UniverseStock("VBL", "Varun Beverages Ltd.", "Fast Moving Consumer Goods"),
    UniverseStock("VEDL", "Vedanta Ltd.", "Metals & Mining"),
    UniverseStock("ZOMATO", "Zomato Ltd.", "Consumer Services"),
    UniverseStock("ZYDUSLIFE", "Zydus Lifesciences Ltd.", "Healthcare"),
    UniverseStock("POLYCAB", "Polycab India Ltd.", "Capital Goods"),
    UniverseStock("PERSISTENT", "Persistent Systems Ltd.", "Information Technology"),
    UniverseStock("MAXHEALTH", "Max Healthcare Institute Ltd.", "Healthcare"),
    UniverseStock("MANKIND", "Mankind Pharma Ltd.", "Healthcare"),
    UniverseStock("CGPOWER", "CG Power and Industrial Solutions Ltd.", "Capital Goods"),
    UniverseStock("BHEL", "Bharat Heavy Electricals Ltd.", "Capital Goods"),
]

# NIFTY 100 is NIFTY 50 + NIFTY NEXT 50
NIFTY_100_STOCKS: list[UniverseStock] = NIFTY_50_STOCKS + NIFTY_NEXT_50_STOCKS

# Additional liquid stocks for Midcap / Nifty 200 / 500 coverage
NIFTY_MIDCAP_LIQUID: list[UniverseStock] = [
    UniverseStock("ASTRAL", "Astral Ltd.", "Building Materials"),
    UniverseStock("AUROPHARMA", "Aurobindo Pharma Ltd.", "Healthcare"),
    UniverseStock("BALKRISIND", "Balkrishna Industries Ltd.", "Automobile and Auto Components"),
    UniverseStock("BANDHANBNK", "Bandhan Bank Ltd.", "Financial Services"),
    UniverseStock("BATAINDIA", "Bata India Ltd.", "Consumer Durables"),
    UniverseStock("BERGEPAINT", "Berger Paints India Ltd.", "Consumer Durables"),
    UniverseStock("BHARATFORG", "Bharat Forge Ltd.", "Capital Goods"),
    UniverseStock("BIOCON", "Biocon Ltd.", "Healthcare"),
    UniverseStock("COFORGE", "Coforge Ltd.", "Information Technology"),
    UniverseStock("CONCOR", "Container Corporation of India Ltd.", "Services"),
    UniverseStock("CUMMINSIND", "Cummins India Ltd.", "Capital Goods"),
    UniverseStock("DEEPAKNTR", "Deepak Nitrite Ltd.", "Chemicals"),
    UniverseStock("DIXON", "Dixon Technologies (India) Ltd.", "Consumer Durables"),
    UniverseStock("ESCORTS", "Escorts Kubota Ltd.", "Capital Goods"),
    UniverseStock("FEDERALBNK", "The Federal Bank Ltd.", "Financial Services"),
    UniverseStock("GLENMARK", "Glenmark Pharmaceuticals Ltd.", "Healthcare"),
    UniverseStock("GMRINFRA", "GMR Airports Infrastructure Ltd.", "Services"),
    UniverseStock("GODREJPROP", "Godrej Properties Ltd.", "Realty"),
    UniverseStock("IDFCFIRSTB", "IDFC First Bank Ltd.", "Financial Services"),
    UniverseStock("INDIAMART", "IndiaMART InterMESH Ltd.", "Consumer Services"),
    UniverseStock("INDUSTOWER", "Indus Towers Ltd.", "Telecommunication"),
    UniverseStock("IPCALAB", "IPCA Laboratories Ltd.", "Healthcare"),
    UniverseStock("JUBLFOOD", "Jubilant Foodworks Ltd.", "Consumer Services"),
    UniverseStock("KPITTECH", "KPIT Technologies Ltd.", "Information Technology"),
    UniverseStock("L&TFH", "L&T Finance Holdings Ltd.", "Financial Services"),
    UniverseStock("LALPATHLAB", "Dr. Lal PathLabs Ltd.", "Healthcare"),
    UniverseStock("LICHSGFIN", "LIC Housing Finance Ltd.", "Financial Services"),
    UniverseStock("LUPIN", "Lupin Ltd.", "Healthcare"),
    UniverseStock("M&MFIN", "Mahindra & Mahindra Financial Services Ltd.", "Financial Services"),
    UniverseStock("METROPOLIS", "Metropolis Healthcare Ltd.", "Healthcare"),
    UniverseStock("MFSL", "Max Financial Services Ltd.", "Financial Services"),
    UniverseStock("MPHASIS", "Mphasis Ltd.", "Information Technology"),
    UniverseStock("MRF", "MRF Ltd.", "Automobile and Auto Components"),
    UniverseStock("MUTHOOTFIN", "Muthoot Finance Ltd.", "Financial Services"),
    UniverseStock("OBEROIRLTY", "Oberoi Realty Ltd.", "Realty"),
    UniverseStock("PAGEIND", "Page Industries Ltd.", "Textiles"),
    UniverseStock("PETRONET", "Petronet LNG Ltd.", "Oil Gas & Consumable Fuels"),
    UniverseStock("PIIND", "PI Industries Ltd.", "Chemicals"),
    UniverseStock("PRESTIGE", "Prestige Estates Projects Ltd.", "Realty"),
    UniverseStock("RAMCOCEM", "The Ramco Cements Ltd.", "Construction Materials"),
    UniverseStock("SAIL", "Steel Authority of India Ltd.", "Metals & Mining"),
    UniverseStock("SUNTV", "Sun TV Network Ltd.", "Media"),
    UniverseStock("SYNGENE", "Syngene International Ltd.", "Healthcare"),
    UniverseStock("TATACOMM", "Tata Communications Ltd.", "Telecommunication"),
    UniverseStock("TATAPOWER", "Tata Power Co. Ltd.", "Power"),
    UniverseStock("TORNTPOWER", "Torrent Power Ltd.", "Power"),
    UniverseStock("VOLTAS", "Voltas Ltd.", "Consumer Durables"),
    UniverseStock("WHIRLPOOL", "Whirlpool of India Ltd.", "Consumer Durables"),
    UniverseStock("YESBANK", "Yes Bank Ltd.", "Financial Services"),
    UniverseStock("ZEEL", "Zee Entertainment Enterprises Ltd.", "Media"),
]

NIFTY_200_STOCKS: list[UniverseStock] = NIFTY_100_STOCKS + NIFTY_MIDCAP_LIQUID

# Alias NIFTY 500 to the current combined set (can be extended with CSV/file load)
NIFTY_500_STOCKS: list[UniverseStock] = NIFTY_200_STOCKS


def get_universe_stocks(universe_name: str = "NIFTY_50") -> list[UniverseStock]:
    """
    Returns list of UniverseStock objects for a given universe name.
    Supported: NIFTY_50, NIFTY_NEXT_50, NIFTY_100, NIFTY_200, NIFTY_500
    """
    name = universe_name.upper().replace(" ", "_").replace("-", "_")
    mapping = {
        "NIFTY_50": NIFTY_50_STOCKS,
        "NIFTY50": NIFTY_50_STOCKS,
        "NIFTY_NEXT_50": NIFTY_NEXT_50_STOCKS,
        "NIFTYNEXT50": NIFTY_NEXT_50_STOCKS,
        "NIFTY_100": NIFTY_100_STOCKS,
        "NIFTY100": NIFTY_100_STOCKS,
        "NIFTY_200": NIFTY_200_STOCKS,
        "NIFTY200": NIFTY_200_STOCKS,
        "NIFTY_500": NIFTY_500_STOCKS,
        "NIFTY500": NIFTY_500_STOCKS,
    }
    if name not in mapping:
        available = list(mapping.keys())
        raise ValueError(f"Unknown universe '{universe_name}'. Available: {available}")
    return mapping[name]


def get_universe_symbols(universe_name: str = "NIFTY_50") -> list[str]:
    """Convenience helper to get just the list of symbols for a universe."""
    return [s.symbol for s in get_universe_stocks(universe_name)]
