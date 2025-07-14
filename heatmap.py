import streamlit as st
from sectorticker import sector_tickers
from yffetch import fetch_data
from sam_indicator import calculate_sam
from sat_indicator import calculate_sat
from adviezen import determine_advice, weighted_moving_average
from grafieken import bepaal_grafiekperiode_heat
from datetime import datetime

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
        html += "<div style='display: flex; flex-wrap: wrap; max-width: 620px;'>"

        blokken = []  # tijdelijke opslag voor sortering

        for ticker in tickers[:20]:
            try:
                periode = bepaal_grafiekperiode_heat(interval)
                eind_datum = datetime.now()
                start_datum = eind_datum - periode
                
                df = fetch_data(ticker, interval)
                df = df[df.index >= start_datum]

                if df is None or df.empty or len(df) < 50:
                    advies = "Neutraal"
                else:
                    df = calculate_sam(df)
                    df = calculate_sat(df)
                    advies_lijst, _ = determine_advice(df, threshold=2, risk_aversion=risk_aversion)
                    advies = advies_lijst[-1] if len(advies_lijst) > 0 else "Neutraal"

                kleur = kleurmap.get(advies, "#7f8c8d")
                laatste_koers = df["Close"].iloc[-1] if not df.empty else "-"
                laatste_datum = df.index[-1].strftime("%Y-%m-%d") if not df.empty else "-"

                blokken.append({
                    "ticker": ticker,
                    "advies": advies,
                    "kleur": kleur,
                    "koers": laatste_koers,
                    "datum": laatste_datum
                })

            except Exception as e:
                blokken.append({
                    "ticker": ticker,
                    "advies": "Neutraal",
                    "kleur": kleurmap["Neutraal"],
                    "koers": "-",
                    "datum": "-"
                })

        # Sorteren op kleurvolgorde (Kopen, Neutraal, Verkopen)
        volgorde = {"Kopen": 0, "Neutraal": 1, "Verkopen": 2}
        blokken.sort(key=lambda x: volgorde.get(x["advies"], 99))

        for blok in blokken:
            tooltip = f"Laatste koers: {blok['koers']}\nDatum: {blok['datum']}"
            html += f"""
                <div title='{tooltip}' style='
                    width: 100px;
                    height: 60px;
                    margin: 4px;
                    background-color: {blok['kleur']};
                    color: white;
                    display: flex;
                    flex-direction: column;
                    justify-content: center;
                    align-items: center;
                    border-radius: 6px;
                    font-size: 11px;
                    text-align: center;
                '>
                    <div><b>{blok['ticker']}</b></div>
                    <div>{blok['advies']}</div>
                </div>
            """

        html += "</div><hr style='margin: 20px 0;'>"

    html += "</div>"
    return html

def toon_sector_heatmap(interval, risk_aversion=2):
    st.markdown("### 🔥 Sector Heatmap")
    html = genereer_sector_heatmap(interval, risk_aversion=risk_aversion)
    st.components.v1.html(html, height=1500, scrolling=True)


















# w
