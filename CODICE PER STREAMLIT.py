import streamlit as st
import pandas as pd
import io
import os

# --- 1. SETUP ---
st.set_page_config(page_title="Unipol HUB", layout="wide")

# --- 2. COSTANTI ---
MESI = ["GENNAIO", "FEBBRAIO", "MARZO", "APRILE", "MAGGIO", "GIUGNO", 
        "LUGLIO", "AGOSTO", "SETTEMBRE", "OTTOBRE", "NOVEMBRE", "DICEMBRE"]
PARTNER = ["KONECTA", "COVISIAN"]
V_CARR = ["Gestione Contatti", "Ricontatto", "Documenti", "Firme Digitali", "Solleciti"]
V_MECC = ["Solleciti Officine", "Ticket assistenza"]

# --- 3. INIT SESSION ---
if 'db' not in st.session_state:
    db = {}
    for s in ["Carrozzeria", "Meccanica"]:
        db[s] = {}
        voci = V_CARR if s == "Carrozzeria" else V_MECC
        for m in MESI:
            db[s][m] = {}
            for v in voci:
                db[s][m][v] = {"KONECTA": 0.0, "COVISIAN": 0.0}
    st.session_state['db'] = db

if 'pct_carr' not in st.session_state:
    st.session_state['pct_carr'] = {m: 8.33 for m in MESI}
if 'pct_mecc' not in st.session_state:
    st.session_state['pct_mecc'] = {m: 8.33 for m in MESI}

# --- 4. FUNZIONI EXCEL ---
def crea_template():
    out = io.BytesIO()
    with pd.ExcelWriter(out, engine='xlsxwriter') as writer:
        for sett, voci in [("Carrozzeria", V_CARR), ("Meccanica", V_MECC)]:
            data = []
            for v in voci:
                for p in PARTNER:
                    row = {"Attività": v, "Partner": p}
                    for m in MESI: row[m] = 0.0
                    data.append(row)
            pd.DataFrame(data).to_excel(writer, sheet_name=sett, index=False)
    return out.getvalue()

def esporta_dati():
    out = io.BytesIO()
    with pd.ExcelWriter(out, engine='xlsxwriter') as writer:
        for s in ["Carrozzeria", "Meccanica"]:
            voci = V_CARR if s == "Carrozzeria" else V_MECC
            rows = []
            for v in voci:
                for p in PARTNER:
                    r = {"Attività": v, "Partner": p}
                    for m in MESI:
                        r[m] = st.session_state['db'][s][m][v][p]
                    rows.append(r)
            pd.DataFrame(rows).to_excel(writer, sheet_name=s, index=False)
    return out.getvalue()

# --- 5. SIDEBAR ---
with st.sidebar:
    st.title("🛡️ Pannello")
    st.download_button("📥 Template", crea_template(), "Template.xlsx")
    st.download_button("📤 Esporta", esporta_dati(), "Export.xlsx")
    
    st.divider()
    up = st.file_uploader("📂 Carica Excel", type="xlsx")
    if up:
        try:
            xls = pd.ExcelFile(up)
            for s in ["Carrozzeria", "Meccanica"]:
                if s in xls.sheet_names:
                    df = pd.read_excel(xls, sheet_name=s)
                    for _, row in df.iterrows():
                        # Righe spezzate per evitare troncamenti
                        v_nom = str(row['Attività'])
                        p_nom = str(row['Partner'])
                        for m in MESI:
                            if m in df.columns:
                                val = float(row[m])
                                st.session_state['db'][s][m][v_nom][p_nom] = val
            st.success("Caricato!")
        except Exception as e:
            st.error(f"Errore: {e}")

    if st.button("🗑️ RESET"):
        st.session_state.clear()
        st.rerun()

    b_c = st.number_input("Budget Carr. (€)", value=386393.0)
    b_m = st.number_input("Budget Mecc. (€)", value=120000.0)

# --- 6. DASHBOARD ---
def render_dashboard(sett, budget, voci, p_key):
    with st.expander(f"📅 % {sett}"):
        c_p = st.columns(6)
        for i, m in enumerate(MESI):
            val = st.session_state[p_key][m]
            st.session_state[p_key][m] = c_p[i%6].number_input(
                f"{m} %", 0.0, 100.0, val, key=f"p_{sett}_{m}"
            )

    st.subheader("📝 Consuntivi")
    h = st.columns([2, 1] + [1]*12)
    h[0].write("**Attività**"); h[1].write("**Partner**")
    for i, m in enumerate(MESI): h[i+2].write(f"**{m
