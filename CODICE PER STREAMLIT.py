import streamlit as st
import pandas as pd
import io
import os
from PIL import Image

# --- 1. CONFIGURAZIONE PAGINA ---
st.set_page_config(page_title="Unipolservice Budget HUB", layout="wide")

# Tema grafico Blu Unipol e stile tasto Reset
st.markdown("""
    <style>
    .stApp { background-color: #f4f7f9; }
    .stTabs [aria-selected="true"] { background-color: #003399 !important; color: white !important; }
    .stButton>button { background-color: #003399; color: white; border-radius: 5px; width: 100%; }
    /* Stile rosso per il tasto reset */
    div.stButton > button:first-child {
        background-color: #ff4b4b;
    }
    div[data-testid="stMetricValue"] { color: #003399; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. DATI FISSI ---
MESI = ["GENNAIO", "FEBBRAIO", "MARZO", "APRILE", "MAGGIO", "GIUGNO", 
        "LUGLIO", "AGOSTO", "SETTEMBRE", "OTTOBRE", "NOVEMBRE", "DICEMBRE"]
PARTNER = ["KONECTA", "COVISIAN"]
VOCI_CARR = ["Gestione Contatti", "Ricontatto", "Documenti", "Firme Digitali", "Solleciti"]
VOCI_MECC = ["Solleciti Officine", "Ticket assistenza"]

# --- 3. FUNZIONI DI RESET ---
def reset_dati():
    db = {}
    for s in ["Carrozzeria", "Meccanica"]:
        db[s] = {}
        voci = VOCI_CARR if s == "Carrozzeria" else VOCI_MECC
        for m in MESI:
            db[s][m] = {}
            for v in voci:
                db[s][m
