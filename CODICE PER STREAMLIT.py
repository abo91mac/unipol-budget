import streamlit as st
import pandas as pd
import io

st.set_page_config(page_title="Unipolservice Budget HUB 2.0", layout="wide")

# --- CONFIGURAZIONE ---
MESI = ["GENNAIO", "FEBBRAIO", "MARZO", "APRILE", "MAGGIO", "GIUGNO", "LUGLIO", "AGOSTO", "SETTEMBRE", "OTTOBRE", "NOVEMBRE", "DICEMBRE"]
PARTNER = ["KONECTA", "COVISIAN"]

# Usiamo parole chiave brevi per trovare le righe nell'Excel
MAPPA_VOCI = {
    "Carrozzeria": {
        "Gestione Contatti": "Gestione Contatti",
        "Ricontatto": "Ricontatto",
        "Documenti ricevuti da carrozzeria": "Documenti",
        "Recupero firme Digitali attività outbound": "Firme",
        "solleciti outbound (TODO)": "Solleciti outbound"
    },
    "Meccanica": {
        "Solleciti outbound Officine (TODO)": "Solleciti outbound Officine",
        "Gestione ticket assistenza": "Ticket"
    }
}

if 'db' not in st.session_state:
    st.session_state['db'] = {s: {m: {v: {p: 0.0 for p in PARTNER} for v in MAPPA_VOCI[s]} for m in MESI} for s in ["Carrozzeria", "Meccanica"]}
if 'v' not in st.session_state: st.session_state['v'] = 0

def carica_excel():
    if st.session_state.uploader is None: return
    try:
        # Leggiamo tutto il foglio
        df = pd.read_excel(st.session_state.uploader, sheet_name="External carrozzeria-meccanica", header=None)
        df = df.astype(str).replace('nan', '')
        
        aggiornati = 0
        for settore in ["Carrozzeria", "Meccanica"]:
            for voce_app, chiave_excel in MAPPA_VOCI[settore].items():
                for p in PARTNER:
                    # Cerchiamo la riga che contiene il Partner E la Chiave Attività
                    for i in range(len(df)):
                        riga_testo = " ".join(df.iloc[i, 0:5]).upper()
                        if p in riga_testo and chiave_excel.upper() in riga_testo:
                            # Trovata riga: estraiamo i 12 mesi (Colonna H=7, J=9, L=11...)
                            for m_idx, m_nome in enumerate(MESI):
                                col_idx = 7 + (m_idx * 2)
                                try:
                                    val_raw = df.iloc[i, col_idx].replace('.', '').replace(',', '.')
                                    st.session_state['db'][settore][m_nome][voce_app][p] = float(val_raw)
                                    aggiornati += 1
                                except: pass
        
        st.session_state['v'] += 1
        st.success(f"✅ HUB Aggiornato! Trovate {aggiornati} corrispondenze nel file.")
    except Exception as e:
        st.error(f"Errore: {e}")

# --- INTERFACCIA ---
st.sidebar.title("⚙️ Control Panel")
st.sidebar.file_uploader("Carica File Excel", type="xlsx", key="uploader", on_change=carica_excel)
b_c = st.sidebar.number_input("Budget Carrozzeria", value=386393.0)
b_m = st.sidebar.number_input("Budget Meccanica", value=120000.0)

def display(nome, budget, voci_mappa):
    st.header(f"Sezione {nome}")
    
    # Calcolo dati tabella
    report = []
    for m in MESI:
        val_k = sum(st.session_state['db'][nome][m][v]["KONECTA"] for v in voci_mappa)
        val_c = sum(st.session_state['db'][nome][m][v]["COVISIAN"] for v in voci_mappa)
        report.append({"Mese": m, "Budget": round(budget/12, 2), "Reale": round(val_k + val_c, 2), "KONECTA": val_k, "COVISIAN": val_c})
    
    df = pd.DataFrame(report)
    st.dataframe(df, use_container_width=True)
    st.bar_chart(df.set_index("Mese")[["KONECTA", "COVISIAN"]])

st.title("🛡️ Unipolservice Budget HUB 2.0")
t1, t2 = st.tabs(["🚗 Carrozzeria", "🔧 Meccanica"])
with t1: display("Carrozzeria", b_c, MAPPA_VOCI["Carrozzeria"])
with t2: display("Meccanica", b_m, MAPPA_VOCI["Meccanica"])
