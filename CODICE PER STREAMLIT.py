import streamlit as st
import pandas as pd
import io

st.set_page_config(page_title="Unipolservice Budget HUB", layout="wide")

# --- 1. MEMORIA DI SESSIONE ---
mesi = ["Gennaio", "Febbraio", "Marzo", "Aprile", "Maggio", "Giugno", 
        "Luglio", "Agosto", "Settembre", "Ottobre", "Novembre", "Dicembre"]

if 'dati_mensili' not in st.session_state:
    st.session_state['dati_mensili'] = {m: {'mecc': 0.0, 'carr': 0.0, 'note': ''} for m in mesi}
if 'file_version' not in st.session_state:
    st.session_state['file_version'] = 0

# --- FUNZIONE RESET ---
def reset_dati():
    st.session_state['dati_mensili'] = {m: {'mecc': 0.0, 'carr': 0.0, 'note': ''} for m in mesi}
    st.session_state['file_version'] += 1
    st.session_state['confirm_reset'] = False # Chiude il menu di conferma
    st.toast("⚠️ Tutti i dati sono stati azzerati!")

def process_upload():
    if st.session_state.uploader is not None:
        try:
            df_load = pd.read_excel(st.session_state.uploader)
            nuovi_dati = {m: {'mecc': 0.0, 'carr': 0.0, 'note': ''} for m in mesi}
            for _, row in df_load.iterrows():
                m = row.get('Mese')
                if m in nuovi_dati:
                    nuovi_dati[m] = {
                        'mecc': round(float(row.get('Meccanica', row.get('Spesa Meccanica (€)', 0.0))), 2),
                        'carr': round(float(row.get('Carrozzeria', row.get('Spesa Carrozzeria (€)', 0.0))), 2),
                        'note': str(row.get('Note', row.get('Note/Causali', ''))) if pd.notna(row.get('Note')) else ''
                    }
            st.session_state['dati_mensili'] = nuovi_dati
            st.session_state['file_version'] += 1
            st.toast("✅ Budget HUB Aggiornato!")
        except Exception as e:
            st.error(f"Errore: {e}")

# --- 2. SIDEBAR ---
st.sidebar.title("⚙️ HUB Control Panel")
budget_annuo = st.sidebar.number_input("Budget Totale Annuale (€)", value=300000.0, step=1000.0)
fondo = st.sidebar.slider("Fondo Riserva (€)", 0, 50000, 5000)
p_mecc = st.sidebar.slider("% Target Meccanica", 0, 100, 60)

with st.sidebar.expander("📅 Regolazione Stagionalità (%)", expanded=False):
    # Modificato: ora il default è 0 per tutti i mesi
    var_pct = {m: st.slider(f"{m}", -50, 100, 0) for m in mesi}

# --- TASTO RESET CON CONFERMA ---
st.sidebar.divider()
if 'confirm_reset' not in st.session_state:
    st.session_state['confirm_reset'] = False

if not st.session_state['confirm_reset']:
    if st.sidebar.button("🗑️ RESET TOTALE DATI"):
        st.session_state['confirm_reset'] = True
        st.rerun()
else:
    st.sidebar.warning("Sei sicuro?")
    col_res1, col_res2 = st.sidebar.columns(2)
    if col_res1.button("SÌ ✅", use_container_width=True):
        reset_dati()
        st.rerun()
    if col_res2.button("NO ❌", use_container_width=True):
        st.session_state['confirm_reset'] = False
        st.rerun()

# --- 3. TITOLO ---
st.title("🛡️ Unipolservice Budget HUB")
st.divider()

# --- 4. CARICAMENTO ---
st.file_uploader("📂 Carica Report Precedente", type="xlsx", key="uploader", on_change=process_upload)

# --- 5. INPUT DATI ---
st.subheader("📝 Inserimento Dati Mensili")
with st.expander("Apri Gestione Mensile", expanded=True):
    cols = st.columns(3)
    for i, m in enumerate(mesi):
        with cols[i % 3]:
            d = st.session_state['dati_mensili'][m]
            v = st.session_state.file_version
            s_m = st.number_input(f"Mecc {m} (€)", value=d['mecc'], key=f"m_{m}_{v}", format="%.2f")
            s_c = st.number_input(f"Carr {m} (€)", value=d['carr'], key=f"c_{m}_{v}", format="%.2f")
            txt = st.text_input(f"Note {m}", value=d['note'], key=f"n_{m}_{v}")
            st.session_state['dati_mensili'][m] = {'mecc': round(s_m, 2), 'carr': round(s_c, 2), 'note': txt}

# --- 6. CALCOLI ---
pesi = {m: 1 + (v/100) for m, v in var_pct.items()}
quota_base = (budget_annuo - fondo) / sum(pesi.values())
report = []
for m in mesi:
    target = round(quota_base * pesi[m], 2)
    d = st.session_state['dati_mensili'][m]
    tot = round(d['mecc'] + d['carr'], 2)
    report.append({
        "Mese": m, 
        "Target": target, 
        "Reale": tot,
        "Delta": round(target - tot, 2), 
        "Status": "🔴 SFORO" if (tot > target and tot > 0) else ("🟢 OK" if tot > 0 else "⚪ ATTESA"),
        "Meccanica": d['mecc'], 
        "Carrozzeria": d['carr'], 
        "Note": d['note']
    })
df_rep = pd.DataFrame(report)

# --- 7. DASHBOARD ---
st.divider()
speso_tot = round(df_rep["Reale"].sum(), 2)
c1, c2, c3 = st.columns(3)
c1.metric("Budget Utilizzato", f"{speso_tot} €", f"{round((speso_tot/budget_annuo)*100, 1)}%")
c2.metric("Residuo", f"{round(budget_annuo - speso_tot, 2)} €")
c3.metric("Fondo Riserva", f"{fondo} €")

def color_status(val):
    color = 'red' if 'SFORO' in str(val) else ('green' if 'OK' in str(val) else 'gray')
    return f'color: {color}; font-weight: bold'

fmt = {"Target": "{:.2f}", "Reale": "{:.2f}", "Delta": "{:.2f}", "Meccanica": "{:.2f}", "Carrozzeria": "{:.2f}"}
st.dataframe(df_rep.style.applymap(color_status, subset=['Status']).format(fmt), use_container_width=True)

st.line_chart(df_rep.set_index("Mese")[["Target", "Reale"]])

# --- 8. DOWNLOAD ---
output = io.BytesIO()
with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
    df_rep.to_excel(writer, index=False, sheet_name='Budget_HUB')
st.download_button("📥 Scarica Report HUB", output.getvalue(), "Unipolservice_Budget_HUB.xlsx")
