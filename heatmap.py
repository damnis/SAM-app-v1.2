# === heatmap.py ===

import streamlit as st
from sectorticker import sector_tickers
from yffetch import fetch_data_cached
from sam_indicator import calculate_sam
from sat_indicator import calculate_sat
from adviezen import determine_advice, weighted_moving_average
from grafieken import bepaal_grafiekperiode_heat
from datetime import timedelta



# Kleuren voor de heatmap
kleurmap = {
    "Kopen": "#2ecc71",
    "Verkopen": "#e74c3c",
    "Neutraal": "#95a5a6"
}

@st.cache_data(ttl=900)
def genereer_sector_heatmap(interval, risk_aversion=2):
    html = "<div style='font-family: monospace;'>"

    for sector, tickers in sector_tickers.items():
        html += f"<h4 style='color: white;'>{sector}</h4>"
        html += "<div style='display: flex; flex-wrap: wrap; max-width: 600px;'>"

        for ticker in tickers[:20]:  # max 20 per sector
            try:
                start_date = datetime.now() - bepaal_grafiekperiode_heat(interval)
                df = fetch_data_cached(ticker, interval=interval, start=start_date)

                if df is None or df.empty or len(df) < 50:
                    advies = "Neutraal"
                else:
                    df = calculate_sam(df)
                    df = calculate_sat(df)
                    df, _ = determine_advice(df, threshold=2, risk_aversion=risk_aversion)
                    advies = df["Advies"].iloc[-1]

            except Exception as e:
                st.write(f"⚠️ Fout bij {ticker}: {e}")
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

def toon_sector_heatmap(interval, risk_aversion=2):
    st.markdown("### 🔥 Sector Heatmap")
    html = genereer_sector_heatmap(interval, risk_aversion=risk_aversion)
    st.components.v1.html(html, height=1400, scrolling=True)






















# w
