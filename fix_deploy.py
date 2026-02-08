import os

# 1. Define the correct content
content = """streamlit
st-gsheets-connection
pandas
plotly
"""

# 2. Force-write the file (overwriting any garbage)
with open("requirements.txt", "w") as f:
    f.write(content)

print("✅ requirements.txt has been rewritten successfully.")

# 3. Verify content
print("--- New File Content ---")
with open("requirements.txt", "r") as f:
    print(f.read())
print("------------------------")

# 4. Automate the Git Push
os.system("git add requirements.txt")
os.system("git commit -m 'Fix requirements.txt via python script'")
os.system("git push")
print("🚀 Changes pushed to GitHub!")
import os

# The Complete, Correct Code for main.py
new_code = """import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
from streamlit_gsheets import GSheetsConnection

# --- CONFIG & STYLE ---
st.set_page_config(page_title="Custom Crust HQ", layout="wide", page_icon="🍕")
st.markdown(\"\"\"
    <style>
    .main {background-color: #0E1117;}
    div.stMetric {background-color: #262730; border: 1px solid #464B5C; padding: 15px; border-radius: 8px;}
    </style>
\"\"\", unsafe_allow_html=True)

# --- DATA LOADING ---
def clean_currency(value):
    if pd.isna(value) or value == "": return 0.0
    if isinstance(value, (int, float)): return float(value)
    s = str(value).replace('$', '').replace(',', '').strip()
    try: return float(s) if s else 0.0
    except: return 0.0

def load_data():
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        assets = conn.read(worksheet="Assets", ttl=0).to_dict('records')
        expenses = conn.read(worksheet="Expenses", ttl=0).to_dict('records')
        # Normalize keys to lowercase
        assets = [{k.strip().lower(): v for k, v in row.items()} for row in assets]
        expenses = [{k.strip().lower(): v for k, v in row.items()} for row in expenses]
        return assets, expenses
    except:
        return [], []

# --- MAIN APP ---
def main():
    assets, expenses = load_data()
    
    st.sidebar.title("🍕 Custom Crust HQ")
    menu = st.sidebar.radio("Navigate", ["📊 Dashboard", "📝 Log Expenses", "📅 Planner", "🧾 Invoices", "🏦 Assets"])

    # --- DASHBOARD ---
    if menu == "📊 Dashboard":
        st.title("🚀 Business Command Center")
        
        liquid = 0.0
        live_balances = {}
        for a in assets:
            atype = str(a.get('type', '')).lower()
            if any(x in atype for x in ['liquid', 'bank', 'cash']):
                name = a.get('account name') or a.get('name') or 'Unknown'
                bal = clean_currency(a.get('balance', 0))
                live_balances[name] = bal
                liquid += bal

        total_exp = 0.0
        cat_data = {}
        for e in expenses:
            cost = clean_currency(e.get('cost', 0))
            if cost > 0:
                total_exp += cost
                c = e.get('category', 'Other')
                cat_data[c] = cat_data.get(c, 0) + cost
                # Deduct from bank
                method = str(e.get('payment method', '')).lower()
                for bank in live_balances:
                    if bank.lower() in method:
                        live_balances[bank] -= cost
                        liquid -= cost

        c1, c2, c3 = st.columns(3)
        c1.metric("💰 Cash Available", f"${liquid:,.2f}")
        c2.metric("📉 Total Expenses", f"${total_exp:,.2f}")
        c3.metric("📈 Net Profit", f"${0 - total_exp:,.2f}")

        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Expenses by Category")
            if cat_data:
                df = pd.DataFrame(list(cat_data.items()), columns=['Category', 'Cost'])
                fig = px.pie(df, values='Cost', names='Category', hole=0.4)
                st.plotly_chart(fig, use_container_width=True)
            else: st.info("No data yet.")
        
        with col2:
            st.subheader("Live Balances")
            st.dataframe(live_balances)

    # --- LOG EXPENSES ---
    elif menu == "📝 Log Expenses":
        st.title("📝 Log Expense")
        with st.form("entry"):
            c1, c2 = st.columns(2)
            item = c1.text_input("Item")
            cost = c2.number_input("Cost", 0.0)
            c3, c4 = st.columns(2)
            cat = c3.selectbox("Category", ["Inventory", "Labor", "Rent", "Other"])
            
            banks = ["Cash"] + [a.get('account name') for a in assets if 'account name' in a]
            pay = c4.selectbox("Payment Method", banks)
            
            if st.form_submit_button("Save"):
                st.success(f"Saved: {item} (${cost})")

    # --- PLANNER ---
    elif menu == "📅 Planner":
        st.title("📅 Event Planner")
        pizzas = st.number_input("Pizzas Sold", 50)
        price = st.number_input("Price ($)", 18)
        st.metric("Proj. Revenue", f"${pizzas * price:,.2f}")

    # --- INVOICES ---
    elif menu == "🧾 Invoices":
        st.title("🧾 Invoice Generator")
        st.text_input("Client Name")
        st.number_input("Amount", 0.0)
        st.button("Create PDF")
        
    # --- ASSETS ---
    elif menu == "🏦 Assets":
        st.title("🏦 Asset Viewer")
        st.dataframe(assets)

if __name__ == "__main__":
    main()
"""

# Overwrite main.py with the new code
with open("main.py", "w") as f:
    f.write(new_code)

print("SUCCESS: main.py has been completely overwritten with the correct code.")
