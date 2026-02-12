import streamlit as st
import pandas as pd
import io

# --- SETUP BASE ---
st.set_page_config(page_title="Unipol HUB", layout="wide")

MESI = ["GENNAIO", "FEBBRAIO", "MARZO", "APRILE", "MAGGIO", "GIUGNO", 
        "LUGLIO", "AGOSTO", "SETTEMBRE", "OTTOBRE", "NOVEMBRE", "DICEMBRE"]
PARTNER = ["KONECTA", "COVISIAN"]
V_CARR = ["Gestione Contatti", "Ricontatto", "Documenti", "Firme Digitali", "Solleciti"]
V_MECC = ["Solleciti Officine", "Ticket assistenza"]

# --- MEMORIA ---
if 'db' not in st.session_state:
    st.session_state['db'] = {}
    for s in ["Carrozzeria", "Meccanica"]:
        st.session_state['db'][s] = {}
        voci = V_CARR if s == "Carrozzeria" else V_MECC
        for m in MESI:
            st.session_state['db'][s][m] = {}
            for v in voci:
                st.session_state['db'][s][m][v] = {"KONECTA": 0.0, "COVISIAN": 0.0}

if 'pct' not in st.session_state:
    st.session_state['pct'] = {m: 8.33 for m in MESI}

# --- SIDEBAR ---
with st.sidebar:
    st.title("🛡️ Pannello")
    if st.button("🗑️ RESET"):
        st.session_state.clear()
        st.rerun()
    
    up = st.file_uploader("📂 Carica Excel", type="xlsx")
    if up:
        xls = pd.ExcelFile(up)
        for s in ["Carrozzeria", "Meccanica"]:
            if s in xls.sheet_names:
                df = pd.read_excel(xls, sheet_name=s)
                for _, row in df.iterrows():
                    v_n = str(row['Attività'])
                    p_n = str(row['Partner'])
                    for m in MESI:
                        if m in df.columns:
                            val = float(row[m])
                            st.session_state['db'][s][m][v_n][p_n] = val
        st.success("Dati caricati!")

# --- CORPO CENTRALE ---
st.title("🛡️ Unipolservice Budget HUB")

tab1, tab2 = st.tabs(["🚗 CARROZZERIA", "🔧 MECCANICA"])

def show(sett, voci):
    st.subheader(f"Dati {sett}")
    # Griglia semplificata
    for v in voci:
        exp = st.expander(f"Attività: {v}")
        for p in PARTNER:
            cols = st.columns(6)
            st.write(f"Partner: {p}")
            for i, m in enumerate(MESI):
                idx = i % 6
                v_db = st.session_state['db'][sett][m][v][p]
                new_v = cols[idx].number_input(f"{m[:3]}", value=v_db, key=f"{sett}_{v}_{p}_{m}")
                st.session_state['db'][sett][m][v][p] = new_v

with tab1:
    show("Carrozzeria", V_CARR)

with tab2:
    show("Meccanica", V_MECC)
