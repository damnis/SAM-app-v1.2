# bot.py
import yfinance as yf
import streamlit as st
from alpaca.trading.client import TradingClient
from alpaca.trading.enums import OrderSide, TimeInForce
from alpaca.trading.requests import MarketOrderRequest, TrailingStopOrderRequest

def verbind_met_alpaca():
    try:
        api_key = st.secrets["ALPACA_API_KEY"]
        secret_key = st.secrets["ALPACA_SECRET_KEY"]
        client = TradingClient(api_key, secret_key, paper=True)
        account = client.get_account()
        return client, account
    except Exception as e:
        st.error(f"❌ Fout bij verbinden met Alpaca: {e}")
        return None, None

def haal_laatste_koers(ticker):
    try:
        live_data = yf.download(ticker, period="1d", interval="1d", progress=False)
        if isinstance(live_data, yf.pd.DataFrame) and "Close" in live_data.columns:
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

def sluit_positie(client, ticker, advies):
    try:
        positie = client.get_open_position(ticker)
        aantal = int(float(positie.qty))
        if advies != "Verkopen":
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
