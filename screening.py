import pandas as pd
from datafund import get_ratios, get_profile
from sam_indicator import calculate_sam
from sat_indicator import calculate_sat
from adviezen import determine_advice, weighted_moving_average 
from tickers import tickers_screening
from fmpfetch import fetch_data_fmp 

def get_momentum(df, periode="1w"):
    # df is OHLC dataframe (let op: moet minstens 7 rijen zijn)
    if periode == "1w":
        if df is None or "Close" not in df.columns or len(df) < 7:
            return None
        return (df["Close"].iloc[-1] - df["Close"].iloc[-6]) / df["Close"].iloc[-6] * 100
    # Voeg hier extra periodes toe indien nodig
    return None

def screen_tickers(tickers_screening, min_momentum=5):
    results = []
    for ticker in tickers_screening:
        try:
            profile = get_profile(ticker)
            # profile check mag blijven voor bedrijfsnaam etc.
            if not profile:
                print(f"DEBUG: Geen profiel voor {ticker}")
                continue

            df = fetch_data_fmp(ticker)
            if df is None or "Close" not in df.columns or len(df) < 7:
                print(f"DEBUG: Geen of te weinig koersdata voor {ticker}")
                continue

            momentum = get_momentum(df, periode="1w")
            if momentum is None:
                print(f"DEBUG: Kan momentum niet bepalen voor {ticker}")
                continue

            if momentum < min_momentum:
                print(f"DEBUG: {ticker} momentum te laag ({momentum:.2f}%)")
                continue

            advies = determine_advice(df, interval="1wk")
            print(f"DEBUG: {ticker} Advies={advies}, Momentum={momentum:.2f}%")

            # Toon alleen als advies 'Kopen' of 'Verkopen' is (je gaf aan: alleen die twee mogelijk)
            if advies not in ["Kopen", "Verkopen"]:
                print(f"DEBUG: {ticker} Advies niet Kopen/Verkopen ({advies})")
                continue

            results.append({
                "Ticker": ticker,
                "Naam": profile.get("companyName"),
                "Momentum(1w%)": round(momentum, 2),
                "Advies": advies,
            })
        except Exception as e:
            print(f"Fout bij {ticker}: {e}")  # zichtbaar in logs/console, desnoods st.write()
            continue
    return pd.DataFrame(results)






















# w
