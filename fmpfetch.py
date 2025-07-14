
import pandas as pd
import requests
import streamlit as st
import plotly.graph_objects as go
import pandas_market_calendars as mcal


fmp_api_key = st.secrets["FMP_API_KEY"]

@st.cache_data(ttl=3600)
def search_ticker(query, fmp_api_key):
    query = query.upper().strip()

    # Probeer eerst of het een geldige yfinance-ticker is
    try:
        info = yf.Ticker(query).info
        if info and "regularMarketPrice" in info:
            naam = info.get("shortName") or info.get("longName") or query
            return [(query, naam)]
    except Exception:
        pass  # yfinance gaf geen geldige data terug

    # Als fallback → FMP doorzoeken
    try:
        url = f"https://financialmodelingprep.com/api/v3/search?query={query}&limit=50&apikey={fmp_api_key}"
        response = requests.get(url)
        data = response.json()
        resultaten = [(item["symbol"], item.get("name", item["symbol"])) for item in data]
        return resultaten
    except Exception as e:
        st.error(f"Fout bij ophalen FMP-tickers: {e}")
        return []
        
# ✅ Tickerzoekfunctie met voorkeur voor NYSE/NASDAQ
def search_ticker_fmp(query):
    query = query.upper().strip()
    url = f"https://financialmodelingprep.com/api/v3/search?query={query}&limit=50&apikey={fmp_api_key}"
    try:
        response = requests.get(url)
        data = response.json()
        if not data:
            return []
        # Sorteer op beursvoorkeur (NYSE/NASDAQ eerst)
        def beurs_score(exchange):
            if exchange == "NASDAQ": return 0
            if exchange == "NYSE": return 1
            return 2
        data.sort(key=lambda x: beurs_score(x.get("exchangeShortName", "")))
        return [(item["symbol"], item.get("name", item["symbol"])) for item in data]
    except Exception as e:
        st.error(f"❌ Fout bij zoeken naar tickers: {e}")
        return []

# ✅ Ophalen historische koersdata
def fetch_data_fmp(ticker, periode="1y"):
    st.write(f"📡 Ophalen FMP-data voor: {ticker} ({periode})")
    url = f"https://financialmodelingprep.com/api/v3/historical-price-full/{ticker}?serietype=line&timeseries=1000&apikey={fmp_api_key}"
    try:
        response = requests.get(url)
        data = response.json()
        if "historical" not in data:
            st.warning("⚠️ Geen historische data gevonden")
            return pd.DataFrame()

        df = pd.DataFrame(data["historical"])
        df["date"] = pd.to_datetime(df["date"])
        df.set_index("date", inplace=True)
        df.sort_index(inplace=True)

        st.write("📊 Rijen vóór filtering:", len(df))

        # 📅 Weekdagenfilter (ma-vr)
        df = df[df.index.dayofweek < 5]

        # 📆 Beursdagenfilter
        if not ticker.upper().endswith("-USD"):
            try:
                is_europe = any(exchange in ticker.upper() for exchange in [".AS", ".BR", ".PA", ".DE"])
                cal = mcal.get_calendar("XAMS") if is_europe else mcal.get_calendar("NYSE")
                start_date = df.index.min().date()
                end_date = df.index.max().date()
                schedule = cal.schedule(start_date=start_date, end_date=end_date)
                valid_days = set(schedule.index.normalize())
                df = df[df.index.normalize().isin(valid_days)]
                st.write("✅ Na filtering:", len(df))
            except Exception as e:
                st.error(f"❌ Kalenderfout: {e}")
        else:
            st.write("🪙 Crypto: geen beursdagenfilter toegepast")

        # ➕ Extra kolommen
        df = df.rename(columns={"close": "Close"})
        df["Open"] = df["Close"]
        df["High"] = df["Close"]
        df["Low"] = df["Close"]

        # 📉 Indicatoren
        df["MA35"] = df["Close"].rolling(window=35, min_periods=1).mean()
        df["MA50"] = df["Close"].rolling(window=50, min_periods=1).mean()
        df["MA150"] = df["Close"].rolling(window=150, min_periods=1).mean()
        df["BB_middle"] = df["Close"].rolling(window=20, min_periods=1).mean()
        df["BB_std"] = df["Close"].rolling(window=20, min_periods=1).std()
        df["BB_upper"] = df["BB_middle"] + 2 * df["BB_std"]
        df["BB_lower"] = df["BB_middle"] - 2 * df["BB_std"]

        st.write("📉 Laatste datum:", df.index[-1])
        return df
    except Exception as e:
        st.error(f"❌ Fout bij ophalen FMP-data: {e}")
        return pd.DataFrame()

