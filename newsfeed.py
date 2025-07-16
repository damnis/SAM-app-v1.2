import streamlit as st
from datafund import get_news_fmp, get_news_yahoo, get_news_finviz
from sectorticker import sector_tickers

def toon_newsfeed(ticker):
    st.markdown("### 📰 Laatste beursnieuws")

    filters = ["Alle", "Sector", "Ticker (actief)"]
    fc = st.selectbox("🔎 Nieuwsfilter", filters, index=2)

    news_items = []
    bron_keuzes = ["FMP", "Yahoo", "Finviz"]

    if fc == "Alle":
        b = st.radio("Bron:", bron_keuzes, index=2, horizontal=True)
        news_items = get_news_finviz()

    elif fc == "Sector":
        sector = st.selectbox("Sector:", list(sector_tickers.keys()))
        b = st.radio("Bron:", bron_keuzes, index=2, horizontal=True)
        news_items = []
        for t in sector_tickers[sector]:
            if b == "FMP":
                news_items += get_news_fmp(t, limit=4)
            elif b == "Yahoo":
                news_items += get_news_yahoo(t, limit=3)
            else:
                news_items += get_news_finviz()

    else:  # Ticker (actief)
        b = st.radio("Bron:", bron_keuzes, index=0, horizontal=True)
        if b == "FMP":
            news_items = get_news_fmp(ticker)
        elif b == "Yahoo":
            news_items = get_news_yahoo(ticker, limit=10)
        else:
            news_items = get_news_finviz()

    # dedupe & sort
    seen = set()
    sorted_news = []
    for itm in sorted(news_items, key=lambda x: x.get("publishedDate", x.get("datetime", "")), reverse=True):
        key = itm.get("title") or itm.get("headline", "")
        if key and key not in seen:
            seen.add(key)
            sorted_news.append(itm)
    sorted_news = sorted_news[:15]

    # kaartjes renderen
    def render(item):
        title = item.get("title") or item.get("headline","")
        link = item.get("url") or item.get("link") or "#"
        date = item.get("publishedDate", item.get("datetime", "\u00A0"))
        summary = (item.get("text") or item.get("summary") or "")[:200] + "..."
        site = item.get("site") or item.get("publisher") or "Bron"

        st.markdown(f"""
        <div style="background:#f7f8fa;border-radius:16px;padding:18px;margin-bottom:12px;box-shadow:0 2px 8px rgba(0,0,0,0.1);">
          <div style="font-size:1.05em;font-weight:600;margin-bottom:4px;">
            <a href="{link}" target="_blank" style="color:#1166bb;text-decoration:none;">{title}</a>
          </div>
          <div style="color:#888;font-size:0.9em;margin-bottom:6px;">{site} | {date}</div>
          <div style="color:#222;font-size:1.02em;">{summary}</div>
        </div>
        """, unsafe_allow_html=True)

    if sorted_news:
        for itm in sorted_news:
            render(itm)
    else:
        st.info("Geen nieuws gevonden voor deze selectie.")










        
