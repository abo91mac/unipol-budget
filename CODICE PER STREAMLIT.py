import streamlit as st
import pandas as pd
import io

# --- 1. CONFIGURAZIONE ---
st.set_page_config(layout="wide", page_title="Unipol Budget HUB")

M = ["GENNAIO", "FEBBRAIO", "MARZO", "APRILE", "MAGGIO", "GIUGNO", 
     "LUGLIO", "AGOSTO", "SETTEMBRE", "OTTOBRE", "NOVEMBRE", "DICEMBRE"]
P = ["KONECTA", "COVISIAN"]
VC = ["Gestione Contatti", "Ricontatto", "Documenti", "Firme Digitali", "Solleciti"]
VM = ["Solleciti Officine", "Ticket assistenza"]

# --- 2. INIT ---
def r_db():
    d = {}
    for sk in ["C", "M"]:
        d[sk] = {}
        voci = VC if sk == "C" else VM
        for m in M:
            d[sk][m] = {v: {p: 0.0 for p in P} for v in voci}
    st.session_state['db'] = d
    st.session_state['pct'] = {m: 8.33 for m in M}
    st.session_state['v'] = "9.0"

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
                    # Normalizzazione nomi colonne per evitare errori
                    df.columns = [str(c).strip().upper() for c in df.columns]
                    
                    for _, row in df.iterrows():
                        # Normalizzazione nomi attività e partner
                        vn_file = str(row.get('ATTIVITÀ', row.get('ATTIVITA', ''))).strip().upper()
                        pn_file = str(row.get('PARTNER', '')).strip().upper()
                        
                        v_target = VC if sk == "C" else VM
                        for v_real in v_target:
                            if vn_file == v_real.strip().upper():
                                for p_real in P:
                                    if pn_file == p_real.strip().upper():
                                        for m in M:
                                            if m in df.columns:
                                                val = float(row[m])
                                                st.session_state['db'][sk][m][v_real][p_real] = val
            st.success("Dati Excel caricati con successo!")
        except Exception as e:
            st.error(f"Errore caricamento: {e}")

    if st.button("RESET DATI"):
        r_db()
        st.rerun()
    
    bc = st.number_input("Budget Carr.", 386393.0)
    bm = st.number_input("Budget Mecc.", 120000.0)

# --- 4. REPORT TABELLA ---
def rep(s, b, voci):
    st.write("---")
    st.subheader("📊 Riepilogo Mensile e Totale Annuale")
    dat = []
    tt, tc = 0.0, 0.0
    
    for m in M:
        tr = (b * st.session_state['pct'].get(m, 8.33)) / 100
        cn = 0.0
        for v in voci:
            for pt in P:
                cn += st.session_state['db'][s][m][v][pt]
        
        dat.append({"Mese": m, "Target": tr, "Consuntivo": cn, "Delta": tr-cn})
        tt += tr
        tc += tc # (nota: tc += cn corretto sotto)
        tc = sum(d['Consuntivo'] for d in dat) # ricalcolo sicuro
        tt = sum(d['Target'] for d in dat)

    df = pd.DataFrame(dat)
    tot = pd.DataFrame([{"Mese": "TOTALE ANNUALE", "Target": tt, "Consuntivo": tc, "Delta": tt-tc}])
    df_f = pd.concat([df, tot], ignore_index=True).set_index("Mese")
    
    # Funzione di colorazione compatibile con vecchie e nuove versioni Pandas
    def color_delta(val):
        color = 'red' if val < 0 else 'green'
        return f'color: {color}'

    try:
        # Tenta il nuovo metodo 'map', se fallisce usa 'applymap'
        st.table(df_f.style.format(precision=2).map(color_delta, subset=['Delta']))
    except:
        st.table(df_f.style.format(precision=2).applymap(color_delta, subset=['Delta']))

# --- 5. UI ---
st.title("🛡️ Unipolservice Budget HUB")
t1, t2 = st.tabs(["🚗 CARROZZERIA", "🔧 MECCANICA"])

def UI(s, voci, bud):
    for v in voci:
        with st.expander(f"Attività: {v}"):
            for pt in P:
                st.write(f"**Partner: {pt}**")
                c = st.columns(6)
                for i, m in enumerate(M):
                    val_db = st.session_state['db'][s][m][v][pt]
                    k = f"u_{s}_{v}_{pt}_{m}"
                    nv = c[i%6].number_input(m[:3], value=float(val_db), key=k)
                    st.session_state['db'][s][m][v][pt] = nv
    rep(s, bud, voci)

with t1:
    UI("C", VC, bc)
with t2:
    UI("M", VM, bm)
