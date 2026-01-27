import streamlit as st
import pandas as pd
import io
import os

# --- 1. SETUP ---
st.set_page_config(page_title="Unipolservice Budget HUB", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #f4f7f9; }
    .stTabs [aria-selected="true"] { 
        background-color: #003399 !important; 
        color: white !important; 
    }
    .stButton>button { 
        background-color: #003399; 
        color: white; 
        border-radius: 5px; 
    }
    div.stButton > button:first-child { 
        background-color: #ff4b4b; 
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. COSTANTI ---
MESI = ["GENNAIO", "FEBBRAIO", "MARZO", "APRILE", "MAGGIO", "GIUGNO", 
        "LUGLIO", "AGOSTO", "SETTEMBRE", "OTTOBRE", "NOVEMBRE", "DICEMBRE"]
PARTNER = ["KONECTA", "COVISIAN"]
V_CARR = ["Gestione Contatti", "Ricontatto", "Documenti", "Firme Digitali", "Solleciti"]
V_MECC = ["Solleciti Officine", "Ticket assistenza"]

# --- 3. LOGICA DATI ---
def reset_dati():
    db = {}
    for s in ["Carrozzeria", "Meccanica"]:
        db[s] = {}
        voci_sett = V_CARR if s == "Carrozzeria" else V_MECC
        for m in MESI:
            db[s][m] = {}
            for v in voci_sett:
                db[s][m][v] = {"KONECTA": 0.0, "COVISIAN": 0.0}
    st.session_state['db'] = db
    
    # Inizializzazione percentuali (righe spezzate per sicurezza)
    p_c = {}
    p_m = {}
    for mese in MESI:
        p_c[mese] = 8.33
        p_m[mese] = 8.33
    st.session_state['pct_carr'] = p_c
    st.session_state['pct_mecc'] = p_m

if 'db' not in st.session_state:
    reset_dati()

# --- 4. EXCEL ---
def crea_template():
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        for sett in ["Carrozzeria", "Meccanica"]:
            voci = V_CARR if sett == "Carrozzeria" else V_MECC
            righe = []
            for v in voci:
                for p in PARTNER:
                    r = {"Attività": v, "Partner": p}
                    for m in MESI: 
                        r[m] = 0.0
                    righe.append(r)
            pd.DataFrame(righe).to_excel(writer, sheet_name=sett, index=False)
    return output.getvalue()

def esporta_consolidato():
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        for sett in ["Carrozzeria", "Meccanica"]:
            voci = V_CARR if sett == "Carrozzeria" else V_MECC
            righe = []
            for v in voci:
                for p in PARTNER:
                    r = {"Attività": v, "Partner": p}
                    for m in MESI: 
                        r[m] = st.session_state['db'][sett][m][v][p]
                    righe.append(r)
            pd.DataFrame(righe).to_excel(writer, sheet_name=sett, index=False)
    return output.getvalue()

def carica_excel():
    if st.session_state.uploader:
        try:
            xls = pd.ExcelFile(st.session_state.uploader)
            for sett in ["Carrozzeria", "Meccanica"]:
                if sett in xls.sheet_names:
                    df = pd.read_excel(xls, sheet_name=sett)
                    for _, row in df.iterrows():
                        v = str(row['Attività'])
                        p = str(row['Partner'])
                        for m in MESI:
                            if m in df.columns:
                                val = float(row[m])
                                st.session_state['db'][sett][m][v][p] = val
            st.toast("✅ Caricato!")
        except Exception as e:
            st.error(f"Errore: {e}")

# --- 5. SIDEBAR ---
with st.sidebar:
    if os.path.exists('logo.png'): 
        st.image('logo.png')
    if st.button("🗑️ RESET DATI"):
        reset_dati()
        st.rerun()
    st.divider()
    st.download_button("📥 Template", data=crea_template(), file_name="Template.xlsx")
    st.download_button("📤 Esporta", data=esporta_consolidato(), file_name="Dati.xlsx")
    st.file_uploader("📂 Carica", type="xlsx", key="uploader", on_change=carica_excel)
    st.divider()
    b_c = st.number_input("Budget Carr. (€)", value=386393.0)
    b_m = st.number_input("Budget Mecc. (€)", value=120000.0)

# --- 6. DASHBOARD ---
def render_dashboard(settore, budget_totale, voci, pct_key):
    with st.expander(f"📅 Distribuzione % {settore}"):
        cols = st.columns(6)
        for i, m in enumerate(MESI):
            val_p = st.session_state[pct_key][m]
            new_p = cols[i%6].number_input(f"{m} %", 0.0, 100.0, val_p, key=f"p_{settore}_{m}")
            st.session_state[pct_key][m] = new_p
    
    for v in voci:
        st.write(f"**{v}**")
        r_cols = st.columns(12)
        for i, m in enumerate(MESI):
            val = st.session_state['db'][settore][m][v]["KONECTA"]
            key_in = f"in_{settore}_{v}_{m}"
            new_v = r_cols[i].number_input(m[:3], value=val, key=key_in, label_visibility="collapsed")
            st.session_state['db'][settore][m][v]["KONECTA"] = new_v

    rep = []
    for m in MESI:
        tar = (budget_totale * st.session_state[pct_key][m]) / 100
        cons = sum(st.session_state['db'][settore])
