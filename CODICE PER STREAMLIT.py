import streamlit as st
import pandas as pd
import io
import os

# --- 1. CONFIGURAZIONE PAGINA ---
st.set_page_config(page_title="Unipolservice Budget HUB", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #f4f7f9; }
    .stTabs [aria-selected="true"] { background-color: #003399 !important; color: white !important; }
    .stButton>button { background-color: #003399; color: white; border-radius: 5px; width: 100%; }
    div[data-testid="stMetricValue"] { color: #003399; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. COSTANTI ---
MESI = ["GENNAIO", "FEBBRAIO", "MARZO", "APRILE", "MAGGIO", "GIUGNO", 
        "LUGLIO", "AGOSTO", "SETTEMBRE", "OTTOBRE", "NOVEMBRE", "DICEMBRE"]
PARTNER = ["KONECTA", "COVISIAN"]
VOCI_CARR = ["Gestione Contatti", "Ricontatto", "Documenti", "Firme Digitali", "Solleciti"]
VOCI_MECC = ["Solleciti Officine", "Ticket assistenza"]

# --- 3. FUNZIONI CORE ---
def reset_dati():
    st.session_state['db'] = {s: {m: {v: {p: 0.0 for p in PARTNER} for v in (VOCI_CARR if s=="Carrozzeria" else VOCI_MECC)} for m in MESI} for s in ["Carrozzeria", "Meccanica"]}
    st.session_state['pct_carr'] = {m: 8.33 for m in MESI}
    st.session_state['pct_mecc'] = {m: 8.33 for m in MESI}

if 'db' not in st.session_state:
    reset_dati()

# --- 4. LOGICA EXCEL ---
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

# --- 5. SIDEBAR ---
with st.sidebar:
    st.title("🛡️ Unipolservice")
    st.download_button("📥 Scarica Template", data=crea_template(), file_name="Template.xlsx")
    st.download_button("📤 Esporta Dati", data=esporta_consolidato(), file_name="Export.xlsx")
    
    st.divider()
    uploaded_file = st.file_uploader("📂 Carica Excel", type="xlsx")
    
    if uploaded_file:
        try:
            xls = pd.ExcelFile(uploaded_file)
            for sett in ["Carrozzeria", "Meccanica"]:
                if sett in xls.sheet_names:
                    df = pd.read_excel(xls, sheet_name=sett)
                    for _, row in df.iterrows():
                        v, p = str(row['Attività']), str(row['Partner'])
                        for m in MESI:
                            if m in df.columns:
                                # AGGIORNAMENTO DIRETTO DEL DATABASE
                                st.session_state['db'][sett][m][v][p] = float(row[m])
            st.success("Dati importati!")
            # Il rerun è fuori dal callback, quindi ora funziona
            if st.button("🔄 Applica Modifiche"):
                st.rerun()
        except Exception as e:
            st.error(f"Errore: {e}")

    if st.button("🗑️ RESET TOTALE"):
        reset_dati()
        st.rerun()

    st.divider()
    b_carr = st.number_input("Budget Carrozzeria (€)", value=386393.0)
    b_mecc = st.number_input("Budget Meccanica (€)", value=120000.0)

# --- 6. DASHBOARD ---
def render_dashboard(settore, budget_totale, voci, pct_key):
    # 1. Percentuali
    with st.expander(f"📅 Distribuzione % {settore}"):
        cols_p = st.columns(6)
        for i, m in enumerate(MESI):
            st.session_state[pct_key][m] = cols_p[i%6].number_input(f"{m} %", 0.0, 100.0, st.session_state[pct_key][m], key=f"p_{settore}_{m}")

    # 2. Inserimento Consuntivi
    st.subheader("📝 Inserimento Consuntivi")
    header = st.columns([2, 1] + [1]*12)
    header[0].write("**Attività**"); header[1].write("**Partner**")
    for i, m in enumerate(MESI): header[i+2].write(f"**{m[:3]}**")

    for v in voci:
        for p in PARTNER:
            r_cols = st.columns([2, 1] + [1]*12)
            r_cols[0].write(v)
            r_cols[1].write(p)
            for i, m in enumerate(MESI):
                # Chiave univoca per il widget
                k = f"in_{settore}_{v}_{p}_{m}"
                
                # Questa riga è il segreto: leggiamo il valore dal database 
                # e
