import streamlit as st
import pandas as pd
from datafund import get_income_statement, get_ratios
from datafund import (
    get_profile, get_key_metrics, get_earning_calendar,
    get_dividend_history, get_quarterly_eps, get_eps_forecast
)

def format_value(value, is_percent=False):
    try:
        if value is None:
            return "-"
        value = float(value)
        if is_percent:
            return f"{value:.2%}"
        if abs(value) >= 99_000_000:
            return f"{value / 1_000_000_000:,.2f} mld"
        return f"{value:,.2f}"
    except:
        return "-"

st.set_page_config(page_title="Fundamentele Analyse Tool", layout="wide")
st.title("📊 Fundamentool: Ratio-analyse van aandelen")

if "recent_tickers" not in st.session_state:
    st.session_state["recent_tickers"] = []

ticker_input = st.text_input("Voer een ticker in (bijv. AAPL, MSFT)", value="AAPL").upper().strip()

if ticker_input:
    profile = get_profile(ticker_input)
    if profile:
        ticker = ticker_input
        if ticker not in st.session_state["recent_tickers"]:
            st.session_state["recent_tickers"].append(ticker)
    else:
        st.error("❌ Ticker niet gevonden. Controleer de spelling.")
        ticker = None
else:
    ticker = None

if ticker:
    st.info(f"📥 Data wordt opgehaald voor: {ticker}")

    profile = get_profile(ticker)
    key_metrics = get_key_metrics(ticker)
    income_data = get_income_statement(ticker)
    ratio_data = get_ratios(ticker)
    earnings = get_earning_calendar(ticker)
    dividends = get_dividend_history(ticker)
    eps_quarters = get_quarterly_eps(ticker)
    eps_forecast = get_eps_forecast(ticker)

    # 🔹 Kerninfo
    if profile and key_metrics:
        with st.expander("🧾 Bedrijfsprofiel & Kerninfo", expanded=True):
            col1, col2, col3 = st.columns(3)
            col1.metric("Prijs", format_value(profile.get("price")))
            col1.metric("Marktkapitalisatie", format_value(profile.get("mktCap")))
            col2.metric("Dividend (per aandeel)", format_value(profile.get("lastDiv")))
            col2.metric("Dividendrendement", format_value(key_metrics.get("dividendYield", 0), is_percent=True))
            col3.metric("Payout Ratio", format_value(key_metrics.get("payoutRatio", 0), is_percent=True))
            st.caption(profile.get("description", ""))

    # 🔹 Omzet, Winst, EPS
    if income_data:
        df_income = pd.DataFrame(income_data)
        df_income_fmt = df_income.copy()
        df_income_fmt["revenue"] = df_income_fmt["revenue"].apply(format_value)
        df_income_fmt["netIncome"] = df_income_fmt["netIncome"].apply(format_value)
        df_income_fmt["eps"] = df_income_fmt["eps"].apply(format_value)
        df_income_fmt.rename(columns={"revenue": "Omzet", "netIncome": "Winst", "eps": "WPA", "date": "Jaar"}, inplace=True)

        with st.expander("📈 Omzet, Winst en EPS"):
            st.dataframe(df_income_fmt.set_index("Jaar")[["Omzet", "Winst", "WPA"]])

    # 🔹 Ratio's jaarlijks
    col_renames = {
        "currentRatio": "Current ratio",
        "quickRatio": "Quick ratio",
        "grossProfitMargin": "Bruto marge",
        "operatingProfitMargin": "Operationele marge",
        "netProfitMargin": "Netto marge",
        "returnOnAssets": "Rentabiliteit",
        "inventoryTurnover": "Omloopsnelheid",
    }

    if ratio_data:
        df_ratio = pd.DataFrame(ratio_data)
        df_ratio_fmt = df_ratio.copy()
        df_ratio_fmt["priceEarningsRatio"] = df_ratio_fmt["priceEarningsRatio"].apply(format_value)
        df_ratio_fmt["returnOnEquity"] = df_ratio_fmt["returnOnEquity"].apply(lambda x: format_value(x * 100))
        df_ratio_fmt["debtEquityRatio"] = df_ratio_fmt["debtEquityRatio"].apply(format_value)
        df_ratio_fmt.rename(columns={
            "priceEarningsRatio": "K/W", "returnOnEquity": "ROE (%)", "debtEquityRatio": "Debt/Equity", "date": "Jaar"
        }, inplace=True)

        with st.expander("📐 Ratio's over de jaren"):
            st.dataframe(df_ratio_fmt.set_index("Jaar")[["K/W", "ROE (%)", "Debt/Equity"]])

        with st.expander("🧮 Extra Ratio's"):
            df_extra = df_ratio.copy()
            df_extra.rename(columns={**col_renames, "date": "Jaar"}, inplace=True)
            for col in col_renames.values():
                if col in df_extra.columns:
                    is_pct = "marge" in col.lower()
                    df_extra[col] = df_extra[col].apply(lambda x: format_value(x, is_percent=is_pct))
            st.dataframe(df_extra.set_index("Jaar")[list(col_renames.values())])

        
        # 🔹 Extra ratio's per kwartaal (FMP-data)
        with st.expander("🧮 Extra Ratio's per kwartaal (FMP-data)"):
            df_qr = get_ratios(ticker + "?period=quarter")
            if isinstance(df_qr, list) and len(df_qr) > 0:
                df_qr = pd.DataFrame(df_qr)

        # Herbenoemen van kolommen waar mogelijk
                df_qr.rename(columns=col_renames, inplace=True)
                df_qr.rename(columns={"date": "Kwartaal"}, inplace=True)

                df_qr["Kwartaal"] = pd.to_datetime(df_qr["Kwartaal"]).dt.date

        # Format alle numerieke kolommen
                for col in df_qr.columns:
                    if col == "Kwartaal":
                        continue
                    try:
                        if "marge" in col.lower() or "%" in col or "Yield" in col:
                            df_qr[col] = df_qr[col].apply(lambda x: format_value(x, is_percent=True))
                        else:
                            df_qr[col] = df_qr[col].apply(format_value)
                    except:
                        pass  # Niet-numeriek of error: negeren

                st.dataframe(df_qr.set_index("Kwartaal"))
            else:
                st.warning("Geen kwartaalratio-data gevonden.")
        
        
    # 🔹 Grafieken
    with st.expander("📊 Grafieken"):
        col1, col2 = st.columns(2)
        with col1:
            st.line_chart(df_income.set_index("date")[["revenue", "netIncome"]])
        with col2:
            chart_df = df_ratio.set_index("date")[["priceEarningsRatio", "returnOnEquity"]].copy()
            chart_df["returnOnEquity"] *= 100
            chart_df.rename(columns={"priceEarningsRatio": "K/W", "returnOnEquity": "ROE (%)"}, inplace=True)
            st.line_chart(chart_df)

    # 🔹 Belangrijke datums
    with st.expander("📅 Belangrijke datums"):
        if isinstance(earnings, list) and len(earnings) > 0:
            df_earn = pd.DataFrame(earnings)[["date", "eps", "epsEstimated"]]
            df_earn.columns = ["Datum", "Werkelijke EPS", "Verwachte EPS"]
            st.subheader("Earnings kalender:")
            st.dataframe(df_earn.set_index("Datum"))

        if isinstance(dividends, list) and len(dividends) > 0:
            df_div = pd.DataFrame(dividends)[["date", "dividend"]]
            df_div.columns = ["Datum", "Dividend"]
            st.subheader("Dividend historie:")
            st.dataframe(df_div.set_index("Datum"))

    
