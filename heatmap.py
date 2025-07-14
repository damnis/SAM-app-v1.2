# === heatmap.py ===

import streamlit as st
from datetime import datetime
import pandas as pd
import yfinance as yf

from sectorticker import sector_tickers
from sam_indicator import calculate_sam
from sat_indicator import calculate_sat
from adviezen import determine_advice, weighted_moving_average
from grafieken import bepaal_grafiekperiode_heat
from datafund import get_profile

# ✅ Kleuren voor de heatmap
kleurmap = {
    "Kopen": "#2ecc71",
    "Verkopen": "#e74c3c",
    "Neutraal": "#95a5a6"
}

# ✅ Lokale data-ophaalfunctie met startdatum
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

# ✅ Heatmap generator
@st.cache_data(ttl=900)
def genereer_sector_heatmap(interval, risk_aversion=2, volgorde="marketcap"):
    html_output = "<div style='font-family: monospace;'>"
    start_date = datetime.today() - bepaal_grafiekperiode_heat(interval)

    for i, (sector, tickers) in enumerate(sector_tickers.items()):

        # Sorteer tickers
        if volgorde == "alfabetisch":
            sorted_tickers = sorted(tickers[:20])
        else:
            def get_cap(t):
                prof = get_profile(t)
                return prof.get("marketCap", 0) if prof else 0
            sorted_tickers = sorted(tickers[:20], key=get_cap, reverse=True)

        # Expander per sector (eerste twee open)
        with st.expander(f"📈 {sector}", expanded=(i < 2)):
            sector_html = "<div style='display: flex; flex-wrap: wrap; max-width: 620px;'>"

            for ticker in sorted_tickers:
                try:
                    df = fetch_data_by_dates(ticker, interval=interval, start=start_date)
                    if df.empty or len(df) < 50:
                        advies = "Neutraal"
                    else:
                        df = calculate_sam(df)
                        df = calculate_sat(df)
                        adviezen = determine_advice(df, threshold=2, risk_aversion=risk_aversion)
                        advies = adviezen[-1] if adviezen else "Neutraal"
                except Exception as e:
                    st.warning(f"⚠️ Fout bij {ticker}: {e}")
                    advies = "Neutraal"

                kleur = kleurmap.get(advies, "#7f8c8d")

                # HTML-blokje per ticker
                sector_html += f"""
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
                    ' title='{ticker}: {advies}'>
                        <div><b>{ticker}</b></div>
                        <div>{advies}</div>
                    </div>
                """

            sector_html += "</div>"
            st.components.v1.html(sector_html, height=300, scrolling=False)

    html_output += "</div>"
    return html_output

# ✅ Aanroepfunctie

def toon_sector_heatmap(interval, risk_aversion=2, volgorde="marketcap"):
    st.markdown("### 🔥 Sector Heatmap")

    sorteer_optie = st.radio(
        "📌 Sorteer tickers per sector op:",
        ["marktkapitalisatie", "alfabetisch"],
        index=0,
        horizontal=True
    )

def toon_sector_heatmap(interval, risk_aversion=2, volgorde="marketcap"):
    st.markdown("### 🔥 Sector Heatmap")
    genereer_sector_heatmap(interval, risk_aversion=risk_aversion, volgorde=volgorde)






















# w
