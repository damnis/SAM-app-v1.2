
import pandas as pd
import requests
import streamlit as st
import plotly.graph_objects as go
import pandas_market_calendars as mcal

FMP_API_KEY = "D2MyI4eYNXDNJzpYT4N6nTQ2amVbJaG5"

# ✅ Tickerzoekfunctie met voorkeur voor NYSE/NASDAQ
def search_ticker_fmp(query):
    query = query.upper().strip()
    url = f"https://financialmodelingprep.com/api/v3/search?query={query}&limit=50&apikey={FMP_API_KEY}"
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
    url = f"https://financialmodelingprep.com/api/v3/historical-price-full/{ticker}?serietype=line&timeseries=1000&apikey={FMP_API_KEY}"
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

# ✅ Candlestick-grafiek
def draw_custom_candlestick_chart(df, ticker="", selected_lines=[]):
    fig = go.Figure()

    for i in range(len(df)):
        kleur = "green" if df["Close"][i] > df["Open"][i] else "red"
        fig.add_trace(go.Scatter(
            x=[df.index[i], df.index[i]],
            y=[df["Low"][i], df["High"][i]],
            mode="lines",
            line=dict(color=kleur, width=1),
            showlegend=False,
            hoverinfo='skip'
        ))

        fig.add_trace(go.Scatter(
            x=[df.index[i], df.index[i]],
            y=[df["Open"][i], df["Close"][i]],
            mode="lines",
            line=dict(color=kleur, width=3),
            showlegend=False,
            hoverinfo="text",
            text=f"Open: {df['Open'][i]:.2f}<br>Close: {df['Close'][i]:.2f}"
        ))

    if not df.empty:
        if "MA35" in selected_lines:
            fig.add_trace(go.Scatter(x=df.index, y=df["MA35"], mode="lines", name="MA 35"))
        if "MA50" in selected_lines:
            fig.add_trace(go.Scatter(x=df.index, y=df["MA50"], mode="lines", name="MA 50"))
        if "MA150" in selected_lines:
            fig.add_trace(go.Scatter(x=df.index, y=df["MA150"], mode="lines", name="MA 150"))
        if "Bollinger Bands" in selected_lines:
            fig.add_trace(go.Scatter(x=df.index, y=df["BB_upper"], mode="lines", name="BB Upper", line=dict(dash="dot")))
            fig.add_trace(go.Scatter(x=df.index, y=df["BB_lower"], mode="lines", name="BB Lower", line=dict(dash="dot")))

    fig.update_layout(
        title=f"📊 Aangepaste Candlestick-grafiek: {ticker}",
        xaxis_title="Datum",
        yaxis_title="Prijs",
        xaxis_rangeslider_visible=False,
        template="plotly_white",
        height=600,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5)
    )

    return fig
