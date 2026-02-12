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
if 'db' not in st.session_state:
    db = {}
    for sk in ["C", "M"]:
        db[sk] = {}
        voci = VC if sk == "C" else VM
        for m in M:
            db[sk][m] = {v: {p: 0.0 for p in P} for v in voci}
    st.session_state['db'] = db
    st.session_state['pct'] = {m: 8.33 for m in M}

# --- 3. FUNZIONE EXPORT ---
def genera_export():
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        for sk, sn in [("C", "Carrozzeria"), ("M", "Meccanica")]:
            v_list = VC if sk == "C" else VM
            rows = []
            for v in v_list:
                for p in P:
                    r = {"Attività": v, "Partner": p}
                    for m in M:
                        r[m] = st.session_state['db'][sk][m][v][p]
                    rows.append(r)
            pd.DataFrame(rows).to_excel(writer, sheet_name=sn, index=False)
    return output.getvalue()

# --- 4. SIDEBAR ---
with st.sidebar:
    st.title("🛡️ Pannello")
    
    # PULSANTE EXPORT
    st.download_button(
        label="📥 Scarica Export Consolidato",
        data=genera_export(),
        file_name="Export_Budget_Consolidato.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    
    st.divider()
    
    with st.expander("% Budget Mensile"):
        for m in M:
            v_pct = st.session_state['pct'].get(m, 8.33)
            st.session_state['pct'][m] = st.number_input(m, value=v_pct, key=f"p_{m}")
    
    st.divider()
    u = st.file_uploader("📂 Carica Excel", type="xlsx")
    
    if u:
        try:
            x = pd.ExcelFile(u)
            contatore = 0
            for sk, sn in [("C", "Carrozzeria"), ("M
