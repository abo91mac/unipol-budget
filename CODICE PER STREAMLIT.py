import streamlit as st
import pandas as pd
import io

# --- SETUP ---
st.set_page_config(layout="wide")

M = ["GEN", "FEB", "MAR", "APR", "MAG", "GIU", 
     "LUG", "AGO", "SET", "OTT", "NOV", "DIC"]
P = ["KONECTA", "COVISIAN"]
V_C = ["Contatti", "Ricontatto", "Doc", "Firme", "Soll"]
V_M = ["Soll Off", "Ticket"]

# --- INIT ---
if 'db' not in st.session_state:
    db = {}
    for s in ["C", "M"]:
        db[s] = {}
        voci = V_C if s == "C" else V_M
        for mese in M:
            db[s][mese] = {}
            for v in voci:
                db[s][mese][v] = {p: 0.0 for p in P}
    st.session_state['db'] = db

if 'pct' not in st.session_state:
    st.session_state['pct'] = {mese: 8.33 for mese in M}

# --- SIDEBAR ---
with st.sidebar:
    st.title("🛡️ Unipol")
    if st.button("🗑️ RESET"):
        st.session_state.clear()
        st.rerun()
    
    bc = st.number_input("Bud. Carr", 386393.0)
    bm = st.number_input("Bud. Mecc", 120000.0)

# --- ANALISI ---
def mostra_tab(sett, budget, voci):
    st.divider()
    res = []
    t_tar = 0.0
    t_con = 0.0
    
    for mese in M:
        # Codice spezzato per evitare tagli
        d = st.session_state['pct']
        q = d.get(mese, 8.33)
        tar = (budget * q) / 100
        
        con = 0.0
        for v in voci:
            for pt in P:
                con += st.session_state['db'][sett][mese][v][pt]
        
        res.append({
            "Mese": mese,
            "Target": tar,
            "Cons": con,
            "Delta": tar - con
        })
        t_tar += tar
        t_con += con

    df = pd.DataFrame(res)
    tot = pd.DataFrame([{
        "Mese": "TOTALE",
        "Target": t_tar,
        "Cons": t_con,
        "Delta": t_tar - t_con
    }])
    
    df_f = pd.concat([df, tot], ignore_index=True)
    df_f = df_f.set_index("Mese")
    
    st.write(f"### Report {sett}")
    st.table(df_f.style.format(precision=2))

# --- MAIN ---
st.title("🛡️ Unipolservice Budget")

t1, t2 = st.tabs(["🚗 CARR", "🔧 MECC"])

def inputs(s, voci):
    for v in voci:
        with st.exp
