import streamlit as st
import pandas as pd
import io

st.set_page_config(page_title="Unipolservice Budget HUB 2.0", layout="wide")

# --- 1. CONFIGURAZIONE STRUTTURA ---
mesi_col = ["GENNAIO", "FEBBRAIO", "MARZO", "APRILE", "MAGGIO", "GIUGNO", 
            "LUGLIO", "AGOSTO", "SETTEMBRE", "OTTOBRE", "NOVEMBRE", "DICEMBRE"]
partner = ["KONECTA", "COVISIAN"]

voci_carr = [
    "Gestione Contatti", "Ricontatto", "Documenti ricevuti da carrozzeria", 
    "Recupero firme Digitali attività outbound", "solleciti outbound (TODO)"
]
voci_mecc = [
    "Solleciti outbound Officine (TODO)", "Gestione ticket assistenza"
]

# --- 2. MEMORIA DI SESSIONE ---
if 'db' not in st.session_state:
    st.session_state['db'] = {
        "Carrozzeria": {m: {v: {p: 0.0 for p in partner} for v in voci_carr} for m in mesi_col},
        "Meccanica": {m: {v: {p: 0.0 for p in partner} for v in voci_mecc} for m in mesi_col}
    }
    st.session_state['v'] = 0

# --- 3. LOGICA DI CARICAMENTO (MAPPATURA FILE) ---
def process_upload():
    if st.session_state.uploader is not None:
        try:
            # Carichiamo il foglio specifico
            df = pd.read_excel(st.session_state.uploader, sheet_name="External carrozzeria-meccanica", header=None)
            
            # Funzione interna per cercare i dati nel foglio
            def estrai_dati(settore, voci, start_row, end_row):
                current_partner = None
                for i in range(start_row, end_row):
                    row_label = str(df.iloc[i, 0]).strip()
                    # Identifica il partner
                    if "KONECTA" in row_label: current_partner = "KONECTA"
                    elif "COVISIAN" in row_label: current_partner = "COVISIAN"
                    
                    # Identifica l'attività (colonna B o C a seconda del file)
                    attivita_label = str(df.iloc[i, 1]).strip() if pd.notna(df.iloc[i, 1]) else str(df.iloc[i, 2]).strip()
                    
                    for v in voci:
                        if v.lower() in attivita_label.lower() and current_partner:
                            # Cerca i consuntivi nei mesi (le colonne nel tuo file sono alternate Volumi/Consuntivo)
                            # In base al tuo file, GENNAIO Consuntivo è alla colonna 7, FEBBRAIO alla 9, ecc.
                            for idx, m in enumerate(mesi_col):
                                col_idx = 7 + (idx * 2) 
                                val = df.iloc[i, col_idx]
                                try:
                                    st.session_state['db'][settore][m][v][current_partner] = float(val) if pd.notna(val) else 0.0
                                except: pass

            # Eseguiamo l'estrazione per Carrozzeria e Meccanica (basandoci sulla struttura del file)
            estrai_dati("Carrozzeria", voci_carr, 0, 40)
            estrai_dati("Meccanica", voci_mecc, 40, 60)
            
            st.session_state['v'] += 1
            st.toast("✅ Dati caricati correttamente dal file Unipolservice!")
        except Exception as e:
            st.error(f"Errore durante la lettura: {e}. Controlla il nome del foglio.")

# --- 4. SIDEBAR ---
st.sidebar.title("⚙️ HUB Control Panel")
st.sidebar.file_uploader("📂 Carica Excel Consuntivi", type="xlsx", key="uploader", on_change=process_upload)

b_carr = st.sidebar.number_input("Budget Annuale Carrozzeria (€)", value=386393.0)
b_mecc = st.sidebar.number_input("Budget Annuale Meccanica (€)", value=120000.0)

# --- 5. RENDER DASHBOARD ---
def render_settore(nome_settore, budget, voci):
    st.header(f"Sezione {nome_settore.upper()}")
    
    # Calcolo Dati per Tabella
    report = []
    q_base = budget / 12
    for m in mesi_col:
        reale_m = sum(st.session_state['db'][nome_settore][m][v][p] for v in voci for p in partner)
        report.append({
            "Mese": m,
            "Target": round(q_base, 2),
            "Reale": round(reale_m, 2),
            "Delta": round(q_base - reale_m, 2),
            "KONECTA": sum(st.session_state['db'][nome_settore][m][v]["KONECTA"] for v in voci),
            "COVISIAN": sum(st.session_state['db'][nome_settore][m][v]["COVISIAN"] for v in voci)
        })
    
    df_rep = pd.DataFrame(report)
    
    # Metriche
    speso = df_rep["Reale"].sum()
    c1, c2, c3 = st.columns(3)
    c1.metric("Budget Speso", f"{speso:,.2f} €")
    c2.metric("Residuo", f"{(budget - speso):,.2f} €")
    c3.metric("% Avanzamento", f"{round((speso/budget)*100, 1)}%")

    # Tabella e Grafico
    st.dataframe(df_rep.style.format({c: "{:.2f}" for c in df_rep.columns if c != "Mese"}), use_container_width=True)
    st.area_chart(df_rep.set_index("Mese")[["KONECTA", "COVISIAN"]])

# --- 6. MAIN ---
st.title("🛡️ Unipolservice Budget HUB 2.0")
t1, t2 = st.tabs(["🚗 CARROZZERIA", "🔧 MECCANICA"])
with t1: render_settore("Carrozzeria", b_carr, voci_carr)
with t2: render_settore("Meccanica", b_mecc, voci_mecc)
