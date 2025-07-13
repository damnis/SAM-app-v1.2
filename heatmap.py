# === heatmap.py ===

import streamlit as st
from sectorticker import sector_tickers
from yffetch import fetch_data_cached
from sam_indicator import calculate_sam
from sat_indicator import calculate_sat
from adviezen import determine_advice

# Kleuren voor de heatmap
kleurmap = {"Kopen": "#2ecc71", "Verkopen": "#e74c3c", "Neutraal": "#95a5a6"}

@st.cache_data(ttl=900)
def genereer_sector_heatmap(interval):
    html = "<div style='font-family: monospace;'>"

    for sector, tickers in sector_tickers.items():
        html += f"<h4 style='color: white;'>{sector}</h4>"
        html += "<div style='display: flex; flex-wrap: wrap; max-width: 540px;'>"

        for ticker in tickers[:20]:
            try:
                df = fetch_data_cached(ticker, interval=interval)
                df = df.dropna()
                if df.empty:
                    advies = "Neutraal"
                else:
                    # SAM en SAT berekenen vóór advies
                    df = calculate_sam(df)
                    df = calculate_sat(df)
                    st.write(f"{ticker}:", df.tail())  # ⬅️ tijdelijk toevoegen

                    advies = "Kopen" if ticker.startswith("A") else "Verkopen"
    #                advies = determine_advice(df)[-1]
            except:
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
                '>
                    <div><b>{ticker}</b></div>
                    <div>{advies}</div>
                </div>
            """

        html += "</div><hr style='margin: 20px 0;'>"

    html += "</div>"
    return html

def toon_sector_heatmap(interval):
    st.markdown("### 🔥 Sector Heatmap")
    html = genereer_sector_heatmap(interval)
    st.components.v1.html(html, height=1200, scrolling=True)


















# w
