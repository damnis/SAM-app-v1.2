import pandas as pd
import streamlit as st
import requests
from datafund import get_profile, get_analyst_recommendations
from fmpfetch import fetch_data_fmp
from adviezen import determine_advice, weighted_moving_average 
from sam_indicator import calculate_sam 
from sat_indicator import calculate_sat 
from tickers import tickers_screening

def get_momentum(df, periode="1w"):
    if periode == "1w":
        if df is not None and len(df) >= 7 and "Close" in df.columns:
            try:
                return (df["Close"].iloc[-1] - df["Close"].iloc[-6]) / df["Close"].iloc[-6] * 100
            except Exception as e:
#                print(f"Momentum exceptie bij indexering: {e}")
 #               st.write(f"Momentum exceptie bij indexering: {e}")
                return None
    return None

def screen_tickers(
        tickers_screening, 
        min_momentum=1, 
        adviezen_toevoegen=("Kopen", "Verkopen"),
        threshold=2,
        risk_aversion=1,
        debug=False 
    ):
    results = []
    for ticker in tickers_screening:
        try:
#            if debug: print(f"\n▶️ Screening {ticker} ...")
#            if debug: st.write(f"\n▶️ Screening {ticker} ...")
            
            profile = get_profile(ticker)
#            if debug: print("Profile:", profile)
#            if debug: st.write("Profile:", profile)
            naam = profile.get("companyName", "") if profile else ""

            df = fetch_data_fmp(ticker, periode="2y")
#            if debug: 
#                print(f"FMP-data voor {ticker}: leeg? {df is None or df.empty}, columns: {df.columns if df is not None else None}")
#                st.write(f"FMP-data voor {ticker}: leeg? {df is None or df.empty}, columns: {df.columns if df is not None else None}")
            if df is None or df.empty or "Close" not in df.columns:
   #             print(f"⛔ Geen geldige dataframe voor {ticker}")
  #              st.write(f"⛔ Geen geldige dataframe voor {ticker}")
                continue

            momentum = get_momentum(df, periode="1w")
  #          if debug: print(f"Momentum: {momentum}")
   #         if debug: st.write(f"Momentum: {momentum}")
            if momentum is None or momentum < min_momentum:
   #             print(f"⛔ Momentum te laag of None voor {ticker}: {momentum}")
    #            st.write(f"⛔ Momentum te laag of None voor {ticker}: {momentum}")
                continue

            df = calculate_sat(df)
            df = calculate_sam(df)
            advies = determine_advice(df, threshold=threshold, risk_aversion=risk_aversion)
#            st.write("Advies:", advies)
            if isinstance(advies, tuple):
                _, advies_tekst = advies
            else:
                advies_tekst = advies
#            st.write("Advies tekst:", advies_tekst)
            if advies_tekst not in adviezen_toevoegen:
                st.write(f"⛔ Advies niet toegestaan ({advies_tekst}) voor {ticker}")
                continue

            results.append({
                "Ticker": ticker,
                "Naam": naam,
                "Momentum(1w%)": momentum,
                "Advies": advies_tekst,
            })
 #           print(f"✅ Toegevoegd: {ticker}")
#            st.write(f"✅ Toegevoegd: {ticker}")

        except Exception as e:
            print(f"🚨 Fout bij {ticker}: {e}")
            st.write(f"🚨 Fout bij {ticker}: {e}")
            continue
    df_result = pd.DataFrame(results)
#    if debug: 
 #       print("Resultaat:\n", df_result)
#        st.write("Resultaat:", df_result)
    return df_result



def analyst_recs_for_screened(screened_tickers, base_url, api_key):
    results = []
    for ticker in screened_tickers:
        try:
            recs = get_analyst_recommendations(ticker)
            # recs = requests.get(f"{base_url}/analyst-stock-recommendations/{ticker}?apikey={api_key}").json()
            if not recs or isinstance(recs, dict) and recs.get("error"):
                results.append({
                    "Ticker": ticker,
                    "Buy": None,
                    "Hold": None,
                    "Sell": None,
                    "Consensus": "Onbekend"
                })
                continue
            # Pak de laatste entry (meest recente maand)
            last = recs[0] if isinstance(recs, list) and recs else {}
            results.append({
                "Ticker": ticker,
                "Buy": last.get("buy", 0),
                "Hold": last.get("hold", 0),
                "Sell": last.get("sell", 0),
                "Consensus": last.get("consensus", "n.v.t.")
            })
        except Exception as e:
            results.append({
                "Ticker": ticker,
                "Buy": None,
                "Hold": None,
                "Sell": None,
                "Consensus": f"Fout: {e}"
            })
    return pd.DataFrame(results)






















# w
