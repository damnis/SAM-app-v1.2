import streamlit as st
import pandas as pd
import numpy as np
from datetime import date
from grafieken import bepaal_grafiekperiode 

def bereken_sam_rendement(df_signalen, signaal_type="Beide", close_col="Close", df_orig=None):
    rendementen = []
    trades = []
    entry_price = None
    entry_date = None
    entry_type = None

    for i in range(len(df_signalen)):
        advies = df_signalen["Advies"].iloc[i]
        close = df_signalen[close_col].iloc[i]
        datum = df_signalen.index[i]

        if entry_type is not None:
            if advies != entry_type and (signaal_type == "Beide" or entry_type == signaal_type):
                sluit_datum = datum
                sluit_close = close

                rendement = ((sluit_close - entry_price) / entry_price * 100) if entry_type == "Kopen" else ((entry_price - sluit_close) / entry_price * 100)

                if entry_price != sluit_close and entry_date != sluit_datum:
                    trades.append({
                        "Type": entry_type,
                        "Open datum": entry_date.date(),
                        "Open prijs": entry_price,
                        "Sluit datum": sluit_datum.date(),
                        "Sluit prijs": sluit_close,
                        "Rendement (%)": rendement,
                        "SAM": df_orig.loc[entry_date, "SAM"] if df_orig is not None and entry_date in df_orig.index else None,
                        "Trend": df_orig.loc[entry_date, "Trend"] if df_orig is not None and entry_date in df_orig.index else None,
                    })
                    rendementen.append(rendement)

                if signaal_type == "Beide" or advies == signaal_type:
                    entry_type = advies
                    entry_price = close
                    entry_date = datum
                else:
                    entry_type = None
                    entry_price = None
                    entry_date = None

        elif advies in ["Kopen", "Verkopen"] and (signaal_type == "Beide" or advies == signaal_type):
            entry_type = advies
            entry_price = close
            entry_date = datum

    if entry_type and entry_price is not None:
        laatste_datum = df_signalen.index[-1]
        laatste_koers = df_signalen[close_col].iloc[-1]
        rendement = ((laatste_koers - entry_price) / entry_price * 100) if entry_type == "Kopen" else ((entry_price - laatste_koers) / entry_price * 100)

        if entry_price != laatste_koers and entry_date != laatste_datum:
            trades.append({
                "Type": entry_type,
                "Open datum": entry_date.date(),
                "Open prijs": entry_price,
                "Sluit datum": laatste_datum.date(),
                "Sluit prijs": laatste_koers,
                "Rendement (%)": rendement
            })
            rendementen.append(rendement)

    sam_rendement = (np.prod([1 + r / 100 for r in rendementen]) - 1) * 100 if rendementen else 0.0
    return sam_rendement, trades, rendementen

def backtest_functie(df, signaalkeuze, selected_tab, interval):
    st.subheader("Marktrendement VS SAT+SAM-rendement")

    # Gebruik dezelfde logica als in grafiekweergave
    grafiek_periode = bepaal_grafiekperiode(interval)
    cutoff_datum = df.index.max() - grafiek_periode

    default_start = cutoff_datum.date()
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
#        st.stop()

    st.text(f"Geselecteerde signaalkeuze (bij risk aversion): {signaalkeuze}")
    
    df_period[close_col] = pd.to_numeric(df_period[close_col], errors="coerce")
    df_valid = df_period[close_col].dropna()

    
    marktrendement = None
    if len(df_valid) >= 2 and df_valid.iloc[0] != 0.0:
        koers_start = df_valid.iloc[0]
        koers_eind = df_valid.iloc[-1]
        marktrendement = ((koers_eind - koers_start) / koers_start) * 100

    eerste_valid_index = df_period[df_period["Advies"].notna()].index[0]
    df_signalen = df_period.loc[eerste_valid_index:].copy()
    df_signalen = df_signalen[df_signalen["Advies"].isin(["Kopen", "Verkopen"])].copy()

    sam_rendement, _, _ = bereken_sam_rendement(df_signalen, signaal_type=signaalkeuze, close_col=close_col, df_orig=df_period)
    _, trades_all, _ = bereken_sam_rendement(df_signalen, signaal_type="Beide", close_col=close_col, df_orig=df_period)

    if trades_all:
        df_trades = pd.DataFrame(trades_all)
        df_trades["SAM-% Koop"] = df_trades.apply(lambda row: row["Rendement (%)"] if row["Type"] == "Kopen" else None, axis=1)
        df_trades["SAM-% Verkoop"] = df_trades.apply(lambda row: row["Rendement (%)"] if row["Type"] == "Verkopen" else None, axis=1)
        df_trades["Markt-%"] = df_trades.apply(lambda row: ((row["Sluit prijs"] - row["Open prijs"]) / row["Open prijs"]) * 100, axis=1)

        metric_sam = (df_trades["Rendement (%)"].dropna().apply(lambda x: 1 + x / 100).prod() - 1) * 100

        rendement_koop = (df_trades["SAM-% Koop"].dropna().apply(lambda x: 1 + x / 100).prod() - 1) * 100
        rendement_verkoop = (df_trades["SAM-% Verkoop"].dropna().apply(lambda x: 1 + x / 100).prod() - 1) * 100
        aantal_trades = len(df_trades)
        aantal_koop = df_trades["SAM-% Koop"].notna().sum()
        aantal_verkoop = df_trades["SAM-% Verkoop"].notna().sum()
        aantal_succesvol = (df_trades["Rendement (%)"] > 0).sum()
        aantal_succesvol_koop = (df_trades["SAM-% Koop"] > 0).sum()
        aantal_succesvol_verkoop = (df_trades["SAM-% Verkoop"] > 0).sum()

        col1, col2 = st.columns(2)
        col1.metric("Marktrendement (Buy & Hold)", f"{marktrendement:+.2f}%" if marktrendement is not None else "n.v.t.")
        if signaalkeuze == "Koop":
            waarde = rendement_koop
        elif signaalkeuze == "Verkoop":
            waarde = rendement_verkoop
        else:
            waarde = metric_sam

        col2.metric(f"SAT+SAM-rendement ({signaalkeuze})", f"{waarde:+.2f}%" if waarde is not None else "n.v.t.")

   #     col2.metric(f"SAM-rendement ({signaalkeuze})", f"{sam_rendement:+.2f}%" if isinstance(sam_rendement, (int, float)) else "n.v.t.")
        
 #       col2.metric("📊 SAM-rendement", f"{metric_sam:+.2f}%")
  #      col2.metric("SAM-rendement", f"{metric_sam:+.2f}%" if isinstance(sam_rendement, (int, float)) else "n.o.t.")
   #      col2.metric("SAM-rendement", f"{sam_rendement:+.2f}%" if isinstance(sam_rendement, (int, float)) else "n.v.t.")
 
        
                       
        st.caption(f"Aantal afgeronde **trades**: **{aantal_trades}**, totaal resultaat SAT+SAM-%: **{metric_sam:+.2f}%**, succesvol: **{aantal_succesvol}**")
        st.caption(f"Aantal **koop** trades: **{aantal_koop}**, SAT+SAM-% koop: **{rendement_koop:+.2f}%**, succesvol: **{aantal_succesvol_koop}**")
        st.caption(f"Aantal **verkoop** trades: **{aantal_verkoop}**, SAT+SAM-% verkoop: **{rendement_verkoop:+.2f}%**, succesvol: **{aantal_succesvol_verkoop}**")

        



        # ✅ Weergave
        
        # Definieer kolommen
        geldige_kolommen = ["Markt-%", "SAM-% tot.", "SAM-% Koop", "SAM-% Verkoop"]

        # ✅ Rename en basisselectie (zonder 'Dagen')
        df_display = df_trades.rename(columns={"Rendement (%)": "SAM-% tot."})[[
            "Open datum", "Open prijs", "Sluit datum", "Sluit prijs",
            "Markt-%", "SAM-% tot.", "SAM-% Koop", "SAM-% Verkoop"
        ]]

        # ✅ Voeg kolom 'Dagen' toe
        df_display["Dagen"] = (
            pd.to_datetime(df_display["Sluit datum"]) - pd.to_datetime(df_display["Open datum"])
        ).dt.days

        # ✅ Zet kolommen in gewenste volgorde (Dagen achter Sluit prijs)
        df_display = df_display[[
            "Open datum", "Open prijs", "Sluit datum", "Sluit prijs", "Dagen",
            "Markt-%", "SAM-% tot.", "SAM-% Koop", "SAM-% Verkoop"
        ]]
        
        
        # ➕ Afronding op 2 decimalen
        for col in ["Markt-%", "SAM-% tot.", "SAM-% Koop", "SAM-% Verkoop"]:
            df_display[col] = df_display[col].astype(float).map("{:+.2f}%".format)

        styler = df_display.style.format({col: "{:+.2f}%" for col in geldige_kolommen})
   #     for i, col in enumerate(df_display.columns):
    #        st.write(f"Kolom {i}: {col}")
    
        
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




# ✅ Geforceerde kolomhoofdstijl: tekst op 2 regels door vaste breedte (visuele truc)
        # HTML/CSS workaround: breek automatisch bij spatie als de breedte beperkt is
  #      styler = styler.set_table_styles([
   #         {"selector": "th.col6", "props": [("min-width", "40px"), ("max-width", "60px"), ("white-space", "normal")]},
   #         {"selector": "th.col7", "props": [("min-width", "40px"), ("max-width", "45px"), ("no-white-space", "normal")]}
   #     ])


  # ➕ Kolomnamen op 2 regels
  #      df_display = df_display.rename(columns={
 #           "SAM-% Koop": "SAM-% Koop",
  #          "SAM-% Verkoop": "SAM-%\nVerkoop"
 #       })
        
#        df_display = df_display.rename(columns={
 #           "SAM-% Verkoop": "SAM-%\u200B Verkoop"
#}) 

#          df_display = df_trades.rename(columns={"Rendement (%)": "SAM-% tot."})[[
 #           "Open datum", "Open prijs", "Sluit datum", "Sluit prijs",
  #          "Markt-%", "SAM-% tot.", "SAM-% Koop", "SAM-% Verkoop"]]

  #      for col in ["Markt-%", "SAM-% tot.", "SAM-% Koop", "SAM-% Verkoop"]:
 #           df_display[col] = df_display[col].astype(float).map("{:+.2f}%".format)
#
  
#        geldige_kolommen = [col for col in ["Markt-%", "SAM-% tot.", "SAM-% Koop", "SAM-% Verkoop"] if df_display[col].notna().any()]

 #       def kleur_positief_negatief(val):
 #           if pd.isna(val): return "color: gray"
  #          try:
  #              val = float(val.replace('%', ''))
 #               if val > 0: return "color: green"
 #               elif val < 0: return "color: red"
  #              else: return "color: gray"
   #         except: return "color: gray"

#        styler = df_display.style.format({col: "{:+.2f}%" for col in geldige_kolommen})
  #      styler = styler.applymap(kleur_positief_negatief, subset=geldige_kolommen)

 #       toon_alle = st.toggle("Toon alle trades", value=False)
 #       if not toon_alle and len(df_display) > 12:
  #          df_display = df_display.iloc[-12:]

  #      if selected_tab == "🌐 Crypto":
  #          df_display["Open prijs"] = df_display["Open prijs"].astype(float).map("{:.3f}".format)
  #          df_display["Sluit prijs"] = df_display["Sluit prijs"].astype(float).map("{:.3f}".format)
  #      else:
   #         df_display["Open prijs"] = df_display["Open prijs"].astype(float).map("{:.2f}".format)
   #         df_display["Sluit prijs"] = df_display["Sluit prijs"].astype(float).map("{:.2f}".format)

   #     st.dataframe(styler, use_container_width=True)
#    else:
 #       st.info("ℹ️ Geen trades gevonden binnen de geselecteerde periode.")




























# w
