import streamlit as st
import pandas as pd
import io

# --- 1. SETUP ---
st.set_page_config(page_title="Unipol HUB", layout="wide")

MESI = ["GENNAIO", "FEBBRAIO", "MARZO", "APRILE", "MAGGIO", "GIUGNO", 
        "LUGLIO", "AGOSTO", "SETTEMBRE", "OTTOBRE", "NOVEMBRE", "DICEMBRE"]
PARTNER = ["KONECTA", "COVISIAN"]
V_CARR = ["Gestione Contatti", "Ricontatto", "Documenti", "Firme Digitali", "Solleciti"]
V_MECC = ["Solleciti Officine", "Ticket assistenza"]

# --- 2. MEMORIA (Inizializzazione sicura) ---
if 'db' not in st.session_state:
    db = {}
    for s in ["Carrozzeria", "Meccanica"]:
        db[s] = {}
        voci = V_CARR if s == "Carrozzeria" else V_MECC
        for m in MESI:
            db[s][m] = {}
            for v in voci:
                db[s][m][v] = {"KONECTA": 0.0, "COVISIAN": 0.0}
    st.session_state['db'] = db

if 'pct' not in st.session_state:
    st.session_state['pct'] = {m: 8.33 for m in MESI}

# --- 3. SIDEBAR ---
with st.sidebar:
    st.title("🛡️ Unipolservice")
    if st.button("🗑️ RESET DATI"):
        st.session_state.clear()
        st.rerun()
    
    st.divider()
    b_carr = st.number_input("Budget Carrozzeria (€)", value=386393.0)
    b_mecc = st.number_input("Budget Meccanica (€)", value=120000.0)

# --- 4. FUNZIONE TABELLA ANALISI ---
def mostra_analisi(settore, budget_annuale, voci):
    st.divider()
    st.subheader(f"📊 Analisi Delta e Totali - {settore}")
    
    dati_tabella = []
    tot_target = 0.0
    tot_consuntivo = 0.0
    
    for m in MESI:
        # Calcolo Target basato sulla % (qui fissa a 8.33% o personalizzabile)
        quota_mese = st.session_state['pct
