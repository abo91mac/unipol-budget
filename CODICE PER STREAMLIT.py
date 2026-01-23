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
    st.session_state['note'] = {"Carrozzeria": {m: "" for m in mesi_col}, "Meccanica": {m: "" for m in mesi_col}}
if 'v' not in st.session_state: st.session_state['v'] = 0

# --- 3. LOGICA DI CARICAMENTO EXCEL ---
def process_upload():
    if st.session_state.uploader is not None:
        try:
            df = pd.read_excel(st.session_state.uploader, sheet_name="External carrozzeria-meccanica", header=None)
            
            def estrai_dati(settore, voci, start_row, end_row):
                current_partner = None
                for i in range(start_row, min(end_row, len(df))):
                    row_label = str(df.iloc[i, 0]).strip() if pd.notna(df.iloc[i, 0]) else ""
                    if "KONECTA" in row_label: current_partner = "KONECTA"
                    elif "COVISIAN" in row_label: current_partner = "COVISIAN"
                    
                    # Cerca l'attività nelle colonne B o C
                    attivita_label = ""
                    for col_test in [1, 2]:
                        if pd.notna(df.iloc[i, col_test]):
                            attivita_label = str(df.iloc[i, col_test]).strip()
                            break
                    
                    for v in voci:
                        if v.lower() in attivita_label.lower() and current_partner:
                            for idx, m in enumerate(mesi_col):
                                col_idx = 7 + (idx * 2) # Colonna Consuntivo
                                try:
                                    val = df.iloc[i, col_idx]
                                    st.session_state['db'][settore][m][v][current_partner] = float(val) if pd.notna(val) else 0.0
                                except: pass

            estrai_dati("Carrozzeria", voci_carr, 0, 45)
            estrai_dati("Meccanica", voci_mecc, 45, 70)
            st.session_state['v'] += 1 # Forza il refresh dei widget manuali
            st.toast("✅ Excel importato: i campi manuali sono stati aggiornati!")
        except Exception as e:
            st.error(f"Errore caricamento: {e}")

# --- 4. SIDEBAR ---
st.sidebar.title("⚙️ HUB Control Panel")
st.sidebar.subheader("📂 Importazione")
st.sidebar.file_uploader("Carica Excel Consuntivi", type="xlsx", key="uploader", on_change=process_upload)

st.sidebar.divider()
st.sidebar.subheader("💰 Budget Annuali")
b_carr = st.sidebar.number_input("Budget Carrozzeria (€)", value=386393.0, step=1000.0)
b_mecc = st.sidebar.number_input("Budget Meccanica (€)", value=120000.0, step=1000.0)

if st.sidebar.button("🗑️ RESET TOTALE"):
    st.session_state['db'] = {
        "Carrozzeria": {m: {v: {p: 0.0 for p in partner} for v in voci_carr} for m in mesi_col},
        "Meccanica": {m: {v: {p: 0.0 for p in partner} for v in voci_mecc} for m in mesi_col}
    }
    st.session_state['v'] += 1
    st.rerun()

# --- 5. RENDER SETTORE ---
def render_settore(nome_settore, budget, voci):
    # --- PARTE 1: INSERIMENTO MANUALE ---
    with st.expander(f"📝 Gestione Dati e Note {nome_settore}", expanded=True):
        m_scelto = st.selectbox(f"Seleziona Mese da modificare ({nome_settore})", mesi_col, key=f"sel_{nome_settore}")
        
        st.session_state['note'][nome_settore][m_scelto] = st.text_area(
            f"Note {m_scelto}", value=st.session_state['note'][nome_settore][m_scelto], key
