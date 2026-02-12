import streamlit as st
import pandas as pd
import io

# --- 1. CONFIGURAZIONE ---
st.set_page_config(layout="wide", page_title="Unipol Budget HUB")

M = ["GENNAIO", "FEBBRAIO", "MARZO", "APRILE", "MAGGIO", "GIUGNO", 
     "LUGLIO", "AGOSTO", "SETTEMBRE", "OTTOBRE", "NOVEMBRE", "DICEMBRE"]
P = ["KONECTA", "COVISIAN"]
VC = ["Gestione Contatti", "Ricontatto", "Documenti", "Firme Digitali", "Solleciti"]
VM = ["Solleciti Officine", "Ticket assistenza"]

# --- 2. INIT ---
def r_db():
    d = {}
    for sk in ["C", "M"]:
        d[sk] = {}
        voci = VC if sk == "C" else VM
        for m in M:
            d[sk][m] = {v: {p: 0.0 for p in P} for v in voci}
    st.session_state['db'] = d
    st.session_state['pct'] = {m: 8.33 for m in M}
    st.session_state['v'] = "10.0"

if 'v' not in st.session_state:
    r_db()

# --- 3. FUNZIONE CREAZIONE TEMPLATE ---
def crea_template():
    out = io.BytesIO()
    with pd.ExcelWriter(out, engine='xlsxwriter') as writer:
        for sk, sn, voci in [("C", "Carrozzeria", VC), ("M", "Meccanica", VM)]:
            rows = []
            for v in voci:
                for p in P:
                    row = {"Attività": v, "Partner": p}
                    for m in M:
                        row[m] = 0.0
                    rows.append(row)
            pd.DataFrame(rows).to_excel(writer, sheet_name=sn, index=False)
    return out.getvalue()

# --- 4. SIDEBAR ---
with st.sidebar:
    st.title("🛡️ Pannello")
    
    # TASTO TEMPLATE
    st.download_button(
        label="📥 Scarica Template Excel",
        data=crea_template(),
        file_name="Template_Budget_Unipol.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    
    st.divider()
    
    # CARICAMENTO
    u = st.file_uploader("📂 Carica Excel Compilato", type="xlsx")
    if u:
        try:
            x = pd.ExcelFile(u)
            for sk, sn in [("C", "Carrozzeria"), ("M", "Meccanica")]:
                if sn in x.sheet_names:
                    df = pd.read_excel(x, sheet_name=sn)
                    for _, row in df.iterrows():
                        v_f = str(row['Attività']).strip()
                        p_f = str(row['Partner']).strip()
                        if v_f in st.session_state['db'][sk][M[0]]:
                            for m in M:
                                if m in df.columns:
                                    st.session_state['db'][sk][m][v_f][p
