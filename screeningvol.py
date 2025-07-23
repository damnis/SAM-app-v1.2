import pandas as pd
import streamlit as st
import requests
import numpy as np
from datafund import get_profile, get_analyst_recommendations
from fmpfetch import fetch_data_fmp
from adviezen import determine_advice, weighted_moving_average
from sam_indicator import calculate_sam
from sat_indicator import calculate_sat
from tickers import tickers_screening

@st.cache_data(ttl=3600)
def get_volume_momentum(df, periode="1w", debug=False, ticker=None):
    if periode == "1w":
        if df is None:
            if debug: st.write(f"⛔ Geen dataframe voor {ticker}")
            return None
        if len(df) < 35:
            if debug: st.write(f"⛔ Te weinig data voor {ticker}: {len(df)} rijen (min 35 nodig)")
            return None

        # Debug: kolomnamen
        if debug: st.write(f"{ticker} kolommen: {df.columns}")

        # Harmoniseer kolomnaam
        if "Volume" not in df.columns and "volume" in df.columns:
            df["Volume"] = df["volume"]
        if "Volume" not in df.columns:
            if debug: st.write(f"⛔ Geen volume-kolom voor {ticker}")
            return None

        try:
            last_7 = df["Volume"].iloc[-7:].sum()
            prev_28 = df["Volume"].iloc[-35:-7].sum()
            if debug:
                st.write(f"{ticker} | Volume laatste 7 dagen: {last_7}, Volume vorige 28 dagen: {prev_28}")
            if prev_28 == 0:
                if debug: st.write(f"⛔ Volume vorige 4 weken is 0 voor {ticker} (geen momentum mogelijk)")
                return None
            momentum_pct = ((last_7 - prev_28 / 4) / (prev_28 / 4)) * 100
            if debug: st.write(f"{ticker} | Volume-momentum t.o.v. weekgemiddelde: {momentum_pct:.2f}%")
            return momentum_pct
        except Exception as e:
            if debug: st.write(f"Volume-momentum exceptie bij {ticker}: {e}")
            return None
    return None

@st.cache_data(ttl=3600)
def screen_tickers_vol(
        tickers_screening, 
        min_momentum=50,     # = 50% stijging t.o.v. weekgemiddelde 4wk
        adviezen_toevoegen=("Kopen"),
        threshold=2,
        risk_aversion=1,
        debug=False 
    ):
    results = []
    for ticker in tickers_screening:
        try:
            if debug: st.write(f"\n▶️ Screening {ticker} ...")

            profile = get_profile(ticker)
            naam = profile.get("companyName", "") if profile else ""
            if debug: st.write(f"{ticker} profiel: {naam}")

            df = fetch_data_fmp(ticker, periode="2y")
            if debug: 
                st.write(f"FMP-data voor {ticker}: leeg? {df is None or df.empty}, kolommen: {df.columns if df is not None else None}")
                if df is not None:
                    st.write(f"{ticker} aantal rijen: {len(df)}")

            if df is None or df.empty:
                if debug: st.write(f"⛔ Geen geldige dataframe voor {ticker}")
                continue

            # Optioneel: sla tickers zonder volume over
            if "Volume" not in df.columns and "volume" not in df.columns:
                if debug: st.write(f"⛔ Geen volume in dataframe voor {ticker}")
                continue

            momentum = get_volume_momentum(df, periode="1w", debug=debug, ticker=ticker)
            if debug: st.write(f"{ticker} Momentum: {momentum}")
            if momentum is None or momentum < min_momentum:
                if debug: st.write(f"⛔ Momentum te laag of None voor {ticker}: {momentum}")
                continue

            # Indien je SAT/SAM en advies wilt toevoegen
            if "Close" in df.columns:
                df = calculate_sat(df)
                df = calculate_sam(df)
                advies = determine_advice(df, threshold=threshold, risk_aversion=risk_aversion)
                if isinstance(advies, tuple):
                    _, advies_tekst = advies
                else:
                    advies_tekst = advies
                if debug: st.write("Advies tekst:", advies_tekst)
                if advies_tekst not in adviezen_toevoegen:
                    if debug: st.write(f"⛔ Advies niet toegestaan ({advies_tekst}) voor {ticker}")
                    continue
            else:
                advies_tekst = "N.v.t."  # Geen advies mogelijk zonder Close

            results.append({
                "Ticker": ticker,
                "Naam": naam,
                "1wk Volume-momentum (%)": f"{momentum:.1f}%",
                "Advies": advies_tekst,
            })
            if debug: st.write(f"✅ Toegevoegd: {ticker}")

        except Exception as e:
            st.write(f"🚨 Fout bij {ticker}: {e}")
            continue
    df_result = pd.DataFrame(results)
    if debug: 
        st.write("Resultaat screening:")
        st.write(df_result)
    return df_result

# ------------------------------
# Voorbeeld aanroep:
# df_screen = screen_tickers_vol(tickers_screening, min_momentum=50, debug=True)
# st.dataframe(df_screen)
















# w
