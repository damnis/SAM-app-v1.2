import pandas as pd
import streamlit as st
from datafund import get_profile
from fmpfetch import fetch_data_fmp
from adviezen import determine_advice
from tickers import tickers_screening

def get_momentum(df, periode="1w"):
    if periode == "1w":
        if df is not None and len(df) >= 7 and "Close" in df.columns:
            try:
                return (df["Close"].iloc[-1] - df["Close"].iloc[-6]) / df["Close"].iloc[-6] * 100
            except Exception as e:
                print(f"Momentum exceptie bij indexering: {e}")
                st.write(f"Momentum exceptie bij indexering: {e}")
                return None
    return None

def screen_tickers(
        tickers_screening, 
        min_momentum=1, 
        adviezen_toevoegen=("Kopen", "Verkopen"),
        debug=True
    ):
    results = []
    for ticker in tickers_screening:
        try:
            if debug: print(f"\n▶️ Screening {ticker} ...")
            if debug: st.write(f"\n▶️ Screening {ticker} ...")
            
            profile = get_profile(ticker)
            if debug: print("Profile:", profile)
            if debug: st.write("Profile:", profile)
            naam = profile.get("companyName", "") if profile else ""

            df = fetch_data_fmp(ticker, periode="2y")
 #           df = fetch_data_fmp(ticker, years=2)
            if debug: 
                print(f"FMP-data voor {ticker}: leeg? {df is None or df.empty}, columns: {df.columns if df is not None else None}")
                st.write(f"FMP-data voor {ticker}: leeg? {df is None or df.empty}, columns: {df.columns if df is not None else None}")
            if df is None or df.empty or "Close" not in df.columns:
                print(f"⛔ Geen geldige dataframe voor {ticker}")
                st.write(f"⛔ Geen geldige dataframe voor {ticker}")
                continue

            momentum = get_momentum(df, periode="1w")
            if debug: print(f"Momentum: {momentum}")
            if debug: st.write(f"Momentum: {momentum}")
            if momentum is None or momentum < min_momentum:
                print(f"⛔ Momentum te laag of None voor {ticker}: {momentum}")
                st.write(f"⛔ Momentum te laag of None voor {ticker}: {momentum}")
                continue

            advies = determine_advice(df, threshold=threshold, risk_aversion=risk_aversion)
#            advies = determine_advice(df, interval="1wk")
            if debug: print(f"Advies: {advies}")
            if debug: st.write(f"Advies: {advies}")
            if advies not in adviezen_toevoegen:
                print(f"⛔ Advies niet toegestaan ({advies}) voor {ticker}")
                st.write(f"⛔ Advies niet toegestaan ({advies}) voor {ticker}")
                continue

            results.append({
                "Ticker": ticker,
                "Naam": naam,
                "Momentum(1w%)": momentum,
                "Advies": advies,
            })
            print(f"✅ Toegevoegd: {ticker}")
            st.write(f"✅ Toegevoegd: {ticker}")

        except Exception as e:
            print(f"🚨 Fout bij {ticker}: {e}")
            st.write(f"🚨 Fout bij {ticker}: {e}")
            continue
    df_result = pd.DataFrame(results)
    if debug: 
        print("Resultaat:\n", df_result)
        st.write("Resultaat:", df_result)
    return df_result


















# w
