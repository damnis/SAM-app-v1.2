# === heatmap.py ===

import streamlit as st
from datetime import datetime
from sectorticker import sector_tickers
from sam_indicator import calculate_sam
from sat_indicator import calculate_sat
from adviezen import determine_advice, weighted_moving_average
from grafieken import bepaal_grafiekperiode_heat
import yfinance as yf
import pandas as pd

# Kleuren voor de heatmap
kleurmap = {
    "Kopen": "#2ecc71",
    "Verkopen": "#e74c3c",
    "Neutraal": "#95a5a6"
}

# Lokale data-ophaalfunctie met startdatum
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
def genereer_sector_heatmap(interval, risk_aversion=2, alfabetisch=False):
    html = "<div style='font-family: monospace;'>"

    periode = bepaal_grafiekperiode_heat(interval)
    start_date = datetime.today() - periode

    for i, (sector, tickers) in enumerate(sector_tickers.items()):
        if alfabetisch:
            tickers = sorted(tickers)
        open_attr = "open" if i < 2 else ""

        html += f"""
        <details {open_attr} style='margin-bottom: 10px;'>
        <summary style='font-size: 18px; color: white; cursor: pointer;'>{sector}</summary>
        <div style='display: flex; flex-wrap: wrap; max-width: 600px; margin-top: 10px;'>
        """

        for ticker in tickers[:20]:
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

        html += "</div></details><hr style='margin: 20px 0;'>"

    html += "</div>"
    return html

def toon_sector_heatmap(interval, risk_aversion=2, alfabetisch=False):
    st.markdown("### \ud83d\udd25 Sector Heatmap")
    html = genereer_sector_heatmap(interval, risk_aversion=risk_aversion, alfabetisch=alfabetisch)
    st.components.v1.html(html, height=1400, scrolling=True)
























# w
