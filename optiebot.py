import streamlit as st
from alpaca.trading.client import TradingClient
from alpaca.trading.enums import OrderSide, TimeInForce
from alpaca.trading.requests import OptionOrderRequest

def verbind_met_alpaca(mode):
    sectie = "alpaca_paper" if mode == "Paper" else "alpaca_live"
    api_key = st.secrets[sectie]["ALPACA_API_KEY"]
    secret_key = st.secrets[sectie]["ALPACA_SECRET_KEY"]
    client = TradingClient(api_key, secret_key, paper=(mode == "Paper"))
    account = client.get_account()
    return client, account

def plaats_optie_order(client, onderliggende, expiry, strike, optietype, side, qty, order_type="market", price=None):
    try:
        # Belangrijk: OptionOrderRequest kan per Alpaca-versie wijzigen. Check docu bij errors!
        order = OptionOrderRequest(
            symbol=onderliggende,
            qty=qty,
            side=OrderSide.BUY if side == "Long (Buy)" else OrderSide.SELL,
            type=order_type,
            option_type=optietype,  # "call" of "put"
            strike=str(strike),
            expiry=expiry,
            time_in_force=TimeInForce.GTC,
            limit_price=price,
        )
        response = client.submit_order(order)
        st.success(f"✅ Optie-order geplaatst: {side} {qty}x {onderliggende} {optietype.upper()} {strike} {expiry}")
        st.write(response)
    except Exception as e:
        st.error(f"❌ Fout bij optie-order: {e}")

def toon_optie_trading_bot_interface():
    st.header("🎯 Alpaca Optie Trading Bot")

    mode = st.selectbox("Kies Alpaca-account:", ["Paper", "Live"], index=0)
    client, account = verbind_met_alpaca(mode)
    if not client:
        return

    if account:
        st.success(f"Verbonden met Alpaca {mode} account ({account.status})")
        st.write(f"Beschikbaar cash: ${float(account.cash):,.2f}")
        st.write(f"Portfolio waarde: ${float(account.portfolio_value):,.2f}")

    st.markdown("---")

    # Optie parameters
    st.subheader("📑 Optiecontract invoeren")

    onderliggende = st.text_input("Onderliggende waarde (ticker)", value="AAPL")
    expiry = st.text_input("Expiratiedatum (YYYY-MM-DD)", value="2024-08-16")
    strike = st.number_input("Strike prijs", min_value=0.0, value=200.0)
    optietype = st.selectbox("Type optie", ["call", "put"])
    side = st.selectbox("Long/Short", ["Long (Buy)", "Short (Sell)"])
    qty = st.number_input("Aantal contracten", min_value=1, value=1)
    order_type = st.selectbox("Order type", ["market", "limit"])
    price = None
    if order_type == "limit":
        price = st.number_input("Limietprijs per contract ($)", min_value=0.01, value=1.00, step=0.01)

    if st.button("📤 Plaats optie-order"):
        plaats_optie_order(
            client=client,
            onderliggende=onderliggende,
            expiry=expiry,
            strike=strike,
            optietype=optietype,
            side=side,
            qty=qty,
            order_type=order_type,
            price=price
        )

    st.markdown("---")

    # Open opties tonen (optioneel)
    st.subheader("📂 Open Optieposities")
    if st.button("🔍 Toon open opties"):
        try:
            posities = client.get_all_positions()
            opties = [p for p in posities if hasattr(p, "asset_class") and p.asset_class == "option"]
            if opties:
                for optie in opties:
                    st.write(f"{optie.symbol}: {optie.qty} @ ${optie.avg_entry_price}")
            else:
                st.info("Geen open optieposities gevonden.")
        except Exception as e:
            st.error(f"❌ Fout bij ophalen posities: {e}")

    st.markdown("---")

    st.info("ℹ️ **Let op:** Opties trading kan per account/land beperkt zijn. Paper trading werkt meestal altijd.")

# Voor standalone testen: 
if __name__ == "__main__":
    toon_optie_trading_bot_interface()
