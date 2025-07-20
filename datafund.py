import requests
import streamlit as st
import yfinance as yf
from finvizfinance.news import News

API_KEY = st.secrets["FMP_API_KEY"]

BASE_URL = "https://financialmodelingprep.com/api/v3"


# income statement - annual 
@st.cache_data(ttl=3600)
def get_income_statement(ticker, years=20):
    url = f"{BASE_URL}/income-statement/{ticker}?limit={years}&apikey={API_KEY}"
    try:
        response = requests.get(url)
        return response.json()
    except:
        return []

# Ratio's- annual 
@st.cache_data(ttl=3600)
def get_ratios(ticker, years=5):
    url = f"{BASE_URL}/ratios/{ticker}?limit={years}&apikey={API_KEY}"
    try:
        response = requests.get(url)
        return response.json()
    except:
        return []

# company profile 
@st.cache_data(ttl=3600)
def get_profile(ticker):
    url = f"{BASE_URL}/profile/{ticker}?apikey={API_KEY}"
    try:
        data = requests.get(url).json()
        return data[0] if data else None
    except:
        return None

# key metrics  - annual 
@st.cache_data(ttl=3600)
def get_key_metrics(ticker, years=20):
    url = f"{BASE_URL}/key-metrics/{ticker}?limit={years}&apikey={API_KEY}"
    try:
        data = requests.get(url).json()
        return data if isinstance(data, list) else []
    except:
        return []

# earnings calendar - does nothing? 
@st.cache_data(ttl=3600)
def get_earning_calendar(ticker):
    url = f"{BASE_URL}/earning_calendar/{ticker}?limit=10&apikey={API_KEY}"
    try:
        return requests.get(url).json()
    except:
        return []

# dividend calendar 
@st.cache_data(ttl=3600)
def get_dividend_history(ticker):
    url = f"{BASE_URL}/historical-price-full/stock_dividend/{ticker}?apikey={API_KEY}"
    try:
        return requests.get(url).json().get("historical", [])
    except:
        return []

# income statement- quarterly 
@st.cache_data(ttl=3600)
def get_quarterly_eps(ticker):
    url = f"{BASE_URL}/income-statement/{ticker}?period=quarter&limit=20&apikey={API_KEY}"
    try:
        return requests.get(url).json()
    except:
        return []


# analyst-estimates- quarterly 
@st.cache_data(ttl=3600)
def get_eps_forecast(ticker):
    url = f"{BASE_URL}/analyst-estimates/{ticker}?period=quarter&limit=20&apikey={API_KEY}"
    try:
        return requests.get(url).json()
    except:
        return []

# Koersdata per jaar (high, low, close etc.)
#@st.cache_data(ttl=3600)
#def get_historical_prices_yearly(ticker, years=20):
#    url = f"{BASE_URL}/historical-price-full/{ticker}?serietype=year&apikey={API_KEY}"
#    try:
#        data = requests.get(url).json()
        # De koersdata zit onder 'historical' als lijst
#        return data.get("historical", [])[:years]
#    except:
#        return []

# Koersdata per jaar (high, low, close etc.)
@st.cache_data(ttl=3600)
def get_historical_prices_yearly(ticker, years=20):
    url = f"{BASE_URL}/historical-price-eod/{ticker}?serietype=year&apikey={API_KEY}"
    try:
        data = requests.get(url).json()
        # De koersdata zit onder 'historical' als lijst
        return data.get("historical", [])[:years]
    except:
        return []
#https://financialmodelingprep.com/stable/historical-price-eod/full?symbol=AAPL&apikey=D2MyI4eYNXDNJzpYT4N6nTQ2amVbJaG5
# DCF-data (historisch, meestal jaarlijks, soms kwartaal)
#@st.cache_data(ttl=3600)
#def get_historical_dcf(ticker, years=20):
#    url = f"{BASE_URL}/historical-discounted-cash-flow-statement/{ticker}?limit={years}&apikey={API_KEY}"
#    try:
#        return requests.get(url).json()[:years]
#    except:
 #       return []



# DCF-data (historisch, meestal jaarlijks, soms kwartaal)
@st.cache_data(ttl=3600)
def get_historical_dcf(ticker, years=20):
    url = f"{BASE_URL}/discounted-cash-flow/{ticker}?limit={years}&apikey={API_KEY}"
    try:
        return requests.get(url).json()[:years]
    except:
        return []



# est eps https://financialmodelingprep.com/api/v3/analyst-estimates/AAPL?apikey=
# aanbevelingen er zijn meerdere https://financialmodelingprep.com/api/v3/analyst-stock-recommendations/AAPL?apikey=
# balans score https://financialmodelingprep.com/api/v4/score?symbol=AAPL&apikey=
# dcf https://financialmodelingprep.com/api/v3/discounted-cash-flow/AAPL?apikey=
# dcf stable https://financialmodelingprep.com/stable/discounted-cash-flow?symbol=AAPL&apikey=

# new real https://financialmodelingprep.com/api/v3/fmp/articles?page=0&size=5&apikey=.....
# news ticker https://financialmodelingprep.com/api/v3/press-releases/AAPL?apikey=
# stocks news https://financialmodelingprep.com/api/v3/stock_news?tickers=AAPL,FB&page=3&from=2024-01-01&to=2024-03-01&apikey=
# crypto news https://financialmodelingprep.com/api/v4/crypto_news?page=0&apikey=
# press https://financialmodelingprep.com/api/v3/press-releases?page=0&apikey=
# press ticker https://financialmodelingprep.com/api/v3/press-releases/AAPL?apikey=




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



@st.cache_data(ttl=600)
def get_news_finviz(view="STOCKS_NEWS"):
    """
    Haal nieuws op van Finviz.
    view: STOCKS_NEWS / MARKET_NEWS / ETF_NEWS
    """
    try:
        fnews = News(view_option=view)
        df = fnews.get_news()
        # blijf bij hoofdkolommen
        items = df.to_dict("records") if not df.empty else []
        return items
    except Exception:
        return []

























# w
