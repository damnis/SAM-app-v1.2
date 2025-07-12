import streamlit as st
import yfinance as yf
import pandas as pd
import ta
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timedelta, date
import matplotlib.pyplot as plt
from ta.trend import ADXIndicator

# 📆 Periode voor SAM-grafiek op basis van interval
def bepaal_grafiekperiode(interval):
    if interval == "15m":
        return timedelta(days=5)        # 7 dagen à ~96 candles per dag = ±672 punten
    elif interval == "1h":
        return timedelta(days=5)        # 5 dagen à ~7 candles = ±35 punten
    elif interval == "4h":
        return timedelta(days=60)       # 3 maanden à ~6 candles per week
    elif interval == "1d":
        return timedelta(days=360)      # 180=6 maanden à 1 candle per dag
    elif interval == "1wk":
        return timedelta(weeks=450)     # 104=2 jaar aan weekly candles (104 candles)
    elif interval == "1mo":
        return timedelta(weeks=520)     # 520=0 jaar aan monthly candles (120 candles)
    else:
        return timedelta(weeks=260)     # Fallback = 5 jaar
# periode voor koersgrafiek 
#def bepaal_grafiekperiode2(interval):
#    if interval == "15m":
#        return timedelta(days=7)
 #   elif interval == "1h":
 #       return timedelta(days=5)
 #   elif interval == "4h":
 #       return timedelta(days=90)
#    elif interval == "1d":
#        return timedelta(days=180)
 #   else:
  #      return timedelta(weeks=260)  # bijv. bij weekly/monthly data


# --- Koersgrafiek ---
def plot_koersgrafiek(df, ticker_name, interval):
    toon_koersgrafiek = st.toggle("\U0001F4C8 Toon koersgrafiek", value=False)
    if not toon_koersgrafiek:
        return

    grafiek_periode = bepaal_grafiekperiode(interval)
    cutoff_datum = df.index.max() - grafiek_periode
    df_koers = df[df.index >= cutoff_datum].copy()

    if "MA30" not in df.columns or "MA150" not in df.columns:
        df["MA30"] = df["Close"].rolling(window=30).mean()
        df["MA150"] = df["Close"].rolling(window=150).mean()

    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(df_koers.index, df_koers["Close"], color="black", linewidth=2.0, label="Koers")
    ax.plot(df.index, df["MA30"], color="orange", linewidth=1.0, label="MA(30)")
    ax.plot(df.index, df["MA150"], color="pink", linewidth=1.0, label="MA(150)")
    ax.set_xlim(df_koers.index.min(), df_koers.index.max())

    try:
        koers_values = df_koers["Close"].astype(float).dropna()
        if not koers_values.empty:
            koers_min = koers_values.min()
            koers_max = koers_values.max()
            marge = (koers_max - koers_min) * 0.05
            ax.set_ylim(koers_min - marge, koers_max + marge)
    except Exception as e:
        st.warning(f"Kon y-as limieten niet instellen: {e}")

    ax.set_title(f"Koersgrafiek van {ticker_name}")
    ax.set_ylabel("Close")
    ax.set_xlabel("Datum")
    ax.legend()
    fig.tight_layout()
    st.subheader("Koersgrafiek")
    st.pyplot(fig)


# --- SAM en Trend ---
def plot_sam_trend(df, interval):
    st.subheader("Grafiek met SAM en Trend")
    grafiek_periode = bepaal_grafiekperiode(interval)
    cutoff_datum = df.index.max() - grafiek_periode
    df_grafiek = df[df.index >= cutoff_datum].copy()

    fig, ax = plt.subplots(figsize=(10, 4))
    kleuren = ["green" if val >= 0 else "red" for val in df_grafiek["SAM"]]
    ax.bar(df_grafiek.index, df_grafiek["SAM"], color=kleuren, label="SAM")
    ax.plot(df_grafiek.index, df_grafiek["Trend"], color="blue", linewidth=2, label="Trend")

    if "SAT_Stage" in df_grafiek.columns:
        ax.plot(df_grafiek.index, df_grafiek["SAT_Stage"], color="gray", linewidth=1.5, linestyle="--", alpha=0.4)

    ax.axhline(y=0, color="black", linewidth=1, linestyle="--")
    ax.set_ylim(-4.5, 4.5)
    ax.set_xlim(df_grafiek.index.min(), df_grafiek.index.max())
    ax.set_title("SAM-indicator en Trendlijn")
    ax.set_ylabel("Waarde")
    ax.legend()
    fig.tight_layout()
    st.pyplot(fig)


# --- SAT grafiek (tijdelijk uitgeschakeld) ---
def plot_sat_debug(df, interval):
    # st.subheader("Grafiek met SAT en Trend")
    grafiek_periode = bepaal_grafiekperiode(interval)
    cutoff_datum = df.index.max() - grafiek_periode
    df_sat = df[df.index >= cutoff_datum].copy()

    fig, ax = plt.subplots(figsize=(10, 4))
    ax.bar(df_sat.index, df_sat["SAT_Stage"], color="black", label="SAT Stage")
    ax.plot(df_sat.index, df_sat["SAT_Trend"], color="blue", linewidth=2, label="SAT Trend")
    ax.axhline(y=0, color="gray", linewidth=1, linestyle="--")
    ax.set_xlim(df_sat.index.min(), df_sat.index.max())
    ax.set_ylim(-2.25, 2.25)
    ax.set_ylabel("Waarde")
    ax.set_title("SAT-indicator en Trendlijn")
    ax.legend()
    fig.tight_layout()
    st.pyplot(fig)  # handmatig inschakelen indien nodig


# matrix

def toon_adviesmatrix_html(ticker, risk_aversion=2):
toon_matrix = st.toggle("📊 Toon gecombineerde Adviesmatrix (HTML)", value=False)
if not toon_matrix:
return

import calendar

INTERVALLEN = {  
    "1wk": {"stappen": 3, "breedte": 10, "hoogte": 160, "label": "Week", "show_text": True},  
    "1d": {"stappen": 15, "breedte": 10, "hoogte": 32, "label": "Dag", "show_text": True},  
    "4h": {"stappen": 30, "breedte": 10, "hoogte": 16, "label": "4u", "show_text": True},  
    "1h": {"stappen": 120, "breedte": 5, "hoogte": 4, "label": "1u", "show_text": True},  
    "15m": {"stappen": 480, "breedte": 2, "hoogte": 1, "label": "15m", "show_text": False}  
}  

matrix = {}  

for interval, specs in INTERVALLEN.items():  
    stappen = specs["stappen"]  
    try:  
        if ":" in ticker or ticker.upper() in ["AEX", "AMX"]:  
            df = fetch_data_fmp(ticker, interval=interval)  
        else:  
            df = fetch_data(ticker, interval=interval)  

        df = df.dropna().copy()  
        if len(df) < stappen:  
            matrix[interval] = [{"kleur": "🟨", "tekst": ""}] * stappen  
            continue  

        df = calculate_sam(df)  
        df = calculate_sat(df)  
        df, _ = determine_advice(df, threshold=2, risk_aversion=risk_aversion)  

        df = df.dropna(subset=["Advies"])  
        df = df.iloc[-stappen:].copy()  
        df = df[::-1]  # laatste bovenaan  

        waarden = []  
        for i in range(stappen):  
            if i >= len(df):  
                waarden.append({"kleur": "⬛", "tekst": ""})  
                continue  
            advies = df.iloc[i]["Advies"]  
            datum = df.index[i]  
            kleur = "🟩" if advies == "Kopen" else "🟥"  

            if interval == "1wk":  
                tekst = datum.strftime("%Y-%m-%d")  
            elif interval == "1d":  
                tekst = datum.strftime("%a")[:2]  
            elif interval == "4h":  
                tekst = datum.strftime("%H:%M")  
            elif interval == "1h":  
                tekst = datum.strftime("%H:%M")  
            elif interval == "15m":  
                tekst = str(i % 4 + 1)  
            else:  
                tekst = ""  

            waarden.append({"kleur": kleur, "tekst": tekst if specs["show_text"] else ""})  

        matrix[interval] = waarden  

    except Exception as e:  
        matrix[interval] = [{"kleur": "⚠️", "tekst": ""}] * specs["stappen"]  
        st.warning(f"Fout bij {interval}: {e}")  

# HTML-rendering  
html = "<div style='font-family: monospace;'>"  
html += "<div style='display: flex;'>"  

for interval, specs in INTERVALLEN.items():  
    waarden = matrix[interval]  
    blokken_html = "<div style='margin-right: 12px;'>"  
    blokken_html += f"<div style='text-align: center; font-weight: bold; margin-bottom: 6px;'>{interval}</div>"  

    for entry in waarden:  
        kleur = entry["kleur"]  
        tekst = entry["tekst"]  
        blok_html = f"""  
            <div style='  
                width: {specs['breedte'] * 8}px;  
                height: {specs['hoogte'] * 3}px;    
                background-color: {"#2ecc71" if kleur=="🟩" else "#e74c3c" if kleur=="🟥" else "#bdc3c7"};  
                color: white;  
                text-align: center;  
                font-size: 11px;  
                margin-bottom: 1px;  
                border-radius: 3px;  
            '>{tekst}</div>  
        """  
        blokken_html += blok_html  

    blokken_html += "</div>"  
    html += blokken_html

html += "</div></div>"

st_html(html, height=600, scrolling=True)




# ➕ y-as: bepaal min/max + marge
#    try:
#        koers_values = df_koers["Close"].astype(float).dropna()
#        if not koers_values.empty:
#            koers_min = koers_values.min()
 #           koers_max = koers_values.max()
  #          marge = (koers_max - koers_min) * 0.05
   #         ax.set_ylim(koers_min - marge, koers_max + marge)
 #       else:
 #           st.warning("Geen geldige koersdata om y-as limieten op te baseren.")
#    except Exception as e:
#        st.warning(f"Kon y-as limieten niet instellen: {e}")





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
