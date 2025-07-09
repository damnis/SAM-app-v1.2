#'tickerlijsten
# --- Update tab labels en bijbehorende mapping ---

# to script = from tickers import (
#    aex_tickers, amx_tickers, dow_tickers, eurostoxx_tickers,
#    nasdaq_tickers, ustech_tickers, crypto_tickers,
#    tabs_mapping, tab_labels, valutasymbool
#)


# to script from tickers import ustech_tickers, nasdaq_tickers, dow_tickers, aex_tickers, amx_tickers, eurostoxx_tickers, crypto_tickers
aex_tickers = {
"ABN.AS": "ABN AMRO", "ADYEN.AS": "Adyen", "AGN.AS": "Aegon", "AD.AS": "Ahold Delhaize", 
"AKZA.AS": "Akzo Nobel", "MT.AS": "ArcelorMittal", "ASM.AS": "ASM International", "ASML.AS": "ASML Holding", "ASRNL.AS": "ASR Nederland",
"BESI.AS": "BESI", "DSFIR.AS": "DSM-Firmenich", "GLPG.AS": "Galapagos", "HEIA.AS": "Heineken", 
"IMCD.AS": "IMCD", "INGA.AS": "ING Groep", "TKWY.AS": "Just Eat Takeaway", "KPN.AS": "KPN",
"NN.AS": "NN Group", "PHIA.AS": "Philips", "PRX.AS": "Prosus", "RAND.AS": "Randstad",
"REN.AS": "Relx", "SHELL.AS": "Shell", "UNA.AS": "Unilever", "WKL.AS": "Wolters Kluwer"
}

dow_tickers = {
    'MMM': '3M', 'AXP': 'American Express', 'AMGN': 'Amgen', 'AAPL': 'Apple', 'BA': 'Boeing',
    'CAT': 'Caterpillar', 'CVX': 'Chevron', 'CSCO': 'Cisco', 'KO': 'Coca-Cola', 'DIS': 'Disney',
    'GS': 'Goldman Sachs', 'HD': 'Home Depot', 'HON': 'Honeywell', 'IBM': 'IBM', 'INTC': 'Intel',
    'JPM': 'JPMorgan Chase', 'JNJ': 'Johnson & Johnson', 'MCD': 'McDonaldâ€™s', 'MRK': 'Merck',
    'MSFT': 'Microsoft', 'NKE': 'Nike', 'PG': 'Procter & Gamble', 'CRM': 'Salesforce',
    'TRV': 'Travelers', 'UNH': 'UnitedHealth', 'VZ': 'Verizon', 'V': 'Visa', 'WMT': 'Walmart',
    'DOW': 'Dow', 'RTX': 'RTX Corp.', 'WBA': 'Walgreens Boots'
}
nasdaq_tickers = {
    'MSFT': 'Microsoft', 'NVDA': 'NVIDIA', 'ASML': 'ASML', 'AAPL': 'Apple', 'AMZN': 'Amazon', 'META': 'Meta',
    'NFLX': 'Netflix', 'GOOG': 'Google', 'GOOGL': 'Alphabet', 'TSLA': 'Tesla', 'CSCO': 'Cisco',
    'INTC': 'Intel', 'ADBE': 'Adobe', 'CMCSA': 'Comcast', 'PEP': 'PepsiCo', 'COST': 'Costco',
    'AVGO': 'Broadcom', 'QCOM': 'Qualcomm', 'TMUS': 'T-Mobile', 'TXN': 'Texas Instruments',
    'AMAT': 'Applied Materials'
}

ustech_tickers = {
    "SMCI": "Super Micro Computer", "PLTR": "Palantir", "ORCL": "Oracle", "SNOW": "Snowflake",
    "NVDA": "NVIDIA", "AMD": "AMD", "MDB": "MongoDB", "DDOG": "Datadog", "CRWD": "CrowdStrike",
    "ZS": "Zscaler", "TSLA": "Tesla", "AAPL": "Apple", "GOOGL": "Alphabet (GOOGL)",
    "MSFT": "Microsoft"
}
eurostoxx_tickers = {
    'ASML.AS': 'ASML Holding', 'AIR.PA': 'Airbus', 'BAS.DE': 'BASF', 'BAYN.DE': 'Bayer',
    'BNP.PA': 'BNP Paribas', 'MBG.DE': 'Mercedes-Benz Group', 'ENEL.MI': 'Enel',
    'ENGI.PA': 'Engie', 'IBE.MC': 'Iberdrola', 'MC.PA': 'LVMH', 'OR.PA': 'L’Oréal',
    'PHIA.AS': 'Philips', 'SAN.PA': 'Sanofi', 'SAP.DE': 'SAP', 'SIE.DE': 'Siemens',
    'SU.PA': 'Schneider Electric', 'TTE.PA': 'TotalEnergies', 'VIV.PA': 'Vivendi',
    'AD.AS': 'Ahold Delhaize', 'CRH.L': 'CRH', 'DPW.DE': 'Deutsche Post', 'IFX.DE': 'Infineon',
    'ITX.MC': 'Inditex', 'MT.AS': 'ArcelorMittal', 'RI.PA': 'Pernod Ricard', 'STLA.MI': 'Stellantis',
    'UN01.DE': 'Uniper'
}
# --- Toevoeging tickers AMX & Crypto ---
amx_tickers = {
    "AF.PA": "Air France-KLM SA", "APAM.AS": "Aperam S.A.",
    "ARCAD.AS": "Arcadis NV", "BAMNB.AS": "Koninklijke BAM Groep nv", "BESI.AS": "BE Semiconductor Industries N.V.",
    "BFIT.AS": "Basic-Fit N.V.", "CRBN.AS": "Corbion N.V.", "ECMPA.AS": "Eurocommercial Properties N.V.",
    "FAGR.BR": "Fagron NV", "FLOW.AS": "Flow Traders Ltd.", "FUR.AS": "Fugro N.V.",
    "LIGHT.AS": "Signify N.V.", "NSI.AS": "NSI N.V.", "OCI.AS": "OCI N.V.", "PHARM.AS": "Pharming Group N.V.",
    "PNL.AS": "PostNL N.V.", "SBMO.AS": "SBM Offshore N.V.", "TWEKA.AS": "TKH Group N.V.",
    "VPK.AS": "Koninklijke Vopak N.V.", "WDP.BR": "Warehouses De Pauw SA",
    "AMG.AS": "AMG", "AALB.AS": "Aalberts N.V.", "KENDR.AS": "Kendrion", "TKWY.AS": "Just Eat", "VASTN.AS": "Vastned Retail"
}

crypto_tickers = {
    "BTC-USD": "Bitcoin", "ETH-USD": "Ethereum", "SOL-USD": "Solana",
    "BNB-USD": "BNB", "XRP-USD": "XRP", "DOGE-USD": "Dogecoin"
}

mijn_lijst = {
    "ASM.AS": "ASM International", "ASML.AS": "ASML Holding", "AMZN": "Amazon",
    "SMCI": "Super Micro Computer", "PLTR": "Palantir", "ORCL": "Oracle",
    "NVDA": "NVIDIA", "AVGO": "Broadcom", "TSLA": "Tesla", "AAPL": "Apple",
    "GOOGL": "Alphabet (GOOGL)", "MSFT": "Microsoft", "META": "Meta Platforms"
}




# --- Mapping beurs tabs en tickers ---
tabs_mapping = {
    "🇺🇸 Dow Jones": dow_tickers,
    "🇺🇸 Nasdaq": nasdaq_tickers,
    "🇺🇸 US Tech": ustech_tickers,
    "🇪🇺 Eurostoxx": eurostoxx_tickers,
    "📌 Mijn lijst": mijn_lijst,
    "🇳🇱 AEX": aex_tickers,
    "🇳🇱 AMX": amx_tickers,
    "🌐 Crypto": crypto_tickers
}

tab_labels = list(tabs_mapping.keys())

valutasymbool = {
    "🇳🇱 AEX": "€ ",
    "🇳🇱 AMX": "€ ",
    "🇺🇸 Dow Jones": "$ ",
    "🇺🇸 Nasdaq": "$ ",
    "🇪🇺 Eurostoxx": "€ ",
    "🇺🇸 US Tech": "$ ",
    "📌 Mijn lijst": "",
    "🌐 Crypto": ""
}





























# wit

