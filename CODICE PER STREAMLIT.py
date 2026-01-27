import streamlit as st
import pandas as pd
import io
import os
from PIL import Image

# 1. SETUP PAGINA
st.set_page_config(page_title="Unipolservice Budget HUB", layout="wide")

# 2. GESTIONE LOGO (Nella Sidebar)
# L'app cercherà il file 'logo.png' che hai caricato
if os.path.exists('logo.png'):
    st.sidebar.image('logo.png', use_container_width=True)

# 3. DATI FISSI
MESI = ["GENNAIO", "FEBBRAIO", "MARZO", "APRILE", "MAGGIO", "GIUGNO", 
        "LUGLIO", "AGOSTO", "SETTEMBRE", "OTTOBRE", "NOVEMBRE", "DICEMBRE"]
PARTNER = ["KONECTA", "COVISIAN"]
VOCI_CARR = ["Gestione Contatti", "Ricontatto", "Documenti", "Firme Digitali", "Solleciti"]
VOCI_MECC = ["Solleciti Officine", "Ticket assistenza"]

# 4. INIZIALIZZAZIONE SESSION STATE
if 'db' not in st.session_state:
    st.session_state['db'] = {s: {m: {v: {p: 0.0 for p in PARTNER} for v in (VOCI_CARR if s=="Carrozzeria" else VOCI_MECC)} for m in MESI} for s in ["Carrozzeria", "Meccanica"]}
if 'pct_carr' not in st.session_state:
    st.session_state['pct_carr'] = {m: 8.33 for m in MESI}
if 'pct_mecc' not in st.session_state:
    st.session_state['pct_mecc'] = {m: 8.33 for m in MESI}

# 5. SIDEBAR
st.sidebar.header("⚙️ Budget Annuale")
budget_carr = st.sidebar.number_input("Carrozzeria (€)", 386393.0)
budget_mecc = st.sidebar.number_input("Meccanica (€)", 120000.0)

# 6. FUNZIONE DASHBOARD
def render_dashboard(settore, budget_totale, voci, pct_key):
    # Distribuzione %
    with st.expander(f"📅 Distribuzione Percentuale Mensile - {settore}"):
        st.write("Inserisci la % di budget per ogni mese")
        c_pct = st.columns(6)
        for i, m in enumerate(MESI):
            st.session_state[pct_key][m] = c_pct[i%6].number_input(f"{m} %", 0.0, 100.0, st.session_state[pct_key][m], key=f"p_{settore}_{m}")
    
    st.write("---")
    
    # Input Tabellare
    st.subheader(f"📝 Inserimento Consuntivi {settore}")
    h_cols = st.columns([2, 1] + [1]*12)
    h_cols[0].write("**Attività**")
    h_cols[1].write("**Partner**")
    for i, m in enumerate(MESI): 
        h_cols[i+2].write(f"**{m[:3]}**")

    for v in voci:
        for p in PARTNER:
            r_cols = st.columns([2, 1] + [1]*12)
            r_cols[0].write(v)
            r_cols[1].write(p)
            for i, m in enumerate(MESI):
                k = f"in_{settore}_{v}_{p}_{m}"
                st.session_state['db'][settore][m][v][p] = r_cols[i+2].number_input("€", value=st.session_state['db'][settore][m][v][p], key=k, label_visibility="collapsed")

    # Report
    st.write("---")
    rep = []
    for m in MESI:
        tar = (budget_totale * st.session_state[pct_key][m]) / 100
        cons = sum(st.session_state['db'][settore][m][v][p] for v in voci for p in PARTNER)
        rep.append({"Mese": m, "Target": tar, "Consuntivo": cons, "Delta": tar - cons})
    
    df_final = pd.DataFrame(rep).set_index("Mese")
    st.table(df_final.style.format(precision=2))
    st.bar_chart(df_final[["Target", "Consuntivo"]])

# 7. TABS
st.title("🛡️ Unipolservice Budget HUB")
tab_carr, tab_mecc = st.tabs(["🚗 CARROZZERIA", "🔧 MECCANICA"])

with tab_carr:
    render_dashboard("Carrozzeria", budget_carr, VOCI_CARR, 'pct_carr')

with tab_mecc:
    render_dashboard("Meccanica", budget_mecc, VOCI_MECC, 'pct_mecc')
