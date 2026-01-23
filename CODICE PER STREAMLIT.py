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

# --- 2. INIZIALIZZAZIONE SESSIONE ---
if 'db' not in st.session_state:
    st.session_state['db'] = {
        "Carrozzeria": {m: {v: {p: 0.0 for p in PARTNER} for v in VOCI_CARR} for m in MESI},
        "Meccanica": {m: {v: {p: 0.0 for p in PARTNER} for v in VOCI_MECC} for m in MESI}
    }
    st.session_state['note'] = {"Carrozzeria": {m: "" for m in MESI}, "Meccanica": {m: "" for m in MESI}}
if 'v' not in st.session_state: 
    st.session_state['v'] = 0

# --- 3. FUNZIONI EXCEL ---
def crea_template():
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        for sett, voci in [("Carrozzeria", VOCI_CARR), ("Meccanica", VOCI_MECC)]:
            rows = []
            for m in MESI:
                for v in voci:
                    for p in PARTNER:
                        rows.append({"Mese": m, "Attività": v, "Partner": p, "Importo": 0.0})
            pd.DataFrame(rows).to_excel(writer, sheet_name=sett, index=False)
    return output.getvalue()

def processa_caricamento():
    if st.session_state.uploader:
        try:
            xls = pd.ExcelFile(st.session_state.uploader)
            for sett in ["Carrozzeria", "Meccanica"]:
                if sett in xls.sheet_names:
                    df = pd.read_excel(xls, sheet_name=sett)
                    for _, row in df.iterrows():
                        m, v, p, val = row['Mese'], row['Attività'], row['Partner'], row['Importo']
                        if m in MESI and p in PARTNER:
                            st.session_state['db'][sett][m][v][p] = float(val)
            st.session_state['v'] += 1
            st.toast("✅ Excel caricato!")
        except Exception as e:
            st.error(f"Errore: {e}")

# --- 4. SIDEBAR ---
st.sidebar.title("⚙️ HUB Control Panel")
st.sidebar.download_button("📥 Scarica Template", data=crea_template(), file_name="Template_Budget.xlsx")
st.sidebar.file_uploader("📂 Carica Excel", type="xlsx", key="uploader", on_change=processa_caricamento)
st.sidebar.divider()
b_carr = st.sidebar.number_input("Budget Carrozzeria", value=386393.0)
b_mecc = st.sidebar.number_input("Budget Meccanica", value=120000.0)

# --- 5. RENDER DASHBOARD ---
def render_dashboard(settore, budget, voci):
    st.header(f"Sezione {settore}")
    
    # --- MODALITÀ MANUALE ---
    with st.expander(f"📝 Gestione Manuale {settore}", expanded=True):
        m_sel = st.selectbox(f"Mese ({settore})", MESI, key=f"sel_{settore}")
        st.session_state['note'][settore][m_sel] = st.text_area("Note:", value=st.session_state['note'][settore][m_sel], key=f"nt_{settore}_{m_sel}")
        
        for v in voci:
            st.write(f"**{v}**")
            c1, c2 = st.columns(2)
            with c1:
                k_val = st.number_input(f"K - {v}", value=st.session_state['db'][settore][m_sel][v]["KONECTA"], key=f"k_{settore}_{m_sel}_{v}_{st.session_state['v']}")
                st.session_state['db'][settore][m_sel][v]["KONECTA"] = k_val
            with c2:
                c_val = st.number_input(f"C - {v}", value=st.session_state['db'][settore][m_sel][v]["COVISIAN"], key=f"c_{settore}_{m_sel}_{v}_{st.session_state['v']}")
                st.session_state['db'][settore][m_sel][v]["COVISIAN"] = c_val

    # --- GRAFICI E TABELLA ---
    st.divider()
    report = []
    for m in MESI:
        k = sum(st.session_state['db'][settore][m][v]["KONECTA"] for v in voci)
        c = sum(st.session_state['db'][settore][m][v]["COVISIAN"] for v in voci)
        report.append({"Mese": m, "Budget": round(budget/12, 2), "Reale": round(k+c, 2), "K": k, "C": c})
    
    df = pd.DataFrame(report)
    st.metric("Speso Totale", f"{df['Reale'].sum():,.2f} €")
    st.dataframe(df, use_container_width=True)
    st.bar_chart(df.set_index("Mese")[["K", "C"]])

# --- 6. MAIN ---
st.title("🛡️ Unipolservice Budget HUB 2.0")
t1, t2 = st.tabs(["🚗 CARROZZERIA", "🔧 MECCANICA"])
with t1: render_dashboard("Carrozzeria", b_carr, VOCI_CARR)
with t2: render_dashboard("Meccanica", b_mecc, VOCI_MECC)
