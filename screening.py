import pandas as pd
from datafund import get_profile
from fmpfetch import fetch_data_fmp   # <-- ChatGPT was deze vergeten in de vorige voorbeelden
from sam_indicator import calculate_sam
from sat_indicator import calculate_sat
from adviezen import determine_advice, weighted_moving_average 
from tickers import tickers_screening

def get_momentum(df, periode="1w"):
    if periode == "1w":
        if df is not None and len(df) >= 7 and "Close" in df.columns:
            try:
                return (df["Close"].iloc[-1] - df["Close"].iloc[-6]) / df["Close"].iloc[-6] * 100
            except Exception:
                return None
    return None

def screen_tickers(tickers_screening, min_momentum=5, adviezen_toevoegen=("Kopen", "Verkopen")):
    results = []
    for ticker in tickers_screening:
        try:
            profile = get_profile(ticker)
            naam = profile.get("companyName", "") if profile else ""

            # Hier ophalen via fmpfetch!
            df = fetch_data_fmp(ticker, years=2, interval="1wk")
            if df is None or df.empty or "Close" not in df.columns:
                continue

            momentum = get_momentum(df, periode="1w")
            if momentum is None or momentum < min_momentum:
                continue

            advies = determine_advice(df, interval="1wk")
            if advies not in adviezen_toevoegen:
                continue

            results.append({
                "Ticker": ticker,
                "Naam": naam,
                "Momentum(1w%)": momentum,
                "Advies": advies,
            })
        except Exception as e:
            # st.write(f"Fout bij {ticker}: {e}")
            continue
    return pd.DataFrame(results)
































# w
