




@st.cache_data(ttl=900)
def fetch_data_cached(ticker, interval, period):
    return yf.download(ticker, interval=interval, period=period)

# ✅ Weighted Moving Average functie
#def weighted_moving_average(series, window):
#    weights = np.arange(1, window + 1)
#    return series.rolling(window).apply(lambda x: np.dot(x, weights) / weights.sum(), raw=True)

# ✅ Wrapper-functie met dataschoonmaak en fallback
def fetch_data(ticker, interval):
    # 🔁 Interval naar periode
    if interval == "15m":
        period = "30d"
    elif interval == "1h":
        period = "720d"
    elif interval == "4h":
        period = "360d"
    elif interval == "1d":
        period = "20y"
    elif interval == "1wk":
        period = "20y"
    elif interval == "1mo":
        period = "25y"
    else:
        period = "25y"  # fallback

    # ⬇️ Ophalen via gecachete functie
    df = fetch_data_cached(ticker, interval, period)

    # 🛡️ Check op geldige data
    if df.empty or "Close" not in df.columns or "Open" not in df.columns:
        return pd.DataFrame()

    # 🧹 Verwijder irrelevante of foutieve rijen
    df = df[
        (df["Volume"] > 0) &
        ((df["Open"] != df["Close"]) | (df["High"] != df["Low"]))
    ]

    # 🕓 Zorg dat index datetime is
    if not isinstance(df.index, pd.DatetimeIndex):
        df.index = pd.to_datetime(df.index, errors="coerce")
    df = df[~df.index.isna()]

    # 🔁 Vul NaN's per kolom
    for col in ["Close", "Open", "High", "Low", "Volume"]:
        df[col] = df[col].fillna(method="ffill").fillna(method="bfill")

    # 🧪 Check minimale lengte
    if len(df) < 30:
        st.warning(f"⚠️ Slechts {len(df)} datapunten opgehaald — mogelijk te weinig voor indicatoren.")
        return pd.DataFrame()

    return df
    
