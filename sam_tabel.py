import streamlit as st
import pandas as pd

def toon_sam_tabel(df, selected_tab, signaalkeuze):
    st.subheader("Laatste signalen en rendement")

    if "tabel_lengte" not in st.session_state:
        st.session_state.tabel_lengte = 16

    def toggle_lengte():
        if st.session_state.tabel_lengte == 16:
            st.session_state.tabel_lengte = 50
        elif st.session_state.tabel_lengte == 50:
            st.session_state.tabel_lengte = 150
        else:
            st.session_state.tabel_lengte = 16

    knoptekst = {
        16: "🧮 Toon 50 rijen",
        50: "🧮 Toon 150 rijen",
        150: "🔁 Toon minder rijen"
    }[st.session_state.tabel_lengte]

    st.button(knoptekst, on_click=toggle_lengte)
    weergave_lengte = st.session_state.tabel_lengte

    kolommen = ["Close", "Advies", "SAM", "Trend", "SAT_Trend", "Markt-%", "SAM-%"]
    tabel = df[kolommen].dropna().copy()
    tabel = tabel.sort_index(ascending=False).head(weergave_lengte)

    if not isinstance(tabel.index, pd.DatetimeIndex):
        tabel.index = pd.to_datetime(tabel.index, errors="coerce")
    tabel = tabel[~tabel.index.isna()]
    tabel["Datum"] = tabel.index.strftime("%d-%m-%Y")

    tabel = tabel[["Datum"] + kolommen]

    if selected_tab == "🌐 Crypto":
        tabel["Close"] = tabel["Close"].map("{:.3f}".format)
    else:
        tabel["Close"] = tabel["Close"].map("{:.2f}".format)

    tabel["Markt-%"] = tabel["Markt-%"].astype(float) * 100
    tabel["SAM-%"] = tabel["SAM-%"].astype(float) * 100
    tabel["Advies"] = tabel["Advies"].astype(str)

    if signaalkeuze == "Koop":
        tabel["SAM-%"] = [sam if adv == "Kopen" else 0.0 for sam, adv in zip(tabel["SAM-%"], tabel["Advies"])]
    elif signaalkeuze == "Verkoop":
        tabel["SAM-%"] = [sam if adv == "Verkopen" else 0.0 for sam, adv in zip(tabel["SAM-%"], tabel["Advies"])]

    tabel["Markt-% weergave"] = tabel["Markt-%"].map("{:+.2f}%".format)
    tabel["SAM-% weergave"] = tabel["SAM-%"].map("{:+.2f}%".format)
    tabel["SAT Trend Weergave"] = tabel["SAT_Trend"].map("{:+.2f}".format)
    tabel["SAM Trend Weergave"] = tabel["Trend"].map("{:+.2f}".format)
    
    tabel = tabel[["Datum", "Close", "Advies", "SAM", "SAM Trend Weergave", "SAT Trend Weergave", "Markt-% weergave", "SAM-% weergave"]]
    tabel = tabel.rename(columns={
        "Markt-% weergave": "Markt-%",
        "SAM-% weergave": "SAT+SAM-%",
        "SAM Trend Weergave": "SAM Trend",
        "SAT Trend Weergave": "SAT Trend"

    })

    html = """
    <style>
        table {
            border-collapse: collapse;
            width: 100%;
            font-family: Arial, sans-serif;
            font-size: 13px;
        }
        th {
            background-color: #004080;
            color: white;
            padding: 4px;
            text-align: center;
        }
        td {
            border: 1px solid #ddd;
            padding: 4px;
            text-align: left;
            background-color: #f9f9f9;
            color: #222222;
        }
        tr:nth-child(even) td {
            background-color: #eef2f7;
        }
        tr:hover td {
            background-color: #d0e4f5;
        }
    </style>
    <table>
        <thead>
            <tr>
                <th style='width: 95px;'>Datum</th>
                <th style='width: 85px;'>Close</th>
                <th style='width: 80px;'>Advies</th>
                <th style='width: 60px;'>SAM</th>
                <th style='width: 60px;'>SAM Trend</th>
                <th style='width: 60px;'>SAT Trend</th>
                <th style='width: 90px;'>Markt-%</th>
                <th style='width: 95px;'>SAT+SAM-%</th>
            </tr>
        </thead>
        <tbody>
    """

    for _, row in tabel.iterrows():
        html += "<tr>"
        for value in row:
            html += f"<td>{value}</td>"
        html += "</tr>"

    html += "</tbody></table>"

    st.markdown(html, unsafe_allow_html=True)















# w
















# wit
