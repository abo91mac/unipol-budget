import streamlit as st
import pandas as pd
import io

st.set_page_config(page_title="UnipolSai Strategic Planner", layout="wide")

# --- 1. INIZIALIZZAZIONE MEMORIA ---
mesi = ["Gennaio", "Febbraio", "Marzo", "Aprile", "Maggio", "Giugno", 
        "Luglio", "Agosto", "Settembre", "Ottobre", "Novembre", "Dicembre"]

if 'dati_mensili' not in st.session_state:
    st.session_state['dati_mensili'] = {m: (0.0, 0.0) for m in mesi}

if 'file_version' not in st.session_state:
    st.session_state['file_version'] = 0

# --- 2. FUNZIONE CALLBACK PER CARICAMENTO ---
def process_upload():
    if st.session_state.uploader is not None:
        try:
            df_load = pd.read_excel(st.session_state.uploader)
            nuovi_dati = {m: (0.0, 0.0) for m in mesi}
            for _, row in df_load.iterrows():
                m = row.get('Mese')
                if m in nuovi_dati:
                    # Cerchiamo le colonne correggendo eventuali spazi
                    s_m = float(row.get('Spesa Meccanica (€)', 0.0))
                    s_c = float(row.get('Spesa Carrozzeria (€)', 0.0))
                    nuovi_dati[m] = (s_m, s_c)
            
            # Aggiorniamo la memoria e cambiamo la versione per resettare i widget
            st.session_state['dati_mensili'] = nuovi_dati
            st.session_state['file_version'] += 1 
            st.toast("✅ File caricato e campi aggiornati!")
        except Exception as e:
            st.error(f"Errore: {e}")

# --- 3. SIDEBAR ---
st.sidebar.header("💰 Budget & Percentuali")
budget_annuo = st.sidebar.number_input("Budget Totale Annuo (€)", value=300000)
fondo = st.sidebar.slider("Fondo Emergenze (€)", 0, 30000, 5000)

var_pct = {}
with st.sidebar.expander("Regola Stagionalità (%)"):
    for m in mesi:
        def_v = 30 if m in ["Luglio", "Ottobre"] else 0
        var_pct[m] = st.slider(f"{m} (%)", -50, 100, def_v)

pesi = {m: 1 + (v/100) for m, v in var_pct.items()}
quota_base = (budget_annuo - fondo) / sum(pesi.values())

# --- 4. CARICAMENTO FILE ---
st.title("🛡️ Unipolservice Budget HUB")
st.file_uploader("📂 Carica l'Excel salvato in precedenza", type="xlsx", 
                 key="uploader", on_change=process_upload)

# --- 5. INPUT DATI (CON KEY DINAMICA) ---
spese_effettive = {}
with st.expander("📝 Inserimento/Modifica Spese", expanded=True):
    c1, c2 = st.columns(2)
    for i, m in enumerate(mesi):
        with (c1 if i < 6 else c2):
            val_m, val_c = st.session_state['dati_mensili'][m]
            
            # La key include 'file_version': se cambia il file, cambia la key, 
            # e Streamlit aggiorna il valore visualizzato nel box.
            s_m = st.number_input(f"Mecc {m}", value=val_m, 
                                  key=f"m_{m}_{st.session_state.file_version}")
            s_c = st.number_input(f"Carr {m}", value=val_c, 
                                  key=f"c_{m}_{st.session_state.file_version}")
            
            # Salviamo le modifiche manuali subito nella session_state
            st.session_state['dati_mensili'][m] = (s_m, s_c)
            spese_effettive[m] = (s_m, s_c)

# --- 6. REPORT E CALCOLI ---
report = []
spesa_reale_tot = 0
mesi_comp = 0
for m in mesi:
    target = quota_base * pesi[m]
    s_m, s_c = st.session_state['dati_mensili'][m]
    tot_m = s_m + s_c
    if tot_m > 0:
        spesa_reale_tot += tot_m
        mesi_comp += 1
    report.append({
        "Mese": m, "Budget Target (€)": round(target, 2),
        "Spesa Meccanica (€)": s_m, "Spesa Carrozzeria (€)": s_c,
        "Totale Reale (€)": tot_m
    })

df = pd.DataFrame(report)

# --- 7. DASHBOARD ANDAMENTO ---
if mesi_comp > 0:
    st.divider()
    media = spesa_reale_tot / mesi_comp
    proiezione = (media * 12) + fondo
    
    col1, col2 = st.columns(2)
    col1.metric("Proiezione Fine Anno", f"{round(proiezione, 2)} €", 
               delta=f"{round(budget_annuo - proiezione, 2)} €")
    col2.metric("Media Mensile Reale", f"{round(media, 2)} €")
    
    st.line_chart(df.set_index("Mese")[["Budget Target (€)", "Totale Reale (€)"]])

st.dataframe(df, use_container_width=True)

# --- 8. DOWNLOAD ---
output = io.BytesIO()
with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
    df.to_excel(writer, index=False, sheet_name='Budget')
st.download_button("📥 Scarica Report Excel", output.getvalue(), "report_unipol.xlsx")
