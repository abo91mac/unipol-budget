import streamlit as st
import pandas as pd
import io

st.set_page_config(page_title="UnipolSai Strategic Planner", layout="wide")

# --- 1. INIZIALIZZAZIONE MEMORIA ---
mesi = ["Gennaio", "Febbraio", "Marzo", "Aprile", "Maggio", "Giugno", 
        "Luglio", "Agosto", "Settembre", "Ottobre", "Novembre", "Dicembre"]

if 'dati_mensili' not in st.session_state:
    st.session_state['dati_mensili'] = {m: (0.0, 0.0) for m in mesi}

# --- 2. FUNZIONE CALLBACK PER IL CARICAMENTO ---
def carica_dati_da_file():
    if st.session_state.caricatore_file is not None:
        try:
            df_load = pd.read_excel(st.session_state.caricatore_file)
            nuovi_dati = {m: (0.0, 0.0) for m in mesi}
            for _, row in df_load.iterrows():
                m = row['Mese']
                if m in nuovi_dati:
                    s_m = float(row.get('Spesa Meccanica (€)', 0.0))
                    s_c = float(row.get('Spesa Carrozzeria (€)', 0.0))
                    nuovi_dati[m] = (s_m, s_c)
            st.session_state['dati_mensili'] = nuovi_dati
            st.toast("✅ Dati caricati con successo!")
        except Exception as e:
            st.error(f"Errore nella lettura del file: {e}")

# --- 3. SIDEBAR ---
st.sidebar.header("💰 Configurazione Budget")
budget_annuo = st.sidebar.number_input("Budget Totale Annuale (€)", value=300000)
fondo_emergenze = st.sidebar.slider("Fondo Emergenze (€)", 0, 30000, 5000)

st.sidebar.header("⚖️ Ripartizione")
p_mecc = st.sidebar.slider("% Meccanica", 0, 100, 60)
p_carr = 100 - p_mecc

st.sidebar.header("📅 Stagionalità (% variazione)")
var_pct = {}
with st.sidebar.expander("Modifica Percentuali Mensili"):
    for m in mesi:
        def_val = 30 if m in ["Luglio", "Ottobre"] else 0
        var_pct[m] = st.slider(f"{m} (%)", -50, 100, def_val)

pesi = {m: 1 + (v/100) for m, v in var_pct.items()}
quota_base = (budget_annuo - fondo_emergenze) / sum(pesi.values())

# --- 4. CARICAMENTO ---
st.title("🛡️ UnipolSai Budget Control")
# L'uso di on_change e key è la chiave per far funzionare il caricamento
st.file_uploader("📂 Carica Excel per aggiornare i dati", type="xlsx", 
                 key="caricatore_file", on_change=carica_dati_da_file)

# --- 5. INPUT DATI (LEGGONO DALLA MEMORIA) ---
spese_finali = {}
with st.expander("📝 Visualizza/Modifica Spese Mensili", expanded=True):
    c1, c2 = st.columns(2)
    for i, m in enumerate(mesi):
        with (c1 if i < 6 else c2):
            val_m, val_c = st.session_state['dati_mensili'][m]
            # Usiamo i valori caricati come default
            s_m = st.number_input(f"Mecc {m}", value=val_m, key=f"inp_m_{m}")
            s_c = st.number_input(f"Carr {m}", value=val_c, key=f"inp_c_{m}")
            # Aggiorniamo la sessione se l'utente cambia i dati a mano
            st.session_state['dati_mensili'][m] = (s_m, s_c)
            spese_finali[m] = (s_m, s_c)

# --- 6. CALCOLI E FORECASTING ---
report = []
spesa_tot_reale = 0
mesi_chiusi = 0

for m in mesi:
    target = quota_base * pesi[m]
    s_m, s_c = st.session_state['dati_mensili'][m]
    tot = s_m + s_c
    if tot > 0:
        spesa_tot_reale += tot
        mesi_chiusi += 1
    report.append({
        "Mese": m, 
        "Budget Target (€)": round(target, 2), 
        "Spesa Meccanica (€)": s_m, 
        "Spesa Carrozzeria (€)": s_c,
        "Totale Reale (€)": tot
    })

df = pd.DataFrame(report)

# --- 7. DASHBOARD E GRAFICO ---
st.markdown("---")
if mesi_chiusi > 0:
    media = spesa_tot_reale / mesi_chiusi
    stima = (media * 12) + fondo_emergenze
    diff = budget_annuo - stima
    
    m1, m2, m3 = st.columns(3)
    m1.metric("Spesa Media Reale", f"{round(media, 2)} €")
    m2.metric("Stima Fine Anno", f"{round(stima, 2)} €", delta=f"{round(stima-budget_annuo, 2)} €", delta_color="inverse")
    m3.metric("Avanzo Stimato", f"{round(diff, 2)} €")

    st.line_chart(df.set_index("Mese")[["Budget Target (€)", "Totale Reale (€)"]])

st.dataframe(df, use_container_width=True)

# --- 8. DOWNLOAD ---
output = io.BytesIO()
with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
    df.to_excel(writer, index=False, sheet_name='Budget')
st.download_button("📥 Scarica Report Excel", output.getvalue(), "report_budget.xlsx")
