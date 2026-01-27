import streamlit as st
import pandas as pd
import io
import os
from PIL import Image

# --- 1. CONFIGURAZIONE PAGINA ---
st.set_page_config(page_title="Unipolservice Budget HUB", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #f4f7f9; }
    .stTabs [aria-selected="true"] { background-color: #003399 !important; color: white !important; }
    .stButton>button { background-color: #003399; color: white; border-radius: 5px; width: 100%; }
    div[data-testid="stMetricValue"] { color: #003399; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. FUNZIONE LOGIN ---
def check_password():
    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False

    if not st.session_state["authenticated"]:
        st.title("🛡️ Accesso Unipolservice HUB")
        with st.form("login_form"):
            user = st.text_input("Nome Utente")
            password = st.text_input("Password", type="password")
            submit = st.form_submit_button("Accedi")
            if submit:
                if user == "unipolservice" and password == "Grunipol01":
                    st.session_state["authenticated"] = True
                    st.rerun()
                else:
                    st.error("Credenziali errate.")
        return False
    return True

if not check_password():
    st.stop()

# --- 3. DATI FISSI ---
MESI = ["GENNAIO", "FEBBRAIO", "MARZO", "APRILE", "MAGGIO", "GIUGNO", 
        "LUGLIO", "AGOSTO", "SETTEMBRE", "OTTOBRE", "NOVEMBRE", "DICEMBRE"]
PARTNER = ["KONECTA", "COVISIAN"]
VOCI_CARR = ["Gestione Contatti", "Ricontatto", "Documenti", "Firme Digitali", "Solleciti"]
VOCI_MECC = ["Solleciti Officine", "Ticket assistenza"]

# --- 4. FUNZIONI DI RESET ---
def reset_dati():
    st.session_state['db'] = {s: {m: {v: {p: 0.0 for p in PARTNER} for v in (VOCI_CARR if s=="Carrozzeria" else VOCI_MECC)} for m in MESI} for s in ["Carrozzeria", "Me
