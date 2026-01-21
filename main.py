import streamlit as st
import pandas as pd
import plotly.express as px
import gspread
from google.oauth2.service_account import Credentials
import json

# 1. SETUP GOOGLE CONNECTION
def get_gspread_client():
    # Pulls the key from your Replit Secrets
    info = json.loads(st.secrets["GCP_SERVICE_ACCOUNT"])
    scope = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
    creds = Credentials.from_service_account_info(info, scopes=scope)
    return gspread.authorize(creds)

# Connect to your specific sheet
client = get_gspread_client()
sheet = client.open("Custom Crust Kitchen - Master Ledger")
ledger_sheet = sheet.worksheet("Ledger")
menu_sheet = sheet.worksheet("Menu") # Ensure you have a tab named 'Menu'

# 2. BRANDING
st.set_page_config(page_title="Custom Crust Kitchen LLC", layout="wide", page_icon="🍕")
st.title("🍕 Custom Crust Kitchen LLC: Command Center")

# 3. NAVIGATION
menu_choice = st.sidebar.radio("Go To:", ["Dashboard", "Log Expenses", "Sales & Catering", "Menu Management", "Vault"])

# 4. DASHBOARD (LIVE DATA)
if menu_choice == "Dashboard":
    st.header("Financial Overview")
    
    # Fetch data from Google Sheet
    ledger_data = pd.DataFrame(ledger_sheet.get_all_records())
    
    c1, c2, c3 = st.columns(3)
    total_exp = ledger_data["Cost"].sum()
    
    c1.metric("Total Expenses", f"${total_exp:,.2f}")
    c2.metric("Active Assets", "Trailer & Ovens")
    c3.metric("Status", "Operational")

    st.divider()
    
    # The Spending Wheel
    fig_pie = px.pie(ledger_data, values='Cost', names='Category', hole=0.5,
                     title="Expense Distribution (The Wheel)",
                     color_discrete_sequence=px.colors.sequential.RdBu)
    st.plotly_chart(fig_pie, use_container_width=True)

# 5. LOG EXPENSES (SAVES TO GOOGLE)
elif menu_choice == "Log Expenses":
    st.header("Log Business Expenses")
    with st.form("exp_form", clear_on_submit=True):
        col_a, col_b = st.columns(2)
        with col_a:
            name = st.text_input("Item")
            val = st.number_input("Cost ($)", min_value=0.0)
        with col_b:
            cat = st.selectbox("Category", ["Supplies (Food)", "Asset (Trailer)", "Equipment", "Maintenance", "Marketing", "Legal"])
            dt = st.date_input("Date")
        
        if st.form_submit_button("Log to Google Sheet"):
            # This sends the data directly to your spreadsheet row!
            ledger_sheet.append_row([name, cat, val, str(dt)])
            st.success(f"Successfully saved {name} to your Master Ledger!")

# 6. MENU MANAGEMENT (LIVE SYNC)
elif menu_choice == "Menu Management":
    st.header("Menu Management")
    menu_data = pd.DataFrame(menu_sheet.get_all_records())
    
    st.subheader("Edit/Delete Menu Items")
    edited_menu = st.data_editor(menu_data, num_rows="dynamic", use_container_width=True)
    
    if st.button("Save Changes to Google Sheet"):
        # Overwrites the menu tab with your new changes
        menu_sheet.update([edited_menu.columns.values.tolist()] + edited_menu.values.tolist())
        st.success("Menu updated in the cloud!")
