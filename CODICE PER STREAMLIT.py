import streamlit as st
import pandas as pd
import io

st.set_page_config(page_title="UnipolSai Strategic Planner", layout="wide")

# --- 1. INIZIALIZZAZIONE MEMORIA (SESSION STATE) ---
mesi = ["Gennaio", "Febbraio", "Marzo", "Aprile", "Maggio", "Giugno", 
        "Luglio", "Agosto", "Settembre", "Ottobre", "Novembre", "Dicembre"]

if 'dati_mensili' not in st.session_state:
    # Creiamo una memoria vuota all'inizio
    st.session_state['dati_mensili'] = {m: (0.0, 0.0) for m in mesi}

# --- 2. SIDEBAR CONFIGURAZIONE ---
st.sidebar.header("💰 Configurazione Budget")
budget_annuo = st.sidebar.number_input("Budget Totale Annuale (€)", value=300000)
fondo_emergenze = st.sidebar.slider("Fondo Emergenze (€)", 0, 30000, 5000)

st.sidebar.header("⚖️ Ripartizione Settori")
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

# --- 3. CARICAMENTO FILE (UPDATE MEMORIA) ---
st.title("🛡️ UnipolSai Budget Control")
uploaded_file = st.file_uploader("📂 Carica Excel per aggiornare i dati", type="xlsx")

if uploaded_file:
    df_load = pd.read_excel(uploaded_file)
    for _, row in df_load.iterrows():
        m = row['Mese']
        if m in st.session_state['dati_mensili']:
            # Sovrascriviamo la memoria con i dati del file
            s_m = float(row.get('Spesa Meccanica (€)', 0.0))
            s_c = float(row.get('Spesa Carrozzeria (€)', 0.0))
            st.session_state['dati_mensili'][m] = (s_m, s_c)
    st.success("Dati caricati nella memoria dell'app!")

# --- 4. INSERIMENTO/MODIFICA DATI ---
spese_finali = {}
with st.expander("📝 Visualizza/Modifica Spese Mensili"):
    c1, c2 = st.columns(2)
    for i, m in enumerate(mesi):
        with (c1 if i < 6 else c2):
            # Usiamo i dati dalla session_state come valore predefinito
            val_m, val_c = st.session_state['dati_mensili'][m]
            s_m = st.number_input(f"Mecc {m}", value=val_m, key=f"input_m_{m}")
            s_c = st.number_input(f"Carr {m}", value=val_c, key=f"input_c_{m}")
            spese_finali[m] = (s_m, s_c)

# --- 5. CALCOLI E FORECASTING ---
report = []
spesa_tot_reale = 0
mesi_chiusi = 0

for m in mesi:
    target = quota_base * pesi[m]
    s_m, s_c = spese_finali[m]
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

# --- 6. DASHBOARD E PROGRESS BAR ---
st.markdown("---")
st.subheader("🔮 Analisi Avanzamento")
progresso = min(spesa_tot_reale / budget_annuo, 1.0)
st.progress(progresso)

if mesi_chiusi > 0:
    media = spesa_tot_reale / mesi_chiusi
    stima = (media * 12) + fondo_emergenze
    diff = budget_annuo - stima
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Media Mensile Reale", f"{round(media, 2)} €")
    col2.metric("Proiezione Finale", f"{round(stima, 2)} €", delta=f"{round(stima-budget_annuo, 2)} €", delta_color="inverse")
    col3.metric("Avanzo Stimato", f"{round(diff, 2)} €")

st.table(df)

# --- 7. DOWNLOAD ---
output = io.BytesIO()
with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
    df.to_excel(writer, index=False, sheet_name='Budget')
st.download_button("📥 Scarica Report Aggiornato", output.getvalue(), "report_budget.xlsx")
