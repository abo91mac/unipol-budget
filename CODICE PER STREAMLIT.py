import streamlit as st
import pandas as pd
import io

st.set_page_config(page_title="Unipolservice Budget HUB 2.0", layout="wide")

# --- 1. CONFIGURAZIONE STRUTTURA ---
mesi_col = ["GENNAIO", "FEBBRAIO", "MARZO", "APRILE", "MAGGIO", "GIUGNO", 
            "LUGLIO", "AGOSTO", "SETTEMBRE", "OTTOBRE", "NOVEMBRE", "DICEMBRE"]
partner = ["KONECTA", "COVISIAN"]

voci_carr = [
    "Gestione Contatti", "Ricontatto", "Documenti ricevuti da carrozzeria", 
    "Recupero firme Digitali attività outbound", "solleciti outbound (TODO)"
]
voci_mecc = [
    "Solleciti outbound Officine (TODO)", "Gestione ticket assistenza"
]

# --- 2. MEMORIA DI SESSIONE ---
if 'db' not in st.session_state:
    st.session_state['db'] = {
        "Carrozzeria": {m: {v: {p: 0.0 for p in partner} for v in voci_carr} for m in mesi_col},
        "Meccanica": {m: {v: {p: 0.0 for p in partner} for v in voci_mecc} for m in mesi_col}
    }
    st.session_state['note'] = {"Carrozzeria": {m: "" for m in mesi_col}, "Meccanica": {m: "" for m in mesi_col}}
if 'v' not in st.session_state: 
    st.session_state['v'] = 0

# --- 3. LOGICA DI CARICAMENTO EXCEL ---
def process_upload():
    if st.session_state.uploader is not None:
        try:
            df = pd.read_excel(st.session_state.uploader, sheet_name="External carrozzeria-meccanica", header=None)
            
            def estrai_dati(settore, voci, start_row, end_row):
                current_partner = None
                # Scansiona le righe del foglio
                for i in range(start_row, min(end_row, len(df))):
                    row_label = str(df.iloc
