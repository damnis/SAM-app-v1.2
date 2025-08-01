import streamlit as st
import yfinance as yf
import pandas as pd
import ta
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timedelta, date, time
import matplotlib.pyplot as plt
from ta.trend import ADXIndicator
import matplotlib.dates as mdates
from yffetch import fetch_data, fetch_data_cached 
from fmpfetch import fetch_data_fmp
from sam_indicator import calculate_sam 
from sat_indicator import calculate_sat 
from adviezen import determine_advice 
from genereer import genereer_adviesmatrix
from streamlit.components.v1 import html as st_html



# 📆 Periode voor SAM-grafiek op basis van interval
def bepaal_grafiekperiode(interval):
    if interval == "1m":
        return timedelta(days=1)
    elif interval == "5m":
        return timedelta(days=5)
    elif interval == "15m":
        return timedelta(days=15)        # 7 dagen à ~96 candles per dag = ±672 punten
    elif interval == "1h":
        return timedelta(days=30)        # 5 dagen à ~7 candles = ±35 punten
    elif interval == "4h":
        return timedelta(days=125)       # 3 maanden à ~6 candles per week
    elif interval == "1d":
        return timedelta(days=280)      # 180=6 maanden à 1 candle per dag
    elif interval == "1wk":
        return timedelta(weeks=240)     # 104=2 jaar aan weekly candles (104 candles)
    elif interval == "1mo":
        return timedelta(weeks=520)     # 520=0 jaar aan monthly candles (120 candles)
    else:
        return timedelta(weeks=260)     # Fallback = 5 jaar

# periode voor heatmap
def bepaal_grafiekperiode_heat(interval):        
 # time delta version    
    if interval == "1m":
        return timedelta(days=3)
    elif interval == "5m":
        return timedelta(days=5)
    elif interval == "15m":
        return timedelta(days=14)
    elif interval == "1h":
        return timedelta(days=45)
    elif interval == "4h":
        return timedelta(days=75)
    elif interval == "1d":
        return timedelta(days=260)
    elif interval == "1wk":
        return timedelta(weeks=240)     # 104=2 jaar aan weekly candles (104 candles)
    else:
        return timedelta(weeks=240)  # bijv. bij weekly/monthly data
        
# no time delta version
#    if interval == "15m":
#        period = "7d"
 #   elif interval == "1h":
#        period = "15d"
#    elif interval == "4h":
#        period = "60d"
 #   elif interval == "1d":
  #      period = "2y"
  #  elif interval == "1wk":
  #      period = "10y"
  #  elif interval == "1mo":
  #      period = "25y"
  #  else:
   #     period = "25y"  # fallback

# aanvullende overlay grafiek
def plot_overlay_grafiek(df, ticker_name, interval):
    toon_overlay = st.toggle("📊 Toon gecombineerde overlaygrafiek (Koers + SAM + SAT)", value=False)
    if not toon_overlay:
        return

    grafiek_periode = bepaal_grafiekperiode(interval)
    cutoff_datum = df.index.max() - grafiek_periode
    df_plot = df[df.index >= cutoff_datum].copy().reset_index()

    if df_plot.empty:
        st.warning("Geen data beschikbaar voor de gekozen periode.")
        return

    # Bepaal naam van datumkolom (eerste kolom na reset_index)
    datumkolom = df_plot.columns[0]  # meestal 'Date' of 'index'
    df_plot["x"] = range(len(df_plot))

    # --- Plot opstellen ---
    fig, ax1 = plt.subplots(figsize=(14, 6))

    # 1️⃣ Linkeras: Koers
    ax1.plot(df_plot["x"], df_plot["Close"], color="black", linewidth=2, label="Koers")
    ax1.set_ylabel("Koers")
    ax1.grid(True)

    # 2️⃣ Rechteras: SAM + SAT
    ax2 = ax1.twinx()
    ax2.set_ylim(-4.25, 4.25)
#    ax2.set_ylabel("Indicatorwaarden")
    ax2.get_yaxis().set_visible(False)

    kleuren = ["green" if val >= 0 else "red" for val in df_plot["SAM"]]
    ax2.bar(df_plot["x"], df_plot["SAM"], color=kleuren, alpha=0.3, label="SAM")
    ax2.plot(df_plot["x"], df_plot["Trend"], color="blue", linewidth=1.4, marker='.', markersize=3, label="SAM Trend")
    ax2.plot(df_plot["x"], df_plot["SAT_Stage"], color="purple", linestyle="--", linewidth=1.2, alpha=0.5, label="SAT Stage")
    ax2.plot(df_plot["x"], df_plot["SAT_Trend"], color="orange", linewidth=1.2, marker='.', markersize=3, label="SAT Trend")

    # --- X-as slimme labels ---
    labels = df_plot[datumkolom].dt.strftime('%Y-%m-%d')
    step = max(1, len(df_plot) // 12)
    ax1.set_xticks(df_plot["x"][::step])
    ax1.set_xticklabels(labels[::step], rotation=45, ha="right")
    ax1.set_xlim(df_plot["x"].min(), df_plot["x"].max())

    # Legenda combineren
    handles1, labels1 = ax1.get_legend_handles_labels()
    handles2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(handles1 + handles2, labels1 + labels2, loc="upper left")

    ax1.set_title("Overlaygrafiek: Koers + SAM + SAT")
    fig.tight_layout()
    st.pyplot(fig)
    
    
# --- Koersgrafiek ---
def plot_koersgrafiek(df, ticker_name, interval):
    toon_koersgrafiek = st.toggle("📈 Toon koersgrafiek", value=False)
    if not toon_koersgrafiek:
        return

    grafiek_periode = bepaal_grafiekperiode(interval)
    cutoff_datum = df.index.max() - grafiek_periode
    df_koers = df[df.index >= cutoff_datum].copy().reset_index()

    # Zorg dat MA's bestaan
    if "MA30" not in df.columns or "MA150" not in df.columns:
        df["MA30"] = df["Close"].rolling(window=30).mean()
        df["MA150"] = df["Close"].rolling(window=150).mean()

    df_koers["x"] = range(len(df_koers))
    datumkolom = df_koers.columns[0]  # meestal 'Date' of 'index'

    fig, ax = plt.subplots(figsize=(14, 6))

    # Koers en MA-lijnen plotten
    ax.plot(df_koers["x"], df_koers["Close"], color="black", linewidth=2.0, label="Koers")
    ax.plot(df_koers["x"], df_koers["MA30"], color="orange", linewidth=1.0, label="MA(30)")
    ax.plot(df_koers["x"], df_koers["MA150"], color="pink", linewidth=1.0, label="MA(150)")

    # X-as labels (datum)
    labels = df_koers[datumkolom].dt.strftime('%Y-%m-%d')
    step = max(1, len(df_koers) // 12)
    ax.set_xticks(df_koers["x"][::step])
    ax.set_xticklabels(labels[::step], rotation=45, ha="right")

    # Y-as instellen (koers)
    try:
        koers_values = df_koers["Close"].astype(float).dropna()
        if not koers_values.empty:
            koers_min = koers_values.min()
            koers_max = koers_values.max()
            marge = (koers_max - koers_min) * 0.05
            ax.set_ylim(koers_min - marge, koers_max + marge)
    except Exception as e:
        st.warning(f"Kon y-as limieten niet instellen: {e}")

    ax.set_xlim(df_koers["x"].min(), df_koers["x"].max())
    ax.set_title(f"Koersgrafiek van {ticker_name}")
    ax.set_ylabel("Close")
    ax.set_xlabel("Datum")

    # --- Volume als bars op tweede y-as (rechts) ---
    if "Volume" in df_koers.columns:
        ax2 = ax.twinx()
        ax2.bar(df_koers["x"], df_koers["Volume"], color="#b0c4de", width=0.8, alpha=0.5, label="Volume")
        ax2.set_ylabel("Volume")
        ax2.set_ylim(bottom=0)  # Volume altijd vanaf 0
        ax2.get_yaxis().set_visible(False)
        ax2.legend(loc="upper right")
        # optioneel: ax2.set_yticks([])  # geen y-ticks voor volume als je het 'clean' wilt

    ax.legend(loc="upper left")
    fig.tight_layout()
    st.subheader("Koersgrafiek")
    st.pyplot(fig)



# --- SAM en Trend ---
def plot_sam_trend(df, interval):
    st.subheader("Grafiek met SAM en Trend")
    grafiek_periode = bepaal_grafiekperiode(interval)
    cutoff_datum = df.index.max() - grafiek_periode
    df_grafiek = df[df.index >= cutoff_datum].copy().reset_index()

    # Zorg dat we weten hoe de datumkolom heet
    datumkolom = df_grafiek.columns[0]  # meestal 'Date' of 'index'
    df_grafiek["x"] = range(len(df_grafiek))
    kleuren = ["green" if val >= 0 else "red" for val in df_grafiek["SAM"]]

    fig, ax = plt.subplots(figsize=(14, 6))
    ax.bar(df_grafiek["x"], df_grafiek["SAM"], color=kleuren, alpha=0.6, label="SAM")
    ax.plot(df_grafiek["x"], df_grafiek["Trend"], color="blue", linewidth=1.5, marker='.', markersize=3, label="Trend")

    if "SAT_Stage" in df_grafiek.columns:
        ax.plot(df_grafiek["x"], df_grafiek["SAT_Stage"], color="gray", linewidth=1.2, linestyle="--", marker='.', markersize=2, alpha=0.5)

    ax.axhline(y=0, color="black", linewidth=1, linestyle="--")
    ax.set_ylim(-4.5, 4.5)
    ax.set_xlim(df_grafiek["x"].min(), df_grafiek["x"].max())

    # Slimme labels
    labels = df_grafiek[datumkolom].dt.strftime('%Y-%m-%d')
    step = max(1, len(df_grafiek) // 12)
    ax.set_xticks(df_grafiek["x"][::step])
    ax.set_xticklabels(labels[::step], rotation=45, ha="right")

    ax.set_title("SAM-indicator en Trendlijn")
    ax.set_ylabel("Waarde")
    ax.legend()
    fig.tight_layout()
    st.pyplot(fig)

# --- SAT grafiek (tijdelijk uitgeschakeld) ---
def plot_sat_debug(df, interval):
    grafiek_periode = bepaal_grafiekperiode(interval)
    cutoff_datum = df.index.max() - grafiek_periode
    df_sat = df[df.index >= cutoff_datum].copy().reset_index()

    if df_sat.empty:
        st.warning("Geen SAT-data beschikbaar voor de gekozen periode.")
        return

    datumkolom = df_sat.columns[0]  # meestal 'Date' of 'index'
    df_sat["x"] = range(len(df_sat))

    fig, ax = plt.subplots(figsize=(14, 6))

    # Bereken bar spacing
    spacing = 1
    if len(df_sat) > 1:
        spacing = np.median(np.diff(df_sat["x"]))
    bar_width = spacing * 0.45  # 45% van afstand tussen punten

    # Bars tekenen
    ax.bar(df_sat["x"], df_sat["SAT_Stage"], width=bar_width, color="black", label="SAT Stage", alpha=0.6)

    # SAT Trend tekenen met markers
    ax.plot(df_sat["x"], df_sat["SAT_Trend"], color="blue", linewidth=1.5, marker='.', markersize=3, label="SAT Trend")

    # X-as labels instellen
    labels = df_sat[datumkolom].dt.strftime('%Y-%m-%d')
    step = max(1, len(df_sat) // 12)
    ax.set_xticks(df_sat["x"][::step])
    ax.set_xticklabels(labels[::step], rotation=45, ha="right")

    ax.axhline(y=0, color="gray", linewidth=1, linestyle="--")
    ax.set_xlim(df_sat["x"].min(), df_sat["x"].max())
    ax.set_ylim(-2.25, 2.25)
    ax.set_ylabel("Waarde")
    ax.set_title("SAT-indicator en Trendlijn")
    ax.legend()
    fig.tight_layout()
    st.pyplot(fig)


# actual matrix based on fixed calendar structure         

def toon_adviesmatrix_html(ticker, risk_aversion=2):
    toon_matrix = st.toggle("🟩🟥 Toon Adviesmatrix", value=False)
#    toon_matrix = st.toggle("📊 Toon Adviesmatrix (HTML)", value=False)
    if not toon_matrix:
        return

    matrix, intervallen_gekozen = genereer_adviesmatrix(ticker, risk_aversion)
  
    # HTML rendering - long style #
#    html = "<div style='font-family: monospace;'>"
#    html += "<div style='display: flex;'>"

#    kleurmap = {"🟩": "#2ecc71", "🟥": "#e74c3c", "⬛": "#7f8c8d"}  # grijs voor neutraal

#    for interval, specs in intervallen_gekozen.items():
   #     waarden = matrix.get(interval, [])
 #       blokken_html = "<div style='margin-right: 10px;'>"
 #       blokken_html += f"<div style='text-align: center; font-weight: bold; margin-bottom: 6px; color: #FFFF00;'>{interval}</div>"
 #       for entry in waarden:
  #          kleur = entry["kleur"]
 #           tekst = entry["tekst"]
 #           achtergrondkleur = kleurmap.get(kleur, "#95a5a6")  # fallback: lichtgrijs
 #           blok_html = f"""
  #              <div style='
  #                  width: {specs['breedte'] * 16}px;
   #                 height: {specs['hoogte'] * 3}px;
   #                 background-color: {achtergrondkleur};
     #               color: white;
     #               text-align: center;
        #            font-size: 11px;
     #               margin-bottom: 1px;
    #                border-radius: 2px;
     #           '>{tekst}</div>
   #         """
  #          blokken_html += blok_html
#        blokken_html += "</div>"
#        html += blokken_html

#    html += "</div></div>"
#    st_html(html, height=600, scrolling=True)

    
    # HTML rendering - wide
    # Verticale weergave (1 interval per rij)
    html = "<div style='font-family: monospace;'>"
    kleurmap = {"🟩": "#2ecc71", "🟥": "#e74c3c", "⬛": "#7f8c8d"}  # grijs voor neutraal


    for interval, specs in intervallen_gekozen.items():
        waarden = matrix.get(interval, [])
        
        # 🔁 Alleen voor '1wk' en '1d' de volgorde omdraaien (oud → nieuw) LATEN STAAN SOMS NODIG 
#        if interval in ["1wk", "1d"]:
   #         waarden = waarden[::-1]

        html += f"<div style='margin-bottom: 2px;'>"
        html += f"<div style='font-weight: bold; color: white; margin-bottom: 2px;'>{interval}</div>"
        html += "<div style='display: flex;'>"
        for entry in waarden:
            kleur = entry["kleur"]
            tekst = entry["tekst"]
            achtergrondkleur = kleurmap.get(kleur, "#95a5a6")
            blok_html = f"""
                <div style='
                    width: {specs['breedte'] * 7}px;
                    height: {specs['hoogte'] * 3}px;
                    background-color: {achtergrondkleur};
                    color: white;
                    text-align: center;
                    font-size: 11px;
                    margin-right: 1px;
                    margin-bottom: 1px;
                    border-radius: 2px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    flex-shrink: 0;
                '>{tekst}</div>
            """
          
            html += blok_html
        html += "</div></div>"

#    html += blok_html
    html += "</div></div>"  # sluit alles af

    scroll_html = f"""
    <style>
        .scroll-container {{
            max-width: 800px;  /* optioneel, of 100% */
            overflow-x: auto;
            padding-bottom: 10px;
        }}
    </style>
    <div class='scroll-container'>
    {html}
    </div>
    """

    st_html(scroll_html, height=400, scrolling=True)

    

#    st_html(html, height=800, width=600, scrolling=True)


 

            
           




    #  bg_color = (
    #            "#2ecc71" if kleur == "🟩"
   #             else "#e74c3c" if kleur == "🟥"
    #            else "#bdc3c7" if kleur == "🟨"
     #           else "#34495e" if kleur == "⬛"
    #            else "#f1c40f" if kleur == "⚠️"
    #            else "#7f8c8d"
             

# niet gebrukte definitie, oud dus INTERVALLEN = ["1wk", "1d", "4h", "1h", "15min"]
def toon_adviesmatrix_markdown(ticker, risk_aversion=2):
    toon_matrix = st.toggle("📊 Toon automatische Adviesmatrix (Markdown-versie)", value=False)
    if not toon_matrix:
        return

    st.subheader("📊 Automatische Adviesmatrix")
    st.markdown("De matrix toont adviezen per interval (jongste data bovenaan).")

    interval_specs = {
        "1wk": {"stappen": 5, "breedte": 2},
        "1d": {"stappen": 5, "breedte": 2},
        "4h": {"stappen": 10, "breedte": 4},
        "1h": {"stappen": 40, "breedte": 8},
        "15m": {"stappen": 160, "breedte": 16},
    }

    matrix = {}

    for interval, specs in interval_specs.items():
        stappen = specs["stappen"]
        try:
            # Data ophalen
            if ":" in ticker or ticker.upper() in ["AEX", "AMX"]:
                df = fetch_data_fmp(ticker, interval=interval)
            else:
                df = fetch_data(ticker, interval=interval)

            df = df.dropna().copy()
            if len(df) < stappen:
                matrix[interval] = ["🟨"] * stappen
                continue

            df = calculate_sam(df)
            df = calculate_sat(df)
            df, _ = determine_advice(df, threshold=2, risk_aversion=risk_aversion)

            adviezen = df["Advies"].dropna().iloc[-stappen:].tolist()
            adviezen = adviezen[::-1]  # Laatste eerst

            kleuren = []
            for advies in adviezen:
                if advies == "Kopen":
                    kleuren.append("🟩")
                elif advies == "Verkopen":
                    kleuren.append("🟥")
                else:
                    kleuren.append("🟨")
            # Aanvullen als te kort
            while len(kleuren) < stappen:
                kleuren.append("⬛")

            matrix[interval] = kleuren

        except Exception as e:
            matrix[interval] = ["⚠️"] * specs["stappen"]
            st.warning(f"Fout bij {interval}: {e}")

    # 🧱 Weergave op schaal: [2,2,4,8,16]
    max_stappen = max(spec["stappen"] for spec in interval_specs.values())
    rijen = []

    for i in range(max_stappen):
        rij = ""
        for interval, spec in interval_specs.items():
            blokken = spec["breedte"]
            waarden = matrix.get(interval, [])
            if i < len(waarden):
                rij += waarden[i] * blokken
            else:
                rij += "⬛" * blokken
        rijen.append(rij)

    # 🔁 Omgekeerd (jongste boven)
    rijen = rijen[::-1]

    st.markdown("```\n" + "\n".join(rijen) + "\n```")
    


# ⏱ gecompliceerde koersgrafiek werkt niet geheel
# bepaal data weeergaveperiode op basis van interval
#grafiek_periode = bepaal_grafiekperiode(interval)

# Bepaal cutoff-datum
#cutoff_datum = df.index.max() - grafiek_periode

# Filter alleen grafiekdata
#df_grafiek = df[df.index >= cutoff_datum].copy()

#cutoff_datum = datetime.now() - bepaal_grafiekperiode(interval)
#df_filtered = df[df.index >= cutoff_datum]

# 🖼️ Toggle voor grafiek
#if st.toggle("📊 Toon koersgrafiek"):
 #   fig = go.Figure(data=[
#        go.Candlestick(
 #           x=df_filtered.index,
#            open=df_filtered["Open"],
 #           high=df_filtered["High"],
  #          low=df_filtered["Low"],
  #          close=df_filtered["Close"],
 #           increasing_line_color='green',
 #           decreasing_line_color='red',
#            name='Koers'
#        )
#    ])

 #   fig.update_layout(
 #       xaxis_title="Datum",
 #       yaxis_title="Koers",
 #       xaxis_rangeslider_visible=False,
 #       height=400,
 #       margin=dict(l=10, r=10, t=10, b=10)
#    )

#    st.plotly_chart(fig, use_container_width=True)







# wit
