import pandas as pd
from datafund import get_ratios, get_profile
from sam_indicator import calculate_sam
from sat_indicator import calculate_sat
from adviezen import determine_advice, weighted_moving_average 
from tickers import tickers_screening

def get_momentum(df, periode="1w"):
    # df is OHLC dataframe
    if periode == "1w":
        return (df["Close"].iloc[-1] - df["Close"].iloc[-6]) / df["Close"].iloc[-6] * 100
    # Voeg hier extra periodes toe indien nodig
    return None

def screen_tickers(tickers_screening, min_marketcap=1e9, min_momentum=5):
    results = []
    for ticker in tickers_screening:
        try:
            profile = get_profile(ticker)
            if not profile or float(profile.get("mktCap", 0)) < min_marketcap:
                continue

            # Hier kun je koersdata ophalen, bv via yfinance of FMP
            df = fetch_ohlc_data(ticker)
            momentum = get_momentum(df, periode="1w")

            if momentum < min_momentum:
                continue

            advies = determine_advice(df, interval="1wk")  # je eigen signaal logica
            if advies != "Kopen":
                continue

            results.append({
                "Ticker": ticker,
                "Naam": profile.get("companyName"),
                "Marktkap.": float(profile.get("mktCap", 0)),
                "Momentum(1w%)": momentum,
                "Advies": advies,
            })
        except Exception as e:
            # st.write(f"Fout bij {ticker}: {e}")  # voor debugging
            continue
    return pd.DataFrame(results)












































# w
