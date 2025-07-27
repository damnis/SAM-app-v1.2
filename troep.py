
# oudere
# 📌 Twee knoppen in kolommen
col1, col2 = st.columns(2)
zoek_stijgers = col1.button("🔎 Zoek stijgers met koop advies")
zoek_hoog_volume = col2.button("🔎 Zoek hoog volume met koop advies")

def get_analyst_rec_batch(tickers):
    @st.cache_data(ttl=3600)
    def get_latest_analyst_rec(ticker):
        data = get_analyst_recommendations(ticker)
        if data:
            last = data[0]
            return {
                "Markt advies": last.get("date", None),
                "Buy": last.get("analystRatingsbuy", 0) + last.get("analystRatingsStrongBuy", 0),
                "Hold": last.get("analystRatingsHold", 0),
                "Sell": last.get("analystRatingsSell", 0) + last.get("analystRatingsStrongSell", 0),
            }
        else:
            return {"Buy": None, "Hold": None, "Sell": None}
    analyst_data = []
    for ticker in tickers:
        row = {"Ticker": ticker}
        row.update(get_latest_analyst_rec(ticker))
        analyst_data.append(row)
    return pd.DataFrame(analyst_data)

# 📊 Toon resultaten onder de knoppen, over volledige breedte
if zoek_stijgers:
    screeneresult = screen_tickers(tickers_screening, min_momentum=6)
    if not screeneresult.empty:
        st.markdown("### 💡 SAT + SAM Advies en Marktadvies (analisten): (Koers-momentum)")
        df_analyst = get_analyst_rec_batch(list(screeneresult["Ticker"]))
        result = screeneresult.merge(df_analyst, on="Ticker", how="left")
        st.dataframe(result)

if zoek_hoog_volume:
    screeneresult = screen_tickers_vol(tickers_screening, min_momentum=30)
    if not screeneresult.empty:
        st.markdown("### 💡 SAT + SAM Advies en Marktadvies (analisten): (Volume-momentum)")
        df_analyst = get_analyst_rec_batch(list(screeneresult["Ticker"]))
        result = screeneresult.merge(df_analyst, on="Ticker", how="left")
        st.dataframe(result)






# -------------------




#    for i in range(2, len(df)):
#            sam_1 = df["SAM"].iloc[i]
#            trends_1 = df["Trend"].iloc[i]
#            trends_2 = df["Trend"].iloc[i - 1]
#            trend_1 = df["SAT_Trend"].iloc[i]
#            trend_2 = df["SAT_Trend"].iloc[i - 1]
#            trend_3 = df["SAT_Trend"].iloc[i - 2]
#            stage_1 = df["SAT_Stage"].iloc[i]
#            stage_2 = df["SAT_Stage"].iloc[i - 1]
#            stage_3 = df["SAT_Stage"].iloc[i - 2]

#            if trend_1 >= trend_2 and trend_2 >= trend_3 and stage_1 > 0 or (trends_1 - trends_2 >= 0) and sam_1 >= 0:
#                df.at[df.index[i], "Advies"] = "Kopen"
 #           elif trend_1 < trend_2 and stage_1 < 0 and stage_2 < 0: # optie and trend_2 < trend_3 
 #               df.at[df.index[i], "Advies"] = "Verkopen"

#        df["Advies"] = df["Advies"].ffill()

    
#    elif risk_aversion == 2:
#        for i in range(2, len(df)):
#            trend_1 = df["SAT_Trend"].iloc[i]
#            trend_2 = df["SAT_Trend"].iloc[i - 1]
 #           trend_3 = df["SAT_Trend"].iloc[i - 2]
#            stage_1 = df["SAT_Stage"].iloc[i]
 #           stage_2 = df["SAT_Stage"].iloc[i - 1]
 #           stage_3 = df["SAT_Stage"].iloc[i - 2]

#            if trend_1 >= trend_2 and trend_2 >= trend_3 and stage_1 > 0 and stage_2 > 0:
#                df.at[df.index[i], "Advies"] = "Kopen"
 #           elif trend_1 < trend_2 and stage_1 < 0: # optie and trend_2 < trend_3 
  #              df.at[df.index[i], "Advies"] = "Verkopen"

#        df["Advies"] = df["Advies"].ffill()

#    elif risk_aversion == 3:
#        for i in range(2, len(df)):
#            trend_1 = df["SAT_Trend"].iloc[i]
 #           trend_2 = df["SAT_Trend"].iloc[i - 1]
#            trend_3 = df["SAT_Trend"].iloc[i - 2]
#            stage_1 = df["SAT_Stage"].iloc[i]
#            stage_2 = df["SAT_Stage"].iloc[i - 1]
 #           stage_3 = df["SAT_Stage"].iloc[i - 2]
            
  #          if trend_1 > 0 and stage_1 > 0:
  #              df.at[df.index[i], "Advies"] = "Kopen"
  #          elif trend_1 < trend_2 and stage_1 < 0 and stage_2 < 0:
  #              df.at[df.index[i], "Advies"] = "Verkopen"

  #      df["Advies"] = df["Advies"].ffill()








--- Koersgrafiek ---
def plot_koersgrafiek(df, ticker_name, interval):
    toon_koersgrafiek = st.toggle("📈 Toon koersgrafiek", value=False)
    if not toon_koersgrafiek:
        return

    grafiek_periode = bepaal_grafiekperiode(interval)
    cutoff_datum = df.index.max() - grafiek_periode
    df_koers = df[df.index >= cutoff_datum].copy().reset_index()

    # Zorg dat MA's bestaan
    if "MA30" not in df.columns or "MA150" not in df.columns:
        df["MA30"] = df["Close"].rolling(window=30).mean()
        df["MA150"] = df["Close"].rolling(window=150).mean()

    df_koers["x"] = range(len(df_koers))
    datumkolom = df_koers.columns[0]  # meestal 'Date' of 'index'

    fig, ax = plt.subplots(figsize=(14, 6))  # zelfde formaat als SAM/SAT

    # Koers en MA-lijnen plotten
    ax.plot(df_koers["x"], df_koers["Close"], color="black", linewidth=2.0, label="Koers")
    ax.plot(df_koers["x"], df_koers["MA30"], color="orange", linewidth=1.0, label="MA(30)")
    ax.plot(df_koers["x"], df_koers["MA150"], color="pink", linewidth=1.0, label="MA(150)")

    # X-as labels (datum)
    labels = df_koers[datumkolom].dt.strftime('%Y-%m-%d')
    step = max(1, len(df_koers) // 12)
    ax.set_xticks(df_koers["x"][::step])
    ax.set_xticklabels(labels[::step], rotation=45, ha="right")

    # Y-as instellen
    try:
        koers_values = df_koers["Close"].astype(float).dropna()
        if not koers_values.empty:
            koers_min = koers_values.min()
            koers_max = koers_values.max()
            marge = (koers_max - koers_min) * 0.05
            ax.set_ylim(koers_min - marge, koers_max + marge)
    except Exception as e:
        st.warning(f"Kon y-as limieten niet instellen: {e}")

    ax.set_xlim(df_koers["x"].min(), df_koers["x"].max())
    ax.set_title(f"Koersgrafiek van {ticker_name}")
    ax.set_ylabel("Close")
    ax.set_xlabel("Datum")
    ax.legend()
    fig.tight_layout()
    st.subheader("Koersgrafiek")
    st.pyplot(fig)




# zzzz






import streamlit as st
from bs4 import BeautifulSoup
import requests
from sectorticker import sector_tickers_news  # of jouw bestandsnaam

# --- Finviz ticker nieuws (per aandeel) ---
@st.cache_data(ttl=600)
def get_finviz_news(ticker="AAPL", max_items=12):
    url = f"https://finviz.com/quote.ashx?t={ticker}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
    }
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(resp.content, "html.parser")
        table = soup.find("table", class_="fullview-news-outer")
        news_list = []
        if table:
            for row in table.find_all("tr")[:max_items]:
                cols = row.find_all("td")
                if len(cols) == 2:
                    dt = cols[0].get_text(" ", strip=True)
                    a = cols[1].find("a")
                    title = a.get_text(strip=True)
                    link = a["href"]
                    news_list.append({
                        "title": title,
                        "url": link,
                        "datetime": dt,
                        "site": "Finviz"
                    })
        return news_list
    except Exception:
        return []

# --- Finviz market news (algemeen) ---
@st.cache_data(ttl=600)
def get_finviz_market_news(max_items=25):
    url = "https://finviz.com/news.ashx"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
    }
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(resp.content, "html.parser")
        news_list = []
        news_blocks = soup.find_all("div", class_="news-link-box")
        for block in news_blocks[:max_items]:
            a = block.find("a")
            if a:
                title = a.get_text(strip=True)
                link = a["href"]
                timebox = block.find("div", class_="news-link-right")
                dt = timebox.get_text(strip=True) if timebox else ""
                news_list.append({
                    "title": title,
                    "url": link,
                    "datetime": dt,
                    "site": "Finviz (Market)"
                })
        return news_list
    except Exception:
        return []

# --- Tijdschriftstijl kaartje ---
def render_news_card(item):
    title = item.get("title") or ""
    link = item.get("url") or "#"
    date = item.get("datetime", "\u00A0")
    site = item.get("site", "Bron")
    st.markdown(f"""
    <div style="background:#f7f8fa;border-radius:16px;padding:18px;margin-bottom:12px;box-shadow:0 2px 8px rgba(0,0,0,0.08);">
      <div style="font-size:1.08em;font-weight:600;margin-bottom:4px;">
        <a href="{link}" target="_blank" style="color:#1166bb;text-decoration:none;">{title}</a>
      </div>
      <div style="color:#888;font-size:0.91em;margin-bottom:6px;">{site} | {date}</div>
    </div>
    """, unsafe_allow_html=True)

# --- Hoofdnieuwsfeed module ---
def toon_newsfeed():
    st.markdown("### 📰 Laatste beursnieuws")

    # Dynamisch: sectoren plus market news
    opties = list(sector_tickers_news.keys()) + ["Market news (algemeen)"]
    keuze = st.selectbox("Kies sector of algemeen nieuws", opties)

    news_items = []

    if keuze == "Market news (algemeen)":
        news_items = get_finviz_market_news()
    else:
        # Toon per sector per ticker de headlines (voor max. 3 tickers per sector)
        tickers = sector_tickers_news.get(keuze, [])
        st.write(f"DEBUG: Sector '{keuze}' heeft tickers: {tickers}")  # Debug: laat zien wat er in de dict zit
        for t in tickers[:3]:
            headlines = get_finviz_news(t, max_items=6)
            st.write(f"DEBUG: Nieuws voor {t}: {len(headlines)} items")  # Debug: laat aantal gevonden headlines zien
            news_items += headlines

    # Dedupe, sort, toon max 25
    seen = set()
    sorted_news = []
    for itm in news_items:
        key = itm.get("title", "")
        if key and key not in seen:
            seen.add(key)
            sorted_news.append(itm)
    sorted_news = sorted_news[:25]

    if sorted_news:
        for itm in sorted_news:
            render_news_card(itm)
    else:
        st.info("Geen nieuws gevonden voor deze selectie.")






# === heatmap.py ===

import streamlit as st
from datetime import datetime
import pandas as pd
import yfinance as yf

from sectorticker import sector_tickers
from sam_indicator import calculate_sam
from sat_indicator import calculate_sat
from adviezen import determine_advice, weighted_moving_average
from grafieken import bepaal_grafiekperiode_heat
from datafund import get_profile

# ✅ Kleuren voor de heatmap
kleurmap = {
    "Kopen": "#2ecc71",
    "Verkopen": "#e74c3c",
    "Neutraal": "#95a5a6"
}

# ✅ Lokale data-ophaalfunctie met startdatum
@st.cache_data(ttl=900)
def fetch_data_by_dates(ticker, interval, start, end=None):
    if end is None:
        end = datetime.today()
    df = yf.download(ticker, interval=interval, start=start, end=end)
    if df.empty or "Close" not in df.columns:
        return pd.DataFrame()

    df.index = pd.to_datetime(df.index, errors="coerce")
    df = df[~df.index.isna()]
    df = df[(df["Volume"] > 0) & ((df["Open"] != df["Close"]) | (df["High"] != df["Low"]))]
    for col in ["Close", "Open", "High", "Low", "Volume"]:
        df[col] = df[col].fillna(method="ffill").fillna(method="bfill")
    return df

# ✅ Heatmap generator
@st.cache_data(ttl=900)
def genereer_sector_heatmap(interval, risk_aversion=2, volgorde="marketcap"):
    html_output = "<div style='font-family: monospace;'>"
    start_date = datetime.today() - bepaal_grafiekperiode_heat(interval)

    for i, (sector, tickers) in enumerate(sector_tickers.items()):

        # Sorteer tickers
        if volgorde == "alphabetisch":
            sorted_tickers = sorted(tickers[:20])
        else:
            def get_cap(t):
                prof = get_profile(t)
                return prof.get("marketCap", 0) if prof else 0
            sorted_tickers = sorted(tickers[:20], key=get_cap, reverse=True)

        # Expander per sector (eerste twee open)
        with st.expander(f"📈 {sector}", expanded=(i < 2)):
            sector_html = "<div style='display: flex; flex-wrap: wrap; max-width: 620px;'>"

            for ticker in sorted_tickers:
                try:
                    df = fetch_data_by_dates(ticker, interval=interval, start=start_date)
                    if df.empty or len(df) < 50:
                        advies = "Neutraal"
                    else:
                        df = calculate_sam(df)
                        df = calculate_sat(df)
                        adviezen = determine_advice(df, threshold=2, risk_aversion=risk_aversion)
                        advies = adviezen[-1] if adviezen else "Neutraal"
                except Exception as e:
                    st.warning(f"⚠️ Fout bij {ticker}: {e}")
                    advies = "Neutraal"

                kleur = kleurmap.get(advies, "#7f8c8d")

                # HTML-blokje per ticker
                sector_html += f"""
                    <div style='
                        width: 100px;
                        height: 60px;
                        margin: 4px;
                        background-color: {kleur};
                        color: white;
                        display: flex;
                        flex-direction: column;
                        justify-content: center;
                        align-items: center;
                        border-radius: 6px;
                        font-size: 11px;
                        text-align: center;
                    ' title='{ticker}: {advies}'>
                        <div><b>{ticker}</b></div>
                        <div>{advies}</div>
                    </div>
                """

            sector_html += "</div>"
            st.components.v1.html(sector_html, height=300, scrolling=False)

    html_output += "</div>"
    return html_output

# ✅ Aanroepfunctie

def toon_sector_heatmap(interval, risk_aversion=2, volgorde="marketcap"):
    st.markdown("### 🔥 Sector Heatmap")
    genereer_sector_heatmap(interval, risk_aversion=risk_aversion, volgorde=volgorde)







------------------------



import streamlit as st
from datetime import datetime
from sectorticker import sector_tickers
from sam_indicator import calculate_sam
from sat_indicator import calculate_sat
from adviezen import determine_advice, weighted_moving_average
from grafieken import bepaal_grafiekperiode_heat
from datafund import get_profile  
import yfinance as yf
import pandas as pd

kleurmap = {
    "Kopen": "#2ecc71",
    "Verkopen": "#e74c3c",
    "Neutraal": "#95a5a6"
}

@st.cache_data(ttl=900)
def fetch_data_by_dates(ticker, interval, start, end=None):
    if end is None:
        end = datetime.today()
    df = yf.download(ticker, interval=interval, start=start, end=end)
    if df.empty or "Close" not in df.columns:
        return pd.DataFrame()
    df.index = pd.to_datetime(df.index, errors="coerce")
    df = df[~df.index.isna()]
    df = df[(df["Volume"] > 0) & ((df["Open"] != df["Close"]) | (df["High"] != df["Low"]))]
    for col in ["Close", "Open", "High", "Low", "Volume"]:
        df[col] = df[col].fillna(method="ffill").fillna(method="bfill")
    return df

@st.cache_data(ttl=900)
def sorteer_tickers(tickers, methode):
    if methode == "alfabetisch":
        return sorted(tickers)
    elif methode == "marktkapitalisatie":
        kapitalisaties = []
        for ticker in tickers:
            profiel = get_profile(ticker)
            cap = profiel.get("mktCap", 0) if profiel else 0
            kapitalisaties.append((ticker, cap if cap else 0))
        return [t for t, _ in sorted(kapitalisaties, key=lambda x: x[1], reverse=True)]
    else:
        return tickers

@st.cache_data(ttl=900)
def genereer_sector_heatmap(interval, risk_aversion=2, sorteer_op="marktkapitalisatie"):
    html = "<div style='font-family: monospace;'>"
    periode = bepaal_grafiekperiode_heat(interval)
    start_date = datetime.today() - periode

    for i, (sector, tickers) in enumerate(sector_tickers.items()):
        gesorteerde_tickers = sorteer_tickers(tickers, sorteer_op)[:20]

        # ✅ Titel boven dropdown
        html += f"<h4 style='color: white; margin-top: 30px;'>{sector}</h4>"

        # ✅ Uitklapbare sectie
        with st.expander(f"📊 {sector}", expanded=(i < 2)):  # Eerste 2 open
            html += "<div style='display: flex; flex-wrap: wrap; max-width: 600px;'>"

            for ticker in gesorteerde_tickers:
                try:
                    df = fetch_data_by_dates(ticker, interval=interval, start=start_date)
                    if df.empty or len(df) < 50:
                        advies = "Neutraal"
                    else:
                        df = calculate_sam(df)
                        df = calculate_sat(df)
                        adviezen = determine_advice(df, threshold=2, risk_aversion=risk_aversion)
                        advies = adviezen[-1] if len(adviezen) else "Neutraal"
                except Exception as e:
                    st.warning(f"⚠️ Fout bij {ticker}: {e}")
                    advies = "Neutraal"

                kleur = kleurmap.get(advies, "#7f8c8d")

                html += f"""
                    <div style='
                        width: 100px;
                        height: 60px;
                        margin: 4px;
                        background-color: {kleur};
                        color: white;
                        display: flex;
                        flex-direction: column;
                        justify-content: center;
                        align-items: center;
                        border-radius: 6px;
                        font-size: 11px;
                        text-align: center;
                    '>
                        <div><b>{ticker}</b></div>
                        <div>{advies}</div>
                    </div>
                """

            html += "</div><hr style='margin: 20px 0;'>"

    html += "</div>"
    return html

def toon_sector_heatmap(interval, risk_aversion=2, sorteer_op="marktkapitalisatie"):
    st.markdown("### 🔥 Sector Heatmap")

    sorteer_optie = st.radio(
        "📌 Sorteer tickers per sector op:",
        ["marktkapitalisatie", "alfabetisch"],
        index=0,
        horizontal=True
    )

    html = genereer_sector_heatmap(interval, risk_aversion=risk_aversion, sorteer_op=sorteer_optie)
    st.components.v1.html(html, height=1500, scrolling=True)




---------------------------------------

# === heatmap.py ===

import streamlit as st
from datetime import datetime
from sectorticker import sector_tickers
from sam_indicator import calculate_sam
from sat_indicator import calculate_sat
from adviezen import determine_advice, weighted_moving_average
from grafieken import bepaal_grafiekperiode_heat
import yfinance as yf
import pandas as pd

# Kleuren voor de heatmap
kleurmap = {
    "Kopen": "#2ecc71",
    "Verkopen": "#e74c3c",
    "Neutraal": "#95a5a6"
}

# Lokale data-ophaalfunctie met startdatum
@st.cache_data(ttl=900)
def fetch_data_by_dates(ticker, interval, start, end=None):
    if end is None:
        end = datetime.today()
    df = yf.download(ticker, interval=interval, start=start, end=end)
    if df.empty or "Close" not in df.columns:
        return pd.DataFrame()

    df.index = pd.to_datetime(df.index, errors="coerce")
    df = df[~df.index.isna()]
    df = df[(df["Volume"] > 0) & ((df["Open"] != df["Close"]) | (df["High"] != df["Low"]))]
    for col in ["Close", "Open", "High", "Low", "Volume"]:
        df[col] = df[col].fillna(method="ffill").fillna(method="bfill")
    return df

@st.cache_data(ttl=900)
def genereer_sector_heatmap(interval, risk_aversion=2, alfabetisch=False):
    html = "<div style='font-family: monospace;'>"

    periode = bepaal_grafiekperiode_heat(interval)
    start_date = datetime.today() - periode

    for i, (sector, tickers) in enumerate(sector_tickers.items()):
        if alfabetisch:
            tickers = sorted(tickers)
        open_attr = "open" if i < 2 else ""

        html += f"""
        <details {open_attr} style='margin-bottom: 10px;'>
        <summary style='font-size: 18px; color: white; cursor: pointer;'>{sector}</summary>
        <div style='display: flex; flex-wrap: wrap; max-width: 600px; margin-top: 10px;'>
        """

        for ticker in tickers[:20]:
            try:
                df = fetch_data_by_dates(ticker, interval=interval, start=start_date)
                if df.empty or len(df) < 50:
                    advies = "Neutraal"
                else:
                    df = calculate_sam(df)
                    df = calculate_sat(df)
                    adviezen = determine_advice(df, threshold=2, risk_aversion=risk_aversion)
                    advies = adviezen[-1] if len(adviezen) else "Neutraal"
            except Exception as e:
                st.warning(f"⚠️ Fout bij {ticker}: {e}")
                advies = "Neutraal"

            kleur = kleurmap.get(advies, "#7f8c8d")

            html += f"""
                <div style='
                    width: 100px;
                    height: 60px;
                    margin: 4px;
                    background-color: {kleur};
                    color: white;
                    display: flex;
                    flex-direction: column;
                    justify-content: center;
                    align-items: center;
                    border-radius: 6px;
                    font-size: 11px;
                    text-align: center;
                '>
                    <div><b>{ticker}</b></div>
                    <div>{advies}</div>
                </div>
            """

        html += "</div></details><hr style='margin: 20px 0;'>"

    html += "</div>"
    return html

def toon_sector_heatmap(interval, risk_aversion=2, alfabetisch=False):
    st.markdown("### 🔥 Sector Heatmap")
    html = genereer_sector_heatmap(interval, risk_aversion=risk_aversion, alfabetisch=alfabetisch)
    st.components.v1.html(html, height=1400, scrolling=True)






#------------------------------



import streamlit as st
from datetime import datetime
from sectorticker import sector_tickers
from sam_indicator import calculate_sam
from sat_indicator import calculate_sat
from adviezen import determine_advice, weighted_moving_average
from grafieken import bepaal_grafiekperiode_heat

import yfinance as yf
import pandas as pd

# Kleuren voor de heatmap
kleurmap = {
    "Kopen": "#2ecc71",
    "Verkopen": "#e74c3c",
    "Neutraal": "#95a5a6"
}

# Lokale data-ophaalfunctie met startdatum
@st.cache_data(ttl=900)
def fetch_data_by_dates(ticker, interval, start, end=None):
    if end is None:
        end = datetime.today()
    df = yf.download(ticker, interval=interval, start=start, end=end)
    if df.empty or "Close" not in df.columns:
        return pd.DataFrame()
    
    df.index = pd.to_datetime(df.index, errors="coerce")
    df = df[~df.index.isna()]
    df = df[(df["Volume"] > 0) & ((df["Open"] != df["Close"]) | (df["High"] != df["Low"]))]
    for col in ["Close", "Open", "High", "Low", "Volume"]:
        df[col] = df[col].fillna(method="ffill").fillna(method="bfill")
    return df

@st.cache_data(ttl=900)
def genereer_sector_heatmap(interval, risk_aversion=2):
    html = "<div style='font-family: monospace;'>"

    periode = bepaal_grafiekperiode_heat(interval)
    start_date = datetime.today() - periode

    for sector, tickers in sector_tickers.items():
        html += f"<h4 style='color: white;'>{sector}</h4>"
        html += "<div style='display: flex; flex-wrap: wrap; max-width: 600px;'>"

        for ticker in tickers[:20]:
            try:
                df = fetch_data_by_dates(ticker, interval=interval, start=start_date)
                if df.empty or len(df) < 50:
                    advies = "Neutraal"
                else:
                    df = calculate_sam(df)
                    df = calculate_sat(df)
                    adviezen = determine_advice(df, threshold=2, risk_aversion=risk_aversion)
                    advies = adviezen[-1] if len(adviezen) else "Neutraal"
            except Exception as e:
                st.warning(f"⚠️ Fout bij {ticker}: {e}")
                advies = "Neutraal"

            kleur = kleurmap.get(advies, "#7f8c8d")

            html += f"""
                <div style='
                    width: 100px;
                    height: 60px;
                    margin: 4px;
                    background-color: {kleur};
                    color: white;
                    display: flex;
                    flex-direction: column;
                    justify-content: center;
                    align-items: center;
                    border-radius: 6px;
                    font-size: 11px;
                    text-align: center;
                '>
                    <div><b>{ticker}</b></div>
                    <div>{advies}</div>
                </div>
            """

        html += "</div><hr style='margin: 20px 0;'>"

    html += "</div>"
    return html

def toon_sector_heatmap(interval, risk_aversion=2):
    st.markdown("### 🔥 Sector Heatmap")
    html = genereer_sector_heatmap(interval, risk_aversion=risk_aversion)
    st.components.v1.html(html, height=1400, scrolling=True)







# === heatmap.py ===

import streamlit as st
from sectorticker import sector_tickers
from yffetch import fetch_data
from grafieken import bepaal_grafiekperiode
from sam_indicator import calculate_sam
from sat_indicator import calculate_sat
from adviezen import determine_advice, weighted_moving_average

# ðŸŽ¨ Kleuren voor de heatmap
kleurmap = {
    "Kopen": "#2ecc71",
    "Verkopen": "#e74c3c",
    "Neutraal": "#95a5a6"
}

@st.cache_data(ttl=900)
def genereer_sector_heatmap(interval, risk_aversion=2):
    html = "<div style='font-family: monospace;'>"

    for sector, tickers in sector_tickers.items():
        html += f"<h4 style='color: white;'>{sector}</h4>"
        html += "<div style='display: flex; flex-wrap: wrap; max-width: 600px;'>"

        for ticker in tickers[:20]:  # max 20 per sector
            try:
                df = fetch_data(ticker, interval)
                if df is None or df.empty or len(df) < 30:
                    advies = "Neutraal"
                else:
                    df = calculate_sam(df)
                    df = calculate_sat(df)
                    df, _ = determine_advice(df, threshold=2, risk_aversion=risk_aversion)

                    if "Advies" in df.columns:
                        advies = df["Advies"].iloc[-1]
                    else:
                        advies = "Neutraal"

            except Exception as e:
                st.write(f"âš ï¸ Fout bij {ticker}: {e}")
                advies = "Neutraal"

            kleur = kleurmap.get(advies, "#7f8c8d")

            html += f"""
                <div style='
                    width: 100px;
                    height: 60px;
                    margin: 4px;
                    background-color: {kleur};
                    color: white;
                    display: flex;
                    flex-direction: column;
                    justify-content: center;
                    align-items: center;
                    border-radius: 6px;
                    font-size: 11px;
                    text-align: center;
                '>
                    <div><b>{ticker}</b></div>
                    <div>{advies}</div>
                </div>
            """

            # ðŸž DEBUG
  #          st.write(f"ðŸ“ˆ {ticker} ({interval}): {advies}")
  #          if "Advies" in df.columns:
   #             st.dataframe(df[["Close", "SAM", "Trend", "Advies"]].tail(3))

        html += "</div><hr style='margin: 20px 0;'>"

    html += "</div>"
    return html

def toon_sector_heatmap(interval, risk_aversion=2):
    st.markdown("### ðŸ”¥ Sector Heatmap")
    html = genereer_sector_heatmap(interval, risk_aversion=risk_aversion)
    st.components.v1.html(html, height=1400, scrolling=True)



🧱 Bakstenen / Gebouwen / Fundament
🧱 = baksteen

🏗️ = in aanbouw

🏢 = kantoorgebouw

🏛️ = klassiek gebouw (fundament / instituut)

🏠 = huis

🧰 = gereedschapskist (bouwtools)

⚙️ = tandwiel (constructie / instellingen)

💰 Geld / Waarde / Munten / Briefgeld
💰 = geldzak

💵 = briefgeld (dollar)

💶 = eurobiljet

💷 = pond

💴 = yen

🪙 = munt

🏦 = bank

💳 = betaalpas

📈 = koers omhoog

📉 = koers omlaag

💹 = grafiek met yen (maar werkt goed als "marktgrafiek")

🔠 Alfabet / Letters / Tekst
🔠 = hoofdletters

🔡 = kleine letters

🔤 = abc

🔢 = cijfers

🔤 = letters met volgorde (sortering)

🆎 = "AB" knop

🅰️ / 🅱️ / 🆎 = afzonderlijke letters als icoon















# w
