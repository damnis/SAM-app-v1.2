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

@st.cache_data(ttl=3600)
def screen_tickers(
        tickers_screening, 
        min_momentum=1, 
        adviezen_toevoegen=("Kopen"),
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


# wordt hiet gebruikt, voor later
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



# -- screeningvol.py hieronder... deze SVP combineren tot 1

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
        min_momentum=20,     # = 50% stijging t.o.v. weekgemiddelde 4wk
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



@st.cache_data(ttl=3600)
def toppers_worden_gezocht(
        tickers_screening, 
        min_momentum=1, 
        min_volume_momentum=20,
        adviezen_toevoegen=("Kopen",),
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

            df = fetch_data_fmp(ticker, periode="2y")
            if df is None or df.empty:
                if debug: st.write(f"⛔ Geen geldige dataframe voor {ticker}")
                continue

            koers_momentum = get_momentum(df, periode="1w")
            volume_momentum = get_volume_momentum(df, periode="1w", ticker=ticker, debug=debug)

            # ➡️ Nieuw: altijd beide waardes berekenen en tonen
            # Bepaal of minimaal 1 van beide criteria gehaald is
            koers_ok = koers_momentum is not None and koers_momentum >= min_momentum
            volume_ok = volume_momentum is not None and volume_momentum >= min_volume_momentum

            if not (koers_ok or volume_ok):
                if debug: st.write(f"⛔ Geen momentum voor {ticker} (koers: {koers_momentum}, volume: {volume_momentum})")
                continue

            df = calculate_sat(df)
            df = calculate_sam(df)
            advies = determine_advice(df, threshold=threshold, risk_aversion=risk_aversion)
            if isinstance(advies, tuple):
                _, advies_tekst = advies
            else:
                advies_tekst = advies
            if advies_tekst not in adviezen_toevoegen:
                if debug: st.write(f"⛔ Advies niet toegestaan ({advies_tekst}) voor {ticker}")
                continue

            results.append({
                "Ticker": ticker,
                "Naam": naam,
                "Koers (1wk %)": f"{koers_momentum:.2f}%" if koers_momentum is not None else "n.v.t.",
                "Volume (1wk %)": f"{volume_momentum:.1f}%" if volume_momentum is not None else "n.v.t.",
                "Advies": advies_tekst,
            })
            if debug: st.write(f"✅ Toegevoegd: {ticker}")

        except Exception as e:
            st.write(f"🚨 Fout bij {ticker}: {e}")
            continue
    df_result = pd.DataFrame(results)
    if debug:
        st.write("Resultaat screening gecombineerd:")
        st.write(df_result)
    return df_result
















# w
