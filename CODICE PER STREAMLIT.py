import streamlit as st
import pandas as pd
import io

st.set_page_config(page_title="Unipolservice Budget HUB 2.0", layout="wide")

# --- 1. CONFIGURAZIONE ---
MESI = ["GENNAIO", "FEBBRAIO", "MARZO", "APRILE", "MAGGIO", "GIUGNO", "LUGLIO", "AGOSTO", "SETTEMBRE", "OTTOBRE", "NOVEMBRE", "DICEMBRE"]
PARTNER = ["KONECTA", "COVISIAN"]
VOCI_CARR = ["Gestione Contatti", "Ricontatto", "Documenti ricevuti da carrozzeria", "Recupero firme Digitali attività outbound", "solleciti outbound (TODO)"]
VOCI_MECC = ["Solleciti outbound Officine (TODO)", "Gestione ticket assistenza"]

# --- 2. INIZIALIZZAZIONE ---
if 'db' not in st.session_state:
    st.session_state['db'] = {
        "Carrozzeria": {m: {v: {p: 0.0 for p in PARTNER} for v in VOCI_CARR} for m in MESI},
        "Meccanica": {m: {v: {p: 0.0 for p in PARTNER} for v in VOCI_MECC} for m in MESI}
    }
    st.session_state['note'] = {"Carrozzeria": {m: "" for m in MESI}, "Meccanica": {m: "" for m in MESI}}
if 'v' not in st.session_state: 
    st.session_state['v'] = 0

# --- 3. FUNZIONI EXCEL (TEMPLATE E CARICAMENTO) ---
def crea_template():
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        for sett, voci in [("Carrozzeria", VOCI_CARR), ("Meccanica", VOCI_MECC)]:
            rows = []
            for m in MESI:
                for v in voci:
                    for p in PARTNER:
                        rows.append({"Mese": m, "Attività": v, "Partner": p, "Importo": 0.0})
            pd.DataFrame(rows).to_excel(writer, sheet_name=sett, index=False)
    return output.getvalue()

def processa_caricamento():
    if st.session_state.uploader:
        try:
            xls = pd.ExcelFile(st.session_state.uploader)
            for sett in ["Carrozzeria", "Meccanica"]:
                if sett in xls.sheet_names:
                    df = pd.read_excel(xls, sheet_name=sett)
                    for _, row in df.iterrows():
                        m, v, p, val = row['Mese'], row['
