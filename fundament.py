import streamlit as st
import pandas as pd
from datafund import get_income_statement, get_ratios
from datafund import (
    get_profile, get_key_metrics, get_earning_calendar,
    get_dividend_history, get_quarterly_eps, get_eps_forecast
)
from utils import format_value  # hulpfunctie voor formatting



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

# kerninfo
def toon_profiel_en_kerninfo(profile, key_metrics):
    if profile and key_metrics:
        with st.expander("🧾 Bedrijfsprofiel & Kerninfo", expanded=True):
            col1, col2, col3 = st.columns(3)
            col1.metric("Prijs", format_value(profile.get("price")))
            col1.metric("Marktkapitalisatie", format_value(profile.get("mktCap")))
            col2.metric("Dividend (per aandeel)", format_value(profile.get("lastDiv")))
            col2.metric("Dividendrendement", format_value(key_metrics.get("dividendYield", 0), is_percent=True))
            col3.metric("Payout Ratio", format_value(key_metrics.get("payoutRatio", 0), is_percent=True))
            st.caption(profile.get("description", ""))

# omzet en winst
def toon_omzet_winst_eps(income_data):
    if income_data:
        df = pd.DataFrame(income_data)
        df["revenue"] = df["revenue"].apply(format_value)
        df["netIncome"] = df["netIncome"].apply(format_value)
        df["eps"] = df["eps"].apply(format_value)
        df.rename(columns={"revenue": "Omzet", "netIncome": "Winst", "eps": "WPA", "date": "Jaar"}, inplace=True)

        with st.expander("📈 Omzet, Winst en EPS"):
            st.dataframe(df.set_index("Jaar")[["Omzet", "Winst", "WPA"]])

        # 🔹 Grafieken
#        with st.expander("📊 Grafieken"):
 #           col1, col2 = st.columns(2)
   #         with col1:
   #             st.line_chart(df_income.set_index("date")[["revenue", "netIncome"]])
   #         with col2:
     #           chart_df = df_ratio.set_index("date")[["priceEarningsRatio", "returnOnEquity"]].copy()
      #          chart_df["returnOnEquity"] *= 100
     #           chart_df.rename(columns={"priceEarningsRatio": "K/W", "returnOnEquity": "ROE (%)"}, inplace=True)
    #            st.line_chart(chart_df)


# ratio's fmp
def toon_ratios(ratio_data):
    if ratio_data:
        col_renames = {
            "currentRatio": "Current ratio",
            "quickRatio": "Quick ratio",
            "grossProfitMargin": "Bruto marge",
            "operatingProfitMargin": "Operationele marge",
            "netProfitMargin": "Netto marge",
            "returnOnAssets": "Rentabiliteit",
            "inventoryTurnover": "Omloopsnelheid",
        }
        df = pd.DataFrame(ratio_data)
        df["priceEarningsRatio"] = df["priceEarningsRatio"].apply(format_value)
        df["returnOnEquity"] = df["returnOnEquity"].apply(lambda x: format_value(x * 100))
        df["debtEquityRatio"] = df["debtEquityRatio"].apply(format_value)
        df.rename(columns={"priceEarningsRatio": "K/W", "returnOnEquity": "ROE (%)", "debtEquityRatio": "Debt/Equity", "date": "Jaar"}, inplace=True)

        with st.expander("📐 Ratio's over de jaren"):
            st.dataframe(df.set_index("Jaar")[["K/W", "ROE (%)", "Debt/Equity"]])

        with st.expander("🧮 Extra Ratio's"):
            df_extra = df.copy()
            df_extra.rename(columns={**col_renames, "date": "Jaar"}, inplace=True)
            for col in col_renames.values():
                if col in df_extra.columns:
                    is_pct = "marge" in col.lower()
                    df_extra[col] = df_extra[col].apply(lambda x: format_value(x, is_percent=is_pct))
            st.dataframe(df_extra.set_index("Jaar")[list(col_renames.values())])

# belangrijke datums 
def toon_datums(earnings, dividends):
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


# fundamentals voor main
def toon_fundamentals(ticker):
    st.subheader("📊 Fundamentals")

    if not ticker or not isinstance(ticker, str):
        st.warning("⚠️ Geen geldige ticker opgegeven.")
        return

    ticker = ticker.strip().upper()

    try:
        profile = get_profile(ticker)
        key_metrics = get_key_metrics(ticker)
        income_data = get_income_statement(ticker)
        ratio_data = get_ratios(ticker)
        earnings = get_earning_calendar(ticker)
        dividends = get_dividend_history(ticker)
        eps_quarters = get_quarterly_eps(ticker)
    except Exception as e:
        st.error(f"❌ Fout bij ophalen van fundamentele data: {e}")
        return

    if not profile:
        st.warning("📭 Geen fundamentele data gevonden voor deze ticker.")
        return

    # ALLES WAT NU KOMT moet dus binnen de functie blijven!
    # 🔹 Profiel
    with st.expander("🧾 Bedrijfsprofiel & Kerninfo", expanded=True):
        ...

    # 🔹 Profiel
    with st.expander("🧾 Bedrijfsprofiel & Kerninfo", expanded=True):
        col1, col2, col3 = st.columns(3)
        col1.metric("Prijs", format_value(profile.get("price")))
        col1.metric("Marktkapitalisatie", format_value(profile.get("mktCap")))
        col2.metric("Dividend (per aandeel)", format_value(profile.get("lastDiv")))
        col2.metric("Dividendrendement", format_value(key_metrics.get("dividendYield", 0), is_percent=True) if key_metrics else "-")
        col3.metric("Payout Ratio", format_value(key_metrics.get("payoutRatio", 0), is_percent=True) if key_metrics else "-")
        st.caption(profile.get("description", ""))

    # 🔹 Omzet, Winst, EPS
    if income_data:
        df_income = pd.DataFrame(income_data)
        df_income_fmt = df_income.copy()
        df_income_fmt["revenue"] = df_income_fmt["revenue"].apply(format_value)
        df_income_fmt["netIncome"] = df_income_fmt["netIncome"].apply(format_value)
        df_income_fmt["eps"] = df_income_fmt["eps"].apply(format_value)
        df_income_fmt.rename(columns={"revenue": "Omzet", "netIncome": "Winst", "eps": "WPA", "date": "Jaar"}, inplace=True)

        with st.expander("📈 Omzet, Winst en WPA"):
            st.dataframe(df_income_fmt.set_index("Jaar")[["Omzet", "Winst", "WPA"]])

    # 🔹 Ratio’s
    if ratio_data:
        df_ratio = pd.DataFrame(ratio_data)
        df_ratio_fmt = df_ratio.copy()
        df_ratio_fmt["priceEarningsRatio"] = df_ratio_fmt["priceEarningsRatio"].apply(format_value)
        df_ratio_fmt["returnOnEquity"] = df_ratio_fmt["returnOnEquity"].apply(lambda x: format_value(x * 100))
        df_ratio_fmt["debtEquityRatio"] = df_ratio_fmt["debtEquityRatio"].apply(format_value)
        df_ratio_fmt.rename(columns={
            "priceEarningsRatio": "K/W",
            "returnOnEquity": "ROE (%)",
            "debtEquityRatio": "Debt/Equity",
            "date": "Jaar"
        }, inplace=True)

        with st.expander("📐 Ratio's over de jaren"):
            st.dataframe(df_ratio_fmt.set_index("Jaar")[["K/W", "ROE (%)", "Debt/Equity"]])

    # 🔹 Earnings & Dividends
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

    # 🔹 Grafieken
    with st.expander("📊 Grafieken"):
        col1, col2 = st.columns(2)
        with col1:
            try:
                st.line_chart(df_income.set_index("date")[["revenue", "netIncome"]])
            except:
                st.info("📉 Geen omzet/winst grafiek beschikbaar.")
        with col2:
            try:
                df_ratio_graph = df_ratio.set_index("date")[["priceEarningsRatio", "returnOnEquity"]].copy()
                df_ratio_graph["returnOnEquity"] *= 100
                df_ratio_graph.rename(columns={
                    "priceEarningsRatio": "K/W",
                    "returnOnEquity": "ROE (%)"
                }, inplace=True)
                st.line_chart(df_ratio_graph)
            except:
                st.info("📉 Geen ratio grafiek beschikbaar.")

    # 🔹 EPS per kwartaal
    if eps_quarters:
        df_eps_q = pd.DataFrame(eps_quarters)[["date", "eps"]].copy()
        df_eps_q["date"] = pd.to_datetime(df_eps_q["date"])
        df_eps_q = df_eps_q.sort_values("date")
        df_eps_q.set_index("date", inplace=True)
        with st.expander("📆 WPA per kwartaal"):
            st.bar_chart(df_eps_q)






    
    
    


























# w



    
