import streamlit as st
import yfinance as yf
import pandas as pd
import ta
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timedelta, date, time
import matplotlib.pyplot as plt
from ta.trend import ADXIndicator
import matplotlib.dates as mdates
from yffetch import fetch_data, fetch_data_cached 
from fmpfetch import fetch_data_fmp
from sam_indicator import calculate_sam 
from sat_indicator import calculate_sat 
from adviezen import determine_advice 
from streamlit.components.v1 import html as st_html
from tickers import crypto_tickers 



# matrix based on fixed calendar structure
@st.cache_data(ttl=900)
def genereer_adviesmatrix(ticker, risk_aversion=2):
#def genereer_adviesmatrix(ticker, risk_aversion=2):
  #  toon_matrix = st.toggle("🟩🟥 Toon Adviesmatrix (HTML)", value=False)
#    toon_matrix = st.toggle("📊 Toon Adviesmatrix (HTML)", value=False)
#    if not toon_matrix:
  #      return

    INTERVALLEN = {
        "1wk": {"stappen": 3, "breedte": 10, "hoogte": 240, "label": "Week", "show_text": True},
        "1d": {"stappen": 15, "breedte": 10, "hoogte": 47.7, "label": "Dag", "show_text": True},
        "4h": {"stappen": 45, "breedte": 10, "hoogte": 15.68, "label": "4u", "show_text": True},
        "1h": {"stappen": 135, "breedte": 5, "hoogte": 5, "label": "1u", "show_text": True},
        "15m": {"stappen": 540, "breedte": 2, "hoogte": 1, "label": "15m", "show_text": False}
    }

    INTERVALLEN_CRYPTO = {
        "1wk": {"stappen": 3, "breedte": 10, "hoogte": 895.8, "label": "Week", "show_text": True},
        "1d": {"stappen": 21, "breedte": 10, "hoogte": 127.68, "label": "Dag", "show_text": True},
        "4h": {"stappen": 126, "breedte": 10, "hoogte": 21, "label": "4u", "show_text": True},
        "1h": {"stappen": 504, "breedte": 5, "hoogte": 5, "label": "1u", "show_text": True},
        "15m": {"stappen": 2016, "breedte": 2, "hoogte": 1, "label": "15m", "show_text": False}
    }

    # Markt bepalen
    ticker_lower = ticker.lower()
    eu_suffixes = [
        ".as", ".br", ".pa", ".mc", ".mi", ".de", ".l", ".es", ".pl", ".he",
        ".fi", ".at", ".co", ".sw", ".vi", ".ol", ".st", ".ir", ".ls"
    ]

    if ticker.upper() in crypto_tickers or ticker_lower.endswith("-usd"):
        markt = "crypto"
#    if "btc-" or "-usd" in ticker_lower or ticker_lower.startswith("btc-") or ticker_lower.startswith("eth-"):
#        markt = "crypto"
    elif any(suffix in ticker_lower for suffix in eu_suffixes) or ticker.upper() in ["AEX", "AMX"]:
        markt = "eur"
    else:
        markt = "us"

    matrix = {}
    intervallen_gekozen = INTERVALLEN_CRYPTO if markt == "crypto" else INTERVALLEN

    for interval, specs in intervallen_gekozen.items():
        try:
            stappen = specs["stappen"]
            df = fetch_data_fmp(ticker, interval=interval) if ":" in ticker or ticker.upper() in ["AEX", "AMX"] else fetch_data(ticker, interval=interval)
            df = df.dropna().copy()
            df = calculate_sam(df)
            df = calculate_sat(df)
            df, _ = determine_advice(df, threshold=2, risk_aversion=risk_aversion)
            df = df.dropna(subset=["Advies"])
            df.index = pd.to_datetime(df.index).tz_localize(None)

            waarden = []

            if interval == "1wk":
                df_weeks = df.index.isocalendar()
                df["week"] = df_weeks.week
                df["jaar"] = df_weeks.year

                if markt == "crypto":
                    weekmomenten = sorted(set(df.index.normalize()), reverse=True)
                    weekmomenten = [d for d in weekmomenten if d.weekday() == 0][:stappen]
                else:
                    laatste_maandag = df.index.max().normalize() - pd.Timedelta(days=df.index.max().weekday())
                    weekmomenten = [laatste_maandag - pd.Timedelta(weeks=i) for i in range(stappen)]

                for week_start in weekmomenten:
                    week_nr = week_start.isocalendar().week
                    jaar = week_start.isocalendar().year
                    match = df[(df["week"] == week_nr) & (df["jaar"] == jaar)]
                    advies = match["Advies"].values
                    kleur = "🟩" if "Kopen" in advies else "🟥" if "Verkopen" in advies else "⬛"
                    tekst = week_start.strftime("%Y-%m-%d") if specs["show_text"] else ""
                    waarden.append({"kleur": kleur, "tekst": tekst})

            elif interval == "1d":
                laatste_datum = df.index.max().normalize()
                dagen = []
                while len(dagen) < stappen:
                    if markt == "crypto" or laatste_datum.weekday() < 5:
                        dagen.append(laatste_datum)
                    laatste_datum -= pd.Timedelta(days=1)
                dagen = sorted(dagen, reverse=True)

                for dag in dagen:
                    advies = df.loc[df.index.normalize() == dag, "Advies"].values
                    kleur = "🟩" if "Kopen" in advies else "🟥" if "Verkopen" in advies else "⬛"

                    dagnaam = dag.strftime("%A")  # Volledige dagnaam, bijv. "Sunday"
                    datum = dag.strftime("%Y-%m-%d")
    
                    # Probeer de close waarde op te halen van de desbetreffende dag
                    try:
                        koers = df.loc[df.index.normalize() == dag, "Close"].iloc[-1]
                        koers_str = f"${koers:,.2f}"
                    except Exception:
                        koers_str = "n/a"

                    if specs["show_text"]:
                        tekst = f"{dagnaam}<br>{datum}<br>{koers_str}"
                    else:
                        tekst = ""

                    waarden.append({"kleur": kleur, "tekst": tekst})

   
            else:
                stap = pd.Timedelta("4h") if interval == "4h" else pd.Timedelta("1h") if interval == "1h" else pd.Timedelta("15min")
                laatste_dag = df.index.max().normalize()
                dagen = []
                blokjes_per_dag = (6 if interval == "4h" else 24 if interval == "1h" else 96) if markt == "crypto" else (3 if interval == "4h" else 9 if interval == "1h" else 36)

                while len(dagen) < int(stappen / blokjes_per_dag):
                    if markt == "crypto" or laatste_dag.weekday() < 5:
                        dagen.append(laatste_dag)
                    laatste_dag -= pd.Timedelta(days=1)
                dagen = sorted(dagen, reverse=True)

                for dag in dagen:
                    start_uur = 7 if markt == "eur" else 12 if markt == "us" else 0
                    tijdvakken = []
                    eind_uur = 24 if markt == "crypto" else (12 if interval == "4h" else 9)

                    if interval == "4h":
                        tijdvakken = [dag + pd.Timedelta(hours=h) for h in range(start_uur, start_uur + eind_uur, 4)]
                    elif interval == "1h":
                        tijdvakken = [dag + pd.Timedelta(hours=h) for h in range(start_uur, start_uur + eind_uur)]
                    elif interval == "15m":
                        for uur in range(start_uur, start_uur + eind_uur):
                            for kwart in range(0, 60, 15):
                                tijdstip = dag + pd.Timedelta(hours=uur, minutes=kwart)
                                tijdvakken.append(tijdstip)

                    tijdvak_entries = []
                    for ts in tijdvakken:
                        df_sub = df[(df.index >= ts) & (df.index < ts + stap)]
                        advies = df_sub["Advies"].values
                        kleur = "🟩" if "Kopen" in advies else "🟥" if "Verkopen" in advies else "⬛"
                        tekst = ts.strftime("%H:%M") if specs["show_text"] else ""
                        tijdvak_entries.append((ts, {"kleur": kleur, "tekst": tekst}))

                    tijdvak_entries = sorted(tijdvak_entries, key=lambda x: x[0], reverse=True)
                    waarden.extend([entry for _, entry in tijdvak_entries])

            matrix[interval] = waarden

        except Exception as e:
            st.warning(f"⚠️ Fout bij interval {interval}: {e}")
            matrix[interval] = [{"kleur": "⚠️", "tekst": ""} for _ in range(int(stappen))]


    return matrix, intervallen_gekozen





#             for dag in dagen:
    #                advies = df.loc[df.index.normalize() == dag, "Advies"].values
    #                kleur = "🟩" if "Kopen" in advies else "🟥" if "Verkopen" in advies else "⬛"
     #               tekst = dag.strftime("%A")<br>dag.strftime("%Y-%m-%d")<br>{ if specs["show_text"] else ""
    #                waarden.append({"kleur": kleur, "tekst": tekst})



#           matrix[interval] = [{"kleur": "⚠️", "tekst": ""} for _ in range(specs.get("stappen", 10))]
 #       except Exception as e:
  #          st.warning(f"\u26A0\ufe0f Fout bij interval {interval}: {e}")
   #         matrix[interval] = [{"kleur": "\u26A0\ufe0f", "tekst": ""} for _ in range(specs.get("stappen", 10))]

#    st.write(f"Interval: {interval} | kleur: {kleur} | tekst: {tekst}")
    # Debug: controleer alle intervallen en adviesresultaten
#    st.write("🔍 Adviesmatrix Debug Output")

#    for interval, waarden_lijst in matrix.items():
 #       st.write(f"📈 Interval: {interval} | Aantal blokken: {len(waarden_lijst)}")

 #       for i, entry in enumerate(waarden_lijst[:5]):  # Max 5 blokjes per interval voor overzicht
  #          kleur = entry["kleur"]
    #        tekst = entry["tekst"]
   #         st.write(f"  Blok {i+1}: kleur = {kleur} | tekst = {tekst}")

  #      if len(waarden_lijst) == 0:
  #          st.warning(f"⚠️ Geen waarden in matrix voor interval {interval}!")





