import streamlit as st
import time
import hmac
import hashlib
import requests
import json

BASE_URL = "https://api.coinex.com/v2"

def coinex_sign_request(path, api_key, api_secret, params=None, method="GET"):
    # Altijd tonce als int (string is ok, CoinEx v2 expects it)
    tonce = str(int(time.time() * 1000))
    if params is None:
        params = {}
    params_str = "&".join([f"{k}={params[k]}" for k in sorted(params)]) if params else ""
    if params_str:
        sign_string = f"{path}?{params_str}&access_id={api_key}&tonce={tonce}"
    else:
        sign_string = f"{path}?access_id={api_key}&tonce={tonce}"
    signature = hashlib.sha256((sign_string + api_secret).encode()).hexdigest()
    headers = {
        "Authorization": api_key,
        "Content-Type": "application/json",
        "AccessId": api_key,
        "tonce": tonce,
        "signature": signature,
    }
    return headers, params

def coinex_request(path, api_key, api_secret, params=None, method="GET"):
    url = BASE_URL + path
    headers, req_params = coinex_sign_request(path, api_key, api_secret, params, method=method)
    try:
        if method == "GET":
            r = requests.get(url, headers=headers, params=req_params)
        else:  # POST
            r = requests.post(url, headers=headers, data=json.dumps(req_params))
        r.raise_for_status()
        data = r.json()
        if data.get("code") != 0:
            st.error(f"CoinEx API ERROR: {data.get('message','(geen error msg)')}")
            st.code(json.dumps(data, indent=2))
            return None
        return data
    except Exception as e:
        st.error(f"CoinEx API error: {e}")
        try:
            st.code(r.text)
        except:
            pass
        return None

# --- API functies ---
def get_balances(api_key, api_secret):
    return coinex_request("/assets/balance", api_key, api_secret, method="GET")

def get_open_orders(api_key, api_secret, market):
    return coinex_request("/order/pending", api_key, api_secret, params={"market": market}, method="GET")

def get_order_history(api_key, api_secret, market, limit=10):
    return coinex_request("/order/finished", api_key, api_secret, params={"market": market, "limit": limit}, method="GET")

def place_market_order(api_key, api_secret, market, side, amount):
    params = {
        "market": market,
        "side": side,
        "amount": str(amount),
        "type": "market"
    }
    return coinex_request("/order/put_market", api_key, api_secret, params=params, method="POST")

def place_limit_order(api_key, api_secret, market, side, amount, price):
    params = {
        "market": market,
        "side": side,
        "amount": str(amount),
        "price": str(price),
        "type": "limit"
    }
    return coinex_request("/order/put_limit", api_key, api_secret, params=params, method="POST")

def cancel_order(api_key, api_secret, market, order_id):
    params = {
        "market": market,
        "id": str(order_id)
    }
    return coinex_request("/order/cancel", api_key, api_secret, params=params, method="POST")

def cancel_all_orders(api_key, api_secret, market):
    open_orders = get_open_orders(api_key, api_secret, market)
    results = []
    if open_orders and open_orders.get("data", {}).get("records"):
        for order in open_orders["data"]["records"]:
            result = cancel_order(api_key, api_secret, market, order["id"])
            results.append(result)
    return results
















# w
