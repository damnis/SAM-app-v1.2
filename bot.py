import yfinance as yf
from fmpfetch import fetch_data_fmp, search_ticker_fmp
import streamlit as st
import pandas as pd
import time
import requests
from alpaca.trading.client import TradingClient
from alpaca.trading.enums import OrderSide, TimeInForce
from alpaca.trading.requests import (
    MarketOrderRequest,
    TrailingStopOrderRequest,
    LimitOrderRequest
)

# ---------- TICKER MAPPING: Stock & Crypto ----------
def map_ticker_for_alpaca(ticker, asset_type="auto"):
    """
    Maakt van 'ASML.AS' of 'INGA:US' gewoon 'ASML' voor Alpaca (stocks).
    Voor crypto werkt bestaande logica (BTC-USD → BTC/USD).
    asset_type: 'stock', 'crypto', of 'auto' (default: auto-detect via -USD/USDT)
    """
    t = ticker.upper()
    # Auto-detect: als -USD, -USDT of slash → crypto, anders stock
    if asset_type == "auto":
        if any(s in t for s in ["-USD", "-USDT", "/"]):
            asset_type = "crypto"
        else:
            asset_type = "stock"
    if asset_type == "crypto":
        if "-" in t and not "/" in t:
            t = t.replace("-", "/")
        elif "/" in t:
            t = t  # Geen verdere mapping nodig
    else:  # asset_type == "stock"
        t = t.split(".")[0].split(":")[0]
    return t

def crypto_slash_to_plain(ticker):
    """Verwijdert alleen de '/' uit een cryptoticker, bijvoorbeeld ETH/USD → ETHUSD"""
    return ticker.replace("/", "")

# ---------- ALPACA LIVE ASSET CHECK ----------
def check_alpaca_ticker(ticker, api_key, secret_key):
    """Check of ticker bestaat bij Alpaca, geef basisinfo terug (naam, tradable, prijs)."""
    alpaca_url = f"https://paper-api.alpaca.markets/v2/assets/{ticker}"
    headers = {
        "APCA-API-KEY-ID": api_key,
        "APCA-API-SECRET-KEY": secret_key,
    }
    r = requests.get(alpaca_url, headers=headers)
    if r.status_code != 200:
        return None
    asset = r.json()
    # Huidige prijs ophalen via quotes (optioneel)
    price = None
    try:
        quote_url = f"https://data.alpaca.markets/v2/stocks/{ticker}/quotes/latest"
        q = requests.get(quote_url, headers=headers)
        if q.status_code == 200:
            price = q.json().get("quote", {}).get("ap", None)  # ask price
    except:
        pass
    return {
        "symbol": asset.get("symbol"),
        "name": asset.get("name"),
        "exchange": asset.get("exchange"),
        "tradable": asset.get("tradable"),
        "status": asset.get("status"),
        "price": price,
    }

def verbind_met_alpaca(mode):
    try:
        sectie = "alpaca_paper" if mode == "Paper" else "alpaca_live"
        api_key = st.secrets[sectie]["ALPACA_API_KEY"]
        secret_key = st.secrets[sectie]["ALPACA_SECRET_KEY"]
        client = TradingClient(api_key, secret_key, paper=(mode == "Paper"))
        account = client.get_account()
        return client, account, api_key, secret_key
    except Exception as e:
        st.error(f"❌ Fout bij verbinden met Alpaca: {e}")
        return None, None, None, None

def haal_laatste_koers(ticker):
    try:
        live_data = yf.download(ticker, period="1d", interval="1d", progress=False)
        if isinstance(live_data, pd.DataFrame) and "Close" in live_data.columns:
            return float(live_data["Close"].dropna().iloc[-1].squeeze())
    except:
        return None
    return None

# ---------- ORDER FUNCTIES -----------
def plaats_order(client, ticker, bedrag, last_price, order_type="Market Buy", trailing_pct=None, aantal=None, limietkoers=None):
#    symbol = map_ticker_for_alpaca(ticker)
    symbol = map_ticker_for_alpaca(ticker)
    is_crypto = ticker.upper().endswith("-USD") or "/" in ticker
    if aantal is None:
        if is_crypto:
            _aantal = float(bedrag) / float(last_price)
        else:
            _aantal = int(float(bedrag) // float(last_price))
    else:
        _aantal = float(aantal)
    
#    _aantal = float(bedrag) / float(last_price) if aantal is None else float(aantal)
    if _aantal <= 0.0000001:
        st.warning("❌ Te klein bedrag of aantal voor order.")
        return
    try:
        if order_type == "Market Buy":
            order = MarketOrderRequest(
                symbol=symbol,
                qty=_aantal,
                side=OrderSide.BUY,
                time_in_force=TimeInForce.GTC
            )
        elif order_type == "Market Sell":
            order = MarketOrderRequest(
                symbol=symbol,
                qty=_aantal,
                side=OrderSide.SELL,
                time_in_force=TimeInForce.GTC
            )
        elif order_type == "Limit Buy":
            order = LimitOrderRequest(
                symbol=symbol,
                qty=_aantal,
                side=OrderSide.BUY,
                limit_price=limietkoers,
                time_in_force=TimeInForce.GTC
            )
        elif order_type == "Limit Sell":
            order = LimitOrderRequest(
                symbol=symbol,
                qty=_aantal,
                side=OrderSide.SELL,
                limit_price=limietkoers,
                time_in_force=TimeInForce.GTC
            )
        elif order_type == "Trailing Stop Buy":
            order = TrailingStopOrderRequest(
                symbol=symbol,
                qty=_aantal,
                side=OrderSide.BUY,
                trail_percent=trailing_pct,
                time_in_force=TimeInForce.GTC
            )
        elif order_type == "Trailing Stop Sell":
            order = TrailingStopOrderRequest(
                symbol=symbol,
                qty=_aantal,
                side=OrderSide.SELL,
                trail_percent=trailing_pct,
                time_in_force=TimeInForce.GTC
            )
        else:
            st.warning("Onbekend ordertype!")
            return
        response = client.submit_order(order)
        st.success(f"✅ Order geplaatst: {_aantal}x {symbol} ({order_type})")
        st.write(response)
    except Exception as e:
        st.error(f"❌ Order kon niet worden geplaatst: {e}")

def koop_en_trailing_stop(client, ticker, bedrag, last_price, trailing_pct, aantal=None):
    symbol = map_ticker_for_alpaca(ticker)
    _aantal = float(bedrag / last_price) if aantal is None else float(aantal)
    if _aantal <= 0.0000001:
        st.warning("❌ Bedrag of aantal te klein voor aankoop.")
        return
    try:
        kooporder = MarketOrderRequest(
            symbol=symbol,
            qty=_aantal,
            side=OrderSide.BUY,
            time_in_force=TimeInForce.GTC
        )
        koopresp = client.submit_order(kooporder)
        koop_id = koopresp.id
        st.info(f"⏳ Wachten tot kooporder ({_aantal}x {symbol}) is uitgevoerd...")

        # Pollen tot filled (of failed)
        max_wait = 30
        waited = 0
        order_status = None
        while waited < max_wait:
            order_status = client.get_order_by_id(koop_id).status
            if order_status == "filled":
                break
            elif order_status in ["canceled", "rejected", "expired"]:
                st.error(f"❌ Kooporder kon niet uitgevoerd worden (status: {order_status}). OTO wordt geannuleerd.")
                try:
                    client.cancel_order_by_id(koop_id)
                except: pass
                return
            time.sleep(1)
            waited += 1
        if order_status != "filled":
            st.error("❌ Kooporder niet uitgevoerd binnen 30 sec, trailing stop wordt niet geplaatst en order wordt geannuleerd.")
            try:
                client.cancel_order_by_id(koop_id)
            except: pass
            return
        st.success("✅ Kooporder uitgevoerd! Nu trailing stop plaatsen...")

        # Trailing stop SELL plaatsen voor exact aantal
        trailing_order = TrailingStopOrderRequest(
            symbol=symbol,
            qty=_aantal,
            side=OrderSide.SELL,
            trail_percent=trailing_pct,
            time_in_force=TimeInForce.GTC
        )
        ts_resp = client.submit_order(trailing_order)
        st.success(f"✅ Trailing Stop Sell order geplaatst ({_aantal}x {symbol}, {trailing_pct}% onder hoogste koers)")
        st.write(ts_resp)
    except Exception as e:
        st.error(f"❌ Fout bij OTO trailing stop: {e}")

# ---------- SLUITEN & ANNULEREN FUNCTIES -----------

def annuleer_alle_orders_ticker(client, ticker):
    symbol = map_ticker_for_alpaca(ticker)
    try:
        orders = client.get_orders()
        canceled = 0
        found = 0
        for order in orders:
            if order.symbol == symbol and order.status in ("open", "new", "pending", "accepted"):
                found += 1
                try:
                    client.cancel_order_by_id(order.id)
                    st.info(f"🗑️ Order {order.id} voor {symbol} geannuleerd ({getattr(order,'type','')})")
                    canceled += 1
                except Exception as e:
                    st.warning(f"⚠️ Fout bij annuleren van order {order.id}: {e}")
        if found == 0:
            st.info(f"ℹ️ Geen open/pending orders gevonden voor {symbol}.")
        elif canceled == 0:
            st.warning(f"⚠️ Geen orders konden worden geannuleerd voor {symbol}.")
        else:
            st.success(f"✅ {canceled} order(s) geannuleerd voor {symbol}.")
        return canceled
    except Exception as e:
        st.error(f"❌ Fout bij ophalen of annuleren van orders: {e}")
        return 0

def sluit_positie(client, ticker, advies, force=False):
    symbol = map_ticker_for_alpaca(ticker)
    posities = client.get_all_positions()
    positie = None
    for pos in posities:
        if pos.symbol.upper() == symbol.upper():
            positie = pos
            break

    if positie is None:
        st.info(f"📭 Geen open positie gevonden in deze ticker ({symbol}).")
        return

    aantal = float(positie.qty)
    if aantal <= 0.0000001:
        st.info("ℹ️ Geen open positie om te sluiten.")
        return
    if not force and advies != "Verkopen":
        st.info("ℹ️ Huidig advies is geen 'Verkopen'. Geen actie ondernomen.")
        return

    aantal_geannuleerd = annuleer_alle_orders_ticker(client, symbol)
    if aantal_geannuleerd > 0:
        st.info("⏳ Wachten 5 seconden zodat de stukken vrijkomen...")
        time.sleep(5)

    # Afronden op 9 decimalen en als string
    aantal_afronden = round(aantal, 9)
    qty_value = str(aantal_afronden)
    order = MarketOrderRequest(
        symbol=symbol,
        qty=qty_value,
        side=OrderSide.SELL,
        time_in_force=TimeInForce.GTC
    )
    response = client.submit_order(order)
    st.success(f"✅ Verkooporder geplaatst voor {qty_value}x {symbol}")
    st.write(response)

def sluit_alles(client):
    st.warning("⚠️ Noodfunctie actief: alle posities en open orders worden nu gesloten/geannuleerd!")
    try:
        open_orders = client.get_orders()
        canceled = 0
        for order in open_orders:
            if order.status in ("open", "new", "pending", "accepted"):
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

        posities = client.get_all_positions()
        closed = 0
        for positie in posities:
            symbol = positie.symbol
            aantal = float(positie.qty)
            if aantal > 0:
                try:
                    order = MarketOrderRequest(
                        symbol=symbol,
                        qty=aantal,
                        side=OrderSide.SELL,
                        time_in_force=TimeInForce.GTC
                    )
                    response = client.submit_order(order)
                    st.success(f"✅ Market sell geplaatst voor {aantal}x {symbol}.")
                    closed += 1
                except Exception as e:
                    st.warning(f"⚠️ Fout bij sluiten van positie {symbol}: {e}")
        if closed == 0:
            st.info("ℹ️ Geen posities om te sluiten.")
        else:
            st.success(f"✅ {closed} positie(s) gesloten.")
    except Exception as e:
        st.error(f"❌ Fout bij 'sluit alles': {e}")

# ---------- TRADING BOT INTERFACE (UI) ------------

def toon_trading_bot_interface(ticker, huidig_advies):
    st.subheader("📥 Plaats live/paper trade op basis van advies")

    trade_mode = st.selectbox("🔀 Kies Alpaca account type:", ["Paper", "Live"], index=0)
    modus = st.radio("🎛️ Kies handelsmodus", ["Handmatig", "Automatisch", "Beide"], horizontal=True)

    client, account, api_key, secret_key = verbind_met_alpaca(trade_mode)
    if client is None:
        return

    # Live asset feedback (ticker mapping + Alpaca check)
    alpaca_ticker = map_ticker_for_alpaca(ticker)
    asset_info = check_alpaca_ticker(alpaca_ticker, api_key, secret_key)
    if asset_info is None:
        st.error(f"❌ Ticker '{alpaca_ticker}' niet gevonden bij Alpaca (alleen US stocks en grote crypto's zijn toegestaan)")
        return
    else:
        st.success(
            f"✅ {alpaca_ticker} ({asset_info['name']}, {asset_info['exchange']}) "
            f"— {'✔️' if asset_info['tradable'] else '❌'} tradable — "
            f"Prijs: {asset_info['price'] if asset_info['price'] else 'n.v.t.'}"
        )

    if account:
        st.success(f"✅ Verbonden met Alpaca-account ({account.status})")
        st.write(f"👤 Account-ID: {account.id}")
        st.write(f"💰 Beschikbaar cash: ${float(account.cash):,.2f}")
        st.write(f"📈 Portfolio waarde: ${float(account.portfolio_value):,.2f}")

    with st.expander(f"{'💵' if trade_mode=='Live' else '🧪'} Order plaatsen via Alpaca {trade_mode} Account"):
        last = haal_laatste_koers(ticker)
        if last:
            st.write(f"📉 Laatste koers voor {ticker}: **${last:.4f}**")
        else:
            st.warning("⚠️ Geen geldige koers beschikbaar voor dit aandeel/crypto.")
            return

        keuze_bedrag_of_aantal = st.radio("Wil je een bedrag of een exact aantal opgeven?", ["Bedrag", "Aantal"], horizontal=True)
        if keuze_bedrag_of_aantal == "Bedrag":
            bedrag = st.number_input("💰 Te investeren bedrag ($)", min_value=10.0, value=1000.0, step=10.0)
            aantal = None
        else:
            aantal = st.number_input(
                "Aantal stuks",
                min_value=0.000001,
                value=1.0,
                step=0.000001,
                format="%.6f"
            )
            bedrag = 0.0

        st.write(f"📌 Actueel advies voor {ticker}: **{huidig_advies}**")

        order_type = st.selectbox(
            "🛒 Kies ordertype",
            [
                "Market Buy",
                "Market Sell",
                "Limit Buy",
                "Limit Sell",
                "Trailing Stop Buy",
                "Trailing Stop Sell",
                "OTO: Market Buy + Trailing Stop Sell"
            ]
        )

        limietkoers = None
        trailing_pct = None

        if "Limit" in order_type:
            limietkoers = st.number_input("Limit order koers ($)", min_value=0.01, value=round(last, 2), step=0.01)

        if "Trailing Stop" in order_type or order_type == "OTO: Market Buy + Trailing Stop Sell":
            trailing_pct = st.slider("📉 Trailing stop (% vanaf hoogste/laagste koers)", 1.0, 20.0, 2.0)

        handmatig = modus in ["Handmatig", "Beide"]
        automatisch = modus in ["Automatisch", "Beide"]

        if handmatig and st.button("📤 Handmatig order plaatsen"):
            if order_type == "OTO: Market Buy + Trailing Stop Sell":
                koop_en_trailing_stop(client, ticker, bedrag if aantal is None else aantal * last, last, trailing_pct, aantal=aantal)
            else:
                plaats_order(client, ticker, bedrag, last, order_type, trailing_pct, aantal=aantal, limietkoers=limietkoers)

    st.markdown("---")

    # Verkooppositie 
    st.subheader("📤 Verkooppositie controleren en sluiten")
    with st.expander(f"{'💵' if trade_mode=='Live' else '🧪'} Positie check en verkoopactie"):
        posities = client.get_all_positions()
        symbol = map_ticker_for_alpaca(ticker)
        positie = None
        for pos in posities:
            if pos.symbol.upper() == symbol.upper():
                positie = pos
                break

        if positie is not None:
            huidige_qty = float(positie.qty)
            avg_price = float(positie.avg_entry_price)
            st.write(f"📦 Je bezit momenteel **{huidige_qty}x {positie.symbol}** @ ${avg_price:.2f} gemiddeld.")
        else:
            st.info(f"📭 Geen open positie gevonden in deze ticker ({symbol}).")
            st.write("📦 GEVONDEN POSITIES:", [p.symbol for p in posities])
            return

        st.write(f"📌 Huidig advies: **{huidig_advies}**")
        force_verkoop = st.checkbox("🔒 Forceer verkoop, ongeacht advies")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("❗ Verkooppositie sluiten"):
                sluit_positie(client, symbol, huidig_advies, force=force_verkoop)
        with col2:
            if st.button("🚨 Sluit ALLES direct (noodstop)"):
                sluit_alles(client)
