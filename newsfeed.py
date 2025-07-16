import streamlit as st
from bs4 import BeautifulSoup
import requests
from sectorticker import sector_tickers_news  # Jouw nieuwe dict met sectoren!

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
        news_items = []
        for t in sector_tickers_news[keuze][:3]:
            news_items += get_finviz_news(t, max_items=6)

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




















    
