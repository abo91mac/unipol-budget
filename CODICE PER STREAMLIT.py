import streamlit as st
import pandas as pd
import io

# --- 1. CONFIGURAZIONE ---
st.set_page_config(page_title="Unipol Budget HUB", layout="wide")

MESI = ["GENNAIO", "FEBBRAIO", "MARZO", "APRILE", "MAGGIO", "GIUGNO", 
        "LUGLIO", "AGOSTO", "SETTEMBRE", "OTTOBRE", "NOVEMBRE", "DICEMBRE"]
PARTNER = ["KONECTA", "COVISIAN"]
VOCI_C = ["Gestione Contatti", "Ricontatto", "Documenti", "Firme Digitali", "Solleciti"]
VOCI_M = ["Solleciti Officine", "Ticket assistenza"]

# --- 2. INIT SESSION ---
if 'db' not in st.session_state:
    db = {}
    for s in ["Carrozzeria", "Meccanica"]:
        db[s] = {}
        voci = VOCI_C if s == "Carrozzeria" else VOCI_M
        for m in MESI:
            db[s][m] = {}
            for v in voci:
                db[s][m][v] = {p: 0.0 for p in PARTNER}
    st.session_state['db'] = db

if 'pct' not in st.session_state:
    st.session_state['pct'] = {m: 8.33 for m in MESI}

# --- 3. LOGICA EXCEL ---
def esporta_excel():
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        for s in ["Carrozzeria", "Meccanica"]:
            voci = VOCI_C if s == "Carrozzeria" else VOCI_M
            rows = []
            for v in voci:
                for p in PARTNER:
                    r = {"Attività": v, "Partner": p}
                    for m in MESI:
                        r[m] = st.session_state['db'][s][m][v][p]
                    rows.append(r)
            pd.DataFrame(rows).to_excel(writer, sheet_name=s, index=False)
    return output.getvalue()

# --- 4. SIDEBAR ---
with st.sidebar:
    st.title("🛡️ Unipolservice
