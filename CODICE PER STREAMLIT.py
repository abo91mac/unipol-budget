import streamlit as st
import pandas as pd
import io

st.set_page_config(page_title="Unipolservice Budget HUB 2.0", layout="wide")

# --- CONFIGURAZIONE ---
MESI = ["GENNAIO", "FEBBRAIO", "MARZO", "APRILE", "MAGGIO", "GIUGNO", 
        "LUGLIO", "AGOSTO", "SETTEMBRE", "OTTOBRE", "NOVEMBRE", "DICEMBRE"]
PARTNER = ["KONECTA", "COVISIAN"]
VOCI_CARR = ["Gestione Contatti", "Ricontatto", "Documenti ricevuti da carrozzeria", "Recupero firme Digitali attività outbound", "solleciti outbound (TODO)"]
VOCI_MECC = ["Solleciti outbound Officine (TODO)", "Gestione ticket assistenza"]

# --- INIZIALIZZAZIONE ---
if 'db' not in st.session_state:
    st.session_state['db'] = {
        "Carrozzeria": {m: {v: {p: 0.0 for p in PARTNER} for v in VOCI_CARR} for m in MESI},
        "Meccanica": {m: {v: {p: 0.0 for p in PARTNER} for v in VOCI_MECC} for m in MESI}
    }
    st.session_state['note'] = {"Carrozzeria": {m: "" for m in MESI}, "Meccanica": {m: "" for m in MESI}}
if 'v' not in st.session_state: st.session_state['v'] = 0

# --- LOGICA DI CARICAMENTO AVANZATA ---
def carica_excel():
    if st.session_state.uploader is None: return
    try:
        df = pd.read_excel(st.session_state.uploader, sheet_name="External carrozzeria-meccanica", header=None)
        
        for settore, voci in [("Carrozzeria", VOCI_CARR), ("Meccanica", VOCI_MECC)]:
            for v in voci:
                # Cerca la riga che contiene il nome dell'attività
                # Usiamo .stack() per cercare in tutte le colonne (A, B, C...)
                mask = df.apply(lambda row: row.astype(str).str.contains(v, case=False, na=False)).any(axis=1)
                indices = df.index[mask].tolist()
                
                for idx in indices:
                    # Identifica il partner guardando la colonna A della riga stessa o di quella precedente
                    riga_testo = str(df.iloc[idx, 0]).upper()
                    riga_sopra = str(df.iloc[idx-1, 0]).upper() if idx > 0 else ""
                    
                    p_found = None
                    if "KONECTA" in riga_testo or "KONECTA" in riga_sopra: p_found = "KONECTA"
                    elif "COVISIAN" in riga_testo or "COVISIAN" in riga_sopra: p_found = "COVISIAN"
                    
                    if p_found:
                        for m_idx, m_nome in enumerate(MESI):
                            # Colonna 7 è Gennaio Consuntivo, poi saltano di 2 (9, 11...)
                            col_target = 7 + (m_idx * 2)
                            try:
                                valore = df.iloc[idx, col_target]
                                if pd.notna(valore) and isinstance(valore, (int, float)):
                                    st.session_state['db'][settore][m_nome][v][p_found] = float(valore)
                            except: pass
        st.session_state['v'] += 1
        st.toast("✅ Importazione completata!")
    except Exception as e:
        st.error(f"Errore: {e}")

# --- SIDEBAR ---
st.sidebar.title("⚙️ HUB Control Panel")
st.sidebar.file_uploader("Carica Excel", type="xlsx", key="uploader", on_change=carica_excel)
b_carr = st.sidebar.number_input("Budget Carrozzeria (€)", value=386393.0)
b_mecc = st.sidebar.number_input("Budget Meccanica (€)", value=120000.0)

# --- INTERFACCIA ---
def render_dashboard(nome, budget, voci):
    st.header(f"Dashboard {nome}")
    
    # Inserimento Manuale
    with st.expander(f"Modifica Manuale {nome}"):
        m_sel = st.selectbox(f"Seleziona Mese", MESI, key=f"s_{nome}")
        for v in voci:
            st.markdown(f"**{v}**")
            c1, c2 = st.columns(2)
            st.session_state['db'][nome][m_sel][v]["KONECTA"] = c1.number_input(f"KONECTA - {v}", value=st.session_state['db'][nome][m_sel][v]["KONECTA"], key=f"k_{nome}_{m_sel}_{v}_{st.session_state['v']}")
            st.session_state['db'][nome][m_sel][v]["COVISIAN"] = c2.number_input(f"COVISIAN - {v}", value=st.session_state['db'][nome][m_sel][v]["COVISIAN"], key=f"c_{nome}_{m_sel}_{v}_{st.session_state['v']}")

    # Tabella Riepilogo
    rep = []
    for m in MESI:
        k = sum(st.session_state['db'][nome][m][v]["KONECTA"] for v in voci)
        c = sum(st.session_state['db'][nome][m][v]["COVISIAN"] for v in voci)
        rep.append({"Mese": m, "Target": round(budget/12, 2), "Reale": round(k+c, 2), "KONECTA": k, "COVISIAN": c})
    
    df = pd.DataFrame(rep)
    st.dataframe(df, use_container_width=True)
    st.bar_chart(df.set_index("Mese")[["KONECTA", "COVISIAN"]])

st.title("🛡️ Unipolservice Budget HUB 2.0")
t1, t2 = st.tabs(["🚗 CARROZZERIA", "🔧 MECCANICA"])
with t1: render_dashboard("Carrozzeria", b_carr, VOCI_CARR)
with t2: render_dashboard("Meccanica", b_mecc, VOCI_MECC)
