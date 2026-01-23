import streamlit as st
import pandas as pd
import io

st.set_page_config(page_title="Unipolservice Budget HUB 2.0", layout="wide")

# --- CONFIGURAZIONE COSTANTI ---
MESI = ["GENNAIO", "FEBBRAIO", "MARZO", "APRILE", "MAGGIO", "GIUGNO", 
        "LUGLIO", "AGOSTO", "SETTEMBRE", "OTTOBRE", "NOVEMBRE", "DICEMBRE"]
PARTNER = ["KONECTA", "COVISIAN"]
VOCI_CARR = [
    "Gestione Contatti", "Ricontatto", "Documenti ricevuti da carrozzeria", 
    "Recupero firme Digitali attività outbound", "solleciti outbound (TODO)"
]
VOCI_MECC = [
    "Solleciti outbound Officine (TODO)", "Gestione ticket assistenza"
]

# --- INIZIALIZZAZIONE MEMORIA ---
if 'db' not in st.session_state:
    st.session_state['db'] = {
        "Carrozzeria": {m: {v: {p: 0.0 for p in PARTNER} for v in VOCI_CARR} for m in MESI},
        "Meccanica": {m: {v: {p: 0.0 for p in PARTNER} for v in VOCI_MECC} for m in MESI}
    }
    st.session_state['note'] = {"Carrozzeria": {m: "" for m in MESI}, "Meccanica": {m: "" for m in MESI}}
if 'v' not in st.session_state: 
    st.session_state['v'] = 0

# --- LOGICA DI CARICAMENTO EXCEL ---
def carica_excel():
    if st.session_state.uploader is None:
        return
    try:
        df = pd.read_excel(st.session_state.uploader, sheet_name="External carrozzeria-meccanica", header=None)
        
        # Carrozzeria: righe 0-45 | Meccanica: righe 45-80
        for settore, voci, r_start, r_end in [("Carrozzeria", VOCI_CARR, 0, 48), ("Meccanica", VOCI_MECC, 48, 80)]:
            partner_corrente = None
            for i in range(r_start, min(r_end, len(df))):
                cella_a = str(df.iloc[i, 0]).strip() if pd.notna(df.iloc[i, 0]) else ""
                
                if "KONECTA" in cella_a: partner_corrente = "KONECTA"
                elif "COVISIAN" in cella_a: partner_corrente = "COVISIAN"
                
                # Cerca l'attività nelle colonne B o C (indice 1 o 2)
                descr = ""
                if pd.notna(df.iloc[i, 1]): descr = str(df.iloc[i, 1])
                elif pd.notna(df.iloc[i, 2]): descr = str(df.iloc[i, 2])
                
                if partner_corrente and descr:
                    for v in voci:
                        if v.lower() in descr.lower():
                            for idx, m in enumerate(MESI):
                                col_idx = 7 + (idx * 2) # Salta 'Volumi', prende 'Consuntivo'
                                try:
                                    valore = df.iloc[i, col_idx]
                                    st.session_state['db'][settore][m][v][partner_corrente] = float(valore) if pd.notna(valore) else 0.0
                                except:
                                    pass
        st.session_state['v'] += 1
        st.toast("✅ Excel caricato con successo!")
    except Exception as e:
        st.error(f"Errore tecnico nel caricamento: {e}")

# --- SIDEBAR ---
st.sidebar.title("⚙️ HUB Control Panel")
st.sidebar.file_uploader("Carica Excel Consuntivi", type="xlsx", key="uploader", on_change=carica_excel)
st.sidebar.divider()
b_carr = st.sidebar.number_input("Budget Carrozzeria (€)", value=386393.0)
b_mecc = st.sidebar.number_input("Budget Meccanica (€)", value=120000.0)

if st.sidebar.button("🗑️ RESET DATI"):
    st.session_state['db'] = {
        "Carrozzeria": {m: {v: {p: 0.0 for p in PARTNER} for v in VOCI_CARR} for m in MESI},
        "Meccanica": {m: {v: {p: 0.0 for p in PARTNER} for v in VOCI_MECC} for m in MESI}
    }
    st.session_state['v'] += 1
    st.rerun()

# --- FUNZIONE RENDER DASHBOARD ---
def render_dashboard(nome, budget, voci):
    st.header(f"Gestione {nome}")
    
    # 1. INPUT MANUALE E NOTE
    with st.expander(f"📝 Inserimento Manuale e Note - {nome}", expanded=True):
        m_sel = st.selectbox(f"Seleziona Mese ({nome})", MESI, key=f"s_{nome}")
        st.session_state['note'][nome][m_sel] = st.text_area("Note del mese", value=st.session_state['note'][nome][m_sel], key=f"n_{nome}_{m_sel}")
        
        for v in voci:
            st.write(f"**{v}**")
            c1, c2 = st.columns(2)
            with c1:
                key_k = f"in_k_{nome}_{m_sel}_{v}_{st.session_state['v']}"
                val_k = st.number_input(f"KONECTA (€)", value=st.session_state['db'][nome][m_sel][v]["KONECTA"], key=key_k, format="%.2f")
                st.session_state['db'][nome][m_sel][v]["KONECTA"] = val_k
            with c2:
                key_c = f"in_c_{nome}_{m_sel}_{v}_{st.session_state['v']}"
                val_c = st.number_input(f"COVISIAN (€)", value=st.session_state['db'][nome][m_sel][v]["COVISIAN"], key=key_c, format="%.2f")
                st.session_state['db'][nome][m_sel][v]["COVISIAN"] = val_c

    # 2. TABELLA E GRAFICI
    st.divider()
    report = []
    target_mensile = budget / 12
    for m in MESI:
        k_tot = sum(st.session_state['db'][nome][m][v]["KONECTA"] for v in voci)
        c_tot = sum(st.session_state['db'][nome_settore][m][v]["COVISIAN"] for v in voci) if 'nome_settore' in locals() else sum(st.session_state['db'][nome][m][v]["COVISIAN"] for v in voci)
        tot = k_tot + c_tot
        report.append({
            "Mese": m, "Target": round(target_mensile, 2), "Reale": round(tot, 2),
            "Delta": round(target_mensile - tot, 2), "KONECTA": round(k_tot, 2), "COVISIAN": round(c_tot, 2)
        })
    
    df = pd.DataFrame(report)
    speso = df["Reale"].sum()
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Speso Totale", f"{speso:,.2f} €")
    col2.metric("Residuo", f"{(budget - speso):,.2f} €")
    col3.metric("Avanzamento", f"{round((speso/budget)*100, 1)}%")

    st.dataframe(df.style.format({c: "{:.2f}" for c in df.columns if c != "Mese"}), use_container_width=True)
    st.bar_chart(df.set_index("Mese")[["KONECTA", "COVISIAN"]])

# --- MAIN INTERFACE ---
st.title("🛡️ Unipolservice Budget HUB 2.0")
tab_c, tab_m = st.tabs(["🚗 CARROZZERIA", "🔧 MECCANICA"])
with tab_c:
    render_dashboard("Carrozzeria", b_carr, VOCI_CARR)
with tab_m:
    render_dashboard("Meccanica", b_mecc, VOCI_MECC)
