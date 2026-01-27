import streamlit as st
import pandas as pd
import io
from PIL import Image
import os

# --- 1. CONFIGURAZIONE PAGINA ---
st.set_page_config(page_title="Unipolservice Budget HUB 2.0", layout="wide")

# --- 2. GESTIONE LOGO ---
# Assicurati di caricare un file chiamato 'logo.png' su GitHub
logo_path = 'logo.png'
if os.path.exists(logo_path):
    logo = Image.open(logo_path)
    st.sidebar.image(logo, use_container_width=True)
else:
    st.sidebar.title("🛡️ Unipolservice HUB")

# --- 3. CONFIGURAZIONE DATI ---
MESI = ["GENNAIO", "FEBBRAIO", "MARZO", "APRILE", "MAGGIO", "GIUGNO", 
        "LUGLIO", "AGOSTO", "SETTEMBRE", "OTTOBRE", "NOVEMBRE", "DICEMBRE"]
PARTNER = ["KONECTA", "COVISIAN"]
VOCI_CARR = ["Gestione Contatti", "Ricontatto", "Documenti", "Firme Digitali", "Solleciti"]
VOCI_MECC = ["Solleciti Officine", "Ticket assistenza"]

# --- 4. SESSION STATE ---
if 'db' not in st.session_state:
    st.session_state['db'] = {s: {m: {v: {p: 0.0 for p in PARTNER} for v in (VOCI_CARR if s=="Carrozzeria" else VOCI_MECC)} for m in MESI} for s in ["Carrozzeria", "Meccanica"]}

if 'pct_carr' not in st.session_state:
    st.session_state['pct_carr'] = {m: 8.33 for m in MESI}
if 'pct_mecc' not in st.session_state:
    st.session_state['pct_mecc'] = {m: 8.33 for m in MESI}

# --- 5. FUNZIONI EXCEL ---
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

# --- 6. SIDEBAR ---
st.sidebar.title("⚙️ Pannello di Controllo")
st.sidebar.download_button("📥 Scarica Template", data=crea_template(), file_name="Template.xlsx")
st.sidebar.download_button("📤 Esporta Consolidato", data=esporta_consolidato(), file_name="Export_Budget.xlsx")

def distribution_section(label, key_dict):
    st.sidebar.divider()
    st.sidebar.subheader(f"📊 Distribuzione % {label}")
    total = sum(st.session_state[key_dict].values())
    st.sidebar.write(f"Somma: **{total:.2f}%**")
    if abs(total - 100) > 0.05: st.sidebar.error("La somma deve essere 100%")
    for m in MESI:
        st.session_state[key_dict][m] = st.sidebar.number_input(f"{m} % ({label[:2]})", 0.0, 100.0, st.session_state[key_dict][m], 0.01)

b_carr = st.sidebar.number_input("Budget Annuale Carrozzeria", 386393.0)
distribution_section("Carrozzeria", 'pct_carr')

st.sidebar.divider()
b_mecc = st.sidebar.number_input("Budget Annuale Meccanica", 120000.0)
distribution_section("Meccanica", 'pct_mecc')

# --- 7. DASHBOARD ---
def render_dashboard(settore, budget_annuale, voci, pct_key):
    st.subheader(f"📝 Inserimento Dati {settore}")
    cols = st.columns([2, 1] + [1]*12)
    cols[0].write("**Attività**"); cols[1].write("**Partner**")
    for i, m in enumerate(MESI): cols[i+2].write(f"**{m[:3]}**")

    for v in voci:
        for p in PARTNER:
            c = st.columns([2, 1] + [1]*12)
            c[0].write(v); c[1].write(p)
            for i, m in enumerate(MESI):
                val_db = st.session_state['db'][settore][m][v][p]
                st.session_state['db'][settore][m][v][p] = c[i+2].number_input("€", value=val_db, key=f"in_{settore}_{v}_{p}_{m}", label_visibility="collapsed")

    st.divider()
    report = []
    dist = st.session_state[pct_key]
    for m in MESI:
        target_m = (budget_annuale * dist[m]) / 100
        reale_m = sum(st.session_state['db'][settore][m][v][p] for v in voci for p in PARTNER)
        report.append({"Mese": m, "Target (€)": target_m, "Consuntivo (€)": reale_m, "Delta (€)": target_m - reale_m})
    
    df_rep = pd.DataFrame(report)
    st.table(df_rep.set_index("Mese").style.format(precision=2))
    st.bar_chart(df_rep.set_index("Mese")[["Target (€)", "Consuntivo (€)"]])

st.title("🛡️ Unipolservice Budget HUB 2.0")
t1, t2 = st.tabs(["🚗 CARROZZERIA", "🔧 MECCANICA"])
with t1: render_dashboard("Carrozzeria", b_carr, VOCI_CARR, 'pct_carr')
with t2: render_dashboard("Meccanica", b_mecc, VOCI_MECC, 'pct_mecc')
