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



# 📆 Periode voor SAM-grafiek op basis van interval
def bepaal_grafiekperiode(interval):
    if interval == "15m":
        return timedelta(days=10)        # 7 dagen à ~96 candles per dag = ±672 punten
    elif interval == "1h":
        return timedelta(days=75)        # 5 dagen à ~7 candles = ±35 punten
    elif interval == "4h":
        return timedelta(days=120)       # 3 maanden à ~6 candles per week
    elif interval == "1d":
        return timedelta(days=120)      # 180=6 maanden à 1 candle per dag
    elif interval == "1wk":
        return timedelta(weeks=240)     # 104=2 jaar aan weekly candles (104 candles)
    elif interval == "1mo":
        return timedelta(weeks=520)     # 520=0 jaar aan monthly candles (120 candles)
    else:
        return timedelta(weeks=260)     # Fallback = 5 jaar
# periode voor koersgrafiek 
#def bepaal_grafiekperiode2(interval):
#    if interval == "15m":
#        return timedelta(days=7)
 #   elif interval == "1h":
 #       return timedelta(days=5)
 #   elif interval == "4h":
 #       return timedelta(days=90)
#    elif interval == "1d":
#        return timedelta(days=180)
 #   else:
  #      return timedelta(weeks=260)  # bijv. bij weekly/monthly data

# aanvullende overlay grafiek
def plot_overlay_grafiek(df, ticker_name, interval):
    toon_overlay = st.toggle("📊 Toon gecombineerde overlaygrafiek (Koers + SAM + SAT)", value=False)
    if not toon_overlay:
        return

    grafiek_periode = bepaal_grafiekperiode(interval)
    cutoff_datum = df.index.max() - grafiek_periode
    df_plot = df[df.index >= cutoff_datum].copy().reset_index()

    if df_plot.empty:
        st.warning("Geen data beschikbaar voor de gekozen periode.")
        return

    # Bepaal naam van datumkolom (eerste kolom na reset_index)
    datumkolom = df_plot.columns[0]  # meestal 'Date' of 'index'
    df_plot["x"] = range(len(df_plot))

    # --- Plot opstellen ---
    fig, ax1 = plt.subplots(figsize=(14, 6))

    # 1️⃣ Linkeras: Koers
    ax1.plot(df_plot["x"], df_plot["Close"], color="black", linewidth=2, label="Koers")
    ax1.set_ylabel("Koers")
    ax1.grid(True)

    # 2️⃣ Rechteras: SAM + SAT
    ax2 = ax1.twinx()
    ax2.set_ylim(-4.25, 4.25)
    ax2.set_ylabel("Indicatorwaarden")

    kleuren = ["green" if val >= 0 else "red" for val in df_plot["SAM"]]
    ax2.bar(df_plot["x"], df_plot["SAM"], color=kleuren, alpha=0.3, label="SAM")
    ax2.plot(df_plot["x"], df_plot["Trend"], color="orange", linewidth=1.2, marker='.', markersize=3, label="SAM Trend")
    ax2.plot(df_plot["x"], df_plot["SAT_Stage"], color="purple", linestyle="--", linewidth=1.2, alpha=0.5, label="SAT Stage")
    ax2.plot(df_plot["x"], df_plot["SAT_Trend"], color="blue", linewidth=1.5, marker='.', markersize=3, label="SAT Trend")

    # --- X-as slimme labels ---
    labels = df_plot[datumkolom].dt.strftime('%Y-%m-%d')
    step = max(1, len(df_plot) // 12)
    ax1.set_xticks(df_plot["x"][::step])
    ax1.set_xticklabels(labels[::step], rotation=45, ha="right")
    ax1.set_xlim(df_plot["x"].min(), df_plot["x"].max())

    # Legenda combineren
    handles1, labels1 = ax1.get_legend_handles_labels()
    handles2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(handles1 + handles2, labels1 + labels2, loc="upper left")

    ax1.set_title("Overlaygrafiek: Koers + SAM + SAT")
    fig.tight_layout()
    st.pyplot(fig)
    
    
# --- Koersgrafiek ---
def plot_koersgrafiek(df, ticker_name, interval):
    toon_koersgrafiek = st.toggle("\U0001F4C8 Toon koersgrafiek", value=False)
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
    

# --- SAM en Trend ---
def plot_sam_trend(df, interval):
    st.subheader("Grafiek met SAM en Trend")
    grafiek_periode = bepaal_grafiekperiode(interval)
    cutoff_datum = df.index.max() - grafiek_periode
    df_grafiek = df[df.index >= cutoff_datum].copy().reset_index()

    # Zorg dat we weten hoe de datumkolom heet
    datumkolom = df_grafiek.columns[0]  # meestal 'Date' of 'index'
    df_grafiek["x"] = range(len(df_grafiek))
    kleuren = ["green" if val >= 0 else "red" for val in df_grafiek["SAM"]]

    fig, ax = plt.subplots(figsize=(14, 6))
    ax.bar(df_grafiek["x"], df_grafiek["SAM"], color=kleuren, alpha=0.6, label="SAM")
    ax.plot(df_grafiek["x"], df_grafiek["Trend"], color="blue", linewidth=1.5, marker='.', markersize=3, label="Trend")

    if "SAT_Stage" in df_grafiek.columns:
        ax.plot(df_grafiek["x"], df_grafiek["SAT_Stage"], color="gray", linewidth=1.2, linestyle="--", marker='.', markersize=2, alpha=0.5)

    ax.axhline(y=0, color="black", linewidth=1, linestyle="--")
    ax.set_ylim(-4.5, 4.5)
    ax.set_xlim(df_grafiek["x"].min(), df_grafiek["x"].max())

    # Slimme labels
    labels = df_grafiek[datumkolom].dt.strftime('%Y-%m-%d')
    step = max(1, len(df_grafiek) // 12)
    ax.set_xticks(df_grafiek["x"][::step])
    ax.set_xticklabels(labels[::step], rotation=45, ha="right")

    ax.set_title("SAM-indicator en Trendlijn")
    ax.set_ylabel("Waarde")
    ax.legend()
    fig.tight_layout()
    st.pyplot(fig)

# --- SAT grafiek (tijdelijk uitgeschakeld) ---
def plot_sat_debug(df, interval):
    grafiek_periode = bepaal_grafiekperiode(interval)
    cutoff_datum = df.index.max() - grafiek_periode
    df_sat = df[df.index >= cutoff_datum].copy().reset_index()

    if df_sat.empty:
        st.warning("Geen SAT-data beschikbaar voor de gekozen periode.")
        return

    datumkolom = df_sat.columns[0]  # meestal 'Date' of 'index'
    df_sat["x"] = range(len(df_sat))

    fig, ax = plt.subplots(figsize=(14, 6))

    # Bereken bar spacing
    spacing = 1
    if len(df_sat) > 1:
        spacing = np.median(np.diff(df_sat["x"]))
    bar_width = spacing * 0.45  # 45% van afstand tussen punten

    # Bars tekenen
    ax.bar(df_sat["x"], df_sat["SAT_Stage"], width=bar_width, color="black", label="SAT Stage", alpha=0.6)

    # SAT Trend tekenen met markers
    ax.plot(df_sat["x"], df_sat["SAT_Trend"], color="blue", linewidth=1.5, marker='.', markersize=3, label="SAT Trend")

    # X-as labels instellen
    labels = df_sat[datumkolom].dt.strftime('%Y-%m-%d')
    step = max(1, len(df_sat) // 12)
    ax.set_xticks(df_sat["x"][::step])
    ax.set_xticklabels(labels[::step], rotation=45, ha="right")

    ax.axhline(y=0, color="gray", linewidth=1, linestyle="--")
    ax.set_xlim(df_sat["x"].min(), df_sat["x"].max())
    ax.set_ylim(-2.25, 2.25)
    ax.set_ylabel("Waarde")
    ax.set_title("SAT-indicator en Trendlijn")
    ax.legend()
    fig.tight_layout()
    st.pyplot(fig)


# matrix based on fixed calendar structure
# matrix based on fixed calendar structure
def toon_adviesmatrix_html(ticker, risk_aversion=2):
    toon_matrix = st.toggle("📊 Toon Adviesmatrix (HTML)", value=False)
    if not toon_matrix:
        return

    INTERVALLEN = {
        "1wk": {"stappen": 3, "breedte": 10, "hoogte": 200, "label": "Week", "show_text": True},
        "1d": {"stappen": 15, "breedte": 10, "hoogte": 40, "label": "Dag", "show_text": True},
        "4h": {"stappen": 45, "breedte": 10, "hoogte": 13.5, "label": "4u", "show_text": True},
        "1h": {"stappen": 120, "breedte": 5, "hoogte": 5, "label": "1u", "show_text": True},
        "15m": {"stappen": 480, "breedte": 2, "hoogte": 1, "label": "15m", "show_text": False}
    }

    # Markt bepalen
    ticker_lower = ticker.lower()
    if "crypto" in ticker_lower or ticker_lower.startswith("btc") or ticker_lower.startswith("eth"):
        markt = "crypto"
    elif ".as" in ticker_lower or ticker.upper() in ["AEX", "AMX"]:
        markt = "eur"
    else:
        markt = "us"

    matrix = {}

    for interval, specs in INTERVALLEN.items():
        stappen = specs["stappen"]
        try:
            df = fetch_data_fmp(ticker, interval=interval) if ":" in ticker or ticker.upper() in ["AEX", "AMX"] else fetch_data(ticker, interval=interval)
            df = df.dropna().copy()
            df = calculate_sam(df)
            df = calculate_sat(df)
            df, _ = determine_advice(df, threshold=2, risk_aversion=risk_aversion)
            df = df.dropna(subset=["Advies"])
            df.index = pd.to_datetime(df.index).tz_localize(None)

            waarden = []

            if interval == "1wk":
                laatste_maandag = df.index.max().normalize() - pd.Timedelta(days=df.index.max().weekday())
                weekmomenten = [laatste_maandag - pd.Timedelta(weeks=i) for i in range(stappen)]
                weekmomenten = sorted(weekmomenten, reverse=True)

                df_weeks = df.index.isocalendar()
                df["week"] = df_weeks.week
                df["jaar"] = df_weeks.year

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
                    if laatste_datum.weekday() < 5:
                        dagen.append(laatste_datum)
                    laatste_datum -= pd.Timedelta(days=1)
                dagen = sorted(dagen, reverse=True)

                for dag in dagen:
                    advies = df.loc[df.index.normalize() == dag, "Advies"].values
                    kleur = "🟩" if "Kopen" in advies else "🟥" if "Verkopen" in advies else "⬛"
                    tekst = dag.strftime("%a")[:2] if specs["show_text"] else ""
                    waarden.append({"kleur": kleur, "tekst": tekst})

            else:
                stap = pd.Timedelta("4h") if interval == "4h" else pd.Timedelta("1h") if interval == "1h" else pd.Timedelta("15min")

                laatste_dag = df.index.max().normalize()
                dagen = []
                blokjes_per_dag = 3 if interval == "4h" else 8 if interval == "1h" else 32
                while len(dagen) < int(stappen / blokjes_per_dag):
                    if laatste_dag.weekday() < 5:
                        dagen.append(laatste_dag)
                    laatste_dag -= pd.Timedelta(days=1)
                dagen = sorted(dagen, reverse=True)

                waarden = []

                for dag in dagen:
                    if markt == "eur":
                        start_uur = 7
                    elif markt == "us":
                        start_uur = 13:30
                    else:
                        start_uur = 0

                    tijdvakken = []
                    if interval == "4h":
                        tijdvakken = [dag + pd.Timedelta(hours=h) for h in range(start_uur, start_uur + 12, 4)]
                    elif interval == "1h":
                        tijdvakken = [dag + pd.Timedelta(hours=h) for h in range(start_uur, start_uur + 8)]
                    elif interval == "15m":
                        for uur in range(start_uur, start_uur + 8):
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
            
                        
            
                
        
    # ─────────────────────────────────────────────
    # HTML rendering
    html = "<div style='font-family: monospace;'>"
    html += "<div style='display: flex;'>"

    for interval, specs in INTERVALLEN.items():
        waarden = matrix[interval]
        blokken_html = "<div style='margin-right: 12px;'>"
        blokken_html += f"<div style='text-align: center; font-weight: bold; margin-bottom: 6px;'>{interval}</div>"
        for entry in waarden:
            kleur = entry["kleur"]
            tekst = entry["tekst"]
            blok_html = f"""
                <div style='
                    width: {specs['breedte'] * 8}px;
                    height: {specs['hoogte'] * 3}px;
                    background-color: {"#2ecc71" if kleur == "🟩" else "#e74c3c" if kleur == "🟥" else "#bdc3c7"};
                    color: white;
                    text-align: center;
                    font-size: 11px;
                    margin-bottom: 1px;
                    border-radius: 2px;
                '>{tekst}</div>
            """
            blokken_html += blok_html
        blokken_html += "</div>"
        html += blokken_html

    html += "</div></div>"
    st_html(html, height=600, scrolling=True)
    

                       
    


# matrix old working
def toon_adviesmatrix_html_old(ticker, risk_aversion=2):
    toon_matrix = st.toggle("📊 Toon gecombineerde Adviesmatrix (HTML)", value=False)
    if not toon_matrix:
        return

    INTERVALLEN = {
        "1wk": {"stappen": 3, "breedte": 10, "hoogte": 160, "label": "Week", "show_text": True},
        "1d": {"stappen": 15, "breedte": 10, "hoogte": 32, "label": "Dag", "show_text": True},
        "4h": {"stappen": 30, "breedte": 10, "hoogte": 16, "label": "4u", "show_text": True},
        "1h": {"stappen": 120, "breedte": 5, "hoogte": 4, "label": "1u", "show_text": True},
        "15m": {"stappen": 480, "breedte": 2, "hoogte": 1, "label": "15m", "show_text": False}
    }

    matrix = {}

    for interval, specs in INTERVALLEN.items():
        stappen = specs["stappen"]
        try:
            if ":" in ticker or ticker.upper() in ["AEX", "AMX"]:
                df = fetch_data_fmp(ticker, interval=interval)
            else:
                df = fetch_data(ticker, interval=interval)

            df = df.dropna().copy()
            df = calculate_sam(df)
            df = calculate_sat(df)
            df, _ = determine_advice(df, threshold=2, risk_aversion=risk_aversion)
            df = df.dropna(subset=["Advies"])

            df = df[::-1]  # jongste bovenaan

            waarden = []

            if interval == "1d":
                # Aanvullen met lege werkdagen
                laatste_datum = df.index.max().normalize()
                gewenste_dagen = []
                while len(gewenste_dagen) < stappen:
                    if laatste_datum.weekday() < 5:
                        gewenste_dagen.append(laatste_datum)
                    laatste_datum -= timedelta(days=1)

                df.index = df.index.normalize()
                for dag in gewenste_dagen:
                    if dag in df.index:
                        advies = df.loc[dag]["Advies"]
                        kleur = "🟩" if advies == "Kopen" else "🟥"
                        tekst = dag.strftime("%a")[:2] if specs["show_text"] else ""
                    else:
                        kleur = "⬛"
                        tekst = dag.strftime("%a")[:2] if specs["show_text"] else ""
                    waarden.append({"kleur": kleur, "tekst": tekst})

            else:
                df = df.iloc[:stappen]
                for i in range(stappen):
                    if i >= len(df):
                        waarden.append({"kleur": "⬛", "tekst": ""})
                        continue
                    advies = df.iloc[i]["Advies"]
                    datum = df.index[i]
                    kleur = "🟩" if advies == "Kopen" else "🟥"

                    if interval == "1wk":
                        tekst = datum.strftime("%Y-%m-%d")
                    elif interval in ["4h", "1h"]:
                        tekst = datum.strftime("%H:%M")
                    elif interval == "15m":
                        tekst = str(i % 4 + 1)
                    else:
                        tekst = ""
                    waarden.append({"kleur": kleur, "tekst": tekst if specs["show_text"] else ""})

            matrix[interval] = waarden

        except Exception as e:
            matrix[interval] = [{"kleur": "⚠️", "tekst": ""}] * specs["stappen"]
            st.warning(f"Fout bij {interval}: {e}")

    # HTML-rendering
    html = "<div style='font-family: monospace;'>"
    html += "<div style='display: flex;'>"

    for interval, specs in INTERVALLEN.items():
        waarden = matrix[interval]
        blokken_html = "<div style='margin-right: 12px;'>"
        blokken_html += f"<div style='text-align: center; font-weight: bold; margin-bottom: 6px;'>{interval}</div>"

        for entry in waarden:
            kleur = entry["kleur"]
            tekst = entry["tekst"]
            bg = "#2ecc71" if kleur == "🟩" else "#e74c3c" if kleur == "🟥" else "#bdc3c7"
            blok_html = f"""
                <div style='
                    width: {specs['breedte'] * 8}px;
                    height: {specs['hoogte'] * 3}px;
                    background-color: {bg};
                    color: white;
                    text-align: center;
                    font-size: 11px;
                    margin-bottom: 1px;
                    border-radius: 3px;
                '>{tekst}</div>
            """
            blokken_html += blok_html

        blokken_html += "</div>"
        html += blokken_html

    html += "</div></div>"

    st_html(html, height=600, scrolling=True)
    

            
                



# matrix
def toon_adviesmatrix_html_kut(ticker, risk_aversion=2):
    toon_matrix = st.toggle("📊 Toon gecombineerde Adviesmatrix (HTML)", value=False)
    if not toon_matrix:
        return

    INTERVALLEN = {
        "1wk": {"stappen": 3, "breedte": 10, "hoogte": 160, "label": "Week", "show_text": True},
        "1d": {"stappen": 15, "breedte": 10, "hoogte": 32, "label": "Dag", "show_text": True},
        "4h": {"stappen": 30, "breedte": 10, "hoogte": 16, "label": "4u", "show_text": True},
        "1h": {"stappen": 120, "breedte": 5, "hoogte": 4, "label": "1u", "show_text": True},
        "15m": {"stappen": 480, "breedte": 2, "hoogte": 1, "label": "15m", "show_text": False}
    }

    matrix = {}

    for interval, specs in INTERVALLEN.items():
        stappen = specs["stappen"]
        try:
            if ":" in ticker or ticker.upper() in ["AEX", "AMX"]:
                df = fetch_data_fmp(ticker, interval=interval)
            else:
                df = fetch_data(ticker, interval=interval)

            df = df.dropna().copy()
            if len(df) < stappen:
                matrix[interval] = [{"kleur": "🟨", "tekst": ""}] * stappen
                continue

            df = calculate_sam(df)
            df = calculate_sat(df)
            df, _ = determine_advice(df, threshold=2, risk_aversion=risk_aversion)

            df = df.dropna(subset=["Advies"])
            df = df.iloc[-stappen:].copy()
            df = df[::-1]

            waarden = []
            for i in range(stappen):
                if i >= len(df):
                    waarden.append({"kleur": "⬛", "tekst": ""})
                    continue
                advies = df.iloc[i]["Advies"]
                datum = df.index[i]
                kleur = "🟩" if advies == "Kopen" else "🟥"

                if interval == "1wk":
                    tekst = datum.strftime("%Y-%m-%d")
                elif interval == "1d":
                    tekst = datum.strftime("%a")[:2]
                elif interval in ["4h", "1h"]:
                    tekst = datum.strftime("%H:%M")
                elif interval == "15m":
                    tekst = str(i % 4 + 1)
                else:
                    tekst = ""

                waarden.append({"kleur": kleur, "tekst": tekst if specs["show_text"] else ""})

            matrix[interval] = waarden

        except Exception as e:
            matrix[interval] = [{"kleur": "⚠️", "tekst": ""}] * specs["stappen"]
            st.warning(f"Fout bij {interval}: {e}")

    html = "<div style='font-family: monospace;'>"
    html += "<div style='display: flex;'>"

    for interval, specs in INTERVALLEN.items():
        waarden = matrix[interval]
        blokken_html = "<div style='margin-right: 12px;'>"
        blokken_html += f"<div style='text-align: center; font-weight: bold; margin-bottom: 6px;'>{interval}</div>"

        # Voor 15m wrapping, anders standaard kolom
        wrap_style = "flex-wrap: wrap;" if interval == "15m" else "flex-direction: column;"
        blokken_html += f"<div style='display: flex; {wrap_style} width: {specs['breedte'] * 8 + 4}px;'>"

        for entry in waarden:
            kleur = entry["kleur"]
            tekst = entry["tekst"]
            bg_color = (
                "#2ecc71" if kleur == "🟩"
                else "#e74c3c" if kleur == "🟥"
                else "#bdc3c7" if kleur == "🟨"
                else "#34495e" if kleur == "⬛"
                else "#f1c40f" if kleur == "⚠️"
                else "#7f8c8d"
            )
            blok_html = f"""
                <div style='
                    width: {specs['breedte'] * 8}px;
                    height: {specs['hoogte'] * 3}px;
                    background-color: {bg_color};
                    color: white;
                    text-align: center;
                    font-size: 11px;
                    margin: 1px;
                    border-radius: 3px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                '>{tekst}</div>
            """
            blokken_html += blok_html

        blokken_html += "</div></div>"
        html += blokken_html

    html += "</div></div>"

    st.markdown(html, unsafe_allow_html=True)
    

        
    
        



    
# Aanpasbare lijst van intervallen
def toon_adviesmatrix_markdown_flex(ticker, risk_aversion=2):
    toon_matrix = st.toggle("📊 Toon automatische Adviesmatrix (Flex-weergave)", value=False)
    if not toon_matrix:
        return

    st.subheader("📊 Automatische Adviesmatrix")
    st.markdown("De matrix toont adviezen per interval per dag (jongste boven). Visueel geschaald naar tijdsresolutie.")

    interval_specs = {
        "1wk": {"stappen": 3, "breedte": 16},     # 1 advies per week, herhalen per 5 dagen
        "1d":  {"stappen": 15, "breedte": 8},      # 1 advies per dag
        "4h":  {"stappen": 30, "breedte": 16},     # 2 per dag
        "1h":  {"stappen": 120, "breedte": 32},    # 8 per dag
        "15m": {"stappen": 480, "breedte": 64}     # 32 per dag
    }

    dagen = 15  # 3 weken
    matrix = {interval: ["⬛"] * dagen for interval in interval_specs}
    submatrix = {interval: ["⬛"] * interval_specs[interval]["stappen"] for interval in interval_specs}

    for interval, specs in interval_specs.items():
        stappen = specs["stappen"]
        try:
            # Data ophalen
            if ":" in ticker or ticker.upper() in ["AEX", "AMX"]:
                df = fetch_data_fmp(ticker, interval=interval)
            else:
                df = fetch_data(ticker, interval=interval)

            df = df.dropna().copy()
            if len(df) < stappen:
                continue

            df = calculate_sam(df)
            df = calculate_sat(df)
            df, _ = determine_advice(df, threshold=2, risk_aversion=risk_aversion)

            adviezen = df["Advies"].dropna().iloc[-stappen:].tolist()
            adviezen = adviezen[::-1]  # Laatste eerst

            kleuren = []
            for advies in adviezen:
                if advies == "Kopen":
                    kleuren.append("🟩")
                elif advies == "Verkopen":
                    kleuren.append("🟥")
                else:
                    kleuren.append("🟨")
            while len(kleuren) < stappen:
                kleuren.append("⬛")

            submatrix[interval] = kleuren

        except Exception as e:
            st.warning(f"Fout bij {interval}: {e}")
            submatrix[interval] = ["⚠️"] * specs["stappen"]

    # Weekadvies herhalen 5 dagen lang
    if "1wk" in submatrix:
        herhaald = []
        for kleur in submatrix["1wk"]:
            herhaald.extend([kleur] * 5)
        matrix["1wk"] = herhaald[::-1][:dagen]

    # Dagadvies (rechtstreeks)
    matrix["1d"] = submatrix["1d"][::-1][:dagen]

    # 4h, 1h, 15m -> splits in groepen per dag
    for interval in ["4h", "1h", "15m"]:
        kleuren = submatrix[interval][::-1]
        per_dag = int(len(kleuren) / dagen)
        matrix[interval] = [kleuren[i*per_dag:(i+1)*per_dag] for i in range(dagen)]

    html += "</div></div>"

    st_html(html, height=600, scrolling=True)





# INTERVALLEN = ["1wk", "1d", "4h", "1h", "15min"]
def toon_adviesmatrix_markdown(ticker, risk_aversion=2):
    toon_matrix = st.toggle("📊 Toon automatische Adviesmatrix (Markdown-versie)", value=False)
    if not toon_matrix:
        return

    st.subheader("📊 Automatische Adviesmatrix")
    st.markdown("De matrix toont adviezen per interval (jongste data bovenaan).")

    interval_specs = {
        "1wk": {"stappen": 5, "breedte": 2},
        "1d": {"stappen": 5, "breedte": 2},
        "4h": {"stappen": 10, "breedte": 4},
        "1h": {"stappen": 40, "breedte": 8},
        "15m": {"stappen": 160, "breedte": 16},
    }

    matrix = {}

    for interval, specs in interval_specs.items():
        stappen = specs["stappen"]
        try:
            # Data ophalen
            if ":" in ticker or ticker.upper() in ["AEX", "AMX"]:
                df = fetch_data_fmp(ticker, interval=interval)
            else:
                df = fetch_data(ticker, interval=interval)

            df = df.dropna().copy()
            if len(df) < stappen:
                matrix[interval] = ["🟨"] * stappen
                continue

            df = calculate_sam(df)
            df = calculate_sat(df)
            df, _ = determine_advice(df, threshold=2, risk_aversion=risk_aversion)

            adviezen = df["Advies"].dropna().iloc[-stappen:].tolist()
            adviezen = adviezen[::-1]  # Laatste eerst

            kleuren = []
            for advies in adviezen:
                if advies == "Kopen":
                    kleuren.append("🟩")
                elif advies == "Verkopen":
                    kleuren.append("🟥")
                else:
                    kleuren.append("🟨")
            # Aanvullen als te kort
            while len(kleuren) < stappen:
                kleuren.append("⬛")

            matrix[interval] = kleuren

        except Exception as e:
            matrix[interval] = ["⚠️"] * specs["stappen"]
            st.warning(f"Fout bij {interval}: {e}")

    # 🧱 Weergave op schaal: [2,2,4,8,16]
    max_stappen = max(spec["stappen"] for spec in interval_specs.values())
    rijen = []

    for i in range(max_stappen):
        rij = ""
        for interval, spec in interval_specs.items():
            blokken = spec["breedte"]
            waarden = matrix.get(interval, [])
            if i < len(waarden):
                rij += waarden[i] * blokken
            else:
                rij += "⬛" * blokken
        rijen.append(rij)

    # 🔁 Omgekeerd (jongste boven)
    rijen = rijen[::-1]

    st.markdown("```\n" + "\n".join(rijen) + "\n```")
    
#def toon_adviesmatrix_automatisch(ticker, risk_aversion):
#    toon_matrix = st.toggle("🧮 Toon automatische Adviesmatrix", value=False)
#    if not toon_matrix:
#        return

#    st.subheader("📊 Automatische Adviesmatrix")

#    intervallen = {
 #       "1wk": 3,    # laatste 3 weken
#        "1d": 15,    # laatste 3 dagen
#        "4h": 30,    # laatste 15 dagen
#        "1h": 60,    # laatste 30 dagen
 #       "15m": 96    # laatste 4 dagen
#    }

#    matrix_data = {}

#    for interval, stappen in intervallen.items():
#        try:
            # Kies juiste fetch functie op basis van ticker
#            if ":" in ticker or ticker.upper() in ["AEX", "AMX"]:
#                df = fetch_data_fmp(ticker, interval=interval)
 #           else:
 #               df = fetch_data(ticker, interval=interval)

#            df = df.dropna().copy()
 #           if df.empty or len(df) < stappen:
  #              matrix_data[interval] = ["⛔"] * stappen
  #              continue

            # Advies berekenen met meegegeven risk_aversion
#            df = calculate_sam(df)
#            df = calculate_sat(df)
  #          df = determine_advice(df, threshold=2, risk_aversion=risk_aversion)

#            waarden = []
 #           for i in range(-stappen, 0):
 #               try:
 #                   advies = df.iloc[i]["Advies"]
 #                   kleur = "🟩" if advies == "Kopen" else "🟥"
  #              except:
  #                  kleur = "❓"
  #              waarden.append(kleur)

 #           matrix_data[interval] = waarden

#        except Exception as e:
#            matrix_data[interval] = ["⚠️"] * stappen
#            st.warning(f"Fout bij {interval}: {e}")

#    matrix_df = pd.DataFrame(matrix_data).T
#    matrix_df.columns = [f"⏱️-{i+1}" for i in range(matrix_df.shape[1])]
#    matrix_df.index.name = "Interval"

#    st.dataframe(matrix_df, use_container_width=True)
    

# ➕ y-as: bepaal min/max + marge
#    try:
#        koers_values = df_koers["Close"].astype(float).dropna()
#        if not koers_values.empty:
#            koers_min = koers_values.min()
 #           koers_max = koers_values.max()
  #          marge = (koers_max - koers_min) * 0.05
   #         ax.set_ylim(koers_min - marge, koers_max + marge)
 #       else:
 #           st.warning("Geen geldige koersdata om y-as limieten op te baseren.")
#    except Exception as e:
#        st.warning(f"Kon y-as limieten niet instellen: {e}")





# ⏱ gecompliceerde koersgrafiek werkt niet geheel
# bepaal data weeergaveperiode op basis van interval
#grafiek_periode = bepaal_grafiekperiode(interval)

# Bepaal cutoff-datum
#cutoff_datum = df.index.max() - grafiek_periode

# Filter alleen grafiekdata
#df_grafiek = df[df.index >= cutoff_datum].copy()

#cutoff_datum = datetime.now() - bepaal_grafiekperiode(interval)
#df_filtered = df[df.index >= cutoff_datum]

# 🖼️ Toggle voor grafiek
#if st.toggle("📊 Toon koersgrafiek"):
 #   fig = go.Figure(data=[
#        go.Candlestick(
 #           x=df_filtered.index,
#            open=df_filtered["Open"],
 #           high=df_filtered["High"],
  #          low=df_filtered["Low"],
  #          close=df_filtered["Close"],
 #           increasing_line_color='green',
 #           decreasing_line_color='red',
#            name='Koers'
#        )
#    ])

 #   fig.update_layout(
 #       xaxis_title="Datum",
 #       yaxis_title="Koers",
 #       xaxis_rangeslider_visible=False,
 #       height=400,
 #       margin=dict(l=10, r=10, t=10, b=10)
#    )

#    st.plotly_chart(fig, use_container_width=True)







# wit
