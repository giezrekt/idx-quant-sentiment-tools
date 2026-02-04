import random

SECTOR_DATABASE = {
    "BBCA": "Finance",
    "BBRI": "Finance",
    "BMRI": "Finance",
    "BBNI": "Finance",
    "BBTN": "Finance",  
    "BRIS": "Finance",  
    "ARTO": "Finance",  
    "BNGA": "Finance",
    "NISP": "Finance",
    "MEGA": "Finance",

    "ADRO": "Energy",
    "PTBA": "Energy",
    "ITMG": "Energy",
    "BUMI": "Energy",   
    "HRUM": "Energy",
    "INDY": "Energy",
    "PGAS": "Energy",
    "MEDC": "Energy",
    "AKRA": "Energy",

    "MDKA": "Basic Materials",
    "ANTM": "Basic Materials",
    "INCO": "Basic Materials",
    "MBMA": "Basic Materials",
    "TINS": "Basic Materials",
    "BRMS": "Basic Materials",
    "SMGR": "Basic Materials",
    "INTP": "Basic Materials",
    "TPIA": "Basic Materials",
    "BRPT": "Basic Materials",

    "TLKM": "Infrastructure",
    "ISAT": "Infrastructure",
    "EXCL": "Infrastructure",
    "TOWR": "Infrastructure",
    "MTEL": "Infrastructure",
    "JSMR": "Infrastructure",
    "PTPP": "Infrastructure",
    "WIKA": "Infrastructure",

    "ICBP": "Consumer Non-Cyclicals",
    "INDF": "Consumer Non-Cyclicals",
    "MYOR": "Consumer Non-Cyclicals",
    "CMRY": "Consumer Non-Cyclicals",
    "AMRT": "Consumer Non-Cyclicals",
    "UNVR": "Consumer Non-Cyclicals",
    "GGRM": "Consumer Non-Cyclicals",
    "HMSP": "Consumer Non-Cyclicals",
    "CPIN": "Consumer Non-Cyclicals",
    "JPFA": "Consumer Non-Cyclicals",

    "GOTO": "Technology",
    "BUKA": "Technology",
    "EMTK": "Technology",
    "WIRG": "Technology",

    "ASII": "Industrials",
    "UNTR": "Industrials",
    "HEXA": "Industrials",

    "BSDE": "Property & Real Estate",
    "CTRA": "Property & Real Estate",
    "PWON": "Property & Real Estate",
    "SMRA": "Property & Real Estate",
    "PANI": "Property & Real Estate",

    "KLBF": "Healthcare",
    "MIKA": "Healthcare",
    "SILO": "Healthcare",
    "HEAL": "Healthcare",
}

def get_ticker_sector(ticker):
    """
    Returns the sector name for a given ticker.
    Returns 'Unknown' if not found in DB.
    """
    return SECTOR_DATABASE.get(ticker.upper(), "Unknown")

def get_diversification_candidates(current_sector, existing_watchlist=[]):
    """
    Returns a list of 3 random stock recommendations.
    
    Logic:
    1. Must be from a DIFFERENT sector than 'current_sector'.
    2. Must NOT be in 'existing_watchlist' (already owned).
    """
    candidates = []
    
    clean_watchlist = [t.upper() for t in existing_watchlist]

    for ticker, sector in SECTOR_DATABASE.items():
        if sector != current_sector:
            if ticker not in clean_watchlist:
                candidates.append(ticker)
    
    if len(candidates) >= 3:
        return random.sample(candidates, 3)
    
    return candidates