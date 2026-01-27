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

# --- 4. FUNZIONI DI RESET (Riscritte per evitare righe lunghe) ---
def reset_dati():
    # Creiamo il database in modo espanso per evitare errori di troncamento
    db = {}
    for s in ["Carrozzeria", "Meccanica"]:
        db[s] = {}
        voci = VOCI_CARR if s == "Carrozzeria" else VOCI_MECC
        for m in MESI:
            db[s][m] = {}
            for v in voci:
                db[s][m][v] = {p: 0.0 for p in PARTNER}
    
    st.session_state['db'] = db
    st.session_state['pct_carr'] = {m: 8.33 for m in MESI}
    st.session_state['pct_mecc'] = {m: 8.33 for m in MESI}

if 'db' not in st.session_state:
    reset_dati()

# --- 5. LOGICA EXCEL ---
def crea_template():
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        for sett, voci in [("Carrozzeria", VOCI_CARR), ("Meccanica", VOCI_MECC)]:
            data = []
            for v in voci:
                for p in PARTNER:
                    row = {"Attività": v, "Partner": p}
                    for m in MESI: row[m] = 0.0
                    data.append(row)
            pd.DataFrame(data).to_excel(writer, sheet_name=sett, index=False)
    return output.getvalue()

def esporta_consolidato():
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        for sett in ["Carrozzeria", "Meccanica"]:
            voci = VOCI_CARR if sett == "Carrozzeria" else VOCI_MECC
            rows = []
            for v in voci:
                for p in PARTNER:
                    r = {"Attività": v, "Partner": p}
                    for m in MESI: r[m] = st.session_state['db'][sett][m][v][p]
                    rows.append(r)
            pd.DataFrame(rows).to_excel(writer, sheet_name=sett, index=False)
    return output.getvalue()

def carica_excel():
    if st.session_state.uploader:
        try:
            xls = pd.ExcelFile(st.session_state.uploader)
            for sett in ["Carrozzeria", "Meccanica"]:
                if sett in xls.sheet_names:
                    df = pd.read_excel(xls, sheet_name=sett)
                    for _, row in df.iterrows():
                        v, p = str(row['Attività']), str(row['Partner'])
                        for m in MESI:
                            if m in df.columns:
                                st.session_state['db'][sett][m][v][p] = float(row[m])
            st.toast("✅ Excel caricato!")
        except Exception as e:
            st.error(f"Errore: {e}")
