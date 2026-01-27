import streamlit as st
import pandas as pd
import io
import os
from PIL import Image

# Configurazione base
st.set_page_config(page_title="Unipol Budget", layout="wide")

# Inizializzazione dati
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

# Funzioni Excel
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

# Sidebar
st.sidebar.title("Unipol HUB")
if os.path.exists('logo.png'):
    st.sidebar.image('logo.png')
st.sidebar.download_button("Scarica Template", data=crea_template(), file_name="Template.xlsx")
st.sidebar.divider()
b_carr = st.sidebar.number_input("Budget Carrozzeria", 386393.0)
b_mecc = st.sidebar.number_input("Budget Meccanica", 120000.0)

# Dashboard
def render_dashboard(settore, budget_totale, voci, pct_key):
    with st.expander(f"Distribuzione % {settore}"):
        cols = st.columns(6)
        for i, m in enumerate(MESI):
            st.session_state[pct_key][m] = cols[i%6].number_input(f"{m} %", 0.0, 100.0, st.session_state[pct_key][m], key=f"p_{settore}_{m}")
    
    st.subheader(f"Input {settore}")
    for v in voci:
        with st.container():
            st.write(f"**{v}**")
            cols_in = st.columns(12)
            for i, m in enumerate(MESI):
                val = st.session_state['db'][settore][m][v]["KONECTA"] # Esempio semplificato
                st.session_state['db'][settore][m][v]["KONECTA"] = cols_in[i].number_input(f"{m[:3]}", value=val, key=f"{settore}_{v}_{m}", label_visibility="collapsed")
    
    st.divider()
    # Report semplificato per test
    st.write(f"Analisi Budget {settore}")
    res = [{"Mese": m, "Budget": (budget_totale * st.session_state[pct_key][m] / 100)} for m in MESI]
    st.table(pd.DataFrame(res))

# Tabs
t1, t2 = st.tabs(["CARROZZERIA", "MECCANICA"])
with t1: render_dashboard("Carrozzeria", b_carr, VOCI_CARR, 'pct_carr')
with t2: render_dashboard("Meccanica", b_mecc, VOCI_MECC, 'pct_mecc')
