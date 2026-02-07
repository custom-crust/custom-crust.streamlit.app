import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import plotly.express as px
from datetime import datetime

if __name__ == "__main__":
    main()
# --- HELPER FUNCTIONS (Flush Left) ---
def clean_currency(value):
    """Converts string currency (e.g. '$1,200.50') into a float."""
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        clean_str = value.replace('$', '').replace(',', '').strip()
        try:
            return float(clean_str) if clean_str else 0.0
        except ValueError:
            return 0.0
    return 0.0

def load_data():
    """Safe data loader outside of main loop"""
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        assets = conn.read(worksheet="Assets", ttl=0).to_dict('records')
        expenses = conn.read(worksheet="Expenses", ttl=0).to_dict('records')
        return assets, expenses
    except Exception as e:
        # Return empty lists if connection fails so app doesn't crash
        return [], []

# --- SIDEBAR NAVIGATION ---
    st.sidebar.title("Navigation")
    options = [
        "📊 Dashboard", 
        "📅 Planner & Projections", 
        "🧾 Invoice Generator", 
        "💰 Sales & Revenue", 
        "📝 Log Expenses", 
        "🏦 Assets & Debt", 
        "🤝 Vendor Network", 
        "🍕 Menu Editor", 
        "🍳 Recipe Costing", 
        "🗄️ Document Vault"
    ]
    selected = st.sidebar.radio("Go to", options)

    # --- TAB 1: DASHBOARD ---
    if selected == "📊 Dashboard":
        st.markdown("## 🚀 Business Command Center")

        # 1. Get Data (Safe Local Retrieval)
        safe_assets = locals().get('assets', []) or []
        safe_expenses = locals().get('expenses_data', []) or []

        # 2. Filter Liquid Assets
        liquid_assets = []
        for a in safe_assets:
            atype = str(a.get('Type') or a.get('type') or '').strip().lower()
            if atype == 'liquid':
                liquid_assets.append(a)

        # 3. Calculate Live Balances
        live_balances = {}
        # Load Start Balances
        for asset in liquid_assets:
            name = str(asset.get('Account Name') or asset.get('name') or 'Unknown').strip()
            raw_val = str(asset.get('Balance') or asset.get('balance') or '0').replace('$', '').replace(',', '')
            try:
                live_balances[name] = float(raw_val)
            except:
                live_balances[name] = 0.0

        # Subtract Expenses
        for exp in safe_expenses:
            method = str(exp.get('Payment Method') or exp.get('payment_method') or '').strip().lower()
            cost_raw = str(exp.get('Cost') or exp.get('cost') or '0').replace('$', '').replace(',', '')
            try:
                cost = float(cost_raw)
            except:
                cost = 0.0
            
            for asset_name in live_balances:
                if asset_name.lower() in method:
                    live_balances[asset_name] -= cost

        # 4. Render Cards
        st.subheader("💰 Cash on Hand")
        if live_balances:
            cols = st.columns(len(live_balances))
            for idx, (name, val) in enumerate(live_balances.items()):
                cols[idx].metric(label=name, value=f"${val:,.2f}")
        else:
            st.info("No liquid assets found. Check Assets tab.")
        
        st.divider()

    # --- TAB 2: PLANNER ---
    elif selected == "📅 Planner & Projections":
        st.title("📅 Planner & Projections")
        st.info("Planner module coming soon...")

    # --- TAB 3: INVOICE GENERATOR ---
    elif selected == "🧾 Invoice Generator":
        st.title("🧾 Invoice Generator")
        st.info("Invoice module coming soon...")

    # --- TAB 4: SALES & REVENUE ---
    elif selected == "💰 Sales & Revenue":
        st.title("💰 Sales & Revenue")
        st.info("Sales module coming soon...")

    # --- TAB 5: LOG EXPENSES ---
    elif selected == "📝 Log Expenses":
        st.title("📝 Log Business Expenses")
        st.info("Use the form below to add expenses (logic moved to separate block).")

    # --- TAB 6: ASSETS & DEBT ---
    elif selected == "🏦 Assets & Debt":
        st.title("🏦 Assets & Liability Tracker")
        if 'assets' in locals():
            st.dataframe(assets)
        else:
            st.info("Assets data not loaded.")

    # --- TAB 7: VENDOR NETWORK ---
    elif selected == "🤝 Vendor Network":
        st.title("🤝 Vendor Network")
        st.info("Vendor module coming soon...")

    # --- TAB 8: MENU EDITOR ---
    elif selected == "🍕 Menu Editor":
        st.title("🍕 Menu Editor")
        st.info("Menu module coming soon...")

    # --- TAB 9: RECIPE COSTING ---
    elif selected == "🍳 Recipe Costing":
        st.title("🍳 Recipe Costing")
        st.info("Recipe module coming soon...")

    # --- TAB 10: DOCUMENT VAULT ---
    elif selected == "🗄️ Document Vault":
        st.title("🗄️ Document Vault")
        st.info("Vault module coming soon...")
