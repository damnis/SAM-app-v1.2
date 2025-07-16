import streamlit as st

def password_gate():
    PASSWORD = st.secrets["APP_PASSWORD"]
    # Check of sessie al correct is
    if st.session_state.get("pw_correct"):
        return  # niets meer doen; app wordt nu gewoon geladen!

    # Anders: vraag om wachtwoord
    pw = st.text_input("Wachtwoord", type="password")
    if pw:
        if pw == PASSWORD:
            st.session_state["pw_correct"] = True
            st.success("Inloggen gelukt! Laden...")
            st.experimental_rerun()  # rerun nodig zodat sessie wordt gezet
            st.stop()  # absoluut nodig om te stoppen na rerun-trigger
        else:
            st.error("Wachtwoord onjuist!")
            st.stop()  # direct stoppen, geen brute force mogelijk
    else:
        st.stop()  # altijd stoppen als je nog geen wachtwoord hebt ingevoerd
