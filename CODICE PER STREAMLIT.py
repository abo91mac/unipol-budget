import streamlit as st
import pandas as pd
import io

# --- 1. SETUP ---
st.set_page_config(layout="wide")

# Stringhe brevi per evitare troncamenti
TITOLO = "🛡️ Unipol Budget"
MSG_OK = "✅ Caricato!"
L_CON = "Consuntivo (€)"
L_TAR = "Target (€)"
L_DEL = "Delta (€)"

M = ["GENNAIO", "FEBBRAIO", "MARZO", 
     "APRILE", "MAGGIO", "GIUGNO", 
     "LUGLIO", "AGOSTO", "SETTEMBRE", 
     "OTTOBRE", "NOVEMBRE", "DICEMBRE"]

P = ["KONECTA", "COVISIAN"]
VC = ["Contatti", "Ricontatto", "Doc", "Firme", "Soll"]
VM = ["Soll Off", "Ticket"]

# --- 2. INIT ---
if 'db' not in st.session_state:
    db = {}
    for s in ["C", "M"]:
        db[s] = {}
        voci = VC if s == "C" else VM
        for mese in M:
            db[s][mese] = {}
            for v in voci:
                db[s][mese][v] = {pt: 0.0 for pt in P}
    st.session_state['db'] = db

if 'pct' not in st.session_state:
    st.session_state['pct'] = {mese: 8.33 for mese in M}

# --- 3. EXCEL ---
def esporta():
    out = io.BytesIO()
    with pd.ExcelWriter(out, engine='xlsxwriter') as wr:
        for s_n in ["C", "M"]:
            voci = VC if s_n == "C" else VM
            sheet = "Carrozzeria" if s_n == "C" else "Meccanica"
            rows = []
            for v in voci:
                for pt in P:
                    r = {"Attività": v, "Partner": pt}
                    for mese in M:
                        r[mese] = st.session_state['db'][s_n][mese][v][pt]
                    rows.append(r)
            pd.DataFrame(rows).to_excel(wr, sheet_name=sheet, index=False)
    return out.getvalue()

# --- 4. SIDEBAR ---
with st.sidebar:
    st.title("Pannello")
    up = st.file_uploader("Carica Excel", type="xlsx")
    if up:
        xls = pd.ExcelFile(up)
        for s_key, s_name in [("C", "Carrozzeria"), ("M", "Meccanica")]:
            if s_name in xls.sheet_names:
                df = pd.read_excel(xls, sheet_name=s_name)
                for _, row in df.iterrows():
                    v_n = str(row['Attività'])
                    p_n = str(row['Partner'])
                    for mese in M:
                        if mese in df.columns:
                            val = float(row[mese])
                            st.session_state['db'][s_key][mese][v_n][p_n] = val
        st.success(MSG_OK)

    st.divider()
    if st.button("RESET"):
        st.session_state.clear()
        st.rerun()
    
    bc = st.number_input("Bud. Carr", 386393.0)
    bm = st.number_input("Bud. Mecc", 120000.0)

# --- 5. REPORT ---
def report(s, b, voci):
    st.write("---")
    res = []
    tt, tc = 0.0, 0.0
    for mese in M:
        q = st.session_state['pct'].get(mese, 8.33)
        tr = (b * q) / 100
        cn = 0.0
        for v in voci:
            for pt in P:
                cn += st.session_state['db'][s][mese][v][pt]
        res.append({"Mese": mese, L_TAR: tr, L_CON: cn, L_DEL: tr-cn})
        tt += tr
        tc += cn
    
    df = pd.DataFrame(res)
    tot = pd.DataFrame([{"Mese": "TOTALE", L_TAR: tt, L_CON: tc, L_DEL: tt-tc}])
    df_f = pd.concat([df, tot], ignore_index=True).set_index("Mese")
    st.table(df_f.style.format(precision=2))

# --- 6. UI ---
st.title(TITOLO)
t1, t2 = st.tabs(["CARR", "MECC"])

def UI(s, voci, bud):
    for v in voci:
        with st.expander(v):
            for pt in P:
                st.write(pt)
                c = st.columns(6)
                for i, mese in enumerate(M):
                    val = st.session_state['db'][s][mese][v][pt]
                    k = f"{s}{v[0]}{pt[0]}{mese[:2]}"
                    nv = c[i%6].number_input(mese[:3], value=val, key=k)
                    st.session_state['db'][s][mese][v][pt] = nv
    report(s, bud, voci)

with t1:
    UI("C", VC, bc)
with t2:
    UI("M", VM, bm)
