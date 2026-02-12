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
    st.session_state['v'] = "10.0"

if 'v' not in st.session_state:
    r_db()

# --- 3. FUNZIONE TEMPLATE ---
def crea_template():
    out = io.BytesIO()
    with pd.ExcelWriter(out, engine='xlsxwriter') as writer:
        for sk, sn, voci in [("C", "Carrozzeria", VC), ("M", "Meccanica", VM)]:
            rows = []
            for v in voci:
                for p in P:
                    row = {"Attività": v, "Partner": p}
                    for m in M:
                        row[m] = 0.0
                    rows.append(row)
            pd.DataFrame(rows).to_excel(writer, sheet_name=sn, index=False)
    return out.getvalue()

# --- 4. SIDEBAR & EXCEL ---
with st.sidebar:
    st.title("🛡️ Pannello")
    
    st.download_button(
        label="📥 Scarica Template Excel",
        data=crea_template(),
        file_name="Template_Budget_Unipol.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    
    st.divider()
    u = st.file_uploader("📂 Carica Excel", type="xlsx")
    if u:
        try:
            x = pd.ExcelFile(u)
            for sk, sn in [("C", "Carrozzeria"), ("M", "Meccanica")]:
                if sn in x.sheet_names:
                    df = pd.read_excel(x, sheet_name=sn)
                    df.columns = [str(c).strip().upper() for c in df.columns]
                    for _, row in df.iterrows():
                        v_f = str(row.get('ATTIVITÀ', row.get('ATTIVITA', ''))).strip().upper()
                        p_f = str(row.get('PARTNER', '')).strip().upper()
                        v_target = VC if sk == "C" else VM
                        for v_real in v_target:
                            if v_f == v_real.strip().upper():
                                for p_real in P:
                                    if p_f == p_real.strip().upper():
                                        for m in M:
                                            if m in df.columns:
                                                val = float(row[m])
                                                st.session_state['db'][sk][m][v_real][p_real] = val
            st.success("Dati caricati!")
        except Exception as e:
            st.error(f"Errore: {e}")

    if st.button("🗑️ RESET DATI"):
        r_db()
        st.rerun()
    
    bc = st.number_input("Budget Carr.", 386393.0)
    bm = st.number_input("Budget Mecc.", 120000.0)

# --- 5. REPORT TABELLA ---
def rep(s, b, voci):
    st.write("---")
    st.subheader("📊 Riepilogo Mensile e Totale Annuale")
    dat = []
    for m in M:
        tr = (b * st.session_state['pct'].get(m, 8.33)) / 100
        cn = sum(st.session_state['db'][s][m][v][p] for v in voci for p in P)
        dat.append({"Mese": m, "Target": tr, "Consuntivo": cn, "Delta": tr-cn})
    
    df = pd.DataFrame(dat)
    t_tar = df['Target'].sum()
    t_con = df['Consuntivo'].sum()
    tot = pd.DataFrame([{"Mese": "TOTALE ANNUALE", "Target": t_tar, "Consuntivo": t_con, "Delta": t_tar-t_con}])
    df_f = pd.concat([df, tot], ignore_index=True).set_index("Mese")
    
    def color_delta(val):
        return 'color: red' if val < 0 else 'color: green'

    try:
        st.table(df_f.style.format(precision=2).map(color_delta, subset=['Delta']))
    except:
        st.table(df_f.style.format(precision=2).applymap(color_delta, subset=['Delta']))

# --- 6. UI ---
st.title("🛡️ Unipolservice Budget HUB")
t1, t2 = st.tabs(["🚗 CARROZZERIA", "🔧 MECCANICA"])

def UI(s, voci, bud):
    for v in voci:
        with st.expander(f"Attività: {v}"):
            for pt in P:
                st.write(f"**Partner: {pt}**")
                c = st.columns(6)
                for i, m in enumerate(M):
                    val = st.session_state['db'][s][m][v][pt]
                    k = f"u_{s}_{v}_{pt}_{m}"
                    nv = c[i%6].number_input(m[:3], value=float(val), key=k)
                    st.session_state['db'][s][m][v][pt] = nv
    rep(s, bud, voci)

with t1:
    UI("C", VC, bc)
with t2:
    UI("M", VM, bm)
