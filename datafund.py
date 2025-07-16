import requests
import streamlit as st
import yfinance as yf


API_KEY = st.secrets["FMP_API_KEY"]

BASE_URL = "https://financialmodelingprep.com/api/v3"

@st.cache_data(ttl=3600)
def get_income_statement(ticker, years=20):
    url = f"{BASE_URL}/income-statement/{ticker}?limit={years}&apikey={API_KEY}"
    try:
        response = requests.get(url)
        return response.json()
    except:
        return []

@st.cache_data(ttl=3600)
def get_ratios(ticker, years=5):
    url = f"{BASE_URL}/ratios/{ticker}?limit={years}&apikey={API_KEY}"
    try:
        response = requests.get(url)
        return response.json()
    except:
        return []

@st.cache_data(ttl=3600)
def get_profile(ticker):
    url = f"{BASE_URL}/profile/{ticker}?apikey={API_KEY}"
    try:
        data = requests.get(url).json()
        return data[0] if data else None
    except:
        return None

@st.cache_data(ttl=3600)
def get_key_metrics(ticker, years=20):
    url = f"{BASE_URL}/key-metrics/{ticker}?limit={years}&apikey={API_KEY}"
    try:
        data = requests.get(url).json()
        return data if isinstance(data, list) else []
    except:
        return []
        
@st.cache_data(ttl=3600)
def get_earning_calendar(ticker):
    url = f"{BASE_URL}/earning_calendar/{ticker}?limit=10&apikey={API_KEY}"
    try:
        return requests.get(url).json()
    except:
        return []

@st.cache_data(ttl=3600)
def get_dividend_history(ticker):
    url = f"{BASE_URL}/historical-price-full/stock_dividend/{ticker}?apikey={API_KEY}"
    try:
        return requests.get(url).json().get("historical", [])
    except:
        return []

@st.cache_data(ttl=3600)
def get_quarterly_eps(ticker):
    url = f"{BASE_URL}/income-statement/{ticker}?period=quarter&limit=20&apikey={API_KEY}"
    try:
        return requests.get(url).json()
    except:
        return []

def get_news_fmp(ticker):
    url = f"{BASE_URL}/stock_news/{ticker}?limit=10&apikey={API_KEY}"
    try:
        return requests.get(url).json()
    except:
        return None

@st.cache_data(ttl=900)
def get_news_yahoo(ticker, limit=10):
    try:
        stock = yf.Ticker(ticker)
        news = stock.news
        if news:
            return news[:limit]
        return []
    except Exception:
        return []


@st.cache_data(ttl=3600)
def get_eps_forecast(ticker):
    url = f"{BASE_URL}/analyst-estimates/{ticker}?limit=5&apikey={API_KEY}"
    try:
        return requests.get(url).json()
    except:
        return []





























# w
