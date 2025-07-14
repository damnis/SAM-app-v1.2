import streamlit as st
import pandas as pd
from datafund import get_income_statement, get_ratios
from datafund import (
    get_profile, get_key_metrics, get_earning_calendar,
    get_dividend_history, get_quarterly_eps, get_eps_forecast
)
import requests
import json
import yfinance as yf

FMP_API_KEY = st.secrets["FMP_API_KEY"]

def format_value(value, is_percent=False):
    try:
        if value is None or value == "":
            return "-"
        if isinstance(value, str) and value.replace(",", "").isdigit():
            value = float(value.replace(",", ""))
        else:
            value = float(value)

        if is_percent:
            return f"{value:.2%}"
        if abs(value) >= 99_000_000:
            return f"{value / 1_000_000_000:,.2f} mld"
        elif abs(value) >= 1_000_000:
            return f"{value / 1_000_000:,.2f} mln"
        elif abs(value) >= 1_000:
            return f"{value / 1_000:,.1f}k"
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
            col3.metric("Aantal medewerkers", format_value(profile.get("fullTimeEmployees")))
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

        # 🔹 Extra ratio's per kwartaal (FMP-data)
        with st.expander("🧮 Extra Ratio's per kwartaal (FMP-data)"):
            df_qr = get_ratios(ticker + "?period=quarter")
            if isinstance(df_qr, list) and len(df_qr) > 0:
                df_qr = pd.DataFrame(df_qr)


        

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
    st.subheader("🏛️ Fundamentals")

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
        eps_forecast = get_quarterly_eps(ticker)
        
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
        col3.metric("Aantal medewerkers", format_value(profile.get("fullTimeEmployees")))
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


            # 🔹 Extra ratio's over de jaren
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
    
            df_extra = df_ratio.copy()
            df_extra.rename(columns=col_renames, inplace=True)
            df_extra.rename(columns={"date": "Jaar"}, inplace=True)
    
            for col in col_renames.values():
                if col in df_extra.columns:
                    is_pct = "marge" in col.lower()
                    df_extra[col] = df_extra[col].apply(lambda x: format_value(x, is_percent=is_pct))
    
            met_ratios = [col for col in col_renames.values() if col in df_extra.columns]
            if met_ratios:
                with st.expander("🧮 Extra ratio’s per jaar"):
                    st.dataframe(df_extra.set_index("Jaar")[met_ratios])


        
            # 🔹 Kwartaalratio's
        try:
            df_qr = get_ratios(ticker + "?period=quarter")
            if isinstance(df_qr, list) and len(df_qr) > 0:
                df_qr = pd.DataFrame(df_qr)
                col_renames = {
                    "currentRatio": "Current ratio",
                    "quickRatio": "Quick ratio",
                    "grossProfitMargin": "Bruto marge",
                    "operatingProfitMargin": "Operationele marge",
                    "netProfitMargin": "Netto marge",
                    "returnOnAssets": "Rentabiliteit",
                    "inventoryTurnover": "Omloopsnelheid",
                }
    
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
                        pass
    
                with st.expander("🧮 Ratio’s per kwartaal"):
                    st.dataframe(df_qr.set_index("Kwartaal"))
            else:
                st.info("📭 Geen kwartaalratio's gevonden.")
        except Exception as e:
            st.warning(f"⚠️ Fout bij kwartaalratio's: {e}")

                

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


     # 🔹 EPS-analyse (grafiek met verwacht & werkelijk)
        with st.expander("📈 EPS analyse"):
            if isinstance(eps_quarters, list) and len(eps_quarters) > 0:
                df_epsq = pd.DataFrame(eps_quarters)[["date", "eps"]]
                df_epsq.columns = ["Datum", "EPS"]
                df_epsq["Datum"] = pd.to_datetime(df_epsq["Datum"])
                df_epsq = df_epsq.sort_values("Datum")
                eps_df = df_epsq.copy()
                eps_df["Verwachte EPS"] = None
                if isinstance(eps_forecast, list):
                    for f in eps_forecast:
                        try:
                            d = pd.to_datetime(f.get("date"))
                            est = f.get("estimatedEps")
                            if d and est is not None:
                                eps_df.loc[eps_df["Datum"] == d, "Verwachte EPS"] = float(est)
                        except:
                            pass
                chart_data = eps_df.set_index("Datum")[["EPS", "Verwachte EPS"]]
                st.line_chart(chart_data)
                st.dataframe(chart_data.applymap(format_value))



# ---------------------------
# FMP test full

def test_fmp_endpoint():
    st.subheader("🧪 FMP API Test Tool")

    ticker = st.text_input("Voer een ticker in (bijv. AAPL, ASML, BTCUSD):")
    endpoint = st.selectbox("Kies een API-endpoint", [
        "profile", "key-metrics", "income-statement", "balance-sheet-statement",
        "cash-flow-statement", "ratios", "ratios-ttm", "income-statement-growth",
        "historical-price-full", "financial-growth", "esg-environmental-social-governance-data",
        "market-capitalization", "company-outlook", "executives", "score", "dividend", "stock-news",
        "quote", "number-of-employees", "institutional-holders", "etf-holder", "mutual-fund-holder"
    ])

    if st.button("🔍 Test endpoint"):
        if not ticker:
            st.warning("⚠️ Geen ticker opgegeven.")
            return

        url = f"https://financialmodelingprep.com/api/v3/{endpoint}/{ticker}?apikey={FMP_API_KEY}"
        st.code(url, language='text')

        try:
            response = requests.get(url)
            if response.status_code != 200:
                st.error(f"❌ Fout bij ophalen data: {response.status_code} {response.reason}")
                return
            data = response.json()
            st.json(data if data else {"result": "Leeg antwoord"})
        except Exception as e:
            st.error(f"❌ Fout: {e}")

    
 # ---------------
# yfinance test

@st.cache_data(ttl=1800)  # cache 30 minuten
def get_yf_data(ticker):
    yf_ticker = yf.Ticker(ticker)
    return {
        "info": yf_ticker.info,
        "dividends": yf_ticker.dividends,
        "splits": yf_ticker.splits,
        "financials": yf_ticker.financials,
        "balance_sheet": yf_ticker.balance_sheet,
        "cashflow": yf_ticker.cashflow,
        "recommendations": yf_ticker.recommendations,
    }

def test_yfinance():
    st.subheader("📊 YFinance Test Tool")

    ticker = st.text_input("Voer een ticker in (bijv. AAPL, ASML):", key="yf_ticker")
    if st.button("🔍 Haal YF Data op"):
        try:
            data = get_yf_data(ticker)

            st.write("💡 Informatie:")
            st.json(data["info"])

            st.write("📈 Dividenden:")
            st.dataframe(data["dividends"])

            st.write("📉 Splitsingen:")
            st.dataframe(data["splits"])

            st.write("💵 Financiële data:")
            st.dataframe(data["financials"])

            st.write("💰 Balans:")
            st.dataframe(data["balance_sheet"])

            st.write("📊 Cashflow:")
            st.dataframe(data["cashflow"])

        except Exception as e:
            st.error(f"❌ Fout: {e}")


# toevoeging yfinance test

def test_analyst_data_yf(ticker):
    st.subheader("🧠 Analystenadviezen (Yahoo Finance)")

    try:
        data = get_yf_data(ticker)
        info = data["info"]

        col1, col2, col3 = st.columns(3)
        col1.metric("Aantal analisten", info.get("numberOfAnalystOpinions", "-"))
        col2.metric("Gemiddeld advies", info.get("recommendationMean", "-"))
        col3.metric("Samenvatting", info.get("recommendationKey", "-"))

        st.caption("Legenda advies: 1=Strong Buy, 2=Buy, 3=Hold, 4=Underperform, 5=Sell")

        st.markdown("---")
        st.markdown("📜 Laatste aanbevelingen van analisten:")

        df_rec = data["recommendations"]
        if df_rec is not None and not df_rec.empty:
            st.dataframe(df_rec.tail(10))
        else:
            st.info("Geen aanbevelingen beschikbaar voor deze ticker.")

    except Exception as e:
        st.error(f"Fout bij ophalen van yfinance-analystdata: {e}")























# w



    
