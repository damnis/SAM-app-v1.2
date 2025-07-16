import streamlit as st
import requests
from bs4 import BeautifulSoup
from sectorticker import sector_tickers_news  # <-- jouw dict!

# ---- Finviz news per ticker ----
@st.cache_data(ttl=600)
def get_finviz_news(ticker, max_items=7):
    url = f"https://finviz.com/quote.ashx?t={ticker}"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        resp = requests.get(url, headers=headers, timeout=8)
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

# ---- Finviz market news ----
@st.cache_data(ttl=600)
def get_finviz_market_news(max_items=20):
    url = "https://finviz.com/news.ashx"
    headers = {"User-Agent": "Mozilla/5.0"}
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

# ---- Google News fallback per ticker ----
@st.cache_data(ttl=600)
def get_google_news(ticker, max_items=7, lang="en"):
    url = f"https://news.google.com/rss/search?q={ticker}+stock&hl={lang}-US&gl=US&ceid=US:en"
    try:
        resp = requests.get(url, timeout=10)
        soup = BeautifulSoup(resp.content, "xml")
        items = soup.find_all("item")[:max_items]
        news_list = []
        for item in items:
            title = item.title.text
            link = item.link.text
            date = item.pubDate.text
            news_list.append({
                "title": title,
                "url": link,
                "datetime": date,
                "site": "Google News"
            })
        return news_list
    except Exception:
        return []

# ---- Google News market fallback ----
@st.cache_data(ttl=600)
def get_google_market_news(max_items=20, lang="en"):
    url = f"https://news.google.com/rss/search?q=US+stock+market&hl={lang}-US&gl=US&ceid=US:en"
    try:
        resp = requests.get(url, timeout=10)
        soup = BeautifulSoup(resp.content, "xml")
        items = soup.find_all("item")[:max_items]
        news_list = []
        for item in items:
            title = item.title.text
            link = item.link.text
            date = item.pubDate.text
            news_list.append({
                "title": title,
                "url": link,
                "datetime": date,
                "site": "Google News"
            })
        return news_list
    except Exception:
        return []

# ---- Stijlvolle card ----
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

# ---- Newsfeed hoofdcomponent ----
def toon_newsfeed():
    with st.expander("📰 Laatste beursnieuws per sector", expanded=False):
        opties = list(sector_tickers_news.keys()) + ["Market news (algemeen)"]
        keuze = st.selectbox("Kies sector of algemeen nieuws", opties, index=0)

        news_items = []

        if keuze == "Market news (algemeen)":
            news_items = get_finviz_market_news()
            if not news_items:  # fallback Google
                news_items = get_google_market_news()
        else:
            tickers = sector_tickers_news[keuze][:3]  # max 3 tickers per sector
            for t in tickers:
                # Probeer Finviz
                items = get_finviz_news(t)
                # Fallback Google als Finviz leeg is
                if not items:
                    items = get_google_news(t)
                news_items += items

        # Dedupe, max 24 items, stijlvaste weergave
        seen = set()
        unique_news = []
        for itm in news_items:
            key = itm.get("title", "")
            if key and key not in seen:
                seen.add(key)
                unique_news.append(itm)
            if len(unique_news) >= 24:
                break

        if unique_news:
            for itm in unique_news:
                render_news_card(itm)
        else:
            st.info("Geen nieuws gevonden voor deze selectie.")





















    # w
