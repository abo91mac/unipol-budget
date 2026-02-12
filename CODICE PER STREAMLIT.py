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
    # RIPRISTINO PERCENTUALI MENSILI
    st.session_state['pct'] = {m: 8.33 for m in M}
    st.session_state['v'] = "11.0"

if 'v' not in st.session_state:
    r_db()

# --- 3. SIDEBAR & LOGICA EXCEL ---
with st.sidebar:
    st.title("🛡️ Pannello")
    
    # SEZIONE PERCENTUALI (RIPRISTINATA)
    with st.expander("Percentuali Budget Mensile"):
        for m in M:
            st.session_state['pct'][m] = st.number_input(
                f"% {m}", value=st.session_state['pct'][m], step=0.01
            )
    
    st.divider()
    u = st.file_uploader("📂 Carica Excel", type="xlsx")
    
    if u:
        try:
            x = pd.ExcelFile(u)
            for sk, sn in [("C", "Carrozzeria"), ("M", "Meccanica")]:
                if sn in x.sheet_names:
                    df = pd.read_excel(x, sheet_name=sn)
                    # Normalizzazione colonne
                    df.columns = [str(c).strip().upper() for c in df.columns]
                    
                    for _, row in df.iterrows():
                        v_f = str(row.get('ATTIVITÀ', row.get('ATTIVITA', ''))).strip().upper()
                        p_f = str(row.get('PARTNER', '')).strip().upper()
                        
                        v_target = VC if sk == "C" else VM
                        for v_real in v_target:
                            # Confronto flessibile per trovare l'attività
                            if v_real.strip().upper() in v_f or v_f in v_real.strip().upper():
                                for p_real in P:
                                    if p_real in p_f or p_f in p_real:
                                        for m in M:
                                            if m in df.columns:
                                                val = float(row[m])
                                                st.session_state['db'][sk][m][v_real][p_real] = val
            st.success("✅ Dati caricati!")
        except Exception as e:
            st.error(f"Erro
