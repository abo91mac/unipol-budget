import streamlit as st
import pandas as pd
import io
import os
from PIL import Image

# 1. SETUP PAGINA
st.set_page_config(page_title="Unipol Budget HUB", layout="wide")

# 2. GESTIONE LOGO
# Usiamo un blocco 'try' per evitare che il logo blocchi l'intera app
if os.path.exists('logo.png'):
    try:
        st.sidebar.image('logo.png')
    except Exception:
        st.sidebar.warning("Caricamento logo in corso...")

# 3. DATI E INIZIALIZZAZIONE
MESI = ["GENNAIO", "FEBBRAIO", "MARZO", "APRILE", "MAGGIO", "GIUGNO", 
        "LUGLIO", "AGOSTO", "SETTEMBRE", "OTTOBRE", "NOVEMBRE", "DICEMBRE"]
PARTNER = ["KONECTA", "COVISIAN"]
VOCI_CARR = ["Gestione Contatti", "Ricontatto", "Documenti", "Firme Digitali", "Solleciti"]
VOCI_MECC = ["Solleciti Officine", "Ticket assistenza"]

if 'db' not in st.session_state:
    st.session_state['db'] = {s: {m: {v: {p: 0.0 for p in PARTNER} for v in (VOCI_CARR if s=="Carrozzeria" else VOCI_MECC)} for m in MESI} for s in ["Carrozzeria", "Meccanica"]}
if 'pct_carr' not in st.session_state:
    st.session_state['pct_carr'] = {m: 8.33 for m in MESI}
if 'pct_mecc' not in st.session_state:
    st.session_state['pct_mecc'] = {m: 8.33 for m in MESI}

# 4. FUNZIONI EXCEL
def crea_template():
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        for sett, voci in [("Carrozzeria", VOCI_CARR), ("Meccanica", VOCI_MECC)]:
            data = []
            for v in voci:
                for p in PARTNER:
                    row = {"Attività": v, "Partner": p}
                    for m in MESI: row[m] = 0.0
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
                    for m in MESI: r[m] = st.session_state['db'][sett][m][v][p]
                    rows.append(r)
            pd.DataFrame(rows).to_excel(writer, sheet_name=sett, index=False)
    return output.getvalue()

# 5. SIDEBAR
st.sidebar.title("⚙️ Controllo Budget")
st.sidebar.download_button("📥 Scarica Template", data=crea_template(), file_name="Template.xlsx")
st.sidebar.download_button("📤 Esporta Dati", data=esporta_consolidato(), file_name="Budget_Consolidato.xlsx")
b_carr = st.sidebar.number_input("Budget Carrozzeria (€)", 386393.0)
b_mecc = st.sidebar.number_input("Budget Meccanica (€)", 120000.0)

# 6. FUNZIONE DASHBOARD
def render_dashboard(settore, budget_totale, voci, pct_key):
    with st.expander(f"📅 Distribuzione % Mensile {settore}"):
        cols_pct = st.columns(6)
        for i, m in enumerate(MESI):
            st.session_state[pct_key][m] = cols_pct[i%6].number_input(f"{m} %", 0.0, 100.0, st.session_state[pct_key][m], key=f"p_{settore}_{m}")
    
    st.subheader(f"📝 Input {settore}")
    for v in voci:
        st.write(f"**{v}**")
        c = st.columns(12)
        for i, m in enumerate(MESI):
            val = st.session_state['db'][settore][m][v]["KONECTA"]
            st.session_state['db'][settore][m][v]["KONECTA"] = c[i].number_input(m[:3], value=val, key=f"in_{settore}_{v}_{m}", label_visibility="collapsed")
    
    st.divider()
    rep = []
    for m in MESI:
        tar = (budget_totale * st.session_state[pct_key][m]) / 100
        cons = sum(st.session_state['db'][settore][m][v][p] for v in voci for p in PARTNER)
        rep.append({"Mese": m, "Target": tar, "Consuntivo": cons, "Delta": tar - cons})
    
    df = pd.DataFrame(rep).set_index("Mese")
    st.table(df.style.format(precision=2))

# 7. TABS PRINCIPALI
st.title("🛡️ Unipolservice Budget HUB")
t1, t2 = st.tabs(["🚗 CARROZZERIA", "🔧 MECCANICA"])
with t1: render_dashboard("Carrozzeria", b_carr, VOCI_CARR, 'pct_carr')
with t2: render_dashboard("Meccanica", b_mecc, VOCI_MECC, 'pct_mecc')
