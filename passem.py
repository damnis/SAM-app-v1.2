import streamlit as st

def password_gate():
    PASSWORD = st.secrets["APP_PASSWORD"]
    if "pw_correct" not in st.session_state:
        st.session_state.pw_correct = False

    if not st.session_state.pw_correct:
        pw = st.text_input("Wachtwoord", type="password")
        if pw == PASSWORD:
            st.session_state.pw_correct = True
#            st.experimental_rerun()
        elif pw:
            st.error("Wachtwoord onjuist!")
        st.stop()  # stopt de hele app als niet correct!











