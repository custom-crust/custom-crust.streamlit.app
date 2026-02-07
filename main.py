import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

# Try to import GSheets. If missing, show clear error.
try:
    from streamlit_gsheets import GSheetsConnection
except ModuleNotFoundError:
    st.error("🚨 Missing 'st-gsheets-connection'. Please ensure it is in requirements.txt")
    st.stop()

# --- 1. HELPER FUNCTIONS ---
def clean_currency(value):
    """Converts money strings like '$1,200.50' to float 1200.50"""
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
    """Safe data loader. Returns raw lists of dictionaries."""
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        assets = conn.read(worksheet="Assets", ttl=0).to_dict('records')
        expenses = conn.read(worksheet="Expenses", ttl=0).to_dict('records')
        
            # Normalize keys immediately so we don't worry about capitalization later
            clean_assets = normalize_keys(assets)
            clean_expenses = normalize_keys(expenses)
        
        return clean_assets, clean_expenses
    except Exception:
        return [], []

# --- 2. MAIN APPLICATION ---
def main():
    st.set_page_config(page_title="Custom Crust HQ", layout="wide", page_icon="🍕")
    
    # Load Data
    assets, expenses_data = load_data()

    # Sidebar
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

        # Data Processing
        liquid_assets = []
        for a in assets:
            atype = str(a.get('type') or '').strip().lower()
            if atype == 'liquid':
                liquid_assets.append(a)

        # Live Balances
        live_balances = {}
        for asset in liquid_assets:
            name = str(asset.get('account name') or asset.get('name') or 'Unknown').strip()
            val = clean_currency(asset.get('balance') or 0)
            live_balances[name] = val
        
        # Expense Logic & Chart Data
        total_exp = 0.0
        chart_data = [] 
        
        for exp in expenses_data:
            cost = clean_currency(exp.get('cost') or 0)
            category = str(exp.get('category') or 'Uncategorized')
            
            if cost > 0:
                total_exp += cost
                chart_data.append({'Category': category, 'Cost': cost})
                
                method = str(exp.get('payment method') or exp.get('payment_method') or '').strip().lower()
                for asset_name in live_balances:
                    if asset_name.lower() in method:
                        live_balances[asset_name] -= cost

        # Top Metrics
        st.subheader("💰 Cash on Hand (Live)")
        if live_balances:
            cols = st.columns(len(live_balances))
            for idx, (name, val) in enumerate(live_balances.items()):
                cols[idx].metric(label=name, value=f"${val:,.2f}")
        else:
            st.warning("⚠️ No liquid assets found. Check Assets tab.")

        st.divider()

        # Profit & Charts
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
            st.info("No sales data yet.")
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
                pay_options = ["External / Cash"]
                for a in assets:
                    atype = str(a.get('Type') or '').strip().lower()
                    if atype == 'liquid':
                        name = str(a.get('Account Name') or a.get('name') or '').strip()
                        if name:
                            pay_options.append(name)
                payment_method = st.selectbox("Payment Method", pay_options)
                notes = st.text_area("Notes")
            
            submitted = st.form_submit_button("💾 Save Expense")
            if submitted:
                if item_name and cost > 0:
                    st.success(f"✅ Logged: {item_name} (${cost})")
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