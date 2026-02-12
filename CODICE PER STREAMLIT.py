import streamlit as st
import pandas as pd
import io

# --- 1. SETUP ---
st.set_page_config(layout="wide", page_title="Unipol Budget")

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
    st.session_state['v'] = "12.0"

if 'v' not in st.session_state:
    r_db()

# --- 3. TEMPLATE ---
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
    
    st.download_button(
        "📥 Scarica Template Excel",
        crea_template(),
        "Template_Budget.xlsx"
    )
    
    st.divider()
    u = st.file_uploader("📂 Carica Excel", type="xlsx")
    
    if u:
        try:
            x = pd.ExcelFile(u)
            for sk, sn in [("C", "Carrozzeria"), ("M", "Meccanica")]:
                if sn in x.sheet_names:
                    df = pd.read_excel(x, sheet_name=sn)
                    for _, row in df.iterrows():
                        v_f = str(row['Attività']).strip()
                        p_f = str(row['Partner']).strip()
                        # Controllo esistenza chiave
                        if v_f in st.session_state['db'][sk][M[0]]:
                            for m in M:
                                if m in df.columns:
                                    val = float(row[m])
                                    st.session_state['db'][sk][m][v_f][p_f] = val
            st.success("Dati caricati!")
        except Exception as e:
            st.error(f"Errore: {e}")

    if st.button("🗑️ RESET"):
        r_db()
        st.rerun()
    
    bc = st.number_input("Budget Carrozzeria", 386393.0)
    bm = st.number_input("
