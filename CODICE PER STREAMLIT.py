import streamlit as st
import pandas as pd
import io

st.set_page_config(page_title="Unipolservice Budget HUB 2.0", layout="wide")

# --- 1. CONFIGURAZIONE STRUTTURA ---
mesi = ["Gennaio", "Febbraio", "Marzo", "Aprile", "Maggio", "Giugno", 
        "Luglio", "Agosto", "Settembre", "Ottobre", "Novembre", "Dicembre"]

partner = ["KONECTA", "COVISIAN"]

voci_carr = [
    "Gestione Contatti", 
    "Ricontatto", 
    "Documenti da Carrozzeria", 
    "Recupero Firme Digitali", 
    "Solleciti Outbound (TODO)"
]

voci_mecc = [
    "Solleciti Outbound Officine (TODO)", 
    "Gestione Ticket Assistenza"
]

# --- 2. MEMORIA DI SESSIONE ---
# Struttura: session_state[settore][mese][voce][partner]
if 'db' not in st.session_state:
    st.session_state['db'] = {
        "Carrozzeria": {m: {v: {p: 0.0 for p in partner} for v in voci_carr} for m in mesi},
        "Meccanica": {m: {v: {p: 0.0 for p in partner} for v in voci_mecc} for m in mesi}
    }
    st.session_state['note'] = {
        "Carrozzeria": {m: "" for m in mesi},
        "Meccanica": {m: "" for m in mesi}
    }
if 'v' not in st.session_state: st.session_state['v'] = 0

# --- 3. SIDEBAR ---
st.sidebar.title("⚙️ HUB Control Panel")

st.sidebar.subheader("💰 Budget Annuali Separati")
b_carr = st.sidebar.number_input("Budget Annuale Carrozzeria (€)", value=200000.0, step=1000.0)
b_mecc = st.sidebar.number_input("Budget Annuale Meccanica (€)", value=100000.0, step=1000.0)

st.sidebar.divider()
with st.sidebar.expander("📅 Stagionalità (%)"):
    st.info("Applica lo stesso peso a entrambi i settori")
    var_pct = {m: st.slider(f"{m}", -50, 100, 0) for m in mesi}

if st.sidebar.button("🗑️ RESET TUTTI I DATI"):
    st.session_state['db'] = {
        "Carrozzeria": {m: {v: {p: 0.0 for p in partner} for v in voci_carr} for m in mesi},
        "Meccanica": {m: {v: {p: 0.0 for p in partner} for v in voci_mecc} for m in mesi}
    }
    st.session_state['v'] += 1
    st.rerun()

# --- 4. FUNZIONE LOGICA CORE ---
def render_settore(nome_settore, budget_annuo, voci):
    st.header(f"📊 Dashboard {nome_settore}")
    
    # Calcolo Target Mensili
    pesi = {m: 1 + (v/100) for m, v in var_pct.items()}
    q_base = budget_annuo / sum(pesi.values())
    
    # Inserimento Dati
    with st.expander(f"📝 Inserimento Spese {nome_settore}", expanded=False):
        tab_mesi = st.tabs(mesi)
        for i, m in enumerate(mesi):
            with tab_mesi[i]:
                st.session_state['note'][nome_settore][m] = st.text_input(f"Note {m}", value=st.session_state['note'][nome_settore][m], key=f"note_{nome_settore}_{m}")
                cols = st.columns(len(voci))
                for idx, v in enumerate(voci):
                    with cols[idx]:
                        st.markdown(f"**{v}**")
                        for p in partner:
                            val = st.number_input(f"{p} (€)", 
                                                 value=st.session_state['db'][nome_settore][m][v][p],
                                                 key=f"in_{nome_settore}_{m}_{v}_{p}_{st.session_state['v']}",
                                                 format="%.2f")
                            st.session_state['db'][nome_settore][m][v][p] = val

    # Elaborazione Report
    report_data = []
    for m in mesi:
        target = round(q_base * pesi[m], 2)
        reale_m = sum(st.session_state['db'][nome_settore][m][v][p] for v in voci for p in partner)
        diff = round(target - reale_m, 2)
        
        row = {"Mese": m, "Target": target, "Reale Totale": reale_m, "Delta": diff}
        # Dettaglio per Partner
        for p in partner:
            row[p] = sum(st.session_state['db'][nome_settore][m][v][p] for v in voci)
        
        report_data.append(row)
    
    df = pd.DataFrame(report_data)
    
    # Metriche
    tot_speso = df["Reale Totale"].sum()
    c1, c2, c3 = st.columns(3)
    c1.metric(f"Speso {nome_settore}", f"{round(tot_speso, 2)} €", f"{round((tot_speso/budget_annuo)*100, 1)}%")
    c2.metric("Residuo", f"{round(budget_annuo - tot_speso, 2)} €")
    c3.metric("Media Mese", f"{round(tot_speso/12, 2)} €")

    # Tabella
    st.dataframe(df.style.format({c: "{:.2f}" for c in df.columns if c != "Mese"}), use_container_width=True)
    
    # Grafico
    st.line_chart(df.set_index("Mese")[["Target", "Reale Totale"]])

# --- 5. INTERFACCIA PRINCIPALE ---
st.title("🛡️ Unipolservice Budget HUB 2.0")

t_carr, t_mecc = st.tabs(["🚗 CARROZZERIA", "🔧 MECCANICA"])

with t_carr:
    render_settore("Carrozzeria", b_carr, voci_carr)

with t_mecc:
    render_settore("Meccanica", b_mecc, voci_mecc)

# --- 6. DOWNLOAD ---
st.divider()
if st.button("📥 Genera Report Excel Finale"):
    # Logica per creare un excel con due fogli
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        for s in ["Carrozzeria", "Meccanica"]:
            # Trasformazione dei dati complessi in tabella piatta per Excel
            flat_data = []
            for m in mesi:
                for v in (voci_carr if s == "Carrozzeria" else voci_mecc):
                    for p in partner:
                        flat_data.append({
                            "Mese": m, "Settore": s, "Attività": v, "Partner": p, 
                            "Spesa": st.session_state['db'][s][m][v][p],
                            "Note": st.session_state['note'][s][m]
                        })
            pd.DataFrame(flat_data).to_excel(writer, index=False, sheet_name=s)
    st.download_button("Clicca qui per scaricare", output.getvalue(), "Unipolservice_Full_Report.xlsx")
