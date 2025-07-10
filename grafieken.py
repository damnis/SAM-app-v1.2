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
        return timedelta(weeks=120)     # 104=2 jaar aan weekly candles (104 candles)
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

    fig, ax = plt.subplots(figsize=(14, 6))  # grotere grafiek voor duidelijkheid
    kleuren = ["green" if val >= 0 else "red" for val in df_grafiek["SAM"]]

    # SAM als bar
    ax.bar(df_grafiek.index, df_grafiek["SAM"], color=kleuren, label="SAM", alpha=0.6)

    # Trend als lijn met zichtbare punten
    ax.plot(df_grafiek.index, df_grafiek["Trend"], color="blue", linewidth=1.5, marker='.', markersize=3, label="Trend")

    if "SAT_Stage" in df_grafiek.columns:
        ax.plot(df_grafiek.index, df_grafiek["SAT_Stage"], color="gray", linewidth=1.2, linestyle="--", marker='.', markersize=2, alpha=0.5)

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
    grafiek_periode = bepaal_grafiekperiode(interval)
    cutoff_datum = df.index.max() - grafiek_periode
    df_sat = df[df.index >= cutoff_datum].copy()

    fig, ax = plt.subplots(figsize=(14, 6))

    # SAT Stage met markers
    ax.bar(df_sat.index, df_sat["SAT_Stage"], color="black", label="SAT Stage", alpha=0.6)

    # SAT Trend als lijn met marker
    ax.plot(df_sat.index, df_sat["SAT_Trend"], color="blue", linewidth=1.5, marker='.', markersize=3, label="SAT Trend")

    ax.axhline(y=0, color="gray", linewidth=1, linestyle="--")
    ax.set_xlim(df_sat.index.min(), df_sat.index.max())
    ax.set_ylim(-2.25, 2.25)
    ax.set_ylabel("Waarde")
    ax.set_title("SAT-indicator en Trendlijn")
    ax.legend()
    fig.tight_layout()
    st.pyplot(fig)
    

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
