import streamlit as st
import pandas as pd
import io
import os

# --- 1. CONFIGURAZIONE PAGINA ---
st.set_page_config(page_title="Unipolservice Budget HUB", layout="wide")

# --- 2. COSTANTI ---
MESI = ["GENNAIO", "FEBBRAIO", "MARZO", "APRILE", "MAGGIO", "GIUGNO", 
        "LUGLIO", "AGOSTO", "SETTEMBRE", "OTTOBRE", "NOVEMBRE", "DICEMBRE"]
PARTNER = ["KONECTA", "COVISIAN"]
VOCI_CARR = ["Gestione Contatti", "Ricontatto", "Documenti", "Firme Digitali", "Solleciti"]
VOCI_MECC = ["Solleciti Officine", "Ticket assistenza"]

# --- 3. INIZIALIZZAZIONE SESSION STATE (Versione estesa e sicura) ---
if 'db' not in st.session_state:
    db = {}
    for settore in ["Carrozzeria", "Meccanica"]:
        db[settore] = {}
        voci = VOCI_CARR if settore == "Carrozzeria" else VOCI_MECC
        for m in MESI:
            db[settore][m] = {}
            for v in voci:
                db[settore][m][v] = {}
                for p in PARTNER:
                    db[settore][m][v][p] = 0.0
    st.session_state['db'] = db

if 'pct_carr' not in st.session_state:
    st.session_state['pct_carr'] = {m: 8.33 for m in MESI}

if 'pct_mecc' not in st.session_state:
    st.session_state['pct_mecc'] = {m: 8.33 for m in MESI}

# --- 4. FUNZIONI EXCEL ---
def crea_template():
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        for sett, voci in [("Carrozzeria", VOCI_CARR), ("Meccanica", VOCI_MECC)]:
            data = []
            for v in voci:
                for p in PARTNER:
                    row = {"Attività": v, "Partner": p}
                    for m in MESI:
                        row[m] = 0.0
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
                    for m in MESI:
                        r[m] = st.session_state['db'][sett][m][v][p]
                    rows.append(r)
            pd.DataFrame(rows).to_excel(writer, sheet_name=sett, index=False)
    return output.getvalue()

# --- 5. SIDEBAR ---
with st.sidebar:
    st.title("🛡️ Pannello Controllo")
    
    st.download_button("📥 Scarica Template", data=crea_template(), file_name="Template.xlsx")
    st.download_button("📤 Esporta Dati", data=esporta_consolidato(), file_name="Export.xlsx")
    
    st.divider()
    
    uploaded_file = st.file_uploader("📂 Carica Excel", type="xlsx")
    if uploaded_file:
        try:
            xls = pd.ExcelFile(uploaded_file)
            for sett in ["Carrozzeria", "Meccanica"]:
                if sett in xls.sheet_names:
                    df = pd.read_excel(xls, sheet_name=sett)
                    for _, row in df.iterrows():
                        v = str(row['Attività'])
                        p = str(row['
