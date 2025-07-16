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



def plaats_order(client, ticker, bedrag, last_price, order_type="Market Buy", trailing_pct=None):
    aantal = int(bedrag / last_price)
    if aantal <= 0:
        st.warning("❌ Bedrag is te klein voor order.")
        return
    try:
        if order_type == "Market Buy":
            order = MarketOrderRequest(
                symbol=ticker,
                qty=aantal,
                side=OrderSide.BUY,
                time_in_force=TimeInForce.GTC
            )
        elif order_type == "Market Sell":
            order = MarketOrderRequest(
                symbol=ticker,
                qty=aantal,
                side=OrderSide.SELL,
                time_in_force=TimeInForce.GTC
            )
        elif order_type == "Trailing Stop Buy":
            order = TrailingStopOrderRequest(
                symbol=ticker,
                qty=aantal,
                side=OrderSide.BUY,
                trail_percent=trailing_pct,
                time_in_force=TimeInForce.GTC
            )
        elif order_type == "Trailing Stop Sell":
            order = TrailingStopOrderRequest(
                symbol=ticker,
                qty=aantal,
                side=OrderSide.SELL,
                trail_percent=trailing_pct,
                time_in_force=TimeInForce.GTC
            )
        else:
            st.warning("Onbekend ordertype!")
            return
        response = client.submit_order(order)
        st.success(f"✅ Order geplaatst: {aantal}x {ticker} ({order_type})")
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
        
# aanvullende annuleer alles def
def annuleer_alle_orders_ticker(client, ticker):
    """
    Annuleert ALLE open orders (alle soorten!) voor de gekozen ticker.
    Geeft per order debug-output.
    """
    try:
        orders = client.get_orders()  # Haal ALLE orders op (open, filled, cancelled, enz.)
        canceled = 0
        found = 0
        for order in orders:
            # Toon alle details voor debug
            st.write({
                "id": order.id,
                "symbol": order.symbol,
                "side": order.side,
                "status": order.status,
                "type": getattr(order, "type", ""),
                "order_class": getattr(order, "order_class", ""),
                "parent_order_id": getattr(order, "parent_order_id", None),
                "qty": order.qty
            })
            # Alleen orders van deze ticker én status open/new/pending (sommige brokers gebruiken "new")
            if order.symbol == ticker and order.status in ("open", "new", "pending"):
                found += 1
                try:
                    client.cancel_order_by_id(order.id)
                    st.info(f"🗑️ Order {order.id} voor {ticker} geannuleerd ({getattr(order,'type','')})")
                    canceled += 1
                except Exception as e:
                    st.warning(f"⚠️ Fout bij annuleren van order {order.id}: {e}")

        if found == 0:
            st.info(f"ℹ️ Geen open/pending orders gevonden voor {ticker}.")
        elif canceled == 0:
            st.warning(f"⚠️ Geen orders konden worden geannuleerd voor {ticker}.")
        else:
            st.success(f"✅ {canceled} order(s) geannuleerd voor {ticker}.")
        return canceled
    except Exception as e:
        st.error(f"❌ Fout bij ophalen of annuleren van orders: {e}")
        return 0
        
# actual sluit posities def
def sluit_positie(client, ticker, advies, force=False):
    try:
        # 1. Controleer positie
        positie = client.get_open_position(ticker)
        aantal = int(float(positie.qty))
        if aantal == 0:
            st.info("ℹ️ Geen open positie om te sluiten.")
            return

        # 2. Alleen uitvoeren bij force=True of advies == "Verkopen"
        if not force and advies != "Verkopen":
            st.info("ℹ️ Huidig advies is geen 'Verkopen'. Geen actie ondernomen.")
            return

        # 3. Annuleer eerst ALLE open sell-orders voor deze ticker
        # Eerst alles annuleren
        aantal_geannuleerd = annuleer_alle_orders_ticker(client, ticker)
        # Eventueel even wachten na annuleren (optioneel)
        if aantal_geannuleerd > 0:
            st.info("⏳ Wachten 8 seconden zodat de stukken vrijkomen...")
            time.sleep(8)
    
        # 4. Nu directe market sell plaatsen voor alle stukken
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

# PANIEK SLUIT ECHT ALLES
def sluit_alles(client):
    st.warning("⚠️ Noodfunctie actief: alle posities en open orders worden nu gesloten/geannuleerd!")
    try:
        # 1. Annuleer eerst álle open orders (buy en sell, alle tickers)
        open_orders = client.get_orders()
        canceled = 0
        for order in open_orders:
            if order.status in ("open", "new", "pending"):
                try:
                    client.cancel_order_by_id(order.id)
                    st.info(f"🗑️ Order {order.id} ({order.symbol}, {order.side}) geannuleerd.")
                    canceled += 1
                except Exception as e:
                    st.warning(f"⚠️ Fout bij annuleren van order {order.id}: {e}")
        if canceled == 0:
            st.info("ℹ️ Geen open orders om te annuleren.")
        else:
            st.success(f"✅ {canceled} order(s) geannuleerd.")
            st.info("⏳ Wachten 8 seconden zodat alle stukken worden vrijgegeven...")
            time.sleep(8)

        # 2. Haal alle open posities op en sluit ze één voor één (market sell)
        posities = client.get_all_positions()
        closed = 0
        for positie in posities:
            ticker = positie.symbol
            aantal = int(float(positie.qty))
            if aantal > 0:
                try:
                    order = MarketOrderRequest(
                        symbol=ticker,
                        qty=aantal,
                        side=OrderSide.SELL,
                        time_in_force=TimeInForce.DAY
                    )
                    response = client.submit_order(order)
                    st.success(f"✅ Market sell geplaatst voor {aantal}x {ticker}.")
                    closed += 1
                except Exception as e:
                    st.warning(f"⚠️ Fout bij sluiten van positie {ticker}: {e}")
        if closed == 0:
            st.info("ℹ️ Geen posities om te sluiten.")
        else:
            st.success(f"✅ {closed} positie(s) gesloten.")
    except Exception as e:
        st.error(f"❌ Fout bij 'sluit alles': {e}")



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


        order_type = st.selectbox(
        "🛒 Kies ordertype",
          [
            "Market Buy",
            "Market Sell",
            "Trailing Stop Buy",
            "Trailing Stop Sell",
            "OTO: Market Buy + Trailing Stop Sell"
          ]
        )
      
        trailing_pct = None
        if "Trailing Stop" in order_type or order_type == "OTO: Market Buy + Trailing Stop Sell":
            trailing_pct = st.slider("📉 Trailing stop (% vanaf hoogste/laagste koers)", 1.0, 20.0, 2.0)
  
        handmatig = modus in ["Handmatig", "Beide"]
        automatisch = modus in ["Automatisch", "Beide"]

        if handmatig and st.button("📤 Handmatig order plaatsen"):
            if order_type == "OTO: Market Buy + Trailing Stop Sell":
                koop_en_trailing_stop(client, ticker, bedrag, last, trailing_pct)
            else:
                plaats_order(client, ticker, bedrag, last, order_type, trailing_pct)


  
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
        col
        
        if st.button("❗ Verkooppositie sluiten"):
            sluit_positie(client, ticker, huidig_advies, force=force_verkoop)

        if st.button("🚨 Sluit ALLES direct (noodstop)"):
            sluit_alles(client)






















# w
