import streamlit as st
import pandas as pd
import numpy as np
from datetime import date

def backtest_functie(df, signaalkeuze, selected_tab):
    st.subheader("Vergelijk Marktrendement en SAM-rendement")

    current_year = date.today().year
    default_start = date(current_year - 2, 1, 1)
    default_end = df.index.max().date()

    start_date = st.date_input("Startdatum analyse", default_start)
    end_date = st.date_input("Einddatum analyse", default_end)

    df = df.copy()
    df.index = pd.to_datetime(df.index)
    df_period = df.loc[(df.index.date >= start_date) & (df.index.date <= end_date)].copy()

    if isinstance(df_period.columns, pd.MultiIndex):
        df_period.columns = ["_".join([str(i) for i in col if i]) for col in df_period.columns]

    # ðŸ“Š Backtestfunctie: sluit op close van nieuw signaal
# âœ… 0.Data voorbereiden voor advies')
df_signalen = df.copy()
if "Advies" not in df_signalen.columns:
    st.error("Kolom 'Advies' ontbreekt in de data.")
    st.stop()

                
st.subheader("Vergelijk Marktrendement en SAM-rendement")

# ðŸ“… 1. Datumkeuze
current_year = date.today().year
default_start = date(current_year -2, 1, 1)
#default_start = date(2021, 1, 1)
default_end = df.index.max().date()

start_date = st.date_input("Startdatum analyse", default_start)
end_date = st.date_input("Einddatum analyse", default_end)

# ðŸ“† 2. Filter op periode
df = df.copy()
df.index = pd.to_datetime(df.index)
df_period = df.loc[
    (df.index.date >= start_date) & (df.index.date <= end_date)
].copy()

# ðŸ§¹ Flatten MultiIndex indien nodig
if isinstance(df_period.columns, pd.MultiIndex):
    df_period.columns = ["_".join([str(i) for i in col if i]) for col in df_period.columns]

# ðŸ” Zoek geldige 'Close'-kolom
close_col = next((col for col in df_period.columns if col.lower().startswith("close")), None)

if not close_col:
    st.error("âŒ Geen geldige 'Close'-kolom gevonden in deze dataset.")
    st.stop()

# ðŸ“ˆ Marktrendement (Buy & Hold)
df_period[close_col] = pd.to_numeric(df_period[close_col], errors="coerce")
df_valid = df_period[close_col].dropna()

marktrendement = None
if len(df_valid) >= 2 and df_valid.iloc[0] != 0.0:
    koers_start = df_valid.iloc[0]
    koers_eind = df_valid.iloc[-1]
    marktrendement = ((koers_eind - koers_start) / koers_start) * 100

# âœ… Signaalkeuze geforceerd op Beide
#signaalkeuze = "Beide"
advies_col = "Advies"

# Vind eerste geldige advies (geen NaN) om mee te starten
eerste_valid_index = df_period[df_period["Advies"].notna()].index[0]
df_signalen = df_period.loc[eerste_valid_index:].copy()
df_signalen = df_signalen[df_signalen[advies_col].isin(["Kopen", "Verkopen"])].copy()

# ðŸ”„ Backtestfunctie

#def bereken_sam_rendement(df_signalen, signaal_type="Beide", close_col="Close"):
def bereken_sam_rendement(df_signalen, signaal_type="Beide", close_col="Close"):
    rendementen = []
    trades = []
    entry_price = None
    entry_date = None
    entry_type = None

    type_map = {"Koop": "Kopen", "Verkoop": "Verkopen", "Beide": "Beide"}
    mapped_type = type_map.get(signaal_type, "Beide")

    for i in range(len(df_signalen)):
        advies = df_signalen["Advies"].iloc[i]
        close = df_signalen[close_col].iloc[i]
        datum = df_signalen.index[i]

        # Alleen sluiten als er een open positie is
        if entry_type is not None:
            if advies != entry_type and (mapped_type == "Beide" or entry_type == mapped_type):
                sluit_datum = datum
                sluit_close = close

                if entry_type == "Kopen":
                    rendement = (sluit_close - entry_price) / entry_price * 100
                else:
                    rendement = (entry_price - sluit_close) / entry_price * 100

                # Nieuw: filter dummy-trade
                if entry_price != sluit_close and entry_date != sluit_datum:
                    rendementen.append(rendement)
                    trades.append({
                        "Type": entry_type,
                        "Open datum": entry_date.date(),
                        "Open prijs": entry_price,
                        "Sluit datum": sluit_datum.date(),
                        "Sluit prijs": sluit_close,
                        "Rendement (%)": rendement,
                        "SAM": df.loc[entry_date, "SAM"] if entry_date in df.index else None,
                        "Trend": df.loc[entry_date, "Trend"] if entry_date in df.index else None,
                    })

                # Mogelijk nieuwe trade openen
                if mapped_type == "Beide" or advies == mapped_type:
                    entry_type = advies
                    entry_price = close
                    entry_date = datum
                else:
                    entry_type = None
                    entry_price = None
                    entry_date = None

        # Start een nieuwe trade, zonder geforceerd te zijn
        elif advies in ["Kopen", "Verkopen"] and (mapped_type == "Beide" or advies == mapped_type):
            entry_type = advies
            entry_price = close
            entry_date = datum

    # Eventueel open trade afsluiten op laatste koers
    if entry_type and entry_price is not None:
        laatste_datum = df_signalen.index[-1]
        laatste_koers = df_signalen[close_col].iloc[-1]

        if entry_type == "Kopen":
            rendement = (laatste_koers - entry_price) / entry_price * 100
        else:
            rendement = (entry_price - laatste_koers) / entry_price * 100

        # Nieuw: filter dummy-trade (ook laatste)
        if entry_price != laatste_koers and entry_date != laatste_datum:
            rendementen.append(rendement)
            trades.append({
                "Type": entry_type,
                "Open datum": entry_date.date(),
                "Open prijs": entry_price,
                "Sluit datum": laatste_datum.date(),
                "Sluit prijs": laatste_koers,
                "Rendement (%)": rendement
            })
