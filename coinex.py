import streamlit as st
import time
import hmac
import hashlib
import requests

BASE_URL = "https://socket.coinex.com/v2"  # /spot waarschijnlijk


def get_coinex_headers(api_key, api_secret, method, params):
    tonce = str(int(time.time() * 1000))
    params_str = "&".join(f"{k}={v}" for k, v in sorted(params.items()))
    signature = hmac.new(api_secret.encode(), (params_str).encode(), hashlib.sha256).hexdigest().upper()
    return {
        "Authorization": api_key,
        "Content-Type": "application/json",
        "X-CoinEx-Signature": signature,
        "X-CoinEx-Tonce": tonce
    }


def coinex_sign_request(path, api_key, api_secret, params=None):
    # CoinEx expects these headers for every signed API request:
    # 'authorization' (API Key), 'signature', 'tonce'
    if params is None:
        params = {}
    tonce = str(int(time.time() * 1000))
    # Sort params alphabetically
    sorted_params = "&".join([f"{k}={params[k]}" for k in sorted(params)]) if params else ""
    # Build signature string
    signature_str = f"{path}?{sorted_params}&access_id={api_key}&tonce={tonce}"
    signature = hashlib.sha256((signature_str + api_secret).encode()).hexdigest()
    headers = {
        "Authorization": api_key,
        "Content-Type": "application/json",
        "AccessId": api_key,
        "tonce": tonce,
        "signature": signature,
    }
    return headers, params
    

def coinex_request(path, api_key, api_secret, params=None):
    url = f"https://api.coinex.com/v1{path}"
    headers, data = coinex_sign_request(path, api_key, api_secret, params)
    try:
        # Probeer GET (zoals voor balances vereist)
        r = requests.get(url, headers=headers, params=data)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        st.error(f"CoinEx API error: {e}")
        st.code(r.text)  # Dit toont de volledige foutmelding uit de API response!
        return None
# Balances ophalen (alle coins)
def get_balances(api_key, api_secret):
    return coinex_request("/assets/spot", api_key, api_secret)

# Open orders ophalen voor een market (bv. BTCUSDT)
def get_open_orders(api_key, api_secret, market):
    return coinex_request("/order/pending", api_key, api_secret, params={"market": market})

# Orderhistorie ophalen voor een market
def get_order_history(api_key, api_secret, market, limit=10):
    return coinex_request("/order/finished", api_key, api_secret, params={"market": market, "limit": limit})

# Market order plaatsen (directe koop/verkoop)
def place_market_order(api_key, api_secret, market, side, amount):
    params = {
        "market": market,
        "side": side,
        "amount": str(amount),
        "type": "market"
    }
    return coinex_request("/order/put_market", api_key, api_secret, method="POST", params=params)

# Limit order plaatsen (koop/verkoop)
def place_limit_order(api_key, api_secret, market, side, amount, price):
    params = {
        "market": market,
        "side": side,
        "amount": str(amount),
        "price": str(price),
        "type": "limit"
    }
    return coinex_request("/order/put_limit", api_key, api_secret, method="POST", params=params)

# Order annuleren (order_id ophalen uit open orders)
def cancel_order(api_key, api_secret, market, order_id):
    params = {
        "market": market,
        "id": str(order_id)
    }
    return coinex_request("/order/cancel", api_key, api_secret, method="POST", params=params)

# Alle open orders voor een market annuleren
def cancel_all_orders(api_key, api_secret, market):
    open_orders = get_open_orders(api_key, api_secret, market)
    results = []
    if open_orders.get("data", {}).get("records"):
        for order in open_orders["data"]["records"]:
            result = cancel_order(api_key, api_secret, market, order["id"])
            results.append(result)
    return results
