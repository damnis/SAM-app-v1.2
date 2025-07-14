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
def genereer_sector_heatmap(interval, risk_aversion=2, sortering="Marktkapitalisatie"):
    periode = bepaal_grafiekperiode_heat(interval)
    start_date = datetime.today() - periode

    # Sorteer tickers per sector
    sectoren = {}
    for sector, tickers in sector_tickers.items():
        if sortering == "Alfabetisch":
            sectoren[sector] = sorted(tickers)
        else:  # sorteer op marktkapitalisatie
            sectoren[sector] = sorted(
                tickers,
                key=lambda t: market_caps.get(t, 0),
                reverse=True
            )

    resultaten = {}

    for sector, tickers in sectoren.items():
        blokken = ""
        for ticker in tickers[:20]:  # max 20 per sector
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

            blokken += f"""
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

        resultaten[sector] = blokken

    return resultaten

def toon_sector_heatmap(interval, risk_aversion=2, sortering="Marktkapitalisatie"):
    st.markdown("### 🔥 Sector Heatmap")

    resultaten = genereer_sector_heatmap(interval, risk_aversion=risk_aversion, sortering=sortering)

    for i, (sector, blokken) in enumerate(resultaten.items()):
        if i < 2:
            with st.expander(sector, expanded=True):
                st.components.v1.html(f"<div style='display: flex; flex-wrap: wrap;'>{blokken}</div>", height=350)
        else:
            with st.expander(sector, expanded=False):
                st.components.v1.html(f"<div style='display: flex; flex-wrap: wrap;'>{blokken}</div>", height=350)























# w
