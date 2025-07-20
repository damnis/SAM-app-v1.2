import streamlit as st
# acces control
from passem import password_gate
password_gate()
# needed imports
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
from sectorticker import sector_tickers, sector_tickers_news 
from tickers import (
    aex_tickers, amx_tickers, dow_tickers, eurostoxx_tickers,
    nasdaq_tickers, ustech_tickers, crypto_tickers, mijn_lijst, 
    tabs_mapping, tab_labels, valutasymbool, tickers_screening 
)
# Indicatoren berekening
from yffetch import fetch_data, fetch_data_cached 
from sam_indicator import calculate_sam
from sat_indicator import calculate_sat
from adviezen import determine_advice, weighted_moving_average 
# grafieken en tabellen
from grafieken import plot_koersgrafiek, plot_sam_trend, plot_sat_debug, bepaal_grafiekperiode, plot_overlay_grafiek 
from genereer import genereer_adviesmatrix 
from grafieken import toon_adviesmatrix_html
from sam_tabel import toon_sam_tabel 
from heatmap import toon_sector_heatmap
# screening
from screening import screen_tickers
# nieuws
from newsfeed import toon_newsfeed
# --- Fundamentele data ophalen en tonen ---
from datafund import get_income_statement, get_ratios
from datafund import (
    get_profile, get_key_metrics, get_earning_calendar,
    get_dividend_history, get_quarterly_eps, get_eps_forecast,
    get_news_fmp, get_news_yahoo, get_analyst_recommendations 
)
from fundament import (
    toon_profiel_en_kerninfo, toon_omzet_winst_eps, toon_ratios,
    toon_datums, test_fmp_endpoint, test_yfinance, test_analyst_data_yf,
    get_yf_data
)
from fundament import toon_fundamentals 
# Backtestfunctie 
from backtest import backtest_functie, bereken_sam_rendement
# trading bot
from bot import toon_trading_bot_interface
#from coinex import get_spot_balance, get_spot_market, put_limit_order, put_market_order
#from optiebot import toon_optie_trading_bot_interface 
# from bot import verbind_met_alpaca, map_ticker_for_alpaca, crypto_slash_to_plain, haal_laatste_koers, plaats_order, sluit_positie
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest, TrailingStopOrderRequest, LimitOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce
#from alpaca.trading.requests import OptionOrderRequest

#import alpaca_trade_api as tradeapi
from fmpfetch import fetch_data_fmp, search_ticker_fmp


 
# ---------
# SAM TITLE
# ---------
st.markdown(
    f"""
    <h1>SAT+SAM Trading Indicator<span style='color:#3366cc'>   </span></h1>
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

<div class="sam-uitleg" style='display: flex; justify-content: space-between; align-items: flex-start;'>
  <div style='width: 60%;'>
    <h5 style='margin: 0;'>Stage and Trend Simple Alert Monitor</h5>
  </div>
  <div style='width: 40%; text-align: right;'>
    <details>
      <summary style='cursor: pointer; font-weight: bold; color: #555;text-align: right;'>ℹ️ Uitleg indicator</summary>
      <div style='margin-top: 10px;'>
        <p style='font-size: 13px; color: #333; text-align: left'>
        Gebruik de <strong>SAT+SAM Trading Indicator</strong> door voornamelijk te sturen op de blauwe lijn in de SAM en Trend grafiek,
        de trendlijn. De groene en rode SAM waarden (vaak perioden) geven het momentum weer...<br><br>
        Het advies is hiervan afgeleid en kan bijgesteld worden door de gevoeligheid aan te passen.<br>
        De indicator is oorspronkelijk bedoeld voor de <strong>middellange termijn belegger</strong>.
        </p>
      </div>
    </details>
  </div>
</div>
""", unsafe_allow_html=True)

#<div class="sam-uitleg" style='display: flex; justify-content: space-between; align-items: top;'>
#  <div style='flex: 2; min-width:220px; max-width:700px;'>
#    <h5 style='margin: 0;'>Stage and Trend Simple Alert Monitor</h5>
#  </div>
#  <div style='flex: 1; text-align: right;'>
#    <details>
 #     <summary style='cursor: pointer; font-weight: bold; color: #555;text-align: right;'>ℹ️ Uitleg Indicator</summary>
  #    <div style='margin-top: 10px;'>
#        <p style='font-size: 12px; color: #333; text-align: left'>
#        Gebruik de <strong>SAT+SAM Trading Indicator</strong> door voornamelijk te sturen op de blauwe lijn in de SAM en Trend grafiek,
 #       de trendlijn. De groene en rode SAM waarden (vaak perioden) geven het momentum weer...<br><br>
  #      Het advies is hiervan afgeleid en kan bijgesteld worden door de gevoeligheid aan te passen.<br>
#        De indicator is oorspronkelijk bedoeld voor de <strong>middellange termijn belegger</strong>.
#        </p>
#      </div>
#    </details>
#  </div>
#</div>
#""", unsafe_allow_html=True)




# --- Update tab labels en bijbehorende mapping ---

# ---- BEURZEN & DROPDOWN ----
tab_labels = list(tabs_mapping.keys())
selected_tab = st.radio("Kies beurs", tab_labels, horizontal=True)
tickers = tabs_mapping[selected_tab]
valutasymbool = valutasymbool[selected_tab]
#}.get(selected_tab, "")

#def get_live_ticker_data(tickers_dict):
# --- Data ophalen voor dropdown live view ---
def get_live_ticker_data(tickers_dict):
    tickers = list(tickers_dict.keys())
    data = yf.download(tickers, period="2d", interval="1d", progress=False, group_by='ticker')
    result = []

    for ticker in tickers:
        try:
            df = data[ticker]
            # Forceer DataFrame indien Series
            if isinstance(df, pd.Series):
                df = df.to_frame().T
            last = df['Close'].iloc[-1]
            if len(df) >= 2:
                prev = df['Close'].iloc[-2]
            else:
                prev = df['Open'].iloc[-1]
            change = (last - prev) / prev * 100
            kleur = "#00FF00" if change > 0 else "#FF0000" if change < 0 else "#808080"
            naam = tickers_dict[ticker]
            result.append((ticker, naam, last, change, kleur))
        except Exception as e:
            # st.write(f"Ticker {ticker} error: {e}") # Debug, mag weg
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
    live_data = yf.download(ticker, period="1d", interval="1d", progress=False)
    last = live_data["Close"].iloc[-1]
except Exception:
    last = 0.0  # fallback

# --- Andere instellingen ---
zoekterm = st.text_input("🔍 Gebruik 'Vrije keuze...' uit mijn lijst en zoek op naam of ticker", value="Dream finder").strip()

suggesties = search_ticker_fmp(zoekterm)

if suggesties:
    ticker_opties = [f"{sym} - {naam}" for sym, naam in suggesties]
    selectie = st.selectbox("Kies ticker", ticker_opties, index=0)
    query = selectie.split(" - ")[0]  # extract ticker
else:
    st.warning("⚠️ Geen resultaten gevonden.")
    query = ""
    
# overige
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


# --- Als originele ticker een NaN is, en er is een query, gebruik die
if (pd.isna(ticker) or ticker in ["", "nan", None]) and query:
    ticker = query
    ticker_name = query  # eventueel uit selectie halen


# 📌 Slider in kolommen, links met max 50% breedte
col1, col2 = st.columns([1, 1])
with col1:
    risk_aversion = st.slider("Mate van risk aversion", 0, 3, 1, step=1)
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
    "Signaalkeuze: Toon SAT+SAM-rendement voor:",
    options=["Beide", "Koop", "Verkoop"],
    index=0,
    horizontal=True
)


# Grafieken

# Kleur bepalen op basis van advies
advies_kleur = "green" if huidig_advies == "Kopen" else "red" if huidig_advies == "Verkopen" else "gray"

# --- Check op koersdata beschikbaarheid ---
if df is None or df.empty or "Close" not in df.columns or df["Close"].dropna().empty:
    st.warning("⚠️ Geen koersdata beschikbaar voor deze ticker. Analyse en adviezen zijn niet mogelijk.")
    st.stop()  # Of gewoon return als dit in een functie zit
else:
    # Titel met kleur en grootte tonen - indicator
    col1, col2 = st.columns([1, 2])
    with col1:
        st.markdown("### Advies voor:")

    with col2:
        laatste_koers = df["Close"].iloc[-1]
        st.markdown(
            f"""
            <h3>
                <span style='color:#3366cc'>{ticker_name}</span>
                <span style='color:#3366dd;font-weight:400;'>| {valutasymbool}{laatste_koers:,.2f}</span>
            </h3>
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


# screening tool

if st.button("🔎 Zoek stijgers met koop advies (1 wk)"):
    screeneresult = screen_tickers(tickers_screening, min_momentum=2)
#    st.dataframe(screeneresult)

    if not screeneresult.empty:
        st.markdown("### 💡 SAT + SAM Advies en Marktadvies (analisten):")
        tickers = list(screeneresult["Ticker"])

        # Ophalen en combineren
        @st.cache_data(ttl=3600)
        def get_latest_analyst_rec(ticker):
            data = get_analyst_recommendations(ticker)
            if data:
                last = data[0]
                return {
#                    "Symbol": ticker,
                    "Markt advies": last.get("date", None),
                    "Buy": last.get("analystRatingsbuy", 0) + last.get("analystRatingsStrongBuy", 0),
                    "Hold": last.get("analystRatingsHold", 0),
                    "Sell": last.get("analystRatingsSell", 0) + last.get("analystRatingsStrongSell", 0),
                }
                
            else:
                return {"Buy": None, "Hold": None, "Sell": None}

        analyst_data = []
        for ticker in tickers:
            row = {"Ticker": ticker}
            row.update(get_latest_analyst_rec(ticker))
            analyst_data.append(row)
        df_analyst = pd.DataFrame(analyst_data)

        # Merge met screeningresultaat
        result = screeneresult.merge(df_analyst, on="Ticker", how="left")
        st.dataframe(result)


#if st.button("🔎 Zoek koopwaardige aandelen"):
#    screeneresult = screen_tickers(tickers_screening, min_momentum=2)
#    st.dataframe(screeneresult)



# ------- Toggle voor sector-heatmap (bijv. onder je matrix/tabellen) ---
if st.toggle("🔥 Toon sector heatmap"):
    sortering_nice = st.radio(
        "Sorteer tickers per sector op:",
        ["💰 Marktkapitalisatie", "🔠 Alfabetisch"],
        horizontal=True
    )
    
    # Vertaal weer terug naar interne waarde
    mapping = {
        "💰 Marktkapitalisatie": "marktkapitalisatie",
        "🔠 Alfabetisch": "alfabetisch"
    }
    sortering = mapping.get(sortering_nice, "marktkapitalisatie")

    toon_sector_heatmap(interval, risk_aversion, sorteer_op=sortering)



 #   sortering = st.radio("📚 Sorteer tickers", ["Origineel", "Alfabetisch"], horizontal=True)
  #if st.toggle("📌 Toon sector-heatmap"):
# ----------------------------

# advies matrix
toon_adviesmatrix_html(ticker, risk_aversion=risk_aversion)
# weergave grafieken via py

plot_overlay_grafiek(df, ticker_name, interval) 

# 🟢 Toon koersgrafiek (toggle)
#if st.toggle("📈 Toon koersgrafiek", value=False):
plot_koersgrafiek(df, ticker_name, interval)

# 🔵 Toon SAM + Trend grafiek
plot_sam_trend(df, interval)

# ⚫ (optioneel) Debug SAT-grafiek — standaard niet geactiveerd
plot_sat_debug(df, interval)
    
# --- Tabel met signalen en rendement ---
# later in je code, waar de tabel moet komen
toon_sam_tabel(df, selected_tab, signaalkeuze)

# toon news
# ... selecteer ticker zoals altijd:
toon_newsfeed()
#ticker = selected_ticker  # of hoe je hem ook noemt in je app
#toon_newsfeed(ticker)

# Toon Fundamentals
toon_fundamentals(ticker)
#toon_fundamentals(ticker)




#st.subheader("Fundamentals")
#st.write("✅ Profiel:", profile)
#st.write("✅ Key metrics:", key_metrics)
#st.write("✅ Income data:", income_data[:1])  # eerste record
#st.write("✅ Ratio data:", ratio_data[:1])

# Bedrijfsprofiel fmp (fundamental):
#profile = get_profile(ticker)
#key_metrics = get_key_metrics(ticker)
#income_data = get_income_statement(ticker)
#ratio_data = get_ratios(ticker)
#earnings = get_earning_calendar(ticker)
#dividends = get_dividend_history(ticker)

#toon_profiel_en_kerninfo(profile, key_metrics)
#toon_omzet_winst_eps(income_data)
#toon_ratios(ratio_data)
#toon_datums(earnings, dividends)


#st.write("DEBUG signaalkeuze boven Backtest:", signaalkeuze)
# ---------------------

## 📊 Backtestfunctie: sluit op close van nieuw signaal
# ✅ 0.Data voorbereiden voor advies')
df_signalen = df.copy()
if "Advies" not in df_signalen.columns:
    st.error("Kolom 'Advies' ontbreekt in de data.")
    st.stop()
backtest_functie(df, signaalkeuze=signaalkeuze, selected_tab=selected_tab, interval=interval)  
# ✅ #backtest_functie(df, selected_tab, signaalkeuze)


# …na de adviezen en grafiek, etc.
# trading bot
toon_trading_bot_interface(ticker, huidig_advies)
# 📌 Verbinding met Alpaca testen (optioneel, pas uit te voeren als gebruiker dit wil)
# optiebot
#toon_optie_trading_bot_interface(selected_ticker, huidig_advies)

# -----------------
# cryptobot coinex 
#api_key = st.secrets["coinex"]["coin_api_key"]
#api_secret = st.secrets["coinex"]["coin_api_secret"]

#st.title("CoinEx Trading Bot")

#if st.button("Toon saldo"):
#    res = get_spot_balance(api_key, api_secret)
#    st.write(res)

#market = st.text_input("Trading pair (bv. BTCUSDT):", "BTCUSDT")
#side = st.radio("Side", ["buy", "sell"])
#amount = st.number_input("Aantal", min_value=0.00001, value=0.01, format="%.6f")
#price = st.number_input("Limit prijs (optioneel, leeg=market order)", min_value=0.0, value=0.0, format="%.2f")

#if st.button("Plaats order"):
#    if price > 0:
#        res = put_limit_order(api_key, api_secret, market, side, amount, price)
 #       st.write(res)
 #   else:
#        res = put_market_order(api_key, api_secret, market, side, amount)
  #      st.write(res)






# -----------------------------
#FMP testapi
if st.sidebar.checkbox("🧪 FMP Test Tool"):
    test_fmp_endpoint()
#yfinance testapi
if st.sidebar.checkbox("🧪 yfinance Test Tool"):
    test_yfinance()
    if testbron == "yfinance":
        ...
        test_analyst_data_yf(ticker)

 
###### oud

#    for i in range(2, len(df)):
#            sam_1 = df["SAM"].iloc[i]
#            trends_1 = df["Trend"].iloc[i]
#            trends_2 = df["Trend"].iloc[i - 1]
#            trend_1 = df["SAT_Trend"].iloc[i]
#            trend_2 = df["SAT_Trend"].iloc[i - 1]
#            trend_3 = df["SAT_Trend"].iloc[i - 2]
#            stage_1 = df["SAT_Stage"].iloc[i]
#            stage_2 = df["SAT_Stage"].iloc[i - 1]
#            stage_3 = df["SAT_Stage"].iloc[i - 2]

#            if trend_1 >= trend_2 and trend_2 >= trend_3 and stage_1 > 0 or (trends_1 - trends_2 >= 0) and sam_1 >= 0:
#                df.at[df.index[i], "Advies"] = "Kopen"
 #           elif trend_1 < trend_2 and stage_1 < 0 and stage_2 < 0: # optie and trend_2 < trend_3 
 #               df.at[df.index[i], "Advies"] = "Verkopen"

#        df["Advies"] = df["Advies"].ffill()

    
#    elif risk_aversion == 2:
#        for i in range(2, len(df)):
#            trend_1 = df["SAT_Trend"].iloc[i]
#            trend_2 = df["SAT_Trend"].iloc[i - 1]
 #           trend_3 = df["SAT_Trend"].iloc[i - 2]
#            stage_1 = df["SAT_Stage"].iloc[i]
 #           stage_2 = df["SAT_Stage"].iloc[i - 1]
 #           stage_3 = df["SAT_Stage"].iloc[i - 2]

#            if trend_1 >= trend_2 and trend_2 >= trend_3 and stage_1 > 0 and stage_2 > 0:
#                df.at[df.index[i], "Advies"] = "Kopen"
 #           elif trend_1 < trend_2 and stage_1 < 0: # optie and trend_2 < trend_3 
  #              df.at[df.index[i], "Advies"] = "Verkopen"

#        df["Advies"] = df["Advies"].ffill()

#    elif risk_aversion == 3:
#        for i in range(2, len(df)):
#            trend_1 = df["SAT_Trend"].iloc[i]
 #           trend_2 = df["SAT_Trend"].iloc[i - 1]
#            trend_3 = df["SAT_Trend"].iloc[i - 2]
#            stage_1 = df["SAT_Stage"].iloc[i]
#            stage_2 = df["SAT_Stage"].iloc[i - 1]
 #           stage_3 = df["SAT_Stage"].iloc[i - 2]
            
  #          if trend_1 > 0 and stage_1 > 0:
  #              df.at[df.index[i], "Advies"] = "Kopen"
  #          elif trend_1 < trend_2 and stage_1 < 0 and stage_2 < 0:
  #              df.at[df.index[i], "Advies"] = "Verkopen"

  #      df["Advies"] = df["Advies"].ffill()













# w







# wit
