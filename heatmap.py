# === heatmap.py ===

import streamlit as st
import pandas as pd
from genereer import genereer_adviesmatrix  # bestaande functie
from sectorticker import sector_tickers
from streamlit import cache_data

kleurmap = {"Kopen": "#2ecc71", "Verkopen": "#e74c3c", "Neutraal": "#7f8c8d"}

@st.cache_data(ttl=900)
def genereer_sector_heatmap(sector, interval):
    tickers = sector_tickers.get(sector, [])
    matrix_data = []

    for ticker in tickers:
        matrix = genereer_adviesmatrix(ticker)
        advies = matrix.get(interval, {}).get("advies", "Neutraal")
        matrix_data.append({"ticker": ticker, "advies": advies})

    return pd.DataFrame(matrix_data)

def toon_sector_heatmap(interval):
    st.subheader(f"📊 Sector Heatmap – Interval: {interval}")
    for sector in sector_tickers:
        df = genereer_sector_heatmap(sector, interval)
        st.markdown(f"### {sector}")
        cols = st.columns(4)  # 4 kolommen x 4 rijen = 16 blokken
        for i, row in df.iterrows():
            kleur = kleurmap.get(row["advies"], "#bdc3c7")
            with cols[i % 4]:
                st.markdown(f"""
                    <div style='background-color:{kleur}; padding:16px; border-radius:8px; text-align:center; color:white;'>
                        {row['ticker']}<br><small>{row['advies']}</small>
                    </div>
                """, unsafe_allow_html=True)

