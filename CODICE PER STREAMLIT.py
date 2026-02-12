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
if 'db' not in st.session_state:
    db = {}
    for sk in ["C", "M"]:
        db[sk] = {}
        voci = VC if sk == "C" else VM
        for m in M:
            db[sk][m] = {v: {p: 0.0 for p in P} for v in voci}
    st.session_state['db'] = db
    st.session_state['pct'] = {m: 8.33 for m in M}

# --- 3. FUNZIONE EXPORT ---
def genera_export():
    out = io.BytesIO()
    with pd.ExcelWriter(out, engine='xlsxwriter') as writer:
        for sk, sn in [("C", "Carrozzeria"), ("M", "Meccanica")]:
            v_list = VC if sk == "C" else VM
            rows = []
            for v in v_list:
                for p in P:
                    r = {"Attività": v, "Partner": p}
                    for m in M:
                        r[m] = st.session_state['db'][sk][m][v][p]
                    rows.append(r)
            pd.DataFrame(rows).to_excel(writer, sheet_name=sn, index=False)
    return out.getvalue()

# --- 4. SIDEBAR ---
with st.sidebar:
    st.title("🛡️ Pannello")
    
    # PULSANTE EXPORT AGGIUNTO QUI
    st.download_button(
        label="📥 Scarica Export Consolidato",
        data=genera_export(),
        file_name="Export_Budget.xlsx",
        mime="application/vnd.ms-excel"
    )
    
    st.divider()
    
    with st.expander("% Budget Mensile"):
        for m in M:
            v_pct = st.session_state['pct'].get(m, 8.33)
            st.session_state['pct'][m] = st.number_input(m, value=v_pct, key=f"p_{m}")
    
    st.divider()
    u = st.file_uploader("📂 Carica Excel", type="xlsx")
    
    if u:
        try:
            x = pd.ExcelFile(u)
            contatore = 0
            # RIGHE CORTE PER EVITARE SYNTAX ERROR
            S_MAP = [("C", "Carrozzeria"), 
                     ("M", "Meccanica")]
            for sk, sn in S_MAP:
                if sn in x.sheet_names:
                    df = pd.read_excel(x, sheet_name=sn)
                    df.columns = [str(c).strip().upper() for c in df.columns]
                    for _, row in df.iterrows():
                        v_f = str(row.get('ATTIVITÀ', row.get('ATTIVITA', ''))).strip().upper()
                        p_f = str(row.get('PARTNER', '')).strip().upper()
                        v_list = VC if sk == "C" else VM
                        for v_real in v_list:
                            if v_real.upper() in v_f:
                                for p_real in P:
                                    if p_real.upper() in p_f:
                                        for m in M:
                                            if m in df.columns:
                                                st.session_state['db'][sk][m][v_real][p_real] = float(row[m])
                                                contatore += 1
            st.success(f"Aggiornati {contatore} valori!")
        except Exception as e:
            st.error(f"Errore: {e}")

    if st.button("🗑️ RESET DATI"):
        st.session_state.clear()
        st.rerun()
    
    bc = st.number_input("Bud. Carr.", 386393.0)
    bm = st.number_input("Bud. Mecc.", 120000.0)

# --- 5. REPORT ---
def rep(s, b, voci):
    st.write("---")
    st.subheader("📊 Riepilogo Mensile e Totale")
    dat = []
    for m in M:
        tr = (b * st.session_state['pct'].get(m, 8.33)) / 100
        cn = sum(st.session_state['db'][s][m][v][p] for v in voci for p in P)
        dat.append({"Mese": m, "Target": tr, "Consuntivo": cn, "Delta": tr-cn})
    
    df = pd.DataFrame(dat)
    t_tar = df['Target'].sum()
    t_con = df['Consuntivo'].sum()
    tot = pd.DataFrame([{"Mese": "TOTALE", "Target": t_tar, "Consuntivo": t_con, "Delta": t_tar-t_con}])
    df_f = pd.concat([df, tot], ignore_index=True).set_index("Mese")
    st.table(df_f.style.format(precision=2))

# --- 6. UI ---
st.title("🛡️ Unipolservice Budget HUB")
t1, t2 = st.tabs(["🚗 CARROZZERIA", "🔧 MECCANICA"])

def UI(s, voci, bud):
    for v in voci:
        with st.expander(f"Attività: {v}"):
            for pt in P:
                st.write(f"Partner: **{pt}**")
                cols = st.columns(6)
                for i, m in enumerate(M):
                    val = st.session_state['db'][s][m][v][pt]
                    k = f"key_{s}_{v}_{pt}_{m}"
                    nv = cols[i%6].number_input(m[:3], value=float(val), key=k)
                    st.session_state['db'][s][m][v][pt] = nv
    rep(s, bud, voci)

with t1:
    UI("C", VC, bc)
