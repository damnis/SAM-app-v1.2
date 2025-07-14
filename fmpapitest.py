import requests
import json


def test_fmp_endpoint():
    st.subheader("🧪 FMP API Test Tool")

    ticker = st.text_input("Voer een ticker in (bijv. AAPL, ASML, BTCUSD):")
    endpoint = st.selectbox("Kies een API-endpoint", [
        "profile", "key-metrics", "income-statement", "balance-sheet-statement",
        "cash-flow-statement", "ratios", "ratios-ttm", "income-statement-growth",
        "historical-price-full", "financial-growth", "esg-environmental-social-governance-data",
        "market-capitalization", "company-outlook", "executives", "score", "dividend", "stock-news",
        "quote", "number-of-employees", "institutional-holders", "etf-holder", "mutual-fund-holder"
    ])

    if st.button("🔍 Test endpoint"):
        if not ticker:
            st.warning("⚠️ Geen ticker opgegeven.")
            return

        url = f"https://financialmodelingprep.com/api/v3/{endpoint}/{ticker}?apikey={FMP_API_KEY}"
        st.code(url, language='text')

        try:
            response = requests.get(url)
            if response.status_code != 200:
                st.error(f"❌ Fout bij ophalen data: {response.status_code} {response.reason}")
                return
            data = response.json()
            st.json(data if data else {"result": "Leeg antwoord"})
        except Exception as e:
            st.error(f"❌ Fout: {e}")



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
