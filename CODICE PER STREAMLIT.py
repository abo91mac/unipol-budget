import streamlit as st
import pandas as pd
import io
import os
from PIL import Image

# --- 1. CONFIGURAZIONE PAGINA ---
st.set_page_config(page_title="Unipolservice Budget HUB", layout="wide")

# Tema grafico Blu Unipol
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
    """Restituisce True se l'utente ha inserito le credenziali corrette."""
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
                    st.error("Credenziali errate. Riprova.")
        return False
    return True

# Se il login fallisce, interrompiamo l'esecuzione qui
if not check_password():
    st.stop()

# --- 3. DATI E COSTANTI ---
MESI = ["GENNAIO", "FEBBRAIO", "MARZO", "APRILE", "MAGGIO", "GIUGNO", 
        "LUGLIO", "AGOSTO", "SETTEMBRE", "OTTOBRE", "NOVEMBRE", "DICEMBRE"]
PARTNER = ["KONECTA", "COVISIAN"]
VOCI_CARR = ["Gestione Contatti", "Ricontatto", "Documenti", "Firme Digitali", "Solleciti"]
VOCI_MECC = ["Solleciti Officine", "Ticket assistenza"]

# --- 4. FUNZIONI DI RESET ---
def reset_dati():
    st.session_state['db'] = {s: {m: {v: {p: 0.0 for p in PARTNER} for v in (VOCI_CARR if s=="Carrozzeria" else VOCI_MECC)} for m in MESI} for s in ["Carrozzeria", "Meccanica"]}
    st.session_state['pct_carr'] = {m: 8.33 for m in MESI}
    st.session_state['pct_mecc'] = {m: 8.33 for m in MESI}
    st.toast("🧹 Tutti i dati sono stati azzerati!")

# --- 5. INIZIALIZZAZIONE SESSION STATE ---
if 'db' not in st.session_state:
    reset_dati()

# --- 6. FUNZIONI LOGICA EXCEL ---
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
            st.toast("✅ Excel caricato con successo!")
        except Exception as e:
            st.error(f"Errore nel caricamento: {e}")

# --- 7. SIDEBAR ---
with st.sidebar:
    if os.path.exists('logo.png'):
        st.image('logo.png')
    
    st.title("⚙️ Pannello")
    if st.button("🚪 Logout"):
        st.session_state["authenticated"] = False
        st.rerun()
    
    st.divider()
    st.subheader("📥 Download/Upload")
    st.download_button("Scarica Template", data=crea_template(), file_name="Template_Budget.xlsx")
    st.download_button("Esporta Consolidato", data=esporta_consolidato(), file_name="Budget_Consolidato.xlsx")
    st.file_uploader("Carica Excel", type="xlsx", key="uploader", on_change=carica_excel)
    
    st.divider()
    if st.button("🗑️ RESET DATI", help="Azzera tutti i consuntivi"):
        reset_dati()
        st.rerun()

    st.divider()
    st.subheader("💰 Budget Annuale")
    b_carr = st.number_input("Carrozzeria (€)", value=386393.0)
    b_mecc = st.number_input("Meccanica (€)", value=1200
