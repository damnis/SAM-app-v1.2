#'tickerlijsten
# --- Update tab labels en bijbehorende mapping ---

# to script = from tickers import (
#    aex_tickers, amx_tickers, dow_tickers, eurostoxx_tickers,
#    nasdaq_tickers, ustech_tickers, crypto_tickers,
#    tabs_mapping, tab_labels, valutasymbool
#)


# to script from tickers import ustech_tickers, nasdaq_tickers, dow_tickers, aex_tickers, amx_tickers, eurostoxx_tickers, crypto_tickers
aex_tickers = {
"^AEX": "AEX Index", "ABN.AS": "ABN AMRO", "ADYEN.AS": "Adyen", "AGN.AS": "Aegon", "AD.AS": "Ahold Delhaize", 
"AKZA.AS": "Akzo Nobel", "MT.AS": "ArcelorMittal", "ASM.AS": "ASM International", "ASML.AS": "ASML Holding", "ASRNL.AS": "ASR Nederland",
"BESI.AS": "BESI", "DSFIR.AS": "DSM-Firmenich", "GLPG.AS": "Galapagos", "HEIA.AS": "Heineken", 
"IMCD.AS": "IMCD", "INGA.AS": "ING Groep", "TKWY.AS": "Just Eat Takeaway", "KPN.AS": "KPN",
"NN.AS": "NN Group", "PHIA.AS": "Philips", "PRX.AS": "Prosus", "RAND.AS": "Randstad",
"REN.AS": "Relx", "SHELL.AS": "Shell", "UNA.AS": "Unilever", "WKL.AS": "Wolters Kluwer"
}

dow_tickers = {
    '^DJI': 'Dow Jones index', 'MMM': '3M', 'AXP': 'American Express', 'AMGN': 'Amgen', 'AAPL': 'Apple', 'BA': 'Boeing',
    'CAT': 'Caterpillar', 'CVX': 'Chevron', 'CSCO': 'Cisco', 'KO': 'Coca-Cola', 'DIS': 'Disney',
    'GS': 'Goldman Sachs', 'HD': 'Home Depot', 'HON': 'Honeywell', 'IBM': 'IBM', 'INTC': 'Intel',
    'JPM': 'JPMorgan Chase', 'JNJ': 'Johnson & Johnson', 'MCD': 'McDonalds', 'MRK': 'Merck',
    'MSFT': 'Microsoft', 'NKE': 'Nike', 'PG': 'Procter & Gamble', 'CRM': 'Salesforce',
    'TRV': 'Travelers', 'UNH': 'UnitedHealth', 'VZ': 'Verizon', 'V': 'Visa', 'WMT': 'Walmart',
    'DOW': 'Dow', 'RTX': 'RTX Corp.', 'WBA': 'Walgreens Boots'
}
nasdaq_tickers = {
    '^IXIC': 'Nasdaq index', 'MSFT': 'Microsoft', 'NVDA': 'NVIDIA', 'ASML': 'ASML', 'AAPL': 'Apple', 'AMZN': 'Amazon', 'META': 'Meta',
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
    '^STOXX50E': 'Eurostoxx index', 'ASML.AS': 'ASML Holding', 'AIR.PA': 'Airbus', 'BAS.DE': 'BASF', 'BAYN.DE': 'Bayer',
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
    "^AMX": "AMX Index", "AF.PA": "Air France-KLM SA", "APAM.AS": "Aperam S.A.",
    "ARCAD.AS": "Arcadis NV", "BAMNB.AS": "Koninklijke BAM Groep nv", "BESI.AS": "BE Semiconductor Industries N.V.",
    "BFIT.AS": "Basic-Fit N.V.", "CRBN.AS": "Corbion N.V.", "ECMPA.AS": "Eurocommercial Properties N.V.",
    "FAGR.BR": "Fagron NV", "FLOW.AS": "Flow Traders Ltd.", "FUR.AS": "Fugro N.V.",
    "LIGHT.AS": "Signify N.V.", "NSI.AS": "NSI N.V.", "OCI.AS": "OCI N.V.", "PHARM.AS": "Pharming Group N.V.",
    "PNL.AS": "PostNL N.V.", "SBMO.AS": "SBM Offshore N.V.", "TWEKA.AS": "TKH Group N.V.",
    "VPK.AS": "Koninklijke Vopak N.V.", "WDP.BR": "Warehouses De Pauw SA",
    "AMG.AS": "AMG", "AALB.AS": "Aalberts N.V.", "KENDR.AS": "Kendrion", "TKWY.AS": "Just Eat", "VASTN.AS": "Vastned Retail"
}

crypto_tickers = {
    "BTC-USD": "Bitcoin",
    "ETH-USD": "Ethereum",
    "BNB-USD": "BNB",
    "SOL-USD": "Solana",
    "XRP-USD": "XRP",
    "DOGE-USD": "Dogecoin",
    "ADA-USD": "Cardano",
    "AVAX-USD": "Avalanche",
    "DOT-USD": "Polkadot",
    "MATIC-USD": "Polygon",
    "LTC-USD": "Litecoin",
    "LINK-USD": "Chainlink",
    "TRX-USD": "TRON",
    "XLM-USD": "Stellar",
    "ETC-USD": "Ethereum Classic",
    "BCH-USD": "Bitcoin Cash",
    "EGLD-USD": "Elrond",
    "ATOM-USD": "Cosmos",
    "ICP-USD": "Internet Computer",
    "FIL-USD": "Filecoin",
    "NEAR-USD": "NEAR Protocol",
    "HBAR-USD": "Hedera",
    "XTZ-USD": "Tezos",
    "AAVE-USD": "Aave",
    "MKR-USD": "Maker",
    "UNI-USD": "Uniswap",
    "SAND-USD": "The Sandbox",
    "FTM-USD": "Fantom",
    "THETA-USD": "Theta",
    "CHZ-USD": "Chiliz",
    "SUSHI-USD": "SushiSwap",
    "GRT-USD": "The Graph",
    "RUNE-USD": "THORChain",
    "AXS-USD": "Axie Infinity",
    "ALGO-USD": "Algorand",
    "VET-USD": "VeChain",
    "DAI-USD": "Dai",
    "MANA-USD": "Decentraland",
    "CRV-USD": "Curve DAO Token",
    "NEO-USD": "Neo",
    "ZIL-USD": "Zilliqa",
    "BAT-USD": "Basic Attention Token",
    "HC-USD": "HyperCash",
    "BTT-USD": "BitTorrent",
    "GALA-USD": "Gala",
    "ENJ-USD": "Enjin Coin",
    "1INCH-USD": "1inch",
    "CHSB-USD": "SwissBorg",
    "ZRX-USD": "0x",
    "KSM-USD": "Kusama",
    "COMP-USD": "Compound",
    "OKB-USD": "OKB",
    "MX-USD": "MX Token",
    "CELO-USD": "Celo",
    "REN-USD": "Ren",
    "YFI-USD": "yearn.finance",
    "SNX-USD": "Synthetix",
    "HNT-USD": "Helium",
    "FLOW-USD": "Flow",
    "GNO-USD": "Gnosis",
    "RPL-USD": "Rocket Pool",
    "GLM-USD": "Golem",
    "OCEAN-USD": "Ocean Protocol",
    "KAVA-USD": "Kava",
    "LRC-USD": "Loopring",
    "SKL-USD": "Skale",
    "DASH-USD": "Dash",
    "NEXO-USD": "Nexo",
    "KNC-USD": "Kyber Network",
    "ANKR-USD": "Ankr",
    "MINA-USD": "Mina",
    "AMP-USD": "Amp",
    "WAVES-USD": "Waves",
    "CEL-USD": "Celsius Network",
    "BAT-USD": "Basic Attention Token",
    "FTT-USD": "FTX Token",
    "BNT-USD": "Bancor",
    "GUSD-USD": "Gemini Dollar",
    "UMA-USD": "UMA",
    "CHSB-USD": "SwissBorg",
    "RVN-USD": "Ravencoin",
    "AR-USD": "Arweave",
    "RAY-USD": "Raydium",
    "CAKE-USD": "PancakeSwap",
    "GLMR-USD": "Moonbeam",
    "CRV-USD": "Curve DAO Token",
    "SXP-USD": "Swipe",
    "OXT-USD": "Oxen",
    "DNT-USD": "district0x",
    "ICX-USD": "ICON",
    "ZEN-USD": "Horizen",
    "STORJ-USD": "Storj",
    "CVC-USD": "Civic",
    "ENJ-USD": "Enjin Coin",
    "UMA-USD": "Uma",
}
    

mijn_lijst = {
    "": "Vrije keuze...", "ASM.AS": "ASM International", "ASML.AS": "ASML Holding", "AMZN": "Amazon",
    "SMCI": "Super Micro Computer", "PLTR": "Palantir", "ORCL": "Oracle",
    "NVDA": "NVIDIA", "AVGO": "Broadcom", "TSLA": "Tesla", "AAPL": "Apple",
    "GOOGL": "Alphabet (GOOGL)", "MSFT": "Microsoft", "META": "Meta Platforms"
}

tickers_screening = [
    "AAPL", "MSFT", "NVDA", "GOOGL", "AMZN", "META", "TSLA", "AMD", "NFLX", "INTC",
    "ASM", "ASML", "SMCI", "PLTR", "ORCL", "AVGO", "SHOP", "BITF", "COIN",
    "SNOW", "MDB", "DDOG", "CRWD", "ZS", "CSCO", "ADBE", "CMCSA", "PEP", "COST",
    "QCOM", "TMUS", "TXN", "AMAT", "DKNG", "RYTM",
    'MMM', 'AXP', 'AMGN', 'BA', 'CAT', 'CVX', 'CSCO', 'KO', 'DIS',
    'GS', 'HD', 'HON', 'IBM', 'JPM', 'JNJ', 'MCD', 'MRK',
    'NKE', 'PG', 'CRM', 'TRV', 'UNH', 'VZ', 'V', 'WMT', 'DOW', 'RTX', 'WBA',
    "ABN.AS", "ADYEN.AS", "AGN.AS", "AD.AS", "AKZA.AS", "MT.AS", "ASM.AS", "ASML.AS", "ASRNL.AS",
    "BESI.AS", "DSFIR.AS", "GLPG.AS", "HEIA.AS", "IMCD.AS", "INGA.AS", "TKWY.AS", "KPN.AS",
    "NN.AS", "PHIA.AS", "PRX.AS", "RAND.AS", "REN.AS", "SHELL.AS", "UNA.AS", "WKL.AS",
    "AF.PA", "APAM.AS", "ARCAD.AS", "BAMNB.AS", "BESI.AS",
    "BFIT.AS", "CRBN.AS", "ECMPA.AS", "FAGR.BR", "FLOW.AS", "FUR.AS",
    "LIGHT.AS", "NSI.AS", "OCI.AS", "PHARM.AS", "PNL.AS", "SBMO.AS", "TWEKA.AS",
    "VPK.AS", "WDP.BR", "AMG.AS", "AALB.AS", "KENDR.AS", "VASTN.AS"


]
    # ... vul zelf aan, maximaal ±150 is nog prima



# --- Mapping beurs tabs en tickers ---
tabs_mapping = {
    "🇺🇸 Dow Jones": dow_tickers,
    "🇺🇸 Nasdaq": nasdaq_tickers,
    "🇺🇸 US Tech": ustech_tickers,
    "🇪🇺 Eurostoxx": eurostoxx_tickers,
    "📌 Mijn lijst": mijn_lijst,
    "🇳🇱 AEX index": aex_tickers,
    "🇳🇱 AMX index": amx_tickers,
    "🌐 Crypto": crypto_tickers
}

tab_labels = list(tabs_mapping.keys())

valutasymbool = {
    "🇳🇱 AEX index": "€ ",
    "🇳🇱 AMX index": "€ ",
    "🇺🇸 Dow Jones": "$ ",
    "🇺🇸 Nasdaq": "$ ",
    "🇪🇺 Eurostoxx": "€ ",
    "🇺🇸 US Tech": "$ ",
    "📌 Mijn lijst": "",
    "🌐 Crypto": ""
}





























# wit

