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

if 'db' not in st.session_state:
    st.session_state['db'] = {
        "Carrozzeria": {m: {v: {p: 0.0 for p in PARTNER} for v in VOCI_CARR} for m in MESI},
        "Meccanica": {m: {v: {p: 0.0 for p in PARTNER} for v in VOCI_MECC} for m in MESI}
    }
    st.session_state['v'] = 0

# --- LOGICA DI CARICAMENTO "TOTALE" ---
def carica_excel():
    if st.session_state.uploader is None: return
    try:
        # Carichiamo il foglio senza header per scansionare tutto
        df = pd.read_excel(st.session_state.uploader, sheet_name="External carrozzeria-meccanica", header=None)
        df = df.astype(str).replace('nan', '') # Pulizia dati
        
        found_count = 0
        for settore, voci in [("Carrozzeria", VOCI_CARR), ("Meccanica", VOCI_MECC)]:
            for v in voci:
                for p in PARTNER:
                    # Cerchiamo la riga dove appaiono ENTRAMBI (Partner e Attività) nelle prime 4 colonne
                    for i in range(len(df)):
                        testo_riga = " ".join(df.iloc[i, 0:4]).upper()
                        
                        if p in testo_riga and v.upper()[:15] in testo_riga:
                            # Trovata la riga! Ora estraiamo i mesi.
                            # Nel tuo file GENNAIO CONSUNTIVO è alla colonna 7 (H)
                            for m_idx, m_nome in enumerate(MESI):
                                try:
                                    col_idx = 7 + (m_idx * 2)
                                    valore_str = df.iloc[i, col_idx].replace(',', '.')
                                    valore = float(valore_str) if valore_str != '' else 0.0
                                    st.session_state['db'][settore][m_nome][v][p] = valore
                                    found_count += 1
                                except: pass
        
        st.session_state['v'] += 1
        if found_count > 0:
            st.toast(f"✅ Successo! Caricati {found_count} valori.")
        else:
            st.error("⚠️ File letto, ma non ho trovato corrispondenze tra Partner e Attività. Verifica i nomi nel file.")
    except Exception as e:
        st.error(f"Errore tecnico: {e}")

# --- SIDEBAR ---
st.sidebar.title("⚙️ HUB Control Panel")
st.sidebar.file_uploader("Carica Excel Consuntivi", type="xlsx", key="uploader", on_change=carica_excel)
b_carr = st.sidebar.number_input("Budget Carrozzeria", value=386393.0)
b_mecc = st.sidebar.number_input("Budget Meccanica", value=120000.0)

# --- UI DASHBOARD ---
def render_dashboard(nome, budget, voci):
    st.header(f"Sezione {nome}")
    
    # Visualizzazione Tabella
    data = []
    for m in MESI:
        k = sum(st.session_state['db'][nome][m][v]["KONECTA"] for v in voci)
        c = sum(st.session_state['db'][nome][m][v]["COVISIAN"] for v in voci)
        data.append({"Mese": m, "Budget": round(budget/12, 2), "Reale": round(k+c, 2), "KONECTA": k, "COVISIAN": c})
    
    df_vis = pd.DataFrame(data)
    
    # Metriche
    tot_reale = df_vis["Reale"].sum()
    c1, c2 = st.columns(2)
    c1.metric("Totale Speso", f"{tot_reale:,.2f} €")
    c2.metric("Rimanente", f"{(budget-tot_reale):,.2f} €")
    
    st.table(df_vis) # Usiamo table per massima leggibilità
    st.bar_chart(df_vis.set_index("Mese")[["KONECTA", "COVISIAN"]])

    # Input manuale (in fondo per correzioni)
    with st.expander("📝 Modifica manuale valori"):
        m_s = st.selectbox("Mese", MESI, key=f"sel_{nome}")
        for v in voci:
            col1, col2 = st.columns(2)
            st.session_state['db'][nome][m_s][v]["KONECTA"] = col1.number_input(f"{v} (K)", value=st.session_state['db'][nome][m_s][v]["KONECTA"], key=f"k_{nome}_{m_s}_{v}_{st.session_state['v']}")
            st.session_state['db'][nome][m_s][v]["COVISIAN"] = col2.number_input(f"{v} (C)", value=st.session_state['db'][nome][m_s][v]["COVISIAN"], key=f"c_{nome}_{m_s}_{v}_{st.session_state['v']}")

# --- MAIN ---
st.title("🛡️ Unipolservice Budget HUB 2.0")
t1, t2 = st.tabs(["🚗 Carrozzeria", "🔧 Meccanica"])
with t1: render_dashboard("Carrozzeria", b_carr, VOCI_CARR)
with t2: render_dashboard("Meccanica", b_mecc, VOCI_MECC)
