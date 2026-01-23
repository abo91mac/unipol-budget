import streamlit as st
import pandas as pd
import io

st.set_page_config(page_title="Unipolservice Budget HUB 2.0", layout="wide")

# --- 1. CONFIGURAZIONE ---
MESI = ["GENNAIO", "FEBBRAIO", "MARZO", "APRILE", "MAGGIO", "GIUGNO", 
        "LUGLIO", "AGOSTO", "SETTEMBRE", "OTTOBRE", "NOVEMBRE", "DICEMBRE"]
PARTNER = ["KONECTA", "COVISIAN"]
VOCI_CARR = ["Gestione Contatti", "Ricontatto", "Documenti", "Firme Digitali", "Solleciti"]
VOCI_MECC = ["Solleciti Officine", "Ticket assistenza"]

# --- 2. SESSION STATE ---
if 'db' not in st.session_state:
    st.session_state['db'] = {s: {m: {v: {p: 0.0 for p in PARTNER} for v in (VOCI_CARR if s=="Carrozzeria" else VOCI_MECC)} for m in MESI} for s in ["Carrozzeria", "Meccanica"]}

# Inizializzazione percentuali: 100/12 = 8.33%
if 'pct_carr' not in st.session_state:
    st.session_state['pct_carr'] = {m: 8.33 for m in MESI}
if 'pct_mecc' not in st.session_state:
    st.session_state['pct_mecc'] = {m: 8.33 for m in MESI}

# --- 3. FUNZIONI EXCEL ---
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

def carica_excel():
    if st.session_state.uploader:
        xls = pd.ExcelFile(st.session_state.uploader)
        for sett in ["Carrozzeria", "Meccanica"]:
            if sett in xls.sheet_names:
                df = pd.read_excel(xls, sheet_name=sett)
                for _, row in df.iterrows():
                    v, p = row['Attività'], row['Partner']
                    for m in MESI:
                        if m in df.columns:
                            st.session_state['db'][sett][m][v][p] = float(row[m])
        st.toast("✅ Excel caricato!")

# --- 4. SIDEBAR - DISTRIBUZIONE BUDGET ---
st.sidebar.title("⚙️ HUB Control Panel")
st.sidebar.download_button("📥 Template", data=crea_template(), file_name="Template.xlsx")
st.sidebar.file_uploader("📂 Carica Excel", type="xlsx", key="uploader", on_change=carica_excel)

def distribution_section(label, key_dict):
    st.sidebar.divider()
    st.sidebar.subheader(f"📊 Distribuzione % {label}")
    
    if st.sidebar.button(f"Reset Equo (8.33%)", key=f"res_{label}"):
        for m in MESI: st.session_state[key_dict][m] = 8.33
        st.rerun()

    total = sum(st.session_state[key_dict].values())
    st.sidebar.write(f"Somma attuale: **{total:.2f}%**")
    
    if abs(total - 100) > 0.05:
        st.sidebar.error("⚠️ La somma deve essere 100%")
    else:
        st.sidebar.success("✅ Somma corretta")

    # Campi editabili per le percentuali
    for m in MESI:
        st.session_state[key_dict][m] = st.sidebar.number_input(
            f"{m} %", 0.0, 100.0, st.session_state[key_dict][m], 0.01, key=f"inp_{label}_{m}"
        )

distribution_section("Carrozzeria", 'pct_carr')
distribution_section("Meccanica", 'pct_mecc')

# --- 5. RENDER DASHBOARD ---
def render_dashboard(settore, budget_annuale, voci, pct_key):
    st.header(f"Gestione {settore}")
    
    # --- TABELLA INPUT ORIZZONTALE ---
    st.subheader("📝 Input Consuntivi (Orizzontale)")
    cols = st.columns([2, 1] + [1]*12)
    cols[0].write("**Attività**")
    cols[1].write("**Partner**")
    for i, m in enumerate(MESI): cols[i+2].write(f"**{m[:3]}**")

    for v in voci:
        for p in PARTNER:
            c = st.columns([2, 1] + [1]*12)
            c[0].write(v)
            c[1].
