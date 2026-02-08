import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
from streamlit_gsheets import GSheetsConnection

# --- HELPER FUNCTIONS ---
def clean_currency(value):
    """Robust currency cleaner for strings like '$1,200.50'."""
    if pd.isna(value) or value == "":
        return 0.0
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        clean_str = value.replace('$', '').replace(',', '').strip()
        try:
            return float(clean_str) if clean_str else 0.0
        except ValueError:
            return 0.0
    return 0.0

def normalize_keys(data_list):
    """Converts all dictionary keys to lowercase (e.g. 'Account Name' -> 'account name')."""
    normalized = []
    for row in data_list:
        new_row = {k.strip().lower(): v for k, v in row.items()}
        normalized.append(new_row)
    return normalized

def load_data():
    """Loads data and normalizes headers so we don't worry about capitalization."""
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        assets = conn.read(worksheet="Assets", ttl=0).to_dict('records')
        expenses = conn.read(worksheet="Expenses", ttl=0).to_dict('records')
        return normalize_keys(assets), normalize_keys(expenses)
    except Exception:
        # Return empty lists if connection fails
        return [], []

# --- MAIN APPLICATION ---
def main():
    st.set_page_config(page_title="Custom Crust HQ", layout="wide", page_icon="🍕")
    
    # 1. Load Data
    assets, expenses_data = load_data()

    # 2. Sidebar
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

        # Logic: Filter Liquid Assets
        liquid_assets = []
        for a in assets:
            # We look for 'type' because normalize_keys made everything lowercase
            atype = str(a.get('type') or '').strip().lower()
            if atype == 'liquid':
                liquid_assets.append(a)

        # Logic: Calculate Balances
        live_balances = {}
        for asset in liquid_assets:
            name = str(asset.get('account name') or asset.get('name') or 'Unknown').strip()
            val = clean_currency(asset.get('balance') or 0)
            live_balances[name] = val
        
        # Logic: Subtract Expenses
        total_exp = 0.0
        chart_data = [] 
        
        for exp in expenses_data:
            cost = clean_currency(exp.get('cost') or 0)
            category = str(exp.get('category') or 'Uncategorized')
            
            if cost > 0:
                total_exp += cost
                chart_data.append({'Category': category, 'Cost': cost})
                
                # Deduct from Asset if Payment Method matches
                method = str(exp.get('payment method') or exp.get('payment_method') or '').strip().lower()
                for asset_name in live_balances:
                    if asset_name.lower() in method:
                        live_balances[asset_name] -= cost

        # Visuals: Top Metrics
        st.subheader("💰 Cash on Hand (Live)")
        if live_balances:
            cols = st.columns(len(live_balances))
            for idx, (name, val) in enumerate(live_balances.items()):
                cols[idx].metric(label=name, value=f"${val:,.2f}")
        else:
            st.warning("⚠️ No liquid assets found. Check your 'Assets' sheet. Ensure column 'Type' exists and rows are marked 'Liquid'.")

        st.divider()

        # Visuals: Profit & Charts
        total_rev = 0.0 
        net_profit = total_rev - total_exp
        
        m1, m2, m3 = st.columns(3)
        m1.metric("Total Revenue", f"${total_rev:,.2f}")
        m2.metric("Total Expenses", f"${total_exp:,.2f}", delta="-")
        m3.metric("Net Profit", f"${net_profit:,.2f}", delta=f"{net_profit:,.2f}")
        
        st.divider()
        
        c1, c2 = st.columns(2)
        with c1:
            st.caption("Revenue Sources")
            st.info("No sales data recorded yet.")
        with c2:
            st.caption("Expense Breakdown")
            if chart_data:
                df_chart = pd.DataFrame(chart_data)
                fig = px.pie(df_chart, values='Cost', names='Category', hole=0.4)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No expenses logged yet.")

    # --- TAB 5: LOG EXPENSES ---
    elif selected == "📝 Log Expenses":
        st.markdown("## 📝 Log Business Expenses")
        
        with st.form("expense_entry", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                item_name = st.text_input("Item Description")
                cost = st.number_input("Cost ($)", min_value=0.0, format="%.2f")
                category = st.selectbox("Category", [
                    "Startup & Assets", "Inventory", "Equipment", 
                    "Marketing", "Utilities", "Rent", "Labor", "Other"
                ])
            with col2:
                date = st.date_input("Date", datetime.today())
                
                # Dynamic Dropdown (Populates from your Assets sheet)
                pay_options = ["External / Cash"]
                for a in assets:
                    atype = str(a.get('type') or '').strip().lower()
                    if atype == 'liquid':
                        name = str(a.get('account name') or a.get('name') or '').strip()
                        if name:
                            pay_options.append(name)
                            
                payment_method = st.selectbox("Payment Method", pay_options)
                notes = st.text_area("Notes")
            
            submitted = st.form_submit_button("💾 Save Expense")
            if submitted:
                if item_name and cost > 0:
                    st.success(f"✅ Logged: {item_name} (${cost}) via {payment_method}")
                    st.balloons()
                else:
                    st.error("Please enter item and cost.")

    # --- TAB 6: ASSETS ---
    elif selected == "🏦 Assets & Debt":
        st.title("🏦 Assets & Debt")
        if assets:
            st.dataframe(assets)
        else:
            st.info("No assets found in Google Sheet.")

    # --- OTHER TABS ---
    else:
        st.title(selected)
        st.info("🚧 Module coming soon...")

if __name__ == "__main__":
    main()
    