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

# --- INIZIALIZZAZIONE SESSIONE ---
if 'db' not in st.session_state:
    st.session_state['db'] = {
        "Carrozzeria": {m: {v: {p: 0.0 for p in PARTNER} for v in VOCI_CARR} for m in MESI},
        "Meccanica": {m: {v: {p: 0.0 for p in PARTNER} for v in VOCI_MECC} for m in MESI}
    }
if 'v' not in st.session_state: st.session_state['v'] = 0

# --- LOGICA DI CARICAMENTO ---
def carica_excel():
    if st.session_state.uploader is None: return
    try:
        df = pd.read_excel(st.session_state.uploader, sheet_name="External carrozzeria-meccanica", header=None)
        df = df.astype(str).replace('nan', '')
        
        count = 0
        for settore, voci in [("Carrozzeria", VOCI_CARR), ("Meccanica", VOCI_MECC)]:
            for v in voci:
                for p in PARTNER:
                    for i in range(len(df)):
                        testo_riga = " ".join(df.iloc[i, 0:4]).upper()
                        # Match flessibile per attività e partner
                        if p in testo_riga and v.upper()[:12] in testo_riga:
                            for m_idx, m_nome in enumerate(MESI):
                                col_idx = 7 + (m_idx * 2) # Colonna Consuntivo
                                try:
                                    val_str = df.iloc[i, col_idx].replace(',', '.')
                                    valore = float(val_str) if val_str != '' else 0.0
                                    # Salvataggio diretto in session_state
                                    st.session_state['db'][settore][m_nome][v][p] = valore
                                    count += 1
                                except: pass
        
        st.session_state['v'] += 1 # Incremento versione per refresh widget
        st.success(f"Dati caricati: {count} celle aggiornate. Se non vedi i dati, premi il tasto 🔄 sotto.")
    except Exception as e:
        st.error(f"Errore: {e}")

# --- SIDEBAR ---
st.sidebar.title("⚙️ HUB Control Panel")
st.sidebar.file_uploader("Carica Excel", type="xlsx", key="uploader", on_change=carica_excel)

if st.sidebar.button("🔄 Forza Aggiornamento Grafici"):
    st.rerun()

b_carr = st.sidebar.number_input("Budget Carrozzeria", value=386393.0)
b_mecc = st.sidebar.number_input("Budget Meccanica", value=120000.0)

# --- RENDER DASHBOARD ---
def render_dashboard(nome, budget, voci):
    st.header(f"Dashboard {nome}")
    
    # DATI PER VISUALIZZAZIONE
    report = []
    t_m = budget / 12
    for m in MESI:
        # Recupero dinamico dei dati aggiornati dalla sessione
        k = sum(st.session_state['db'][nome][m][v]["KONECTA"] for v in voci)
        c = sum(st.session_state['db'][nome][m][v]["COVISIAN"] for v in voci)
        report.append({
            "Mese": m, 
            "Target": round(t_m, 2), 
            "Reale": round(k + c, 2), 
            "KONECTA": round(k, 2), 
            "COVISIAN": round(c, 2)
        })
    
    df_rep = pd.DataFrame(report)
    
    # METRICHE
    speso = df_rep["Reale"].sum()
    c1, c2, c3 = st.columns(3)
    c1.metric("Speso", f"{speso:,.2f} €")
    c2.metric("Residuo", f"{(budget - speso):,.2f} €")
    c3.metric("%", f"{round((speso/budget)*100, 1)}%")

    # TABELLA E GRAFICO
    st.dataframe(df_rep, use_container_width=True)
    st.bar_chart(df_rep.set_index("Mese")[["KONECTA", "COVISIAN"]])

    # MODIFICA MANUALE
    with st.expander("📝 Modifica Valori Manualmente"):
        m_s = st.selectbox("Mese", MESI, key=f"sel_{nome}")
        for v in voci:
            st.write(f"**{v}**")
            col1, col2 = st.columns(2)
            # Nota: il valore di default 'value' è legato alla session_state aggiornata
            val_k = col1.number_input(f"K - {v}", value=st.session_state['db'][nome][m_s][v]["KONECTA"], key=f"k_{nome}_{m_s}_{v}_{st.session_state['v']}")
            val_c = col2.number_input(f"C - {v}", value=st.session_state['db'][nome][m_s][v]["COVISIAN"], key=f"c_{nome}_{m_s}_{v}_{st.session_state['v']}")
            st.session_state['db'][nome][m_s][v]["KONECTA"] = val_k
            st.session_state['db'][nome][m_s][v]["COVISIAN"] = val_c

# --- MAIN ---
st.title("🛡️ Unipolservice Budget HUB 2.0")
t1, t2 = st.tabs(["🚗 Carrozzeria", "🔧 Meccanica"])
with t1: render_dashboard("Carrozzeria", b_carr, VOCI_CARR)
with t2: render_dashboard("Meccanica", b_mecc, VOCI_MECC)
