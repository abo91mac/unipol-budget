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

# Inizializzazione slider: distribuzione equa (100/12 = 8.33%)
if 'sl_carr' not in st.session_state:
    st.session_state['sl_carr'] = {m: 8.33 for m in MESI}
if 'sl_mecc' not in st.session_state:
    st.session_state['sl_mecc'] = {m: 8.33 for m in MESI}

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

def manual_slider_section(label, key_dict):
    st.sidebar.subheader(f"📊 Distribuzione % {label}")
    current_sum = sum(st.session_state[key_dict].values())
    st.sidebar.write(f"Totale attuale: **{current_sum:.2f}%**")
    if abs(current_sum - 100) > 0.1:
        st.sidebar.warning("⚠️ La somma deve essere 100%")
    else:
        st.sidebar.success("✅ Distribuzione corretta")
    
    for m in MESI:
        st.session_state[key_dict][m] = st.sidebar.slider(f"{m} ({label[:4]})", 0.0, 100.0, st.session_state[key_dict][m], 0.01, key=f"sl_{label}_{m}")

manual_slider_section("Carrozzeria", 'sl_carr')
manual_slider_section("Meccanica", 'sl_mecc')

# --- 5. RENDER DASHBOARD ---
def render_dashboard(settore, budget_annuale, voci, slider_key):
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
            c[1].write(p)
            for i, m in enumerate(MESI):
                val_db = st.session_state['db'][settore][m][v][p]
                st.session_state['db'][settore][m][v][p] = c[i+2].number_input("€", value=val_db, key=f"in_{settore}_{v}_{p}_{m}", label_visibility="collapsed")

    # --- ANALISI RIEPILOGO ---
    st.divider()
    st.subheader("📉 Analisi Budget vs Reale")
    report = []
    distribuzione = st.session_state[slider_key]
    
    for m in MESI:
        # Il target è la % del budget totale impostata dallo slider
        target_m = (budget_annuale * distribuzione[m]) / 100
        reale_m = sum(st.session_state['db'][settore][m][v][p] for v in voci for p in PARTNER)
        
        report.append({
            "Mese": m,
            "Peso %": f"{distribuzione[m]:.2f}%",
            "Target (€)": round(target_m, 2),
            "Consuntivo (€)": round(reale_m, 2),
            "Delta (€)": round(target_m - reale_m, 2)
        })
    
    df_rep = pd.DataFrame(report)
    
    # Metriche
    speso = df_rep["Consuntivo (€)"].sum()
    c1, c2, c3 = st.columns(3)
    c1.metric("Speso Totale", f"{speso:,.2f} €")
    c2.metric("Residuo Annuale", f"{(budget_annuale - speso):,.2f} €")
    c3.metric("Budget Allocato", f"{budget_annuale:,.2f} €")

    st.table(df_rep.set_index("Mese"))
    st.bar_chart(df_rep.set_index("Mese")[["Target (€)", "Consuntivo (€)"]])

# --- MAIN ---
st.title("🛡️ Unipolservice Budget HUB 2.0")
b_carr = st.sidebar.number_input("Budget Annuale Carrozzeria", 386393.0)
b_mecc = st.sidebar.number_input("Budget Annuale Meccanica", 120000.0)

t1, t2 = st.tabs(["🚗 CARROZZERIA", "🔧 MECCANICA"])
with t1: render_dashboard("Carrozzeria", b_carr, VOCI_CARR, 'sl_carr')
with t2: render_dashboard("Meccanica", b_mecc, VOCI_MECC, 'sl_mecc')
