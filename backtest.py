





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
