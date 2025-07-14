import streamlit as st
import requests
import json

API_KEY = "D2MyI4eYNXDNJzpYT4N6nTQ2amVbJaG5"  # jouw FMP API-sleutel

# Beschikbare endpoints voor testdoeleinden
ENDPOINTS = [
    "profile",
    "key-metrics",
    "ratios",
    "income-statement",
    "balance-sheet-statement",
    "cash-flow-statement",
    "financial-growth",
    "enterprise-values",
    "analyst-estimates",
    "historical-market-capitalization",
    "institutional-holder",
    "insider-trading",
    "esg-environmental-social-governance-data",
]

st.title("🔍 FMP API Tester")

with st.expander("🧪 API Test Tool", expanded=True):
    ticker = st.text_input("Ticker (bijv. AAPL, ASML, BTCUSD)", "AAPL")
    endpoint = st.selectbox("Kies een API-endpoint", ENDPOINTS)

    if st.button("🔄 Ophalen"):
        url = f"https://financialmodelingprep.com/api/v3/{endpoint}/{ticker}?apikey={API_KEY}"
        st.code(f"GET {url}", language="text")

        try:
            response = requests.get(url)
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list) and len(data) == 1:
                    data = data[0]
                st.json(data)
            else:
                st.error(f"Fout {response.status_code}: {response.text}")
        except Exception as e:
            st.error(f"❌ Fout bij ophalen: {e}")

st.caption("Gebruik deze tool om te zien welke data beschikbaar zijn in jouw FMP-abonnement.")
