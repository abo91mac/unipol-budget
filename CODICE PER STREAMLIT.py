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

if 'impatti' not in st.session_state:
    # Impatti separati per Carrozzeria e Meccanica, inizializzati al 100% (1.0)
    st.session_state['impatti'] = {
        "Carrozzeria": {m: 1.0 for m in MESI},
        "Meccanica": {m: 1.0 for m in MESI}
    }

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

# --- 4. SIDEBAR ---
st.sidebar.title("⚙️ HUB Control Panel")
st.sidebar.download_button("📥 Template", data=crea_template(), file_name="Template.xlsx")
st.sidebar.file_uploader("📂 Carica Excel", type="xlsx", key="uploader", on_change=carica_excel)

st.sidebar.divider()

# --- SLIDER CARROZZERIA ---
st.sidebar.subheader("📈 Impatto % Carrozzeria")
for m in MESI:
    current_val = st.session_state['impatti']["Carrozzeria"][m] * 100
    new_pct = st.sidebar.slider(f"{m} (Carr)", 0, 100, int(current_val), 1)
    st.session_state['impatti']["Carrozzeria"][m] = new_pct / 100

st.sidebar.divider()

# --- SLIDER MECCANICA ---
st.sidebar.subheader("📈 Impatto % Meccanica")
for m in MESI:
    current_val = st.session_state['impatti']["Meccanica"][m] * 100
    new_pct = st.sidebar.slider(f"{m} (Mecc)", 0, 100, int(current_val), 1)
    st.session_state['impatti']["Meccanica"][m] = new_pct / 100

# --- 5. DASHBOARD ---
def render_dashboard(settore, budget_annuale, voci):
    st.header(f"Gestione {settore}")
    
    # Calcolo Target Mensile Dinamico basato sui propri slider
    tot_pesi = sum(st.session_state['impatti'][settore].values())
    
    # --- TABELLA INPUT ORIZZONTALE ---
    st.subheader("📝 Input Dati (Orizzontale)")
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
                new_val = c[i+2].number_input("€", value=val_db, key=f"in_{settore}_{v}_{p}_{m}", label_visibility="collapsed")
                st.session_state['db'][settore][m][v][p] = new_val

    # --- ANALISI ---
    st.divider()
    report = []
    for m in MESI:
        # Budget teorico del mese pesato sugli slider specifici del settore
        target_m = (budget_annuale / tot_pesi) * st.session_state['impatti'][settore][m] if tot_pesi > 0 else 0
        reale_m = sum(st.session_state['db'][settore][m][v][p] for v in voci for p in PARTNER)
        
        report.append({
            "Mese": m, 
            "Target (Slider)": round(target_m, 2), 
            "Consuntivo": round(reale_m, 2),
            "Delta": round(target_m - reale_m, 2)
        })
    
    df_rep = pd.DataFrame(report)
    speso = df_rep["Consuntivo"].sum()
    
    m1, m2, m3 = st.columns(3)
    m1.metric("Speso Totale", f"{speso:,.2f} €")
    m2.metric("Residuo Annuale", f"{(budget_annuale - speso):,.2f} €")
    m3.metric("Peso Totale Slider", f"{int(tot_pesi * 100)}%")

    st.table(df_rep.set_index("Mese"))
    st.bar_chart(df_rep.set_index("Mese")[["Target (Slider)", "Consuntivo"]])

# --- MAIN ---
st.title("🛡️ Unipolservice Budget HUB 2.0")
b_carr = st.sidebar.number_input("Budget Annuale Carrozzeria", 386393.0)
b_mecc = st.sidebar.number_input("Budget Annuale Meccanica", 120000.0)

t1, t2 = st.tabs(["🚗 CARROZZERIA", "🔧 MECCANICA"])
with t1: render_dashboard("Carrozzeria", b_carr, VOCI_CARR)
with t2: render_dashboard("Meccanica", b_mecc, VOCI_MECC)
