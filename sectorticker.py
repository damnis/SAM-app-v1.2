# === sectorticker.py ===

# Elke sector bevat een lijst van 16 tickers (of minder bij opstarten)
sector_tickers = {
    "US Tech": ["AAPL", "PLTR", "SMCI", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "ADBE", "CRM", "INTC", "CSCO", "UBER", "TSLA", "AMD", "ORCL", "AVGO", "TXN", "QCOM", "IBM"],
#    "Financials": ["JPM", "BAC", "WFC", "C", "GS", "MS", "AXP", "BK", "USB", "SCHW", "TFC", "COF", "MTB", "FITB", "HBAN", "PNC"],
#    "Energy": ["XOM", "CVX", "COP", "EOG", "PSX", "VLO", "MPC", "HES", "OKE", "PXD", "WMB", "KMI", "SLB", "BKR", "HAL", "APA"],
    "Crypto": ["BTC-USD", "ETH-USD", "SOL-USD", "BNB-USD", "XRP-USD", "ADA-USD", "DOGE-USD", "LINK-USD", "LTC-USD", "XLM-USD"],
    "Nederland": ["ABN.AS", "ADYEN.AS", "AGN.AS", "AD.AS", "AKZA.AS", "MT.AS", "ASM.AS", "ASML.AS", "ASRNL.AS", "BESI.AS", "DSFIR.AS", "HEIA.AS", "IMCD.AS", "INGA.AS", "TKWY.AS", "KPN.AS", "NN.AS", "PHIA.AS", "UNA.AS", "WKL.AS"]
    
    
    # Voeg eenvoudig meer sectoren toe in hetzelfde formaat
}
#DOT-USD", "AVAX-USD", ""MATIC-USD""BCH-USD""ATOM-USD", "UNI-USD"


# === sectorticker.py ===

# Elke sector bevat een lijst van 16 tickers (of minder bij opstarten)
sector_tickers_news = {
    "US Tech": ["AAPL", "PLTR", "SMCI", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "ADBE", "CRM", "INTC", "CSCO", "UBER", "TSLA", "AMD", "ORCL", "AVGO", "TXN", "QCOM", "IBM"],
    "Financials": ["JPM", "BAC", "WFC", "C", "GS", "MS", "AXP", "BK", "USB", "SCHW", "TFC", "COF", "MTB", "FITB", "HBAN", "PNC"],
    "Energy": ["XOM", "CVX", "COP", "EOG", "PSX", "VLO", "MPC", "HES", "OKE", "PXD", "WMB", "KMI", "SLB", "BKR", "HAL", "APA"],
    "Crypto": ["BTC-USD", "ETH-USD", "SOL-USD", "BNB-USD", "XRP-USD", "ADA-USD", "DOGE-USD", "LINK-USD", "LTC-USD", "XLM-USD"],
    "Nederland": ["ABN.AS", "ADYEN.AS", "AGN.AS", "AD.AS", "AKZA.AS", "MT.AS", "ASM.AS", "ASML.AS", "ASRNL.AS", "BESI.AS", "DSFIR.AS", "HEIA.AS", "IMCD.AS", "INGA.AS", "TKWY.AS", "KPN.AS", "NN.AS", "PHIA.AS", "UNA.AS", "WKL.AS"]
    
    
    # Voeg eenvoudig meer sectoren toe in hetzelfde formaat
}
#DOT-USD", "AVAX-USD", ""MATIC-USD""BCH-USD""ATOM-USD"


# Elke sector bevat een lijst van 16 tickers (of minder bij opstarten)
sector_tickers_screening = {
    "US Tech": ["AAPL", "PLTR", "SMCI", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "ADBE", "CRM", "INTC", "CSCO", "UBER", "TSLA", "AMD", "ORCL", "AVGO", "TXN", "QCOM", "IBM"],
    "Financials": ["JPM", "BAC", "WFC", "C", "GS", "MS", "AXP", "BK", "USB", "SCHW", "TFC", "COF", "MTB", "FITB", "HBAN", "PNC"],
    "Energy": ["XOM", "CVX", "COP", "EOG", "PSX", "VLO", "MPC", "HES", "OKE", "PXD", "WMB", "KMI", "SLB", "BKR", "HAL", "APA"],
    "Crypto": ["BTC-USD", "ETH-USD", "SOL-USD", "BNB-USD", "XRP-USD", "ADA-USD", "DOGE-USD", "LINK-USD", "LTC-USD", "XLM-USD"],
    "Nederland": 
    [""ABN.AS", "ADYEN.AS", "AGN.AS", "AD.AS", "AKZA.AS", "MT.AS", "ASM.AS", "ASML.AS", "ASRNL.AS",
    "BESI.AS", "DSFIR.AS", "GLPG.AS", "HEIA.AS", "IMCD.AS", "INGA.AS", "TKWY.AS", "KPN.AS",
    "NN.AS", "PHIA.AS", "PRX.AS", "RAND.AS", "REN.AS", "SHELL.AS", "UNA.AS", "WKL.AS",
    "AF.PA", "APAM.AS", "ARCAD.AS", "BAMNB.AS",  
    "BFIT.AS", "CRBN.AS", "ECMPA.AS", "FAGR.BR", "FLOW.AS", "FUR.AS",
    "LIGHT.AS", "NSI.AS", "OCI.AS", "PHARM.AS", "PNL.AS", "SBMO.AS", "TWEKA.AS",
    "VPK.AS", "WDP.BR", "AMG.AS", "AALB.AS", "KENDR.AS", "VASTN.AS",]
    
    
    # Voeg eenvoudig meer sectoren toe in hetzelfde formaat
}


tickers_screening = [
    "AAPL", "MSFT", "NVDA", "GOOGL", "AMZN", "META", "TSLA", "AMD", "NFLX", "INTC",
    "ASM", "ASML", "SMCI", "PLTR", "ORCL", "AVGO", "SHOP", "BITF", "COIN",
    "SNOW", "MDB", "DDOG", "CRWD", "ZS", "CSCO", "ADBE", "CMCSA", "PEP", "COST",
    "QCOM", "TMUS", "TXN", "AMAT", "DKNG", "RYTM",
    'MMM', 'AXP', 'AMGN', 'BA', 'CAT', 'CVX', 'CSCO', 'KO', 'DIS',
    'GS', 'HD', 'HON', 'IBM', 'JPM', 'JNJ', 'MCD',
    'NKE', 'PG', 'CRM', 'TRV', 'UNH', 'VZ', 'V', 'WMT', 'DOW', 'RTX', 'WBA',
    
    "LLY","ABBV","MRK","PFE","GILD","AZN","NVO","BMY",
    "VRTX","REGN","ALNY","BNTX","BIIB","BEAM","CRSP","EXEL","MRNA","BGNE",
    "ARGX","GMAB","CRMD","RIGL","TGTX","ABVX","ACAD","VKTX","ONCT",
    "IONS","PTCT","CRNX","NBIX","JUNS","AMRN","LIXT","YHC","VOR", 
    "CIGL"










# w
