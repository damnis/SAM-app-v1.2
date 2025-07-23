import pandas as pd
import streamlit as st
import requests
from datafund import get_profile, get_analyst_recommendations
from fmpfetch import fetch_data_fmp
from adviezen import determine_advice, weighted_moving_average 
from sam_indicator import calculate_sam 
from sat_indicator import calculate_sat 
from tickers import tickers_screening


@st.cache_data(ttl=3600)
def get_volume_momentum(df, periode="1w"):
    if periode == "1w":
        if df is not None and len(df) >= 35 and "Volume" in df.columns:
            try:
                # Laatste 7 dagen
                last_7 = df["Volume"].iloc[-7:].sum()
                # 28 dagen daarvoor
                prev_28 = df["Volume"].iloc[-35:-7].sum()
                if prev_28 == 0:  # Voorkom delen door nul
                    return None
                # Relatief verschil in %
#               rel = (last_7 - prev_28/4) / (prev_28/4) * 100  # t.o.v. weekgemiddelde
              
                return (last_7 - prev_28/4) / (prev_28/4) *100
                # Of als je echt de ratio wilt:
                # rel = last_7 / (prev_28 / 4)
 #               return rel
            except Exception as e:
                # st.write(f"Volume-momentum exceptie: {e}")
                return None
    return None




@st.cache_data(ttl=3600)
def screen_tickers_vol(
        tickers_screening, 
        min_momentum=1, 
        adviezen_toevoegen=("Kopen", "Verkopen"),
        threshold=2,
        risk_aversion=1,
        debug=True 
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

            momentum = get_volume_momentum(df, periode="1w")
            if debug: print(f"Momentum: {momentum}")
            if debug: st.write(f"Momentum: {momentum}")
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
                "1wk (%)": momentum,
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



















# w
