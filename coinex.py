import time
import hmac
import hashlib
import json
import requests
from urllib.parse import urlparse, urlencode

BASE_URL = "https://api.coinex.com/v2"

def gen_sign(method, request_path, body, timestamp, api_secret):
    """Genereer CoinEx signature-string volgens docs"""
    prepared_str = f"{method}{request_path}{body}{timestamp}"
    signature = hmac.new(
        bytes(api_secret, 'latin-1'),
        msg=bytes(prepared_str, 'latin-1'),
        digestmod=hashlib.sha256
    ).hexdigest().lower()
    return signature

def coinex_request(method, endpoint, api_key, api_secret, params=None, data=None):
    url = f"{BASE_URL}{endpoint}"
    if params is None: params = {}
    if data is None: data = ""
    else: data = json.dumps(data)

    req = urlparse(url)
    request_path = req.path

    timestamp = str(int(time.time() * 1000))
    query_str = ""
    # GET: query params in path + signature
    if method.upper() == "GET" and params:
        query_str = "?" + urlencode({k: v for k, v in params.items() if v is not None})
        request_path += query_str
    # POST: nothing in path, only body is signed

    sign = gen_sign(method.upper(), request_path, body=(data if method.upper()=="POST" else ""), timestamp=timestamp, api_secret=api_secret)
    headers = {
        "Content-Type": "application/json; charset=utf-8",
        "Accept": "application/json",
        "X-COINEX-KEY": api_key,
        "X-COINEX-SIGN": sign,
        "X-COINEX-TIMESTAMP": timestamp,
    }
    # API call
    if method.upper() == "GET":
        resp = requests.get(url + query_str, headers=headers, params=None)
    else:
        resp = requests.post(url, headers=headers, data=data)
    try:
        resp.raise_for_status()
    except Exception as e:
        # API fout/debug info
        print(f"CoinEx API error: {e}")
        print(resp.text)
        return None
    return resp.json()

# ✅ Easy-use wrappers:

def get_spot_balance(api_key, api_secret):
    """Spot balances voor alle coins"""
    return coinex_request("GET", "/assets/spot/balance", api_key, api_secret)

def get_spot_market(api_key, api_secret, market="BTCUSDT"):
    return coinex_request("GET", "/spot/market", api_key, api_secret, params={"market": market})

def put_limit_order(api_key, api_secret, market, side, amount, price, client_id=None, is_hide=False):
    data = {
        "market": market,
        "market_type": "SPOT",
        "side": side,
        "type": "limit",
        "amount": str(amount),
        "price": str(price),
        "is_hide": is_hide,
    }
    if client_id:
        data["client_id"] = client_id
    return coinex_request("POST", "/spot/order", api_key, api_secret, data=data)

def put_market_order(api_key, api_secret, market, side, amount, client_id=None):
    data = {
        "market": market,
        "market_type": "SPOT",
        "side": side,
        "type": "market",
        "amount": str(amount)
    }
    if client_id:
        data["client_id"] = client_id
    return coinex_request("POST", "/spot/order", api_key, api_secret, data=data)





















# w
