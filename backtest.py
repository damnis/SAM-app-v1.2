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

    close_col = next((col for col in df_period.columns if col.lower().startswith("close")), None)
    if not close_col:
        st.error("❌ Geen geldige 'Close'-kolom gevonden in deze dataset.")
        st.stop()

    df_period[close_col] = pd.to_numeric(df_period[close_col], errors="coerce")
    df_valid = df_period[close_col].dropna()

    marktrendement = None
    if len(df_valid) >= 2 and df_valid.iloc[0] != 0.0:
        koers_start = df_valid.iloc[0]
        koers_eind = df_valid.iloc[-1]
        marktrendement = ((koers_eind - koers_start) / koers_start) * 100

    advies_col = "Advies"
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




# ------------
        # ✅ Weergave
        
        # Definieer kolommen
        geldige_kolommen = ["Markt-%", "SAM-% tot.", "SAM-% Koop", "SAM-% Verkoop"]

        
        
        # ✅ Afronding en formattering op 2 decimalen met plusteken
        df_display = df_trades.rename(columns={"Rendement (%)": "SAM-% tot."})[[
            "Open datum", "Open prijs", "Sluit datum", "Sluit prijs",
            "Markt-%", "SAM-% tot.", "SAM-% Koop", "SAM-% Verkoop"]]

        # ➕ Afronding op 2 decimalen
        for col in ["Markt-%", "SAM-% tot.", "SAM-% Koop", "SAM-% Verkoop"]:
            df_display[col] = df_display[col].astype(float).map("{:+.2f}%".format)

        styler = df_display.style.format({col: "{:+.2f}%" for col in geldige_kolommen})
   #     for i, col in enumerate(df_display.columns):
    #        st.write(f"Kolom {i}: {col}")
    

        # ➕ Kolomnamen op 2 regels
  #      df_display = df_display.rename(columns={
 #           "SAM-% Koop": "SAM-% Koop",
  #          "SAM-% Verkoop": "SAM-%\nVerkoop"
 #       })
        
#        df_display = df_display.rename(columns={
 #           "SAM-% Verkoop": "SAM-%\u200B Verkoop"
#})
        # ➕ Styling: kleuren
        def kleur_positief_negatief(val):
            if pd.isna(val): return "color: gray"
            try:
                val = float(val.replace('%', ''))
                if val > 0: return "color: green"
                elif val < 0: return "color: red"
                else: return "color: gray"
            except: return "color: gray"

        styler = styler.applymap(kleur_positief_negatief, subset=geldige_kolommen)

        # ✅ Geforceerde kolomhoofdstijl: tekst op 2 regels door vaste breedte (visuele truc)
        # HTML/CSS workaround: breek automatisch bij spatie als de breedte beperkt is
  #      styler = styler.set_table_styles([
   #         {"selector": "th.col6", "props": [("min-width", "40px"), ("max-width", "60px"), ("white-space", "normal")]},
   #         {"selector": "th.col7", "props": [("min-width", "40px"), ("max-width", "45px"), ("no-white-space", "normal")]}
   #     ])

        toon_alle = st.toggle("Toon alle trades", value=False)
        if not toon_alle and len(df_display) > 12:
            df_display = df_display.iloc[-12:]

        if selected_tab == "🌐 Crypto":
            df_display["Open prijs"] = df_display["Open prijs"].astype(float).map("{:.3f}".format)
            df_display["Sluit prijs"] = df_display["Sluit prijs"].astype(float).map("{:.3f}".format)
        else:
            df_display["Open prijs"] = df_display["Open prijs"].astype(float).map("{:.2f}".format)
            df_display["Sluit prijs"] = df_display["Sluit prijs"].astype(float).map("{:.2f}".format)

        
        
        
        # goed en oud
        geldige_kolommen = [col for col in ["Markt-%", "SAM-% tot.", "SAM-% Koop", "SAM-% Verkoop"] if df_display[col].notna().any()]
        styler = styler.format({col: "{:+.2f}%" for col in geldige_kolommen})
        styler = df_display.style.applymap(kleur_positief_negatief, subset=geldige_kolommen)
        
        st.dataframe(styler, use_container_width=True)


   
    else:
        st.info("ℹ️ Geen trades gevonden binnen de geselecteerde periode.")






























# w
