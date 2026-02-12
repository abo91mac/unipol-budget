import streamlit as st
import pandas as pd
import io

# --- 1. CONFIGURAZIONE ---
st.set_page_config(layout="wide")

# Nomi costanti - DEVONO coincidere con l'Excel
M = ["GENNAIO", "FEBBRAIO", "MARZO", "APRILE", "MAGGIO", "GIUGNO", 
     "LUGLIO", "AGOSTO", "SETTEMBRE", "OTTOBRE", "NOVEMBRE", "DICEMBRE"]
P = ["KONECTA", "COVISIAN"]
VC = ["Gestione Contatti", "Ricontatto", "Documenti", "Firme Digitali", "Solleciti"]
VM = ["Solleciti Officine", "Ticket assistenza"]

# --- 2. INIT SICURO ---
def r_db():
    d = {}
    for s_key in ["C", "M"]:
        d[s_key] = {}
        voci_settore = VC if s_key == "C" else VM
        for mese in M:
            d[s_key][mese] = {}
            for v in voci_settore:
                d[s_key][mese][v] = {pt: 0.0 for pt in P}
    st.session_state['db'] = d
    st.session_state['pct'] = {mese: 8.33 for mese in M}
    st.session_state['v_app'] = "8.1"

# Reset se versione vecchia o db mancante
if 'v_app' not in st.session_state or 'db' not in st.session_state:
    r_db()

# --- 3. SIDEBAR & EXCEL ---
with st.sidebar:
    st.title("Pannello")
    u = st.file_uploader("Carica Excel", type="xlsx")
    if u:
        try:
            x = pd.ExcelFile(u)
            for sk, sn in [("C", "Carrozzeria"), ("M", "Meccanica")]:
                if sn in x.sheet_names:
                    df = pd.read_excel(x, sheet_name=sn)
                    for _, row in df.iterrows():
                        vn = str(row['Attività']).strip()
                        pn = str(row['Partner']).strip()
                        for mese in M:
                            # Carica solo se la chiave esiste nel DB per evitare KeyError
                            if mese in df.columns:
                                if vn in st.session_state['db'][sk][mese]:
                                    val = float(row[mese])
                                    st.session_state['db'][sk][mese][vn][pn] = val
            st.success("Dati caricati!")
        except Exception as e:
            st.error(f"Errore: {e}")

    if st.button("RESET DATI"):
        r_db()
        st.rerun()
    
    bc = st.number_input("Budget Carr.", 386393.0)
    bm = st.number_input("Budget Mecc.", 120000.0)

# --- 4. REPORT TABELLA ---
def rep(s, b, voci):
    st.write("---")
    st.subheader("📊 Riepilogo Mensile e Totale")
    dat = []
    tt, tc = 0.0, 0.0
    for m in M:
        q = st.session_state['pct'].get(m, 8.33)
        tr = (b * q) / 100
        # Somma sicura dei consuntivi
        cn = 0.0
        for v in voci:
            cn += st.session_state['db'][s][m][v]["KONECTA"]
            cn += st.session_state['db'][s][m][v]["COVISIAN"]
            
        dat.append({"Mese": m, "Target": tr, "Consuntivo": cn, "Delta": tr-cn})
        tt += tr
        tc += cn
    
    df = pd.DataFrame(dat)
    tot = pd.DataFrame([{"Mese": "TOTALE ANNUALE", "Target": tt, "Consuntivo": tc, "Delta": tt-tc}])
    df_f = pd.concat([df, tot], ignore_index=True).set_index("Mese")
    
    # Formattazione colori
    st.table(df_f.style.format(precision=2).applymap(
        lambda x: 'color: red' if x < 0 else 'color: green', subset=['Delta']
    ))

# --- 5. UI ---
st.title("🛡️ Unipolservice Budget HUB")
t1, t2 = st.tabs(["🚗 CARROZZERIA", "🔧 MECCANICA"])

def UI(s, voci, bud):
    for v in voci:
        with st.expander(f"Attività: {v}"):
            for pt in P:
                st.write(f"**Partner: {pt}**")
                c = st.columns(6)
                for i, mese in enumerate(M):
                    # Accesso al DB con i nuovi nomi costanti
                    val_db = st.session_state['db'][s][mese][v][pt]
                    k = f"u_{s}_{v}_{pt}_{mese}"
                    nv = c[i%6].number_input(mese[:3], value=val_db, key=k)
                    st.session_state['db'][s][mese][v][pt] = nv
    rep(s, bud, voci)

with t1:
    UI("C", VC, bc)
with t2:
    UI("M", VM, bm)
