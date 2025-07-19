import streamlit as st
import time
import hmac
import hashlib
import requests
import json

# BASE_URL = "https://api.coinex.com/v2"



BASE_URL = "https://api.coinex.com"

def _coinex_signature(method, path, body_str, timestamp, api_secret):
    """Maakt CoinEx signature string volgens v2 docs."""
    prestr = method + path + body_str + timestamp
    signature = hmac.new(
        api_secret.encode("utf-8"),
        prestr.encode("utf-8"),
        hashlib.sha256
    ).hexdigest().lower()
    return signature

def _coinex_headers(api_key, api_secret, method, path, body_str=""):
    timestamp = str(int(time.time() * 1000))
    signature = _coinex_signature(method, path, body_str, timestamp, api_secret)
    headers = {
        "X-COINEX-APIKEY": api_key,
        "X-COINEX-TIMESTAMP": timestamp,
        "X-COINEX-SIGNATURE": signature,
        "Content-Type": "application/json"
    }
    return headers, timestamp

# --- BALANCES (GET) ---
def get_balances(api_key, api_secret):
    method = "GET"
    path = "/v2/assets/balance"
    headers, _ = _coinex_headers(api_key, api_secret, method, path)
    r = requests.get(BASE_URL + path, headers=headers)
    r.raise_for_status()
    return r.json()

# --- OPEN ORDERS (GET) ---
def get_open_orders(api_key, api_secret, market, limit=50):
    method = "GET"
    path = f"/v2/spot/pending-order?market={market}&limit={limit}"
    headers, _ = _coinex_headers(api_key, api_secret, method, path)
    r = requests.get(BASE_URL + path, headers=headers)
    r.raise_for_status()
    return r.json()

# --- MARKET ORDER (POST) ---
def place_market_order(api_key, api_secret, market, side, amount):
    method = "POST"
    path = "/v2/order/market"
    body = {"market": market, "side": side, "amount": str(amount)}
    body_str = json.dumps(body, separators=(",", ":"))
    headers, _ = _coinex_headers(api_key, api_secret, method, path, body_str)
    r = requests.post(BASE_URL + path, headers=headers, data=body_str)
    r.raise_for_status()
    return r.json()

# --- LIMIT ORDER (POST) ---
def place_limit_order(api_key, api_secret, market, side, amount, price):
    method = "POST"
    path = "/v2/order/limit"
    body = {"market": market, "side": side, "amount": str(amount), "price": str(price)}
    body_str = json.dumps(body, separators=(",", ":"))
    headers, _ = _coinex_headers(api_key, api_secret, method, path, body_str)
    r = requests.post(BASE_URL + path, headers=headers, data=body_str)
    r.raise_for_status()
    return r.json()

# --- CANCEL ORDER (POST) ---
def cancel_order(api_key, api_secret, market, order_id):
    method = "POST"
    path = "/v2/order/cancel"
    body = {"market": market, "id": str(order_id)}
    body_str = json.dumps(body, separators=(",", ":"))
    headers, _ = _coinex_headers(api_key, api_secret, method, path, body_str)
    r = requests.post(BASE_URL + path, headers=headers, data=body_str)
    r.raise_for_status()
    return r.json()

# --- ORDER HISTORY (GET) ---
def get_order_history(api_key, api_secret, market, limit=50):
    method = "GET"
    path = f"/v2/order/finished?market={market}&limit={limit}"
    headers, _ = _coinex_headers(api_key, api_secret, method, path)
    r = requests.get(BASE_URL + path, headers=headers)
    r.raise_for_status()
    return r.json()

# --- Cancel ALL open orders for a market (convenience) ---
def cancel_all_orders(api_key, api_secret, market):
    open_orders = get_open_orders(api_key, api_secret, market)
    results = []
    for order in open_orders.get("data", {}).get("records", []):
        result = cancel_order(api_key, api_secret, market, order["id"])
        results.append(result)
    return results














# w
