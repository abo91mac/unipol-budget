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
if 'db' not in st.session_state:
    db = {}
    for sk in ["C", "M"]:
        db[sk] = {}
        voci = VC if sk == "C" else VM
        for m in M:
            db[sk][m] = {v: {p: 0.0 for p in P} for v in voci}
    st.session_state['db'] = db
    st.session_state['pct'] = {m: 8.33 for m in M}

# --- 3. SIDEBAR ---
with st.sidebar:
    st.title("Pannello")
    
    with st.expander("% Budget Mensile"):
        for m in M:
            v_pct = st.session_state['pct'].get(m, 8.33)
            st.session_state['pct'][m] = st.number_input(m, value=v_pct, key=f"p_{m}")
    
    st.divider()
    u = st.file_uploader("Carica Excel", type="xlsx")
    
    if u:
        try:
            x = pd.ExcelFile(u)
            contatore = 0
            for sk, sn in [("C", "Carrozzeria"), ("M", "Meccanica")]:
                if sn in x.sheet_names:
                    df = pd.read_excel(x, sheet_name=sn)
                    # Pulizia colonne: tutto in maiuscolo senza spazi
                    df.columns = [str(c).strip().upper() for c in df.columns]
                    
                    for _, row in df.iterrows():
                        # Legge Attività e Partner ignorando maiuscole/minuscole
                        v_file = str(row.get('ATTIVITÀ', row.get('ATTIVITA', ''))).strip().upper()
                        p_file = str(row.get('PARTNER', '')).strip().upper()
                        
                        v_list = VC if sk == "C" else VM
                        for v_real in v_list:
                            if v_real.upper() in v_file:
                                for p_real in P:
                                    if p_real.upper() in p_file:
                                        for m in M:
                                            if m in df.columns:
                                                valore = float(row[m])
                                                st.session_state['db'][sk][m][v_real][p_real] = valore
                                                contatore += 1
            if contatore > 0:
                st.success(f"Aggiornati {contatore} valori!")
            else:
                st.warning("File letto, ma nessuna attività corrispondente trovata.")
        except Exception as e:
            st.error(f"Errore tecnico: {e}")

    if st.button("RESET"):
        st.session_state.clear()
        st.rerun()
    
    bc = st.number_input("Bud. Carr.", 386393.0)
    bm = st.number_input("Bud. Mecc.", 120000.0)

# --- 4. REPORT ---
def rep(s, b, voci):
    st.write("---")
    st.subheader("📊 Riepilogo Mensile e Totale")
    dat = []
    for m in M:
        tr = (b * st.session_state['pct'].get(m, 8.33)) / 100
        cn = sum(st.session_state['db'][s][m][v][p] for v in voci for p in P)
        dat.append({"Mese": m, "Target": tr, "Cons": cn, "Delta": tr-cn})
    
    df = pd.DataFrame(dat)
    t_tar = df['Target'].sum()
    t_con = df['Cons'].sum()
    tot = pd.DataFrame([{"Mese": "TOTALE", "Target": t_tar, "Cons": t_con, "Delta": t_tar-t_con}])
    df_f = pd.concat([df, tot], ignore_index=True).set_index("Mese")
    st.table(df_f.style.format(precision=2))

# --- 5. UI ---
st.title("🛡️ Unipol Budget Hub")
t1, t2 = st.tabs(["CARROZZERIA", "MECCANICA"])

def UI(s, voci, bud):
    for v in voci:
        with st.expander(v):
            for pt in P:
                st.write(f"**{pt}**")
                cols = st.columns(6)
                for i, m in enumerate(M):
                    val = st.session_state['db'][s][m][v][pt]
                    # Chiave univoca per evitare errori
                    k = f"key_{s}_{v}_{pt}_{m}"
                    nv = cols[i%6].number_input(m[:3], value=float(val), key=k)
                    st.session_state['db'][s][m][v][pt] = nv
    rep(s, bud, voci)

with t1:
    UI("C", VC, bc)
with t2:
    UI("M", VM, bm)
