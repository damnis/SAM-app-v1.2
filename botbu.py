import yfinance as yf
import streamlit as st
import pandas as pd
import time
from alpaca.trading.client import TradingClient
from alpaca.trading.enums import OrderSide, TimeInForce
from alpaca.trading.requests import MarketOrderRequest, TrailingStopOrderRequest

def verbind_met_alpaca(mode):
    try:
        sectie = "alpaca_paper" if mode == "Paper" else "alpaca_live"
        api_key = st.secrets[sectie]["ALPACA_API_KEY"]
        secret_key = st.secrets[sectie]["ALPACA_SECRET_KEY"]
        client = TradingClient(api_key, secret_key, paper=(mode == "Paper"))
        account = client.get_account()
        return client, account
    except Exception as e:
        st.error(f"❌ Fout bij verbinden met Alpaca: {e}")
        return None, None
        

def haal_laatste_koers(ticker):
    try:
        live_data = yf.download(ticker, period="1d", interval="1d", progress=False)
        if isinstance(live_data, pd.DataFrame) and "Close" in live_data.columns:
            return float(live_data["Close"].dropna().iloc[-1].squeeze())
    except:
        return None
    return None

def plaats_order(client, ticker, bedrag, last_price, advies, order_type="Market", trailing_pct=None):
    aantal = int(bedrag / last_price)
    if aantal <= 0:
        st.warning("❌ Bedrag is te klein voor aankoop.")
        return
    side = OrderSide.BUY if advies == "Kopen" else OrderSide.SELL
    try:
        if order_type == "Market":
            order = MarketOrderRequest(
                symbol=ticker,
                qty=aantal,
                side=side,
                time_in_force=TimeInForce.GTC
            )
        else:
            order = TrailingStopOrderRequest(
                symbol=ticker,
                qty=aantal,
                side=side,
                trail_percent=trailing_pct,
                time_in_force=TimeInForce.GTC
            )
        response = client.submit_order(order)
        st.success(f"✅ Order geplaatst: {aantal}x {ticker} ({advies}) via {order_type}")
        st.write(response)
    except Exception as e:
        st.error(f"❌ Order kon niet worden geplaatst: {e}")



def koop_en_trailing_stop(client, ticker, bedrag, last_price, trailing_pct):
    aantal = int(bedrag / last_price)
    if aantal <= 0:
        st.warning("❌ Bedrag is te klein voor aankoop.")
        return

    # 1. Koop (market)
    try:
        kooporder = MarketOrderRequest(
            symbol=ticker,
            qty=aantal,
            side=OrderSide.BUY,
            time_in_force=TimeInForce.GTC
        )
        koopresp = client.submit_order(kooporder)
        koop_id = koopresp.id
        st.info(f"⏳ Wachten tot kooporder ({aantal}x {ticker}) is uitgevoerd...")

        # 2. Poll tot filled
        max_wait = 30  # seconden
        waited = 0
        while waited < max_wait:
            order_status = client.get_order_by_id(koop_id).status
            if order_status == "filled":
                break
            time.sleep(1)
            waited += 1
        if order_status != "filled":
            st.error("❌ Kooporder niet uitgevoerd binnen 30 sec, geen trailing stop geplaatst.")
            return
        st.success("✅ Kooporder uitgevoerd! Nu trailing stop plaatsen...")

        # 3. Trailing stop SELL plaatsen voor exact aantal
        trailing_order = TrailingStopOrderRequest(
            symbol=ticker,
            qty=aantal,
            side=OrderSide.SELL,
            trail_percent=trailing_pct,
            time_in_force=TimeInForce.GTC
        )
        ts_resp = client.submit_order(trailing_order)
        st.success(f"✅ Trailing Stop Sell order geplaatst ({aantal}x {ticker}, {trailing_pct}% onder hoogste koers)")
        st.write(ts_resp)
    except Exception as e:
        st.error(f"❌ Fout bij OTO trailing stop: {e}")
        

def sluit_positie(client, ticker, advies, force=False):
    try:
        positie = client.get_open_position(ticker)
        aantal = int(float(positie.qty))
        if not force and advies != "Verkopen":
            st.info("ℹ️ Huidig advies is geen 'Verkopen'. Geen actie ondernomen.")
            return
        order = MarketOrderRequest(
            symbol=ticker,
            qty=aantal,
            side=OrderSide.SELL,
            time_in_force=TimeInForce.DAY
        )
        response = client.submit_order(order)
        st.success(f"✅ Verkooporder geplaatst voor {aantal}x {ticker}")
        st.write(response)
    except Exception as e:
        st.info("📭 Geen open positie of fout bij ophalen: " + str(e))

def toon_trading_bot_interface(ticker, huidig_advies):
    st.subheader("📥 Plaats live/paper trade op basis van advies")
    
    # ⭐ Modekeuze toegevoegd
    trade_mode = st.selectbox("🔀 Kies Alpaca account type:", ["Paper", "Live"], index=0)
    modus = st.radio("🎛️ Kies handelsmodus", ["Handmatig", "Automatisch", "Beide"], horizontal=True)

    # Verbind met gekozen account
    client, account = verbind_met_alpaca(trade_mode)
    if client is None:
        return

    # UI waarschuwing bij LIVE
    if trade_mode == "Live":
        st.warning("⚠️ LIVE TRADING - ECHT GELD! Dubbelcheck bedrag & ticker!")
    else:
        st.info("🧪 Paper Trading (virtueel geld, geen risico)")

    if account:
        st.success(f"✅ Verbonden met Alpaca-account ({account.status})")
        st.write(f"👤 Account-ID: {account.id}")
        st.write(f"💰 Beschikbaar cash: ${float(account.cash):,.2f}")
        st.write(f"📈 Portfolio waarde: ${float(account.portfolio_value):,.2f}")

    with st.expander(f"{'💵' if trade_mode=='Live' else '🧪'} Order plaatsen via Alpaca {trade_mode} Account"):
        last = haal_laatste_koers(ticker)
        if last:
            st.write(f"📉 Laatste koers voor {ticker}: **${last:.2f}**")
        else:
            st.warning("⚠️ Geen geldige koers beschikbaar voor dit aandeel.")
            return

        bedrag = st.number_input("💰 Te investeren bedrag ($)", min_value=10.0, value=1000.0, step=10.0)
        st.write(f"📌 Actueel advies voor {ticker}: **{huidig_advies}**")


        order_type = st.radio("🛒 Kies ordertype", ["Market", "Trailing Stop", "OTO: Market Buy + Trailing Stop Sell"], horizontal=True)
        trailing_pct = None
        if order_type in ["Trailing Stop", "OTO: Market Buy + Trailing Stop Sell"]:
            trailing_pct = st.slider("📉 Trailing stop (% vanaf hoogste koers)", 1.0, 20.0, 2.0)

        handmatig = modus in ["Handmatig", "Beide"]
        automatisch = modus in ["Automatisch", "Beide"]

        if handmatig and st.button("📤 Handmatig order plaatsen"):
            if order_type == "OTO: Market Buy + Trailing Stop Sell":
                koop_en_trailing_stop(client, ticker, bedrag, last, trailing_pct)
            else:
                plaats_order(client, ticker, bedrag, last, huidig_advies, order_type, trailing_pct)
        
        
   #     order_type = st.radio("🛒 Kies ordertype", ["Market", "Trailing Stop"], horizontal=True)
   #     trailing_pct = None
  #      if order_type == "Trailing Stop":
   #         trailing_pct = st.slider("📉 Trailing stop (% vanaf hoogste koers)", 1.0, 20.0, 5.0)

   #     handmatig = modus in ["Handmatig", "Beide"]
   #     automatisch = modus in ["Automatisch", "Beide"]

   #     if handmatig and st.button("📤 Handmatig order plaatsen"):
   #         plaats_order(client, ticker, bedrag, last, huidig_advies, order_type, trailing_pct)

   #     if automatisch and huidig_advies in ["Kopen", "Verkopen"]:
   #         st.info("🤖 Automatisch advies actief...")
   #         plaats_order(client, ticker, bedrag, last, huidig_advies, order_type, trailing_pct)

    st.markdown("---")

    st.subheader("📤 Verkooppositie controleren en sluiten")
    with st.expander(f"{'💵' if trade_mode=='Live' else '🧪'} Positie check en verkoopactie"):
        try:
            positie = client.get_open_position(ticker)
            huidige_qty = int(float(positie.qty))
            avg_price = float(positie.avg_entry_price)
            st.write(f"📦 Je bezit momenteel **{huidige_qty}x {ticker}** @ ${avg_price:.2f} gemiddeld.")
        except Exception:
            st.info("📭 Geen open positie gevonden in deze ticker.")
            return

        st.write(f"📌 Huidig advies: **{huidig_advies}**")
        force_verkoop = st.checkbox("🔒 Forceer verkoop, ongeacht advies")

        if st.button("❗ Verkooppositie sluiten"):
            sluit_positie(client, ticker, huidig_advies, force=force_verkoop)
























# w
