import streamlit as st
import pandas as pd
from datetime import date

def backtest_functie(df, selected_tab, signaalkeuze):
    st.subheader("Vergelijk Marktrendement en SAM-rendement")

    # 📅 1. Datumkeuze
    current_year = date.today().year
    default_start = date(current_year - 2, 1, 1)
    default_end = df.index.max().date()

    start_date = st.date_input("Startdatum analyse", default_start)
    end_date = st.date_input("Einddatum analyse", default_end)

    # 📆 2. Filter op periode
    df = df.copy()
    df.index = pd.to_datetime(df.index)
    df_period = df.loc[
        (df.index.date >= start_date) & (df.index.date <= end_date)
    ].copy()

    if isinstance(df_period.columns, pd.MultiIndex):
        df_period.columns = ["_".join([str(i) for i in col if i]) for col in df_period.columns]

    close_col = next((col for col in df_period.columns if col.lower().startswith("close")), None)
    if not close_col:
        st.error("❌ Geen geldige 'Close'-kolom gevonden.")
        return

    df_period[close_col] = pd.to_numeric(df_period[close_col], errors="coerce")
    df_valid = df_period[close_col].dropna()

    marktrendement = None
    if len(df_valid) >= 2 and df_valid.iloc[0] != 0.0:
        koers_start = df_valid.iloc[0]
        koers_eind = df_valid.iloc[-1]
        marktrendement = ((koers_eind - koers_start) / koers_start) * 100

    # 🔄 Filter adviezen
    advies_col = "Advies"
    if "Advies" not in df_period.columns:
        st.error("Kolom 'Advies' ontbreekt in de data.")
        return

    eerste_valid_index = df_period[df_period["Advies"].notna()].index[0]
    df_signalen = df_period.loc[eerste_valid_index:].copy()
    df_signalen = df_signalen[df_signalen[advies_col].isin(["Kopen", "Verkopen"])].copy()

    # 🧠 Interne functie: rendementberekening
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

            if entry_type is not None:
                if advies != entry_type and (mapped_type == "Beide" or entry_type == mapped_type):
                    sluit_datum = datum
                    sluit_close = close

                    rendement = (
                        (sluit_close - entry_price) / entry_price * 100
                        if entry_type == "Kopen"
                        else (entry_price - sluit_close) / entry_price * 100
                    )

                    if entry_price != sluit_close and entry_date != sluit_datum:
                        rendementen.append(rendement)
                        trades.append({
                            "Type": entry_type,
                            "Open datum": entry_date.date(),
                            "Open prijs": entry_price,
                            "Sluit datum": sluit_datum.date(),
                            "Sluit prijs": sluit_close,
                            "Rendement (%)": rendement,
                        })

                    if mapped_type == "Beide" or advies == mapped_type:
                        entry_type = advies
                        entry_price = close
                        entry_date = datum
                    else:
                        entry_type = None
                        entry_price = None
                        entry_date = None

            elif advies in ["Kopen", "Verkopen"] and (mapped_type == "Beide" or advies == mapped_type):
                entry_type = advies
                entry_price = close
                entry_date = datum

        if entry_type and entry_price is not None:
            laatste_datum = df_signalen.index[-1]
            laatste_koers = df_signalen[close_col].iloc[-1]

            rendement = (
                (laatste_koers - entry_price) / entry_price * 100
                if entry_type == "Kopen"
                else (entry_price - laatste_koers) / entry_price * 100
            )

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

        sam_rendement = sum(rendementen) if rendementen else 0.0
        return sam_rendement, trades, rendementen

    # ✅ Berekeningen
    sam_rendement_filtered, _, _ = bereken_sam_rendement(df_signalen, signaal_type=signaalkeuze, close_col=close_col)
    _, trades_all, _ = bereken_sam_rendement(df_signalen, signaal_type="Beide", close_col=close_col)

    # ✅ Metrics
    col1, col2 = st.columns(2)
    col1.metric("Marktrendement (Buy & Hold)", f"{marktrendement:+.2f}%" if marktrendement is not None else "n.v.t.")
    col2.metric("📊 SAM-rendement", f"{sam_rendement_filtered:+.2f}%" if isinstance(sam_rendement_filtered, (int, float)) else "n.v.t.")

    # ✅ Trades tonen (optioneel: kun je verder uitbouwen zoals in je script)
    if trades_all:
        st.caption(f"Aantal trades: {len(trades_all)}, totaal SAM-rendement: {sum([t['Rendement (%)'] for t in trades_all]):+.2f}%")
        df_trades = pd.DataFrame(trades_all)
        st.dataframe(df_trades)

    else:
        st.info("ℹ️ Geen trades gevonden binnen de geselecteerde periode.")

















# wit

