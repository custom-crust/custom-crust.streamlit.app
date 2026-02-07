import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import plotly.express as px
from datetime import datetime

# --- 1. HELPER FUNCTIONS ---
def load_data():
    """Safe data loader that won't crash the app if sheets are empty."""
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        assets = conn.read(worksheet="Assets", ttl=0).to_dict('records')
        expenses = conn.read(worksheet="Expenses", ttl=0).to_dict('records')
        return assets, expenses
    except Exception as e:
        return [], []

def clean_currency(value):
    """Converts money strings like '$1,200.50' to float 1200.50"""
    if isinstance(value, (int, float)):
        return float(value)
    return float(str(value).replace('$', '').replace(',', '').strip() or 0)

# --- 2. MAIN APPLICATION ---
def main():
    st.set_page_config(page_title="Custom Crust HQ", layout="wide", page_icon="🍕")
    
    # Load Data Immediately
    assets, expenses_data = load_data()
    
    # Process Liquid Assets (Safe Logic)
    liquid_assets = []
    if assets:
        for a in assets:
            # Check for 'Type', 'type', 'Classification' safely
            atype = str(a.get('Type') or a.get('type') or '').strip().lower()
            if atype == 'liquid':
                liquid_assets.append(a)

    # --- SIDEBAR ---
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

    if selected == "📊 Dashboard":
        st.markdown("## 🚀 Business Command Center")

        # --- A. ROBUST DATA FILTERING ---
        # 1. Clean Column Names (Strip spaces from keys)
        safe_assets = []
        if 'assets' in locals() and assets:
            for a in assets:
                # Create a new dict with stripped keys
                clean_a = {k.strip(): v for k, v in a.items()}
                safe_assets.append(clean_a)
        
        safe_expenses = []
        if 'expenses_data' in locals() and expenses_data:
            for e in expenses_data:
                clean_e = {k.strip(): v for k, v in e.items()}
                safe_expenses.append(clean_e)

        # 2. Filter Liquid Assets
        liquid_assets = []
        for a in safe_assets:
            # Check 'Type' case-insensitive
            atype = str(a.get('Type') or a.get('type') or '').strip().lower()
            if atype == 'liquid':
                liquid_assets.append(a)

        # 3. Calculate Live Balances
        live_balances = {}
        for asset in liquid_assets:
            name = str(asset.get('Account Name') or asset.get('name') or 'Unknown')
            val = clean_currency(asset.get('Balance') or asset.get('balance') or 0)
            live_balances[name] = val

        # 4. Subtract Expenses
        total_exp = 0.0
        if safe_expenses:
            for exp in safe_expenses:
                cost = clean_currency(exp.get('Cost') or exp.get('cost') or 0)
                total_exp += cost
                
                # Payment Method Matching
                method = str(exp.get('Payment Method') or exp.get('payment_method') or '').strip().lower()
                for asset_name in live_balances:
                    if asset_name.lower() in method:
                        live_balances[asset_name] -= cost

        # --- B. VISUALS & METRICS ---
        st.subheader("💰 Cash on Hand (Live)")
        if live_balances:
            cols = st.columns(len(live_balances))
            for idx, (name, val) in enumerate(live_balances.items()):
                cols[idx].metric(label=name, value=f"${val:,.2f}")
        else:
            st.warning("⚠️ No liquid assets found. Check if your Google Sheet has a column named 'Type' set to 'Liquid'.")

        st.divider()

        # Profit Metrics
        total_rev = 0.0 # Placeholder for Revenue logic
        net_profit = total_rev - total_exp
        
        m1, m2, m3 = st.columns(3)
        m1.metric("Total Revenue", f"${total_rev:,.2f}")
        m2.metric("Total Expenses", f"${total_exp:,.2f}", delta="-")
        m3.metric("Net Profit", f"${net_profit:,.2f}", delta=f"{net_profit:,.2f}")

        st.divider()

        # --- C. CHARTS ---
        c1, c2 = st.columns(2)
        with c1:
            st.caption("Revenue Sources")
            st.info("No sales data recorded yet.")
            
        with c2:
            st.caption("Expense Breakdown")
            if safe_expenses:
                # Prepare data for Pie Chart
                chart_data = []
                for e in safe_expenses:
                    cat = e.get('Category') or 'Uncategorized'
                    amt = clean_currency(e.get('Cost') or 0)
                    if amt > 0:
                        chart_data.append({'Category': cat, 'Cost': amt})
                
                if chart_data:
                    df_chart = pd.DataFrame(chart_data)
                    fig = px.pie(df_chart, values='Cost', names='Category', hole=0.4)
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("No expenses > $0 to chart.")
            else:
                st.info("No expenses logged yet.")

    # --- TAB 2: PLANNER ---
    elif selected == "📅 Planner & Projections":
        st.title("📅 Planner & Projections")
        st.info("Coming soon...")

    # --- TAB 3: INVOICE GENERATOR ---
    elif selected == "🧾 Invoice Generator":
        st.title("🧾 Invoice Generator")
        st.info("Coming soon...")

    # --- TAB 4: SALES ---
    elif selected == "💰 Sales & Revenue":
        st.title("💰 Sales & Revenue")
        st.info("Coming soon...")

    elif selected == "📝 Log Expenses":
        st.markdown("## 📝 Log Business Expenses")
        
        # Form Container
        with st.form("expense_entry_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            
            with col1:
                item_name = st.text_input("Item / Description")
                cost = st.number_input("Cost ($)", min_value=0.0, format="%.2f")
                category = st.selectbox("Category", [
                    "Startup & Assets", "Inventory", "Equipment", 
                    "Marketing", "Utilities", "Rent", "Labor", "Other"
                ])
                
            with col2:
                date = st.date_input("Date", datetime.today())
                
                # Dynamic Payment Method (Links to Assets)
                # We rebuild the safe asset list locally to ensure dropdown works
                pay_options = ["External / Cash"]
                if 'assets' in locals() and assets:
                    for a in assets:
                        aname = str(a.get('Account Name') or a.get('name') or '').strip()
                        atype = str(a.get('Type') or '').strip().lower()
                        if aname and atype == 'liquid':
                            pay_options.append(aname)
                            
                payment_method = st.selectbox("Payment Method", pay_options)
                notes = st.text_area("Notes (Optional)")

            submitted = st.form_submit_button("💾 Save Expense")
            
            if submitted:
                if item_name and cost > 0:
                    # In a full app, we would write this back to Google Sheets here.
                    # For now, we show a success message to confirm UI works.
                    st.success(f"✅ Logged: {item_name} (${cost}) via {payment_method}")
                    st.balloons()
                else:
                    st.error("⚠️ Please enter an Item Name and Cost.")

    # --- TAB 6: ASSETS ---
    elif selected == "🏦 Assets & Debt":
        st.title("🏦 Assets")
        if assets:
            st.dataframe(assets)
        else:
            st.warning("No assets data found.")

    # --- OTHER TABS (Placeholders) ---
    else:
        st.title(selected)
        st.info("Module under construction.")

# --- 3. EXECUTION TRIGGER (CRITICAL) ---
if __name__ == "__main__":
    main()
# --- END OF COMPLETE MAIN.PY ---
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
