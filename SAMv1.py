import streamlit as st
import yfinance as yf
import pandas as pd
import ta
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timedelta, date
import matplotlib.pyplot as plt
from ta.trend import ADXIndicator
#from ta.momentum import TRIXIndicator
# from .py imports
#-- Volledige tickerlijsten ---
from tickers import (
    aex_tickers, amx_tickers, dow_tickers, eurostoxx_tickers,
    nasdaq_tickers, ustech_tickers, crypto_tickers,
    tabs_mapping, tab_labels, valutasymbool
)
# Indicatoren berekening
from sam_indicator import calculate_sam
from sat_indicator import calculate_sat
# grafieken en tabellen
from grafieken import plot_koersgrafiek, plot_sam_trend, plot_sat_debug, bepaal_grafiekperiode 
from sam_tabel import toon_sam_tabel
# Backtestfunctie 
from backtest import backtest_functie
# trading bot
from bot import toon_trading_bot_interface
from bot import verbind_met_alpaca, haal_laatste_koers, plaats_order, sluit_positie
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce
#import alpaca_trade_api as tradeapi

#--- Functie om data op te halen ---
# ✅ Gecachete downloadfunctie (15 minuten geldig)
@st.cache_data(ttl=900)
def fetch_data_cached(ticker, interval, period):
    return yf.download(ticker, interval=interval, period=period)

# ✅ Weighted Moving Average functie
def weighted_moving_average(series, window):
    weights = np.arange(1, window + 1)
    return series.rolling(window).apply(lambda x: np.dot(x, weights) / weights.sum(), raw=True)

# ✅ Wrapper-functie met dataschoonmaak en fallback
def fetch_data(ticker, interval):
    # 🔁 Interval naar periode
    if interval == "15m":
        period = "30d"
    elif interval == "1h":
        period = "720d"
    elif interval == "4h":
        period = "360d"
    elif interval == "1d":
        period = "20y"
    elif interval == "1wk":
        period = "20y"
    elif interval == "1mo":
        period = "25y"
    else:
        period = "25y"  # fallback

    # ⬇️ Ophalen via gecachete functie
    df = fetch_data_cached(ticker, interval, period)

    # 🛡️ Check op geldige data
    if df.empty or "Close" not in df.columns or "Open" not in df.columns:
        return pd.DataFrame()

    # 🧹 Verwijder irrelevante of foutieve rijen
    df = df[
        (df["Volume"] > 0) &
        ((df["Open"] != df["Close"]) | (df["High"] != df["Low"]))
    ]

    # 🕓 Zorg dat index datetime is
    if not isinstance(df.index, pd.DatetimeIndex):
        df.index = pd.to_datetime(df.index, errors="coerce")
    df = df[~df.index.isna()]

    # 🔁 Vul NaN's per kolom
    for col in ["Close", "Open", "High", "Low", "Volume"]:
        df[col] = df[col].fillna(method="ffill").fillna(method="bfill")

    # 🧪 Check minimale lengte
    if len(df) < 30:
        st.warning(f"⚠️ Slechts {len(df)} datapunten opgehaald — mogelijk te weinig voor indicatoren.")
        return pd.DataFrame()

    return df
    


#--- Advies en rendementen ---
# ✅ Helperfunctie voor veilige conversie naar float - alleen in sat dus uitgeschakeld, wel in satpy
#def safe_float(val):
#    try:
#        return float(val) if pd.notna(val) else 0.0
#    except:
#        return 0.0

    
def determine_advice(df, threshold, risk_aversion=0):
    df = df.copy()

    # ✅ Trendberekening over SAM
    df["Trend"] = weighted_moving_average(df["SAM"], 12)
    df["TrendChange"] = df["Trend"] - df["Trend"].shift(1)
    df["Richting"] = np.sign(df["TrendChange"])
    df["Trail"] = 0
    df["Advies"] = np.nan

    # ✅ Bereken Trail (opeenvolgende richting-versterking)
    huidige_trend = 0
    for i in range(1, len(df)):
        huidige = df["Richting"].iloc[i]
        vorige = df["Richting"].iloc[i - 1]

        if huidige == vorige and huidige != 0:
            huidige_trend += 1
        elif huidige != 0:
            huidige_trend = 1
        else:
            huidige_trend = 0

        df.at[df.index[i], "Trail"] = huidige_trend

    # ✅ Advieslogica
    if risk_aversion == 0:
        mask_koop = (df["Richting"] == 1) & (df["Trail"] >= threshold) & (df["Advies"].isna())
        mask_verkoop = (df["Richting"] == -1) & (df["Trail"] >= threshold) & (df["Advies"].isna())

        df.loc[mask_koop, "Advies"] = "Kopen"
        df.loc[mask_verkoop, "Advies"] = "Verkopen"
        df["Advies"] = df["Advies"].ffill()

    elif risk_aversion == 1:
        for i in range(2, len(df)):
            trend_1 = df["SAT_Trend"].iloc[i]
            trend_2 = df["SAT_Trend"].iloc[i - 1]
            trend_3 = df["SAT_Trend"].iloc[i - 2]
            stage_1 = df["SAT_Stage"].iloc[i]
            stage_2 = df["SAT_Stage"].iloc[i - 1]
            stage_3 = df["SAT_Stage"].iloc[i - 2]

            if trend_1 >= trend_2 and trend_2 >= trend_3 and stage_1 > 0 and stage_2 > 0:
                df.at[df.index[i], "Advies"] = "Kopen"
            elif trend_1 < trend_2 and stage_1 < 0 and stage_2 < 0: # optie and trend_2 < trend_3 
                df.at[df.index[i], "Advies"] = "Verkopen"

        df["Advies"] = df["Advies"].ffill()

    elif risk_aversion == 2:
        for i in range(2, len(df)):
            trend_1 = df["SAT_Trend"].iloc[i]
            trend_2 = df["SAT_Trend"].iloc[i - 1]
            trend_3 = df["SAT_Trend"].iloc[i - 2]
            stage_1 = df["SAT_Stage"].iloc[i]
            stage_2 = df["SAT_Stage"].iloc[i - 1]
            stage_3 = df["SAT_Stage"].iloc[i - 2]
            
            if trend_1 > 0 and stage_1 > 0:
                df.at[df.index[i], "Advies"] = "Kopen"
            elif trend_1 < trend_2 and stage_1 < 0 and stage_2 < 0:
                df.at[df.index[i], "Advies"] = "Verkopen"

        df["Advies"] = df["Advies"].ffill()

    # ✅ Bereken rendementen op basis van adviesgroepering
    df["AdviesGroep"] = (df["Advies"] != df["Advies"].shift()).cumsum()
    rendementen = []
    sam_rendementen = []

    groepen = list(df.groupby("AdviesGroep"))

    for i in range(len(groepen)):
        _, groep = groepen[i]
        advies = groep["Advies"].iloc[0]

        start = groep["Close"].iloc[0]
        if i < len(groepen) - 1:
            eind = groepen[i + 1][1]["Close"].iloc[0]
        else:
            eind = groep["Close"].iloc[-1]

        try:
            start = float(start)
            eind = float(eind)
            if start != 0.0:
                markt_rendement = (eind - start) / start
                sam_rendement = markt_rendement if advies == "Kopen" else -markt_rendement
            else:
                markt_rendement = 0.0
                sam_rendement = 0.0
        except Exception:
            markt_rendement = 0.0
            sam_rendement = 0.0

        rendementen.extend([markt_rendement] * len(groep))
        sam_rendementen.extend([sam_rendement] * len(groep))

    if len(rendementen) != len(df):
        raise ValueError(f"Lengte mismatch: rendementen={len(rendementen)}, df={len(df)}")

    df["Markt-%"] = rendementen
    df["SAM-%"] = sam_rendementen

    if "Advies" in df.columns and df["Advies"].notna().any():
        huidig_advies = df["Advies"].dropna().iloc[-1]
    else:
        huidig_advies = "Niet beschikbaar"

    return df, huidig_advies

            
#--- Advies en rendement EINDE


  
# --- Streamlit UI ---
#st.title("SAM Trading Indicator")
# Titel met kleur en grootte tonen
# Kleur bepalen op basis van advies
#advies_kleur = "green" if huidig_advies == "Kopen" else "red" if huidig_advies == "Verkopen" else "gray"

# SAM TITLE
st.markdown(
    f"""
    <h1>SAM Trading Indicator<span style='color:#3366cc'>   </span></h1>
    """,
    unsafe_allow_html=True
)
# Simple Alert Monitor met responsive uitleg
st.markdown("""
<style>
.sam-uitleg details[open] {
  position: absolute;
  top: 0;
  left: 50%;
  transform: translateX(-50%);
  width: 90vw;
  max-width: 700px;
  z-index: 999;
  background-color: #f9f9f9;
  padding: 1em;
  box-shadow: 0 0 10px rgba(0,0,0,0.1);
  border-radius: 10px;
}
</style>

<div class="sam-uitleg" style='display: flex; justify-content: space-between; align-items: top;'>
  <div style='flex: 1;'>
    <h5 style='margin: 0;'>Simple Alert Monitor</h5>
  </div>
  <div style='flex: 1; text-align: right;'>
    <details>
      <summary style='cursor: pointer; font-weight: bold; color: #555;text-align: right;'>ℹ️ Uitleg SAM Trading Indicator</summary>
      <div style='margin-top: 10px;'>
        <p style='font-size: 13px; color: #333; text-align: left'>
        Gebruik de <strong>SAM Trading Indicator</strong> door voornamelijk te sturen op de blauwe lijn in de SAM en Trend grafiek,
        de trendlijn. De groene en rode SAM waarden (vaak perioden) geven het momentum weer...<br><br>
        Het advies is hiervan afgeleid en kan bijgesteld worden door de gevoeligheid aan te passen.<br>
        De indicator is oorspronkelijk bedoeld voor de <strong>middellange termijn belegger</strong>.
        </p>
      </div>
    </details>
  </div>
</div>
""", unsafe_allow_html=True)




# --- Update tab labels en bijbehorende mapping ---
# tab_labels = list(tabs_mapping.keys())
selected_tab = st.radio("Kies beurs", tab_labels, horizontal=True)
tickers = tabs_mapping[selected_tab]
valutasymbool = valutasymbool[selected_tab]
# }.get(selected_tab, "")

#def get_live_ticker_data(tickers_dict):
# --- Data ophalen voor dropdown live view ---
def get_live_ticker_data(tickers_dict):
    tickers = list(tickers_dict.keys())
    data = yf.download(tickers, period="1wk", interval="1wk", progress=False, group_by='ticker')
    result = []

    for ticker in tickers:
        try:
            last = data[ticker]['Close'].iloc[-1]
            prev = data[ticker]['Open'].iloc[-1]
            change = (last - prev) / prev * 100
            kleur = "#00FF00" if change > 0 else "#FF0000" if change < 0 else "#808080"
            naam = tickers_dict[ticker]
            result.append((ticker, naam, last, change, kleur))
        except Exception:
            continue

    return result

# --- Weergave dropdown met live info ---
live_info = get_live_ticker_data(tabs_mapping[selected_tab])
# --- Dropdown dictionary voorbereiden ---
dropdown_dict = {}  # key = ticker, value = (display_tekst, naam)

for t, naam, last, change, kleur in live_info:
    emoji = "🟢" if change > 0 else "🔴" if change < 0 else "⚪"
    display = f"{t} - {naam} | {valutasymbool}{last:.2f} {emoji} {change:+.2f}%"
    dropdown_dict[t] = (display, naam)

# --- Bepalen van de juiste default key voor selectie
# Herstel vorige selectie als deze nog bestaat
default_ticker_key = st.session_state.get(f"ticker_select_{selected_tab}")
if default_ticker_key not in dropdown_dict:
    default_ticker_key = list(dropdown_dict.keys())[0]  # fallback naar eerste

# --- Dropdown zelf ---
selected_ticker = st.selectbox(
    f"Selecteer {selected_tab} ticker:",
    options=list(dropdown_dict.keys()),  # alleen tickers als stabiele optie-key
    format_func=lambda x: dropdown_dict[x][0],  # toon koers etc.
    key=f"ticker_select_{selected_tab}",
    index=list(dropdown_dict.keys()).index(default_ticker_key)
)

# --- Ophalen ticker info ---
ticker = selected_ticker
ticker_name = dropdown_dict[ticker][1]

# --- Live koers opnieuw ophalen voor de geselecteerde ticker ---
try:
    live_data = yf.download(ticker, period="1wk", interval="1wk", progress=False)
    last = live_data["Close"].iloc[-1]
except Exception:
    last = 0.0  # fallback

# --- Andere instellingen ---
# --- Intervalopties ---
interval_optie = st.selectbox(
    "Kies de interval",
    ["Wekelijks", "Dagelijks", "4-uur", "1-uur", "15-minuten"]
)

# Vertaal gebruikerskeuze naar Yahoo Finance intervalcode
interval_mapping = {
    "Dagelijks": "1d",
    "Wekelijks": "1wk",
    "4-uur": "4h",
    "1-uur": "1h",
    "15-minuten": "15m"
}

interval = interval_mapping[interval_optie]
# -------

# 📌 Titel SAM UITLEG als toggle (zelfde stijl als eerder)
st.markdown("""
<style>
.sam-uitleg details[open] {
  position: absolute;
  top: 0;
  left: 50%;
  transform: translateX(-50%);
  width: 90vw;
  max-width: 700px;
  z-index: 999;
  background-color: #f9f9f9;
  padding: 1em;
  box-shadow: 0 0 10px rgba(0,0,0,0.1);
  border-radius: 10px;
}
</style>

<div class="sam-uitleg" style='display: flex; justify-content: space-between; align-items: top;'>
  <div style='flex: 1;'>
    <h4 style='margin-bottom: 10px;'>⚙️ Voorzichtigheid van advies (risk aversion)</h4>
  </div>
  <div style='flex: 1; text-align: right;'>
    <details>
      <summary style='cursor: pointer; font-weight: bold; color: #555;text-align: right;'>ℹ️ Uitleg risk aversion</summary>
      <div style='margin-top: 10px;'>
        <p style='font-size: 13px; color: #333; text-align: left'>
        Deze instelling bepaalt hoe voorzichtig het advies reageert op marktbewegingen.<br><br>
        - <strong>0 - Geen</strong>: Advies puur op basis van SAM (standaard trailing logica).<br>
        - <strong>1 - Laag</strong>: SAT moet 2 dagen positief/negatief zijn én trend stijgend/dalend.<br>
        - <strong>2 - Hoog</strong>: Alleen advies bij duidelijke SAT-trend met bevestiging.<br><br>
        Hogere waardes leiden tot minder signalen maar meer zekerheid.
        </p>   
      </div>
    </details>
  </div>
</div>
""", unsafe_allow_html=True)

# 📌 Slider in kolommen, links met max 50% breedte
col1, col2 = st.columns([1, 1])
with col1:
    risk_aversion = st.slider("Mate van risk aversion", 0, 2, 1, step=1)
with col2:
    pass  # lege kolom, zodat slider links blijft

# advies wordt geladen daarna
@st.cache_data(ttl=900)
def advies_wordt_geladen(ticker, interval, risk_aversion):
    df = fetch_data(ticker, interval)

    if df is None or df.empty or "Close" not in df.columns:
        return None, None

    # ✅ Altijd SAM en SAT berekenen
    df = calculate_sam(df)
    df = calculate_sat(df)

    # ✅ Advies bepalen
    threshold = 2  # ← Default trail voor risk_aversion = 0
    df, huidig_advies = determine_advice(df, threshold=threshold, risk_aversion=risk_aversion)

    return df, huidig_advies
    
# ✅ Gebruik en foutafhandeling
#df, huidig_advies = advies_wordt_geladen(ticker, interval, thresh, risk_aversion)
df, huidig_advies = advies_wordt_geladen(ticker, interval, risk_aversion)
# Keuze welke adviezen worden meegenomen in SAM-rendement
signaalkeuze = st.radio(
    "Toon SAM-rendement voor:",
    options=["Beide", "Koop", "Verkoop"],
    index=1,
    horizontal=True
)


# Grafieken

# Kleur bepalen op basis van advies
advies_kleur = "green" if huidig_advies == "Kopen" else "red" if huidig_advies == "Verkopen" else "gray"

# Titel met kleur en grootte tonen - indicator
col1, col2 = st.columns([1, 2])
with col1:
    st.markdown("### Advies voor:")

with col2:
    st.markdown(
    f"""
    <h3><span style='color:#3366cc'>{ticker_name}</span</h3>
    """,
    unsafe_allow_html=True
   )

# Titel met kleur en grootte tonen - advies
col1, col2 = st.columns([1, 2])
with col1:
    st.markdown("### Huidig advies:")

with col2:
    st.markdown(
    f"""
    <h2 style='color:{advies_kleur}'>{huidig_advies}</h2>
    """,
    unsafe_allow_html=True
    )

# -------------

# weergave grafieken via py
# 🟢 Toon koersgrafiek (toggle)
#if st.toggle("📈 Toon koersgrafiek", value=False):
plot_koersgrafiek(df, ticker_name, interval)

# 🔵 Toon SAM + Trend grafiek
plot_sam_trend(df, interval)

# ⚫ (optioneel) Debug SAT-grafiek — standaard niet geactiveerd
# plot_sat_debug(df, interval)
    
# --- Tabel met signalen en rendement ---
# later in je code, waar de tabel moet komen
toon_sam_tabel(df, selected_tab, signaalkeuze)
#st.subheader("Laatste signalen en rendement")


#st.write("DEBUG signaalkeuze boven Backtest:", signaalkeuze)
# ---------------------

## 📊 Backtestfunctie: sluit op close van nieuw signaal
backtest_functie(df, selected_tab, signaalkeuze)

# ✅ 0.Data voorbereiden voor advies')
df_signalen = df.copy()
if "Advies" not in df_signalen.columns:
    st.error("Kolom 'Advies' ontbreekt in de data.")
    st.stop()

                
st.subheader("Vergelijk Marktrendement en SAM-rendement")

# 📅 1. Datumkeuze
current_year = date.today().year
default_start = date(current_year -2, 1, 1)
#default_start = date(2021, 1, 1)
default_end = df.index.max().date()

start_date = st.date_input("Startdatum analyse", default_start)
end_date = st.date_input("Einddatum analyse", default_end)

# 📆 2. Filter op periode
df = df.copy()
df.index = pd.to_datetime(df.index)
df_period = df.loc[
    (df.index.date >= start_date) & (df.index.date <= end_date)
].copy()

# 🧹 Flatten MultiIndex indien nodig
if isinstance(df_period.columns, pd.MultiIndex):
    df_period.columns = ["_".join([str(i) for i in col if i]) for col in df_period.columns]

# 🔍 Zoek geldige 'Close'-kolom
close_col = next((col for col in df_period.columns if col.lower().startswith("close")), None)

if not close_col:
    st.error("❌ Geen geldige 'Close'-kolom gevonden in deze dataset.")
    st.stop()

# 📈 Marktrendement (Buy & Hold)
df_period[close_col] = pd.to_numeric(df_period[close_col], errors="coerce")
df_valid = df_period[close_col].dropna()

marktrendement = None
if len(df_valid) >= 2 and df_valid.iloc[0] != 0.0:
    koers_start = df_valid.iloc[0]
    koers_eind = df_valid.iloc[-1]
    marktrendement = ((koers_eind - koers_start) / koers_start) * 100

# ✅ Signaalkeuze geforceerd op Beide
#signaalkeuze = "Beide"
advies_col = "Advies"

# Vind eerste geldige advies (geen NaN) om mee te starten
eerste_valid_index = df_period[df_period["Advies"].notna()].index[0]
df_signalen = df_period.loc[eerste_valid_index:].copy()
df_signalen = df_signalen[df_signalen[advies_col].isin(["Kopen", "Verkopen"])].copy()

# 🔄 Backtestfunctie

#def bereken_sam_rendement(df_signalen, signaal_type="Beide", close_col="Close"):
def bereken_sam_rendement(df_signalen, signaal_type="Beide", close_col="Close"):
    rendementen = []
    trades = []
    entry_price = None
    entry_date = None
    entry_type = None

    type_map = {"Koop": "Kopen", "Verkoop": "Verkopen", "Beide": "Beide"}
    mapped_type = type_map.get(signaal_type, "Beide")

    for i in range(len(df_signalen)):
        advies = df_signalen["Advies"].iloc[i]
        close = df_signalen[close_col].iloc[i]
        datum = df_signalen.index[i]

        # Alleen sluiten als er een open positie is
        if entry_type is not None:
            if advies != entry_type and (mapped_type == "Beide" or entry_type == mapped_type):
                sluit_datum = datum
                sluit_close = close

                if entry_type == "Kopen":
                    rendement = (sluit_close - entry_price) / entry_price * 100
                else:
                    rendement = (entry_price - sluit_close) / entry_price * 100

                # Nieuw: filter dummy-trade
                if entry_price != sluit_close and entry_date != sluit_datum:
                    rendementen.append(rendement)
                    trades.append({
                        "Type": entry_type,
                        "Open datum": entry_date.date(),
                        "Open prijs": entry_price,
                        "Sluit datum": sluit_datum.date(),
                        "Sluit prijs": sluit_close,
                        "Rendement (%)": rendement,
                        "SAM": df.loc[entry_date, "SAM"] if entry_date in df.index else None,
                        "Trend": df.loc[entry_date, "Trend"] if entry_date in df.index else None,
                    })

                # Mogelijk nieuwe trade openen
                if mapped_type == "Beide" or advies == mapped_type:
                    entry_type = advies
                    entry_price = close
                    entry_date = datum
                else:
                    entry_type = None
                    entry_price = None
                    entry_date = None

        # Start een nieuwe trade, zonder geforceerd te zijn
        elif advies in ["Kopen", "Verkopen"] and (mapped_type == "Beide" or advies == mapped_type):
            entry_type = advies
            entry_price = close
            entry_date = datum

    # Eventueel open trade afsluiten op laatste koers
    if entry_type and entry_price is not None:
        laatste_datum = df_signalen.index[-1]
        laatste_koers = df_signalen[close_col].iloc[-1]

        if entry_type == "Kopen":
            rendement = (laatste_koers - entry_price) / entry_price * 100
        else:
            rendement = (entry_price - laatste_koers) / entry_price * 100

        # Nieuw: filter dummy-trade (ook laatste)
        if entry_price != laatste_koers and entry_date != laatste_datum:
            rendementen.append(rendement)
            trades.append({
                "Type": entry_type,
                "Open datum": entry_date.date(),
                "Open prijs": entry_price,
                "Sluit datum": laatste_datum.date(),
                "Sluit prijs": laatste_koers,
                "Rendement (%)": rendement
            })

    sam_rendement = sum(rendementen) if rendementen else 0.0
    return sam_rendement, trades, rendementen

# ✅ 4. Berekening
# ✅ 4.1: Berekening voor metric (gefilterd op gekozen signaal)
sam_rendement_filtered, _, _ = bereken_sam_rendement(df_signalen, signaal_type=signaalkeuze, close_col=close_col)

# ✅ 4.2: Berekening voor volledige analyse (altijd "Beide")
_, trades_all, _ = bereken_sam_rendement(df_signalen, signaal_type="Beide", close_col=close_col)

# ✅ 5.0: Alleen metric gebaseerd op keuze
col1, col2 = st.columns(2)
col1.metric("Marktrendement (Buy & Hold)", f"{marktrendement:+.2f}%" if marktrendement is not None else "n.v.t.")
col2.metric("📊 SAM-rendement", f"{sam_rendement_filtered:+.2f}%" if isinstance(sam_rendement_filtered, (int, float)) else "n.v.t.")

# ✅ 5.1: Volledige analyse op basis van alle trades (Beide)
if trades_all:
    df_trades = pd.DataFrame(trades_all)
    df_trades["SAM-% Koop"] = df_trades.apply(lambda row: row["Rendement (%)"] if row["Type"] == "Kopen" else None, axis=1)
    df_trades["SAM-% Verkoop"] = df_trades.apply(lambda row: row["Rendement (%)"] if row["Type"] == "Verkopen" else None, axis=1)
    df_trades["Markt-%"] = df_trades.apply(lambda row: ((row["Sluit prijs"] - row["Open prijs"]) / row["Open prijs"]) * 100, axis=1)

    # ✅ 5.2 Statistieken
    rendement_totaal = df_trades["Rendement (%)"].sum()
    rendement_koop = df_trades["SAM-% Koop"].sum(skipna=True)
    rendement_verkoop = df_trades["SAM-% Verkoop"].sum(skipna=True)
    aantal_trades = len(df_trades)
    aantal_koop = df_trades["SAM-% Koop"].notna().sum()
    aantal_verkoop = df_trades["SAM-% Verkoop"].notna().sum()
    aantal_succesvol = (df_trades["Rendement (%)"] > 0).sum()
    aantal_succesvol_koop = (df_trades["SAM-% Koop"] > 0).sum()
    aantal_succesvol_verkoop = (df_trades["SAM-% Verkoop"] > 0).sum()

    # ✅ 5.3 Captions op basis van volledige set
    st.caption(f"Aantal afgeronde **trades**: **{aantal_trades}**, totaal resultaat SAM-%: **{rendement_totaal:+.2f}%**, aantal succesvol: **{aantal_succesvol}**")
    st.caption(f"Aantal **koop** trades: **{aantal_koop}**, SAM-% koop: **{rendement_koop:+.2f}%**, succesvol: **{aantal_succesvol_koop}**")
    st.caption(f"Aantal **verkoop** trades: **{aantal_verkoop}**, SAM-% verkoop: **{rendement_verkoop:+.2f}%**, succesvol: **{aantal_succesvol_verkoop}**")

    # ✅ 5.4 Tabel tonen
    df_display = df_trades.copy()
    df_display = df_display.rename(columns={"Rendement (%)": "SAM-% tot."})
    df_display = df_display[[
        "Open datum", "Open prijs", "Sluit datum", "Sluit prijs",
        "Markt-%", "SAM-% tot.", "SAM-% Koop", "SAM-% Verkoop"]]

    for col in ["Markt-%", "SAM-% tot.", "SAM-% Koop", "SAM-% Verkoop"]:
        df_display[col] = df_display[col].astype(float)

    def kleur_positief_negatief(val):
        if pd.isna(val): return "color: #808080"
        if val > 0: return "color: #008000"
        if val < 0: return "color: #FF0000"
        return "color: #808080"

    toon_alle = st.toggle("Toon alle trades", value=False)
    if not toon_alle and len(df_display) > 12:
        df_display = df_display.iloc[-12:]

    if selected_tab == "🌐 Crypto":
        df_display["Open prijs"] = df_display["Open prijs"].map("{:.3f}".format)
        df_display["Sluit prijs"] = df_display["Sluit prijs"].map("{:.3f}".format)
    else:
        df_display["Open prijs"] = df_display["Open prijs"].map("{:.2f}".format)
        df_display["Sluit prijs"] = df_display["Sluit prijs"].map("{:.2f}".format)

    geldige_kolommen = [col for col in ["Markt-%", "SAM-% tot.", "SAM-% Koop", "SAM-% Verkoop"] if df_display[col].notna().any()]
    styler = df_display.style.applymap(kleur_positief_negatief, subset=geldige_kolommen)
    styler = styler.format({col: "{:+.2f}%" for col in geldige_kolommen})

    st.dataframe(styler, use_container_width=True)

else:
    st.info("ℹ️ Geen trades gevonden binnen de geselecteerde periode.")
    


# …na de adviezen en grafiek, etc.
#toon_trading_bot_interface(selected_ticker, huidig_advies)
toon_trading_bot_interface(selected_ticker, huidig_advies)
# 📌 Verbinding met Alpaca testen (optioneel, pas uit te voeren als gebruiker dit wil)










# wit
