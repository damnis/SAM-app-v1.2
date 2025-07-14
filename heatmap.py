# === heatmap.py ===

import streamlit as st
from datetime import datetime
from sectorticker import sector_tickers
from sam_indicator import calculate_sam
from sat_indicator import calculate_sat
from adviezen import determine_advice, weighted_moving_average
from grafieken import bepaal_grafiekperiode_heat
from datafund import get_profile  
import yfinance as yf
import pandas as pd

kleurmap = {
    "Kopen": "#2ecc71",
    "Verkopen": "#e74c3c",
    "Neutraal": "#95a5a6"
}

@st.cache_data(ttl=900)
def fetch_data_by_dates(ticker, interval, start, end=None):
    if end is None:
        end = datetime.today()
    df = yf.download(ticker, interval=interval, start=start, end=end)
    if df.empty or "Close" not in df.columns:
        return pd.DataFrame()
    df.index = pd.to_datetime(df.index, errors="coerce")
    df = df[~df.index.isna()]
    df = df[(df["Volume"] > 0) & ((df["Open"] != df["Close"]) | (df["High"] != df["Low"]))]
    for col in ["Close", "Open", "High", "Low", "Volume"]:
        df[col] = df[col].fillna(method="ffill").fillna(method="bfill")
    return df

@st.cache_data(ttl=900)
def sorteer_tickers(tickers, methode):
    if methode == "alfabetisch":
        return sorted(tickers)
    elif methode == "marktkapitalisatie":
        kapitalisaties = []
        for ticker in tickers:
            profiel = get_profile(ticker)
            cap = profiel.get("mktCap", 0) if profiel else 0
            kapitalisaties.append((ticker, cap if cap else 0))
        return [t for t, _ in sorted(kapitalisaties, key=lambda x: x[1], reverse=True)]
    else:
        return tickers

@st.cache_data(ttl=900)
def genereer_sector_heatmap(interval, risk_aversion=2, sorteer_op="marktkapitalisatie"):
    html = "<div style='font-family: monospace;'>"
    periode = bepaal_grafiekperiode_heat(interval)
    start_date = datetime.today() - periode

    for i, (sector, tickers) in enumerate(sector_tickers.items()):
        gesorteerde_tickers = sorteer_tickers(tickers, sorteer_op)[:20]

        # ✅ Titel boven dropdown
        html += f"<h4 style='color: black; margin-top: 30px;'>{sector}</h4>"

        # ✅ Uitklapbare sectie
        with st.expander(f"📊 {sector}", expanded=(i < 2)):  # Eerste 2 open
            html += "<div style='display: flex; flex-wrap: wrap; max-width: 600px;'>"

            for ticker in gesorteerde_tickers:
                try:
                    df = fetch_data_by_dates(ticker, interval=interval, start=start_date)
                    if df.empty or len(df) < 50:
                        advies = "Neutraal"
                    else:
                        df = calculate_sam(df)
                        df = calculate_sat(df)
                        adviezen = determine_advice(df, threshold=2, risk_aversion=risk_aversion)
                        advies = adviezen[-1] if len(adviezen) else "Neutraal"
                except Exception as e:
                    st.warning(f"⚠️ Fout bij {ticker}: {e}")
                    advies = "Neutraal"

                kleur = kleurmap.get(advies, "#7f8c8d")

                html += f"""
                    <div style='
                        width: 100px;
                        height: 60px;
                        margin: 4px;
                        background-color: {kleur};
                        color: white;
                        display: flex;
                        flex-direction: column;
                        justify-content: center;
                        align-items: center;
                        border-radius: 6px;
                        font-size: 11px;
                        text-align: center;
                    '>
                        <div><b>{ticker}</b></div>
                        <div>{advies}</div>
                    </div>
                """

            html += "</div><hr style='margin: 20px 0;'>"

    html += "</div>"
    return html

def toon_sector_heatmap(interval, risk_aversion=2, sorteer_op="marktkapitalisatie"):
    st.markdown("### 🔥 Sector Heatmap")
    html = genereer_sector_heatmap(interval, risk_aversion=risk_aversion, sorteer_op=sorteer_op)
    st.components.v1.html(html, height=500, scrolling=True)


#def toon_sector_heatmap(interval, risk_aversion=2, sorteer_op="marktkapitalisatie"):
 #   st.markdown("### 🔥 Sector Heatmap")

  #  html = genereer_sector_heatmap(interval, risk_aversion=risk_aversion, sorteer_op=sorteer_optie)
   # st.components.v1.html(html, height=500, scrolling=True)


 



















# w
