import streamlit as st
import pandas as pd
import io

# --- 1. CONFIGURAZIONE ---
st.set_page_config(layout="wide")

M = ["GENNAIO", "FEBBRAIO", "MARZO", "APRILE", "MAGGIO", "GIUGNO", 
     "LUGLIO", "AGOSTO", "SETTEMBRE", "OTTOBRE", "NOVEMBRE", "DICEMBRE"]
P = ["KONECTA", "COVISIAN"]
VC = ["Gestione Contatti", "Ricontatto", "Documenti", "Firme Digitali", "Solleciti"]
VM = ["Solleciti Officine", "Ticket assistenza"]

# --- 2. INIT ---
def r_db():
    d = {}
    for s in ["C", "M"]:
        d[s] = {}
        v_list = VC if s == "C" else VM
        for m in M:
            d[s][m] = {v: {pt: 0.0 for pt in P} for v in v_list}
    st.session_state['db'] = d
    st.session_state['pct'] = {mese: 8.33 for mese in M}
    st.session_state['v'] = "7.0"

if 'v' not in st.session_state:
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
                        for m in M:
                            # Caricamento solo se l'attività esiste nel DB
                            if m in df.columns and vn in st.session_state['db'][sk][m]:
                                val = float(row[m])
                                st.session_state['db'][sk][m][vn][pn] = val
            st.success("Dati Excel caricati!")
        except Exception as e:
            st.error(f"Errore Excel: {e}")

    if st.button("RESET DATI"):
        r_db()
        st.rerun()
    
    bc = st.number_input("Budget Carr.", 386393.0)
    bm = st.number_input("Budget Mecc.", 120000.0)

# --- 4. REPORT TABELLA ---
def rep(s, b, voci):
    st.write("---")
    st.subheader("📊 Analisi Mensile e Totale")
    dat = []
    tt, tc = 0.0, 0.0
    for m in M:
        q = st.session_state['pct'].get(m, 8.33)
        tr = (b * q) / 100
        cn = sum(st.session_state['db'][s][m][v][pt] for v in voci for pt in P)
        dat.append({"Mese": m, "Target": tr, "Consuntivo": cn, "Delta": tr-cn})
        tt += tr
        tc += cn
    
    df = pd.DataFrame(dat)
    tot = pd.DataFrame([{"Mese": "TOTALE ANNUALE", "Target": tt, "Consuntivo": tc, "Delta": tt-tc}])
    df_f = pd.concat([df, tot], ignore_index=True).set_index("Mese")
    st.table(df_f.style.format(precision=2).applymap(
        lambda x: 'color: red' if x < 0 else 'color: green', subset=['Delta']
    ))

# --- 5. INTERFACCIA ---
st.title("🛡️ Unipol Budget HUB")
t1, t2 = st.tabs(["🚗 CARROZZERIA", "🔧 MECCANICA"])

def UI(s, voci, bud):
    for v in voci:
        with st.expander(f"Attività: {v}"):
            for pt in P:
                st.write(f"**Partner: {pt}**")
                c = st.columns(6)
                for i, m in enumerate(M):
                    db_v = st.session_state['db'][s][m][v][pt]
                    # Chiave univoca lunga per evitare errori di duplicati
                    k = f"key_{s}_{v}_{pt}_{m}"
                    nv = c[i%6].number_input(m[:3], value=db_v, key=k)
                    st.session_state['db'][s][m][v][pt] = nv
    rep(s, bud, voci)

with t1:
    UI("C", VC, bc)
with t2:
    UI("M", VM, bm)
