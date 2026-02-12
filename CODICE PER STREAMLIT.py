import streamlit as st
import pandas as pd
import io

# --- 1. SETUP ---
st.set_page_config(layout="wide")

# Liste costanti
M = ["GEN", "FEB", "MAR", "APR", "MAG", "GIU", 
     "LUG", "AGO", "SET", "OTT", "NOV", "DIC"]
P = ["KON", "COV"]
VC = ["Contatti", "Ricont", "Doc", "Firme", "Soll"]
VM = ["SollOff", "Ticket"]

# --- 2. INIT SICURO (Previene KeyError) ---
def init_data():
    d = {}
    for s in ["C", "M"]:
        d[s] = {}
        voci = VC if s == "C" else VM
        for m in M:
            d[s][m] = {}
            for v in voci:
                d[s][m][v] = {pt: 0.0 for pt in P}
    return d

# Se il db non esiste o ha un formato vecchio, resettalo
if 'db' not in st.session_state or 'C' not in st.session_state['db']:
    st.session_state['db'] = init_data()

if 'pct' not in st.session_state:
    st.session_state['pct'] = {mese: 8.33 for mese in M}

# --- 3. SIDEBAR ---
with st.sidebar:
    st.title("Pannello")
    if st.button("RESET TOTALE"):
        st.session_state['db'] = init_data()
        st.rerun()
    
    bc = st.number_input("Bud.C", 386393.0)
    bm = st.number_input("Bud.M", 120000.0)

# --- 4. FUNZIONE TABELLA ---
def tab(s, b, v_list):
    st.write("---")
    st.write("### REPORT FINALE")
    res = []
    t_t, t_c = 0.0, 0.0
    
    for m in M:
        q = st.session_state['pct'].get(m, 8.33)
        tr = (b * q) / 100
        cn = 0.0
        for v in v_list:
            for pt in P:
                cn += st.session_state['db'][s][m][v][pt]
        res.append({"Mese": m, "Tar": tr, "Cons": cn, "Delta": tr-cn})
        t_t += tr
        t_c += cn
    
    df = pd.DataFrame(res)
    tot = pd.DataFrame([{"Mese": "TOTAL", "Tar": t_t, "Cons": t_c, "Delta": t_t-t_c}])
    df_f = pd.concat([df, tot], ignore_index=True)
    st.table(df_f.set_index("Mese").style.format(precision=2))

# --- 5. INTERFACCIA ---
st.title("Unipol Budget")
t1, t2 = st.tabs(["CARR", "MECC"])

def UI(s, voci):
    for v in voci:
        st.markdown(f"**Attività: {v}**")
        for pt in P:
            st.text(f"Partner: {pt}")
            c = st.columns(6)
            for i, mese in enumerate(M):
                # Lettura sicura
                val = st.session_state['db'][s][mese][v][pt]
                k = f"{s}_{v[:2]}_{pt[:2]}_{mese}"
                nv = c[i%6].number_input(
                    mese, 
                    value=val, 
                    key=k,
                    label_visibility="visible" # Visibile per debug
                )
                st.session_state['db'][s][mese][v][pt] = nv
    tab(s, (bc if s=="C" else bm), voci)

with t1:
    UI("C", VC)

with t2:
    UI("M", VM)
