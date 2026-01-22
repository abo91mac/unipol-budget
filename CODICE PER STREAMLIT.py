import streamlit as st
import pandas as pd
import io

st.set_page_config(page_title="UnipolSai Budget Planner", layout="wide")

st.title("🛡️ UnipolSai: Allocazione Budget Percentuale")
st.markdown("Pianifica il carico mensile e monitora gli scostamenti in tempo reale.")

# --- 1. SIDEBAR: BUDGET E LOGICA PERCENTUALE ---
st.sidebar.header("💰 Budget Globale")
budget_annuo = st.sidebar.number_input("Budget Totale Annuale (€)", value=300000, step=5000)
fondo_imprevisti = st.sidebar.slider("Riserva Emergenze (€)", 0, 30, 5000) # In euro per precisione

st.sidebar.header("⚖️ Divisione Settori")
p_mecc = st.sidebar.slider("% Quota Meccanica", 0, 100, 60)
p_carr = 100 - p_mecc

st.sidebar.header("📅 Stagionalità (% di variazione)")
st.sidebar.info("0% significa mese standard. +30% significa mese di picco.")

mesi = ["Gennaio", "Febbraio", "Marzo", "Aprile", "Maggio", "Giugno", 
        "Luglio", "Agosto", "Settembre", "Ottobre", "Novembre", "Dicembre"]

variazioni_pct = {}
with st.sidebar.expander("Regola Percentuali Mensili"):
    for m in mesi:
        # Default: +30% per Luglio e Ottobre, 0% per gli altri
        def_val = 30 if m in ["Luglio", "Ottobre"] else 0
        variazioni_pct[m] = st.slider(f"{m} (%)", -50, 100, def_val, 5)

# --- 2. LOGICA ALGORITMICA ---
# Trasformiamo le percentuali in pesi (es: +30% -> 1.3)
pesi = {m: 1 + (v/100) for m, v in variazioni_pct.items()}
peso_totale = sum(pesi.values())
quota_disponibile = budget_annuo - fondo_imprevisti
quota_base = quota_disponibile / peso_totale

# --- 3. INSERIMENTO DATI REALI ---
st.write("### ✍️ Inserimento Spese Correnti")
# Funzione per caricare dati esistenti
uploaded_file = st.file_uploader("Ripristina dati da Excel precedente", type="xlsx")
default_vals = {m: (0.0, 0.0) for m in mesi}

if uploaded_file:
    df_load = pd.read_excel(uploaded_file)
    for _, row in df_load.iterrows():
        m = row['Mese']
        if m in default_vals:
            default_vals[m] = (float(row.get('Spesa Meccanica (€)', 0)), float(row.get('Spesa Carrozzeria (€)', 0)))

spese_inserite = {}
c1, c2 = st.columns(2)
for i, m in enumerate(mesi):
    with (c1 if i < 6 else c2):
        with st.expander(f"Dati {m}"):
            s_m = st.number_input(f"Mecc - {m}", value=default_vals[m][0], key=f"m_{m}")
            s_c = st.number_input(f"Carr - {m}", value=default_vals[m][1], key=f"c_{m}")
            spese_inserite[m] = (s_m, s_c)

# --- 4. CALCOLO REPORT E FORECASTING ---
report = []
spesa_tot_reale = 0
mesi_comp = 0

for m in mesi:
    target_mese = quota_base * pesi[m]
    s_m, s_c = spese_inserite[m]
    tot_mese = s_m + s_c
    if tot_mese > 0:
        spesa_tot_reale += tot_mese
        mesi_comp += 1
    
    report.append({
        "Mese": m,
        "Budget Target (€)": round(target_mese, 2),
        "Spesa Meccanica (€)": round(s_m, 2),
        "Spesa Carrozzeria (€)": round(s_c, 2),
        "Avanzo/Sforamento (€)": round(target_mese - tot_mese, 2) if tot_mese > 0 else 0
    })

df_final = pd.DataFrame(report)

# Forecasting
if mesi_comp > 0:
    st.markdown("---")
    st.subheader("🔮 Forecasting a Fine Anno")
    media_mensile = spesa_tot_reale / mesi_comp
    stima_chiusura = (media_mensile * 12) + fondo_imprevisti
    differenza = budget_annuo - stima_chiusura
    
    f1, f2, f3 = st.columns(3)
    f1.metric("Media Mensile Reale", f"{round(media_mensile, 2)} €")
    f2.metric("Proiezione Finale", f"{round(stima_chiusura, 2)} €")
    f3.metric("Risultato Stimato", f"{round(differenza, 2)} €", delta=round(differenza, 2))

# --- 5. VISUALIZZAZIONE E DOWNLOAD ---
st.write("### 📊 Tabella di Riepilogo")
st.table(df_final)

# Esportazione Excel (con grafici)
output = io.BytesIO()
with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
    df_final.to_excel(writer, index=False, sheet_name='Budget')
    # Qui il codice per i grafici Excel come visto prima...
    
st.download_button("📥 Scarica Report Excel", output.getvalue(), "Report_Unipol_Percentuali.xlsx")