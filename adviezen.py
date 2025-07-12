import pandas as pd
import numpy as np



# ✅ Weighted Moving Average functie
def weighted_moving_average(series, window):
    weights = np.arange(1, window + 1)
    return series.rolling(window).apply(lambda x: np.dot(x, weights) / weights.sum(), raw=True)


def determine_advice(df, threshold, risk_aversion=0):
    df = df.copy()

    # ✅ Trendberekening over SAM
    df["Trend"] = weighted_moving_average(df["SAM"], 12)
    df["TrendChange"] = df["Trend"] - df["Trend"].shift(1)
    df["Richting"] = np.sign(df["TrendChange"])
    df["Trail"] = 0
    df["Advies"] = np.nan

    # ✅ Bereken Trail (opeenvolgende richting-versterking)
    huidige_trend = 0
    for i in range(1, len(df)):
        huidige = df["Richting"].iloc[i]
        vorige = df["Richting"].iloc[i - 1]

        if huidige == vorige and huidige != 0:
            huidige_trend += 1
        elif huidige != 0:
            huidige_trend = 1
        else:
            huidige_trend = 0

        df.at[df.index[i], "Trail"] = huidige_trend

    # ✅ Advieslogica
    if risk_aversion == 0:
        mask_koop = (df["Richting"] == 1) & (df["Trail"] >= threshold) & (df["Advies"].isna())
        mask_verkoop = (df["Richting"] == -1) & (df["Trail"] >= threshold) & (df["Advies"].isna())

        df.loc[mask_koop, "Advies"] = "Kopen"
        df.loc[mask_verkoop, "Advies"] = "Verkopen"
        df["Advies"] = df["Advies"].ffill()

    elif risk_aversion == 1:
        for i in range(2, len(df)):
            sam_1 = df["SAM"].iloc[i]
            trends_1 = df["Trend"].iloc[i]
            trends_2 = df["Trend"].iloc[i - 1]
            trend_1 = df["SAT_Trend"].iloc[i]
            trend_2 = df["SAT_Trend"].iloc[i - 1]
            trend_3 = df["SAT_Trend"].iloc[i - 2]
            stage_1 = df["SAT_Stage"].iloc[i]
            stage_2 = df["SAT_Stage"].iloc[i - 1]
            stage_3 = df["SAT_Stage"].iloc[i - 2]

            if trend_1 >= trend_2 and trend_2 >= trend_3 and stage_1 > 0 or (trends_1 - trends_2 >= 0) and sam_1 >= 0:
                df.at[df.index[i], "Advies"] = "Kopen"
            elif trend_1 < trend_2 and stage_1 < 0 and stage_2 < 0: # optie and trend_2 < trend_3 
                df.at[df.index[i], "Advies"] = "Verkopen"

        df["Advies"] = df["Advies"].ffill()

    
    elif risk_aversion == 2:
        for i in range(2, len(df)):
            trend_1 = df["SAT_Trend"].iloc[i]
            trend_2 = df["SAT_Trend"].iloc[i - 1]
            trend_3 = df["SAT_Trend"].iloc[i - 2]
            stage_1 = df["SAT_Stage"].iloc[i]
            stage_2 = df["SAT_Stage"].iloc[i - 1]
            stage_3 = df["SAT_Stage"].iloc[i - 2]

            if trend_1 >= trend_2 and trend_2 >= trend_3 and stage_1 > 0 and stage_2 > 0:
                df.at[df.index[i], "Advies"] = "Kopen"
            elif trend_1 < trend_2 and stage_1 < 0: # optie and trend_2 < trend_3 
                df.at[df.index[i], "Advies"] = "Verkopen"

        df["Advies"] = df["Advies"].ffill()

    elif risk_aversion == 3: # cannot lose
        for i in range(2, len(df)):
            sam_1 = df["SAM"].iloc[i]
            sam_2 = df["SAM"].iloc[i - 1]
            sam_3 = df["SAM"].iloc[i - 2]
            trends_1 = df["Trend"].iloc[i]
            trends_2 = df["Trend"].iloc[i - 1]
            trend_1 = df["SAT_Trend"].iloc[i]
            trend_2 = df["SAT_Trend"].iloc[i - 1]
            trend_3 = df["SAT_Trend"].iloc[i - 2]
            stage_1 = df["SAT_Stage"].iloc[i]
            stage_2 = df["SAT_Stage"].iloc[i - 1]
            stage_3 = df["SAT_Stage"].iloc[i - 2]
            stage_4 = df["SAT_Stage"].iloc[i - 3]
            stage_5 = df["SAT_Stage"].iloc[i - 4]
            
            if stage_1 >= 2 and stage_2 >= 2 > 0 and stage_3 > 0 and stage_4 > 0 and stage_5 > 0 and trend_1 >= trend_2 and sam_1 > 0 and sam_2 > 0 and sam_1 >= sam_2 and trends_1 > trends_2 and trends_1 >= 0:
                df.at[df.index[i], "Advies"] = "Kopen"
            elif stage_1 < 1.8 and sam_1 < 0 and sam_2 < 0 and trends_1 < trends_2:
                df.at[df.index[i], "Advies"] = "Verkopen"

        df["Advies"] = df["Advies"].ffill()

    # ✅ Bereken rendementen op basis van adviesgroepering
    df["AdviesGroep"] = (df["Advies"] != df["Advies"].shift()).cumsum()
    rendementen = []
    sam_rendementen = []

    groepen = list(df.groupby("AdviesGroep"))

    for i in range(len(groepen)):
        _, groep = groepen[i]
        advies = groep["Advies"].iloc[0]

        start = groep["Close"].iloc[0]
        if i < len(groepen) - 1:
            eind = groepen[i + 1][1]["Close"].iloc[0]
        else:
            eind = groep["Close"].iloc[-1]

        try:
            start = float(start)
            eind = float(eind)
            if start != 0.0:
                markt_rendement = (eind - start) / start
                sam_rendement = markt_rendement if advies == "Kopen" else -markt_rendement
            else:
                markt_rendement = 0.0
                sam_rendement = 0.0
        except Exception:
            markt_rendement = 0.0
            sam_rendement = 0.0

        rendementen.extend([markt_rendement] * len(groep))
        sam_rendementen.extend([sam_rendement] * len(groep))

    if len(rendementen) != len(df):
        raise ValueError(f"Lengte mismatch: rendementen={len(rendementen)}, df={len(df)}")

    df["Markt-%"] = rendementen
    df["SAM-%"] = sam_rendementen

    if "Advies" in df.columns and df["Advies"].notna().any():
        huidig_advies = df["Advies"].dropna().iloc[-1]
    else:
        huidig_advies = "Niet beschikbaar"

    return df, huidig_advies

            
