import streamlit as st
import pandas as pd
import io
import os

# --- 1. SETUP ---
st.set_page_config(page_title="Unipol HUB", layout="wide")

# --- 2. COSTANTI ---
MESI = ["GENNAIO", "FEBBRAIO", "MARZO", "APRILE", 
        "MAGGIO", "GIUGNO", "LUGLIO", "AGOSTO", 
        "SETTEMBRE", "OTTOBRE", "NOVEMBRE", "DICEMBRE"]

PARTNER = ["KONECTA", "COVISIAN"]

V_CARR = ["Gestione Contatti", "Ricontatto", 
          "Documenti", "Firme Digitali", "Solleciti"]

V_MECC = ["Solleciti Officine", "Ticket assistenza"]

# --- 3. INIT ---
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

if 'pct_carr' not in st.session_state:
    st.session_state['pct_carr'] = {m: 8.33 for m in MESI}
if 'pct_mecc' not in st.session_state:
    st.session_state['pct_mecc'] = {m: 8.33 for m in MESI}

# --- 4. EXCEL ---
def crea_template():
    out = io.BytesIO()
    with pd.ExcelWriter(out, engine='xlsxwriter') as wr:
        for sett, voci in [("Carrozzeria", V_CARR), 
                           ("Meccanica", V_MECC)]:
            data = []
            for v in voci:
                for p in PARTNER:
                    r = {"Attività": v, "Partner": p}
                    for m in MESI:
                        r[m] = 0.0
                    data.append(r)
            pd.DataFrame(data).to_excel(wr, 
                                       sheet_name=sett, 
                                       index=False)
    return out.getvalue()

def esporta_dati():
    out = io.BytesIO()
    with pd.ExcelWriter(out, engine='xlsxwriter') as wr:
        for s in ["Carrozzeria", "Meccanica"]:
            voci = V_CARR if s == "Carrozzeria" else V_MECC
            rows = []
            for v in voci:
                for p in PARTNER:
                    r = {"Attività": v, "Partner": p}
                    for m in MESI:
                        val = st.session_state['db'][s][m][v][p]
                        r[m] = val
                    rows.append(r)
            pd.DataFrame(rows).to_excel(wr, 
                                       sheet_name=s, 
                                       index=False)
    return out.getvalue()

# --- 5. SIDEBAR ---
with st.sidebar:
    st.title("🛡️ Pannello")
    st.download_button("📥 Template", 
                       crea_template(), 
                       "Template.xlsx")
    st.download_button("📤 Esporta", 
                       esporta_dati(), 
                       "Export.xlsx")
    
    st.divider()
    up = st
