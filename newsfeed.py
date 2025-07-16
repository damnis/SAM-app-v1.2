import streamlit as st
from datafund import get_news_fmp, get_news_yahoo  # Zorg dat deze functies bestaan (zie vorige berichten)
from sectorticker import sector_tickers

def toon_newsfeed(ticker):
    """
    Nieuwsfeed module. Toon via filter: alles, sector, of actuele ticker.
    """
    filters = ["Alle", "Sector", "Ticker (actief)"]
    filter_choice = st.selectbox("🔎 Nieuwsfilter", filters, index=2)

    sector_dict = sector_tickers
    news_items = []

    if filter_choice == "Alle":
        selected_source = st.radio("Bron:", ["FMP"], horizontal=True, index=0)
        news_items = get_news_fmp(limit=15)

    elif filter_choice == "Sector":
        sector = st.selectbox("Sector:", list(sector_dict.keys()))
        selected_source = st.radio("Bron:", ["FMP"], horizontal=True, index=0)
        tickers = sector_dict[sector]
        # Snelste: per sector alleen FMP, anders kan je limiet raken bij Yahoo
        news_items = []
        for t in tickers:
            news_items += get_news_fmp(t, limit=4)
        # Eventueel: yahoo toevoegen, maar meestal weinig/traag bij bulk

    elif filter_choice == "Ticker (actief)":
        # ticker wordt als argument meegegeven!
        selected_source = st.radio("Bron:", ["FMP", "Yahoo"], horizontal=True, index=0)
        if selected_source == "FMP":
            news_items = get_news_fmp(ticker, limit=10)
        else:
            news_items = get_news_yahoo(ticker, limit=10)

    # Unieke, nieuwste eerst, maximaal 15 headlines
    def sort_news(news):
        seen = set()
        items = []
        for item in sorted(news, key=lambda x: x.get("publishedDate", x.get("providerPublishTime", 0)), reverse=True):
            key = (item.get("title") or item.get("headline"))
            if key and key not in seen:
                seen.add(key)
                items.append(item)
        return items[:15]

    news_items = sort_news(news_items)

    # Tijdschriftstijl cards
    def render_news_card(item):
        # FMP item
        if "title" in item:
            title = item.get("title")
            link = item.get("url")
            date = item.get("publishedDate", "")
            summary = item.get("text", "")[:200] + "..."
            bron = item.get("site", "FMP")
        # Yahoo item
        else:
            title = item.get("title") or item.get("headline", "")
            link = item.get("link") or item.get("url", "#")
            date = ""
            if "providerPublishTime" in item:
                from datetime import datetime
                date = datetime.fromtimestamp(item["providerPublishTime"]).strftime("%Y-%m-%d %H:%M")
            summary = item.get("summary", "")[:200] + "..."
            bron = item.get("publisher", "Yahoo")
        st.markdown(f"""
        <div style="background-color:#f7f8fa;border-radius:16px;padding:18px 22px;margin-bottom:14px;box-shadow:0 2px 12px #0001;">
            <div style="font-size:1.09em;font-weight:600;margin-bottom:4px;">
                <a href="{link}" target="_blank" style="color:#1166bb;text-decoration:none;">{title}</a>
            </div>
            <div style="color:#888;font-size:0.94em;margin-bottom:7px;">{bron} | {date}</div>
            <div style="font-size:1.03em;color:#222;">{summary}</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("### 📰 Laatste beursnieuws")
    if news_items:
        for item in news_items:
            render_news_card(item)
    else:
        st.info("Geen nieuws gevonden voor deze selectie.")






















        # w
