import streamlit as st
import pandas as pd
import numpy as np
from datafund import get_income_statement, get_ratios
from datafund import (
    get_profile, get_key_metrics, get_earning_calendar,
    get_dividend_history, get_quarterly_eps, get_eps_forecast,
    get_historical_dcf, get_historical_prices_yearly
)
import requests
import json
import yfinance as yf
import matplotlib.pyplot as plt

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
            return f"{value / 1:,.2f}"
        return f"{value:,.2f}"
    except:
        return "-"


# kerninfo
def toon_profiel_en_kerninfo(profile, key_metrics, income_statement=None):
    if profile and key_metrics:
        with st.expander("🧾 Bedrijfsprofiel & Kerninfo", expanded=True):
            col1, col2, col3 = st.columns(3)
            col1.metric("Prijs", format_value(profile.get("price")))
            col1.metric("Marktkapitalisatie", format_value(profile.get("mktCap")))
            col2.metric("Dividend (per aandeel)", format_value(profile.get("lastDiv")))
            latest_metrics = key_metrics[0] if key_metrics and isinstance(key_metrics, list) and len(key_metrics) > 0 else {}
            col2.metric("Dividendrendement", format_value(latest_metrics.get("dividendYield", 0), is_percent=True) if latest_metrics else "-")
            col3.metric("Payout Ratio", format_value(latest_metrics.get("payoutRatio", 0), is_percent=True) if latest_metrics else "-")
            col3.metric("Aantal medewerkers", format_value(profile.get("fullTimeEmployees")))

            # ➕ Derde rij uit income_statement
            if income_statement and isinstance(income_statement, list) and len(income_statement) > 0:
                laatste = income_statement[0]  # meest recente
                st.markdown("---")
                col1, col2, col3 = st.columns(3)
                col1.metric("WPA", format_value(laatste.get("eps")))
                col2.metric("Netto winst %", format_value(laatste.get("netIncomeRatio", 0), is_percent=True))
                col3.metric("Bruto winst %", format_value(laatste.get("grossProfitRatio", 0), is_percent=True))

                st.markdown(f"**Beschrijving:** {profile.get('description', '')}")

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

# werkt niet Geen data 
#def merge_price_and_dcf(prices, dcfs):
#    df_prices = pd.DataFrame(prices)
#    df_dcfs = pd.DataFrame(dcfs)
#    df_prices["year"] = pd.to_datetime(df_prices["date"]).dt.year
 #   df_dcfs["year"] = pd.to_datetime(df_dcfs["date"]).dt.year
#    df_merged = pd.merge(df_prices, df_dcfs[["year", "dcf"]], on="year", how="left")
#    df_merged = df_merged.sort_values("year")
#    return df_merged[["year", "close", "high", "low", "dcf"]]

#def plot_price_and_dcf_plotly(df, ticker):
 #   if df.empty:
 #       st.warning("Geen gecombineerde koers en DCF data gevonden.")
 #       return

#    fig = go.Figure()

    # Slotkoers lijn
#    fig.add_trace(go.Scatter(
#        x=df["year"],
#        y=df["close"],
 #       mode="lines+markers",
 #       name="Slotkoers",
#        line=dict(width=2)
#    ))

    # High-Low band (area fill)
#    fig.add_trace(go.Scatter(
  #      x=pd.concat([df["year"], df["year"][::-1]]),
  #      y=pd.concat([df["high"], df["low"][::-1]]),
#        fill="toself",
 #       fillcolor="rgba(0,100,200,0.12)",
#        line=dict(color="rgba(255,255,255,0)"),
  #      hoverinfo="skip",
 #       showlegend=True,
 #       name="Bereik (high/low)"
 #   ))

    # DCF lijn
#    if "dcf" in df.columns:
 #       fig.add_trace(go.Scatter(
#            x=df["year"],
  #          y=df["dcf"],
#            mode="lines+markers",
 #           name="DCF-waarde",
  #          line=dict(dash="dash", color="green", width=2),
#            marker=dict(symbol="square")
   #     ))

 #   fig.update_layout(
 #       title=f"{ticker} | Slotkoers, High/Low en DCF per jaar",
#        xaxis_title="Jaar",
#        yaxis_title="Prijs / DCF ($)",
   #     legend=dict(yanchor="top", y=0.98, xanchor="left", x=0.01),
  #      hovermode="x unified",
  #      template="plotly_white",
#        margin=dict(l=40, r=40, t=60, b=40)
  #  )

#    st.plotly_chart(fig, use_container_width=True)
    



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
        income_statement = get_income_statement(ticker)
        income_data = get_income_statement(ticker)
        ratio_data = get_ratios(ticker)
        earnings = get_earning_calendar(ticker)
        dividends = get_dividend_history(ticker)
        eps_quarters = get_quarterly_eps(ticker)
        eps_forecast = get_eps_forecast(ticker)
#        prices = get_historical_prices_yearly(ticker, years=20)
#        dcfs = get_historical_dcf(ticker, years=20)
#        df_merge = merge_price_and_dcf(prices, dcfs)


        
    except Exception as e:
        st.error(f"❌ Fout bij ophalen van fundamentele data: {e}")
        return

    if not profile:
        st.warning("📭 Geen fundamentele data gevonden voor deze ticker.")
        return

    # ------------------------------------------------------
    # ALLES WAT NU KOMT moet dus binnen de functie blijven!
    # ------------------------------------------------------
    # 🔹 Profiel
#    with st.expander("🧾 Bedrijfsprofiel & Kerninfo", expanded=True):
#        ...

    # 🔹 Profiel
     
    with st.expander("🧾 Bedrijfsprofiel & Kerninfo", expanded=False):
        col1, col2, col3 = st.columns(3)
        col1.metric("Prijs", format_value(profile.get("price")))
        col1.metric("Marktkapitalisatie", format_value(profile.get("mktCap")))
        col2.metric("Dividend (per aandeel)", format_value(profile.get("lastDiv")))
        latest_metrics = key_metrics[0] if key_metrics and isinstance(key_metrics, list) and len(key_metrics) > 0 else {}
        col2.metric("Dividendrendement", format_value(latest_metrics.get("dividendYield", 0), is_percent=True) if latest_metrics else "-")
        col3.metric("Payout Ratio", format_value(latest_metrics.get("payoutRatio", 0), is_percent=True) if latest_metrics else "-")
        col3.metric("Aantal medewerkers", format_value(profile.get("fullTimeEmployees")))
        
        # ➕ Derde rij uit income_statement
        if income_statement and isinstance(income_statement, list) and len(income_statement) > 0:
            laatste = income_statement[0]  # meest recente
            st.markdown("---")
            col1, col2, col3 = st.columns(3)
            col1.metric("WPA", format_value(laatste.get("eps")))
            col2.metric("Netto winst %", format_value(laatste.get("netIncomeRatio", 0), is_percent=True))
            col3.metric("Bruto winst %", format_value(laatste.get("grossProfitRatio", 0), is_percent=True))
        
            st.markdown(f"**Beschrijving:** {profile.get('description', '')}")


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

        
  
    # 🔹 Resultatenrekening plus per jaar! 
        try:
            df_qr = get_quarterly_eps(ticker + "?period=quarter")
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
                        if "marge" in col.lower() or "margin" in col.lower() or "Rate" in col or "%" in col or "Yield" in col:
                            df_qr[col] = df_qr[col].apply(lambda x: format_value(x, is_percent=True))
                        else:
                            df_qr[col] = df_qr[col].apply(format_value)
                    except:
                        pass
    
                with st.expander("🧮 Resultatenrekening per jaar"):
                    st.dataframe(df_qr.set_index("Kwartaal"))
            else:
                st.info("📭 Geen resultaten gevonden.")
        except Exception as e:
            st.warning(f"⚠️ Fout bij resultaten: {e}")

    

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
        # Eerste rij
        col1, col2 = st.columns(2)
        with col1:
            try:
                df_earn_graph = df_income.set_index("date")[["revenue", "netIncome"]].copy()
                df_earn_graph.rename(columns={
                    "revenue": "Omzet",
                    "netIncome": "Netto winst"
                }, inplace=True)
                st.line_chart(df_earn_graph)
                
            except:
                st.info("📉 Geen omzet/winst grafiek beschikbaar.")
        with col2:
            try:
                df_ratio_graph = df_ratio.set_index("date")[["priceEarningsRatio", "returnOnEquity"]].copy()
                df_ratio_graph["returnOnEquity"] *= 100
                df_ratio_graph.rename(columns={
                    "priceEarningsRatio": "K/W",
                    "returnOnEquity": "Rentabiliteit (%)"
                }, inplace=True)
                st.line_chart(df_ratio_graph)
            except:
                st.info("📉 Geen ratio grafiek beschikbaar.")

        # Tweede rij
        col3, col4 = st.columns(2)
        with col3:
            raw_data = key_metrics
            if isinstance(raw_data, list) and len(raw_data) > 0:
                df_ratio2 = pd.DataFrame(raw_data)
                if "date" in df_ratio2.columns:
                    df_ratio2["date"] = pd.to_datetime(df_ratio2["date"])
                    df_ratio2 = df_ratio2.sort_values("date")
                    try:
                        cols1 = [col for col in ["grahamNetNet", "netIncomePerShare"] if col in df_ratio2.columns]
                        if cols1:
                            df_ratio1_graph = df_ratio2.set_index("date")[cols1].copy()
                            df_ratio1_graph.rename(columns={
                                "grahamNetNet": "NCAV Graham",
                                "netIncomePerShare": "WPA/EPS"
                            }, inplace=True)
                            st.line_chart(df_ratio1_graph)
                        else:
                            st.info("📉 Geen NCAV/WPA grafiek data.")
                    except Exception as e:
                        st.info(f"📉 Geen ratio grafiek beschikbaar. ({e})")
                else:
                    st.info("📉 Geen grafiek beschikbaar (kolommen ontbreken).")
            else:
                st.info("Geen grafiek data gevonden voor dit aandeel.")

        with col4:
            raw_data = key_metrics
            if isinstance(raw_data, list) and len(raw_data) > 0:
                df_ratio2 = pd.DataFrame(raw_data)
                if "date" in df_ratio2.columns:
                    df_ratio2["date"] = pd.to_datetime(df_ratio2["date"])
                    df_ratio2 = df_ratio2.sort_values("date")
                    try:
                        df_ratio2_graph = df_ratio2.set_index("date")[["freeCashFlowPerShare", "bookValuePerShare"]].copy()
                        df_ratio2_graph.rename(columns={
                            "freeCashFlowPerShare": "Cash Flow p/a",
                            "bookValuePerShare": "Eigen vermogen p/a"
                        }, inplace=True)
                        st.line_chart(df_ratio2_graph)
                    except Exception as e:
                        st.info(f"📉 Geen grafiek beschikbaar. ({e})")
                else:
                    st.info("📉 Geen grafiek beschikbaar (kolommen ontbreken).")
            else:
                st.info("Geen grafiek data gevonden voor dit aandeel.")



    
            
    # 🔹 EPS per kwartaal - eenvoudige grafiek oud
#    if eps_quarters:
#        df_eps_q = pd.DataFrame(eps_quarters)[["date", "eps"]].copy()
#        df_eps_q["date"] = pd.to_datetime(df_eps_q["date"])
#        df_eps_q = df_eps_q.sort_values("date")
#        df_eps_q.set_index("date", inplace=True)
#        with st.expander("📆 WPA per kwartaal"):
#            st.bar_chart(df_eps_q)
#            st.line_chart(df_eps_q)

     # nieuwe EPS grafiek
        
    with st.expander("📈 EPS analyse"):
        try:
        # -------- Check op aanwezigheid van data --------
            if not (isinstance(eps_quarters, list) and len(eps_quarters) > 0):
                st.info("📭 Geen EPS-data beschikbaar voor deze ticker.")
 #               st.stop()
            if not (isinstance(eps_forecast, list) and len(eps_forecast) > 0):
                eps_forecast = []

        # -------- Dataframes opbouwen --------
            df_epsq = pd.DataFrame(eps_quarters)
            if not {"date", "eps"}.issubset(df_epsq.columns):
                st.info("📭 EPS-data niet compleet voor deze ticker.")
#                st.stop()
            df_epsq = df_epsq[["date", "eps"]]
            df_epsq.columns = ["Datum", "EPS"]
            df_epsq["Datum"] = pd.to_datetime(df_epsq["Datum"])
            df_epsq = df_epsq.sort_values("Datum")

            forecast_cols = ["date", "estimatedEpsAvg", "estimatedEpsLow", "estimatedEpsHigh"]
            if len(eps_forecast) > 0 and all(col in pd.DataFrame(eps_forecast).columns for col in forecast_cols):
                df_forecast = pd.DataFrame(eps_forecast)[forecast_cols].copy()
                df_forecast.columns = ["Datum", "EPS (Avg, est.)", "EPS (Low, est.)", "EPS (High, est.)"]
                df_forecast["Datum"] = pd.to_datetime(df_forecast["Datum"])
                df_forecast = df_forecast.sort_values("Datum")
            else:
                df_forecast = pd.DataFrame(columns=["Datum", "EPS (Avg, est.)", "EPS (Low, est.)", "EPS (High, est.)"])

        # -------- Mergen en plotten --------
            df_all = pd.merge(df_epsq, df_forecast, on="Datum", how="outer").sort_values("Datum")
            df_all.set_index("Datum", inplace=True)
            df_all_plot = df_all.copy()
            df_all_plot['Datum_Grafiek'] = df_all_plot.index.to_period('M').to_timestamp()
            df_plot = df_all_plot.groupby('Datum_Grafiek').mean(numeric_only=True)
            df_plot = df_plot.interpolate(method="linear", limit_direction="both")

            laatste_werkelijke = df_epsq["Datum"].max()
            df_plot.loc[df_plot.index > laatste_werkelijke, "EPS"] = None
            eerste_forecast = df_forecast["Datum"].min() if not df_forecast.empty else None
            for col in ["EPS (Avg, est.)", "EPS (Low, est.)", "EPS (High, est.)"]:
                if eerste_forecast is not None:
                    df_plot.loc[df_plot.index < eerste_forecast, col] = None

            cutoff = pd.Timestamp.now() + pd.DateOffset(years=3)
            df_plot = df_plot[df_plot.index <= cutoff]

            fig, ax = plt.subplots(figsize=(14, 6))
            df_plot["EPS"].plot(ax=ax, marker="o", label="Werkelijke EPS", linewidth=2, color="black")
            df_plot["EPS (Avg, est.)"].plot(ax=ax, marker="o", linestyle="--", label="EPS (Avg, est.)", color="#1e90ff")
            df_plot["EPS (Low, est.)"].plot(ax=ax, marker=".", linestyle=":", label="EPS (Low, est.)", color="#ff6347")
            df_plot["EPS (High, est.)"].plot(ax=ax, marker=".", linestyle=":", label="EPS (High, est.)", color="#2ecc71")
            ax.set_title("Werkelijke EPS en Verwachte EPS (Low/Avg/High)")
            ax.set_ylabel("EPS")
            ax.set_xlabel("Datum")
            ax.legend()
            fig.tight_layout()
            st.pyplot(fig)

        # ----- SAMENVOEGEN PER MAAND VOOR DE TABEL -----
            df_all["Maand"] = df_all.index.to_period('M')
            def last_valid(s):
                s = s.dropna()
                return s.iloc[-1] if not s.empty else None

            df_month = (
                df_all
                .reset_index()
                .groupby("Maand")
                .agg({
                    "Datum": "max",
                    "EPS": last_valid,
                    "EPS (Avg, est.)": last_valid,
                    "EPS (Low, est.)": last_valid,
                    "EPS (High, est.)": last_valid,
                })
            )
           
            def calc_surprise(row):
                verwacht = row["EPS (Avg, est.)"]
                werkelijk = row["EPS"]
                if verwacht == 0 or pd.isna(verwacht):
                    return np.nan
                surprise = (werkelijk - verwacht) / (verwacht) * 100
                if verwacht < 0:
                    surprise = -surprise
                return surprise
            
            df_month["Surprise %"] = df_month.apply(calc_surprise, axis=1)

            df_month = df_month.set_index("Datum")
            df_month = df_month.sort_index(ascending=False)

            kol_volgorde = ["EPS", "Surprise %", "EPS (Avg, est.)", "EPS (Low, est.)", "EPS (High, est.)"]
            def format_surprise(val):
                if pd.isna(val):
                    return "-"
                return f"{val:+.2f}%"
            st.dataframe(
                df_month[kol_volgorde]
                    .assign(**{"Surprise %": df_month["Surprise %"].apply(format_surprise)})
                    .applymap(lambda x: format_value(x) if not isinstance(x, str) or "%" not in x else x)
            )

        except Exception as e:
            st.info("📭 Geen bruikbare EPS-data of fout in verwerking. Foutmelding:")
            st.text(str(e))            

# werkt niet geen data
#    with st.expander("📈 Koers / DCF analyse"):
 #       plot_price_and_dcf_plotly(df_merge, ticker)
    
      
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



    
