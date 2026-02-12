import streamlit as st
import pandas as pd
import io

# --- 1. SETUP ---
st.set_page_config(layout="wide")

M = ["GENNAIO", "FEBBRAIO", "MARZO", "APRILE", "MAGGIO", "GIUGNO", 
     "LUGLIO", "AGOSTO", "SETTEMBRE", "OTTOBRE", "NOVEMBRE", "DICEMBRE"]
P = ["KONECTA", "COVISIAN"]
VC = ["Contatti", "Ricontatto", "Doc", "Firme", "Soll"]
VM = ["Soll Off", "Ticket"]

# --- 2. FUNZIONE RESET (SICURA) ---
def reset_db():
    db = {}
    for s in ["C", "M"]:
        db[s] = {}
        voci = VC if s == "C" else VM
        for mese in M:
            db[s][mese] = {v: {pt: 0.0 for pt in P} for v in voci}
    st.session_state['db'] = db
    st.session_state['pct'] = {mese: 8.33 for mese in M}
    st.session_state['ver'] = "4.0"

# Se la versione non coincide o il db manca, resetta
if 'ver' not in st.session_state or st.session_state['ver'] != "4.0":
    reset_db()

# --- 3. EXCEL LOGIC ---
def esporta():
    out = io.BytesIO()
    with pd.ExcelWriter(out, engine='xlsxwriter') as wr:
        for s_k, s_n in [("C", "Carrozzeria"), ("M", "Meccanica")]:
            voci = VC if s_k == "C" else VM
            rows = []
            for v in voci:
                for pt in P:
                    r = {"Attività": v, "Partner": pt}
                    for mese in M:
                        r[mese] = st.session_state['db'][s_k][mese][v][pt]
                    rows.append(r)
            pd.DataFrame(rows).to_excel(wr, sheet_name=s_n, index=False)
    return out.getvalue()

# --- 4. SIDEBAR ---
with st.sidebar:
    st.title("Pannello")
    up = st.file_uploader("Carica Excel", type="xlsx")
    if up:
        xls = pd.ExcelFile(up)
        for s_k, s_n in [("C", "Carrozzeria"), ("M", "Meccanica")]:
            if s_n in xls.sheet_names:
                df = pd.read_excel(xls, sheet_name=s_n)
                for _, row in df.iterrows():
                    v_n, p_n = str(row['Attività']), str(row['Partner'])
                    for mese in M:
                        if mese in df.columns and v_n in st.session_state['db'][s_k][mese]:
                            st.session_state['db'][s_k][mese][v_n][p_n] = float(row[mese])
        st.success("✅ Car
