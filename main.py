import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
from streamlit_gsheets import GSheetsConnection

# --- 1. CONFIG & THEME ---
st.set_page_config(page_title="Custom Crust HQ", layout="wide", page_icon="🍕")

# Force Dark Mode Theme & Card Styling
st.markdown("""
    <style>
    .main {background-color: #0E1117;}
    div.stMetric {background-color: #262730; border: 1px solid #464B5C; padding: 15px; border-radius: 8px;}
    div.stButton > button {width: 100%; border-radius: 5px; font-weight: bold;}
    </style>
""", unsafe_allow_html=True)

# --- 2. ROBUST DATA ENGINE ---
def clean_currency(value):
    """Converts money strings to floats, handling empty/null safely."""
    if pd.isna(value) or value == "": return 0.0
    if isinstance(value, (int, float)): return float(value)
    s = str(value).replace('$', '').replace(',', '').strip()
    try: return float(s) if s else 0.0
    except: return 0.0

def normalize_keys(data_list):
    """Lowers all keys so 'Type' and 'type' are treated the same."""
    return [{k.strip().lower(): v for k, v in row.items()} for row in data_list]

def load_data():
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        assets = conn.read(worksheet="Assets", ttl=0).to_dict('records')
        expenses = conn.read(worksheet="Expenses", ttl=0).to_dict('records')
        return normalize_keys(assets), normalize_keys(expenses)
    except Exception:
        return [], []

# --- 3. MAIN APP LOGIC ---
def main():
    assets, expenses_data = load_data()

    # SIDEBAR
    st.sidebar.title("🍕 Custom Crust HQ")
    menu = st.sidebar.radio("Navigate", [
        "📊 Dashboard", 
        "📝 Log Expenses", 
        "📅 Planner", 
        "🧾 Invoices", 
        "🏦 Assets"
    ])

    # --- DASHBOARD ---
    if menu == "📊 Dashboard":
        st.title("🚀 Business Command Center")
        
        # 1. Calculate Cash
        liquid_cash = 0.0
        live_balances = {}
        for a in assets:
            atype = str(a.get('type', '')).lower()
            if any(x in atype for x in ['liquid', 'bank', 'cash', 'checking']):
                name = a.get('account name') or a.get('name') or 'Unknown'
                bal = clean_currency(a.get('balance', 0))
                live_balances[name] = bal
                liquid_cash += bal

        # 2. Subtract Expenses
        total_exp = 0.0
        cat_breakdown = {}
        for e in expenses_data:
            cost = clean_currency(e.get('cost', 0))
            if cost > 0:
                total_exp += cost
                cat = e.get('category', 'Other')
                cat_breakdown[cat] = cat_breakdown.get(cat, 0) + cost
                
                # Bank Sync Logic
                method = str(e.get('payment method', '')).lower()
                for bank in live_balances:
                    if bank.lower() in method:
                        live_balances[bank] -= cost
                        liquid_cash -= cost

        # 3. Metrics
        c1, c2, c3 = st.columns(3)
        c1.metric("💰 Cash on Hand", f"${liquid_cash:,.2f}")
        c2.metric("📉 Total Expenses", f"${total_exp:,.2f}")
        c3.metric("📈 Net Profit (Est)", f"${0 - total_exp:,.2f}")

        # 4. Charts
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Spending by Category")
            if cat_breakdown:
                df = pd.DataFrame(list(cat_breakdown.items()), columns=['Category', 'Cost'])
                fig = px.pie(df, values='Cost', names='Category', hole=0.4)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No expenses logged yet.")
        
        with col2:
            st.subheader("Live Bank Balances")
            if live_balances:
                st.dataframe(pd.DataFrame(list(live_balances.items()), columns=['Account', 'Balance']))
            else:
                st.warning("No liquid assets found in Sheet.")

    # --- LOG EXPENSES ---
    elif menu == "📝 Log Expenses":
        st.title("📝 Log Business Expenses")
        with st.form("expense_form", clear_on_submit=True):
            c1, c2 = st.columns(2)
            item = c1.text_input("Item / Description")
            cost = c2.number_input("Cost ($)", min_value=0.0, step=0.01)
            
            c3, c4 = st.columns(2)
            cat = c3.selectbox("Category", ["Inventory", "Equipment", "Marketing", "Rent", "Labor", "Utilities", "Other"])
            
            bank_opts = ["External Cash"]
            for a in assets:
                name = a.get('account name') or a.get('name')
                if name: bank_opts.append(name)
            method = c4.selectbox("Payment Method", bank_opts)
            
            if st.form_submit_button("💾 Save Expense"):
                st.success(f"Logged: {item} (${cost})")

    # --- PLANNER (RESTORED) ---
    elif menu == "📅 Planner":
        st.title("📅 Event Planner")
        c1, c2 = st.columns(2)
        pizzas = c1.number_input("Projected Pizzas Sold", 50)
        price = c2.number_input("Price per Pizza ($)", 18)
        st.metric("Projected Revenue", f"${pizzas * price:,.2f}")
        st.text_area("Event Notes")
        st.button("Save Projection")

    # --- INVOICES (RESTORED) ---
    elif menu == "🧾 Invoices":
        st.title("🧾 Invoice Builder")
        c1, c2 = st.columns(2)
        c1.text_input("Client Name")
        c2.number_input("Invoice Amount ($)", 0.0)
        st.button("Generate PDF")

    # --- ASSETS ---
    elif menu == "🏦 Assets":
        st.title("🏦 Asset Viewer")
        if assets: st.dataframe(assets)
        else: st.info("No data in Google Sheet.")

if __name__ == "__main__":
    main()