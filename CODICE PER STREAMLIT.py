import streamlit as st
import pandas as pd
import io

# --- 1. DEFINIZIONI STRINGHE CORTE ---
T = "Unipol Budget"
OK = "Caricato"
ERR = "Errore"
M = ["GENNAIO", "FEBBRAIO", "MARZO", "APRILE", "MAGGIO", "GIUGNO", 
     "LUGLIO", "AGOSTO", "SETTEMBRE", "OTTOBRE", "NOVEMBRE", "DICEMBRE"]
P = ["KONECTA", "COVISIAN"]
VC = ["Contatti", "Ricontatto", "Doc", "Firme", "Soll"]
VM = ["Soll Off", "Ticket"]

# --- 2. SETUP ---
st.set_page_config(layout="wide")

# --- 3. INIT SICURO ---
def r_db():
    d = {}
    for s in ["C", "M"]:
        d[s] = {}
        v = VC if s == "C" else VM
        for m in M:
            d[s][m] = {i: {j: 0.0 for j in P} for i in v}
    st.session_state['db'] = d
    st.session_state['pct'] = {mese: 8.33 for mese in M}
    st.session_state['v'] = "5.0"

if 'v' not in st.session_state:
    r_db()

# --- 4. SIDEBAR & EXCEL ---
with st.sidebar:
    st.title("Pannello")
    u = st.file_uploader("Excel", type="xlsx")
    if u:
        try:
            x = pd.ExcelFile(u)
            for sk, sn in [("C", "Carrozzeria"), ("M", "Meccanica")]:
                if sn in x.sheet_names:
                    df = pd.read_excel(x, sheet_name=sn)
                    for _, row in df.iterrows():
                        vn, pn = str(row['Attività']), str(row['Partner'])
                        for mese in M:
                            if mese in df.columns:
                                val = float(row[mese])
                                st.session_state['db'][sk][mese][vn][pn] = val
            st.success(OK)
        except:
            st.error(ERR)

    if st.button("RESET"):
        r_db()
        st.rerun()
    
    bc = st.number_input("Bud. C", 386393.0)
    bm = st.number_input("Bud. M", 120000.0)

# --- 5. REPORT ---
def rep(s, b, voci):
    st.write("---")
    st.subheader("Report Mensile")
    dat = []
    tt, tc = 0.0, 0.0
    for m in M:
        q = st.session_state['pct'].get(m, 8.33)
        tr = (b * q) / 100
        cn = sum(st.session_state['db'][s][m][v][pt] for v in voci for pt in P)
        dat.append({"Mese": m, "Target": tr, "Cons": cn, "Delta": tr-cn})
        tt, tc = tt+tr, tc+cn
    
    df = pd.DataFrame(dat)
    tot = pd.DataFrame([{"Mese": "TOTALE", "Target": tt, "Cons": tc, "Delta": tt-tc}])
    df_f = pd.concat([df, tot], ignore_index=True).set_index("Mese")
    st.table(df_f.style.format(precision=2))

# --- 6. UI ---
st.title(T)
t1, t2 = st.tabs(["CARR", "MECC"])

def UI(s, voci, bud):
    for v in voci:
        with st.expander(v):
            for pt in P:
                st.write(pt)
                c = st.columns(6)
                for i, m in enumerate(M):
                    db_v = st.session_state['db'][s][m][v][pt]
                    k = f"{s}{v[0]}{pt[0]}{m[:2]}"
                    nv = c[i%6].number_input(m[:3], value=db_v, key=k)
                    st.session_state['db'][s][m][v][pt] = nv
    rep(s, bud, voci)

with t1:
    UI("C", VC, bc)
with t2:
    UI("M", VM, bm)
