import streamlit as st
import pandas as pd
import math
import os
import datetime
from fpdf import FPDF
import arrow

# --- 1. CONFIGURATION & SECURITY ---
st.set_page_config(page_title="CCK Command Center", layout="wide", page_icon="🍕")
ACCESS_PIN = "CCK2026!"
SHEET_ID = "1yqbd35J140KWT7ui8Ggqn68_OfGXb1wofViJRcSgZBU"
CSV_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=Vault_Index"

# --- 2. LUXURY CSS ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@300;400;600&family=Playfair+Display:ital,wght@0,400;0,600;1,400&display=swap');
    .stApp { background-color: #121212; font-family: 'Montserrat', sans-serif; color: #f5f5f5; }
    section[data-testid="stSidebar"] {display: none !important;}
    h1, h2, h3 {font-family: 'Playfair Display', serif; color: #c5a059;}
    .quick-links-container { display: flex; justify-content: center; gap: 30px; margin-bottom: 30px; flex-wrap: wrap; }
    .quote-box { background-color: #1a1a1a; border: 1px solid #c5a059; border-radius: 8px; padding: 20px; }
    .doc-card { background: #1a1a1a; border: 1px solid #333; padding: 20px; border-radius: 8px; color: #fff; text-decoration: none; display: block; margin-bottom: 10px; }
    </style>
""", unsafe_allow_html=True)

# --- 3. SECURITY GATE ---
if "authenticated" not in st.session_state: st.session_state.authenticated = False
if not st.session_state.authenticated:
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        pin = st.text_input("Enter PIN", type="password")
        if st.button("Unlock"):
            if pin == ACCESS_PIN: st.session_state.authenticated = True; st.rerun()
            else: st.error("Access Denied.")
    st.stop()

# --- 4. DATA ENGINE ---
@st.cache_data(ttl=600)
def load_data():
    try:
        df = pd.read_csv(CSV_URL).dropna(how='all', axis=0).dropna(how='all', axis=1)
        return df
    except: return pd.DataFrame()

# --- 5. MAIN APP ---
def main():
    vault_df = load_data()
    # Basic data setup for the rest of your app
    menu_prices = {"The Plain Jane": 17.00, "The Premium Pepperoni": 23.00, "The Carnivore": 26.00}
    
    tabs = st.tabs(["📅 Calendar", "🎫 Event Quoter", "🍕 Pizza Builder", "🗄️ The Vault"])
    
    with tabs[0]:
        st.subheader("Calendar System")
        st.write("Active.")
    
    with tabs[1]:
        st.subheader("Event Quoter")
        c1, c2 = st.columns(2)
        client = c1.text_input("Client Name")
        adults = c2.number_input("Adults", value=40)
        st.write(f"Estimating for {client if client else 'Guest'}...")
        
    with tabs[2]:
        st.subheader("Pizza Builder")
        base = st.selectbox("Crust", ["10\" Dough Ball", "12\" Dough Ball", "14\" Dough Ball"])
        
    with tabs[3]:
        st.subheader("The Vault")
        if not vault_df.empty:
            for _, row in vault_df.iterrows():
                name = row.get('document name', 'Document')
                link = row.get('link', '#')
                st.markdown(f'<a href="{link}" class="doc-card">{name}</a>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()
