# FORCE UPDATE: V5.0 (Nuclear Reset)
import streamlit as st
import pandas as pd
import plotly.express as px
import gspread
from google.oauth2.service_account import Credentials

# --- 1. SETUP PAGE CONFIGURATION ---
st.set_page_config(page_title="Custom Crust HQ", page_icon="🍕", layout="wide")


# --- 2. CONNECT TO GOOGLE SHEETS (Smart Auth) ---
@st.cache_resource
def connect_to_gsheets():
    scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    
    # Try to find the secret key (UPPERCASE matching user screenshot)
    if "GCP_SERVICE_ACCOUNT" in st.secrets:
        creds_dict = st.secrets["GCP_SERVICE_ACCOUNT"]
    elif "gcp_service_account" in st.secrets:
        creds_dict = st.secrets["gcp_service_account"]
    elif "gsheets" in st.secrets:
        creds_dict = st.secrets["gsheets"]
    else:
        st.error("🚨 Secrets Error: Could not find 'GCP_SERVICE_ACCOUNT' in your secrets.")
        st.stop()
    
    # Create Credentials
    creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
    client = gspread.authorize(creds)
    
    # Open the sheet
    try:
        sheet = client.open("Custom Crust Kitchen - Master Ledger")
        return sheet
    except Exception as e:
        st.error(f"🚨 Sheet Error: Could not open 'Custom Crust Kitchen - Master Ledger'. Check permissions. {e}")
        st.stop()

try:
    sheet = connect_to_gsheets()
except Exception as e:
    st.error(f"🚨 Connection Error: {e}")
    st.stop()

# Helper: Get Worksheet or Create if Missing
def get_worksheet(name, headers):
    try:
        return sheet.worksheet(name)
    except:
        # If tab missing, create it
        ws = sheet.add_worksheet(title=name, rows=100, cols=20)
        ws.append_row(headers)
        return ws

# Load Your Tabs
ledger_sheet = get_worksheet("Ledger", ["Item", "Category", "Cost", "Date"])
sales_sheet = get_worksheet("Sales", ["Event", "Type", "Revenue", "Date"])
assets_sheet = get_worksheet("Assets", ["Account Name", "Type", "Balance", "Last Updated"])
debt_sheet = get_worksheet("Debt_Log", ["Loan Name", "Transaction Type", "Amount", "Date"])
ing_sheet = get_worksheet("Ingredients", ["Item Name", "Bulk Unit (e.g. 50lb)", "Bulk Cost", "Unit Cost"])
menu_sheet = get_worksheet("Menu", ["Item Name", "Description", "Price", "Category"])
vault_sheet = get_worksheet("Vault_Index", ["Document Name", "Type", "Link", "Date"])

# --- 3. CUSTOM CSS ---
st.markdown("""
<style>
    /* 1. Main Background: Dark Mesh Texture */
    .stApp {
        background-color: #0e0e0e;
        background-image: radial-gradient(#262626 1px, transparent 0);
        background-size: 20px 20px;
    }
    
    /* 2. Sidebar: Matching Texture + Right Border */
    [data-testid="stSidebar"] {
        background-color: #0e0e0e;
        background-image: radial-gradient(#262626 1px, transparent 0);
        background-size: 20px 20px;
        border-right: 2px solid #333;
        padding-top: 20px;
    }
    
    /* 3. Sidebar Navigation "Cards" */
    [data-testid="stSidebar"] div[role="radiogroup"] {
        display: flex;
        flex-direction: column;
        gap: 8px; /* Gap between buttons */
    }
    
    [data-testid="stSidebar"] label[data-baseweb="radio"] {
        background: linear-gradient(145deg, #1e1e1e, #141414); /* Gradient Card */
        border: 1px solid #333;       /* Subtle Border */
        border-radius: 10px;          /* Rounded Corners */
        padding: 12px 15px;           /* Inner Spacing */
        width: 100%;
        margin-bottom: 0px !important;
        transition: all 0.2s ease-in-out;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.3); /* Drop Shadow */
    }
    
    /* Hover Effect: Slide Right & Red Border */
    [data-testid="stSidebar"] label[data-baseweb="radio"]:hover {
        border-color: #FF4B4B;        
        transform: translateX(5px);   
        box-shadow: 4px 4px 8px rgba(0,0,0,0.5);
    }

    /* 4. Dashboard Metric Cards (The Boxes at the Top) */
    [data-testid="stMetric"] {
        background-color: #161616;
        border: 1px solid #333;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0px 4px 10px rgba(0,0,0,0.4);
    }
    
    /* Metric Label (Small Text) */
    [data-testid="stMetricLabel"] {
        color: #888 !important;
        font-size: 14px;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    
    /* Metric Value (Big Number) */
    [data-testid="stMetricValue"] {
        font-family: 'Roboto', sans-serif;
        font-weight: 700;
        color: #E0E0E0 !important;
    }

    /* 5. Thicker Dividers */
    hr {
        border: 0;
        height: 3px; /* Thicker line */
        background: #333;
        margin-top: 30px;
        margin-bottom: 30px;
        border-radius: 2px;
    }

    /* 6. General Text & Headers */
    h1, h2, h3, p, div, span {
        color: #E0E0E0 !important;
    }
    
    /* 7. 'Command Center' Label Styling */
    .st-emotion-cache-16idsys p {
        font-size: 11px;
        text-transform: uppercase;
        color: #666 !important;
        letter-spacing: 2px;
        font-weight: 700;
        margin-left: 5px;
        margin-bottom: 10px;
    }
</style>
""", unsafe_allow_html=True)

# --- 4. GLOBAL HELPER FUNCTIONS ---
def clean_money(val):
    """Converts '$17,000.00' string to 17000.0 float"""
    if isinstance(val, (int, float)): return float(val)
    if isinstance(val, str):
        clean = val.replace('$', '').replace(',', '').strip()
        if not clean: return 0.0
        try: return float(clean)
        except: return 0.0
    return 0.0

def get_df_robust(sheet_obj):
    """Loads sheet data safely, fixing headers"""
    try:
        data = sheet_obj.get_all_values()
        if len(data) < 2: return pd.DataFrame()
        # Clean headers: Title Case and Strip Whitespace
        headers = [str(h).strip().title() for h in data[0]]
        return pd.DataFrame(data[1:], columns=headers)
    except:
        return pd.DataFrame()

# --- 5. SIDEBAR NAVIGATION ---
st.sidebar.title("🍕 Custom Crust HQ")
st.sidebar.markdown("---")
st.sidebar.markdown("COMMAND CENTER")
menu_choice = st.sidebar.radio("Navigation",["📊 Dashboard", "🏦 Assets & Debt", "🍳 Recipe Costing", "📝 Log Expenses", "💰 Sales & Revenue", "🍕 Menu Editor", "🗄️ Document Vault"], label_visibility="collapsed")
st.sidebar.markdown("---")

# --- 6. PAGE LOGIC ---

# 📊 DASHBOARD
if menu_choice == "📊 Dashboard":
    st.header("Business Health Overview")
    # Load Data
    df_exp = get_df_robust(ledger_sheet)
    df_sales = get_df_robust(sales_sheet)
    df_assets = get_df_robust(assets_sheet)
    df_debt = get_df_robust(debt_sheet)
    # Calculate Expenses
    total_exp = 0.0
    if not df_exp.empty and "Cost" in df_exp.columns:
        df_exp["Clean_Cost"] = df_exp["Cost"].apply(clean_money)
        total_exp = df_exp["Clean_Cost"].sum()
    # Calculate Sales
    total_rev = 0.0
    if not df_sales.empty and "Revenue" in df_sales.columns:
        df_sales["Clean_Rev"] = df_sales["Revenue"].apply(clean_money)
        total_rev = df_sales["Clean_Rev"].sum()
    # Calculate Assets
    total_assets = 0.0
    if not df_assets.empty and "Balance" in df_assets.columns:
        df_assets["Clean_Bal"] = df_assets["Balance"].apply(clean_money)
        total_assets = df_assets["Clean_Bal"].sum()
    # Calculate Debt (Fuzzy Match Borrow/Repay)
    total_debt = 0.0
    if not df_debt.empty and "Amount" in df_debt.columns:
        df_debt["Clean_Amt"] = df_debt["Amount"].apply(clean_money)
        # Find Type Column
        type_col = next((c for c in df_debt.columns if "Type" in c), None)
        if type_col:
            df_debt["Norm_Type"] = df_debt[type_col].astype(str).str.lower()
            borrowed = df_debt[df_debt["Norm_Type"].str.contains("borrow")]["Clean_Amt"].sum()
            repaid = df_debt[df_debt["Norm_Type"].str.contains("repay")]["Clean_Amt"].sum()
            total_debt = borrowed - repaid
    # Metrics
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Sales", f"${total_rev:,.0f}")
    c2.metric("Total Expenses", f"${total_exp:,.0f}")
    c3.metric("Net Profit", f"${total_rev - total_exp:,.0f}", delta=total_rev - total_exp)
    net_worth = total_assets - total_debt
    c4.metric("Business Equity", f"${net_worth:,.0f}", delta=f"Debt: ${total_debt:,.0f}", delta_color="off")
    st.divider()
    # Charts
    col_charts1, col_charts2 = st.columns(2)
    with col_charts1:
        st.subheader("💸 Spending Breakdown")
        if total_exp > 0 and "Category" in df_exp.columns:
            fig_exp = px.pie(df_exp, values="Clean_Cost", names="Category", hole=0.4)
            st.plotly_chart(fig_exp, use_container_width=True)
        else:
            st.info("No expenses logged.")
    with col_charts2:
        st.subheader("⚖️ Assets vs Debt")
        if total_assets > 0 or total_debt > 0:
            ad_data = pd.DataFrame({
                "Type": ["Assets (Trailers/Ovens)", "Outstanding Debt"],
                "Value": [total_assets, total_debt]
            })
            fig_net = px.bar(ad_data, x="Type", y="Value", color="Type", 
                             color_discrete_map={"Outstanding Debt":"#FF4B4B", "Assets (Trailers/Ovens)":"#00CC96"})
            st.plotly_chart(fig_net, use_container_width=True)
        else:
            st.info("No assets or debt logged.")

# 🏦 ASSETS & DEBT MANAGER
elif menu_choice == "🏦 Assets & Debt":
    st.header("Assets & Liability Tracker")
    tab_debt, tab_assets = st.tabs(["📉 Manage Debt", "💵 Manage Assets"])
    # DEBT TAB
    with tab_debt:
        st.subheader("Loan Repayment Tracker")
        with st.form("debt_form", clear_on_submit=True):
            c1, c2 = st.columns(2)
            loan_name = c1.text_input("Creditor Name", value="Business Loan")
            trans_type = c2.selectbox("Action", ["Repayment", "Borrow"])
            amount = st.number_input("Amount ($)", min_value=0.01)
            date = st.date_input("Date")
            if st.form_submit_button("Update Loan Balance"):
                debt_sheet.append_row([loan_name, trans_type, amount, str(date)])
                st.success("Transaction Logged!")
                st.rerun()
        # Show Debt Cards
        try:
            debts = get_df_robust(debt_sheet)
            if not debts.empty and "Amount" in debts.columns:
                debts['Clean_Amt'] = debts['Amount'].apply(clean_money)
                for loan in debts['Loan Name'].unique():
                    subset = debts[debts['Loan Name'] == loan]
                    # Find type col
                    t_col = next((c for c in subset.columns if "Type" in c), None)
                    if t_col:
                        subset['Norm_Type'] = subset[t_col].astype(str).str.lower()
                        borrowed = subset[subset['Norm_Type'].str.contains('borrow')]['Clean_Amt'].sum()
                        repaid = subset[subset['Norm_Type'].str.contains('repay')]['Clean_Amt'].sum()
                        balance = borrowed - repaid
                        st.divider()
                        st.write(f"**{loan}**")
                        k1, k2, k3 = st.columns(3)
                        k1.metric("Original Loan", f"${borrowed:,.0f}")
                        k2.metric("Paid Off", f"${repaid:,.0f}")
                        k3.metric("Remaining Balance", f"${balance:,.0f}", delta=-balance)
        except Exception as e:
            st.error(f"Error loading debt: {e}")
    # ASSETS TAB
    with tab_assets:
        st.subheader("Bank Accounts & Credit Limits")
        st.info("📝 Tip: Edit the balances below and click 'Save'.")
        # Load Existing Or Default
        assets_df = get_df_robust(assets_sheet)
        if assets_df.empty:
            default_data = [
                {"Account Name": "Business Checking", "Type": "Cash", "Balance": 0, "Last Updated": str(pd.Timestamp.now().date())},
                {"Account Name": "Savings / Reserve", "Type": "Cash", "Balance": 0, "Last Updated": str(pd.Timestamp.now().date())},
                {"Account Name": "Credit Card Limit", "Type": "Credit", "Balance": 10000, "Last Updated": str(pd.Timestamp.now().date())}
            ]
            assets_df = pd.DataFrame(default_data)
        edited_assets = st.data_editor(
            assets_df, 
            num_rows="dynamic",
            use_container_width=True,
            column_config={
                "Balance": st.column_config.NumberColumn("Balance ($)", format="$%d"),
                "Type": st.column_config.SelectboxColumn("Type", options=["Cash", "Credit", "Investment", "Fixed Asset (Trailer/Oven)"])
            }
        )
        if st.button("Save Asset Balances"):
            assets_sheet.clear()
            assets_sheet.append_row(["Account Name", "Type", "Balance", "Last Updated"])
            if not edited_assets.empty:
                assets_sheet.append_rows(edited_assets.values.tolist())
            st.success("✅ Balances Updated!")
            st.rerun()
# 🍳 RECIPE COSTING
elif menu_choice == "🍳 Recipe Costing":
    st.header("Recipe & Food Cost Calculator")
    tab_pantry, tab_calc = st.tabs(["🥕 Ingredient Pantry", "🧮 Pizza Builder"])
    with tab_pantry:
        st.subheader("Manage Raw Ingredients")
        with st.form("ing_form", clear_on_submit=True):
            c1, c2, c3 = st.columns(3)
            name = c1.text_input("Ingredient Name")
            unit = c2.text_input("Unit (e.g. lb, oz)")
            cost = c3.number_input("Cost ($)", min_value=0.01)
            if st.form_submit_button("Add to Pantry"):
                ing_sheet.append_row([name, unit, cost, cost])
                st.success(f"Added {name}")
                st.rerun()
        ing_df = get_df_robust(ing_sheet)
        if not ing_df.empty:
            st.dataframe(ing_df, use_container_width=True)
    with tab_calc:
        st.subheader("Price Your Pizza")
        ing_df = get_df_robust(ing_sheet)
        if ing_df.empty:
            st.warning("Add ingredients to pantry first.")
        else:
            if "recipe_items" not in st.session_state: st.session_state.recipe_items = []
            c1, c2, c3 = st.columns([2, 1, 1])
            sel_ing = c1.selectbox("Select Ingredient", ing_df["Item Name"].tolist())
            qty = c2.number_input("Qty", 1.0)
            if c3.button("Add"):
                row = ing_df[ing_df["Item Name"] == sel_ing].iloc[0]
                cost_val = clean_money(str(row.get("Unit Cost", 0)))
                st.session_state.recipe_items.append({"Ingredient": sel_ing, "Qty": qty, "Cost": cost_val * qty})
            if st.session_state.recipe_items:
                r_df = pd.DataFrame(st.session_state.recipe_items)
                st.dataframe(r_df)
                st.metric("Total Cost", f"${r_df['Cost'].sum():.2f}")
                if st.button("Clear Recipe"):
                    st.session_state.recipe_items = []
                    st.rerun()
# 📝 LOG EXPENSES
elif menu_choice == "📝 Log Expenses":
    st.header("Log Business Expenses")
    with st.form("expense_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        item_name = col1.text_input("Item Name (e.g. Mozzarella 50lbs)")
        category = col2.selectbox("Category", ["Startup & Assets (Trailer, Truck, Ovens)","Inventory (Food & Drink)", "Equipment & Supplies","Vehicle & Fuel", "Marketing & Ads", "Utilities", "Other"])
        cost = st.number_input("Cost ($)", min_value=0.01)
        date = st.date_input("Date")
        if st.form_submit_button("Add Expense"):
            ledger_sheet.append_row([item_name, category, cost, str(date)])
            st.success("Expense Logged!")
# 💰 SALES & REVENUE
elif menu_choice == "💰 Sales & Revenue":
    st.header("Log Sales Revenue")
    with st.form("sales_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        event = c1.text_input("Event Name (e.g. Tuesday Lunch)")
        s_type = c2.selectbox("Type", ["Festival/Event", "Catering", "Private Party"])
        rev = st.number_input("Total Revenue ($)", min_value=0.01)
        date = st.date_input("Date")
        if st.form_submit_button("Log Sales"):
            sales_sheet.append_row([event, s_type, rev, str(date)])
            st.success("Sales Logged!")
# 🍕 MENU EDITOR
elif menu_choice == "🍕 Menu Editor":
    st.header("Menu Management")
    menu_df = get_df_robust(menu_sheet)
    edited_menu = st.data_editor(menu_df, num_rows="dynamic", use_container_width=True)
    if st.button("Save Menu Changes"):
        menu_sheet.clear()
        menu_sheet.append_row(["Item Name", "Description", "Price", "Category"])
        menu_sheet.append_rows(edited_menu.values.tolist())
        st.success("Menu Updated!")
# 🗄️ DOCUMENT VAULT
elif menu_choice == "🗄️ Document Vault":
    st.header("Document Vault")
    with st.form("vault_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        doc_name = c1.text_input("Document Name")
        doc_link = c2.text_input("Google Drive Link")
        doc_type = st.selectbox("Type", ["License/Permit", "Receipt/Invoice", "Contract", "Other"])
        if st.form_submit_button("Save Document"):
            vault_sheet.append_row([doc_name, doc_type, doc_link, str(pd.Timestamp.now().date())])
            st.success("Saved!")
    vault_df = get_df_robust(vault_sheet)
    if not vault_df.empty:
        st.dataframe(vault_df, column_config={"Link": st.column_config.LinkColumn("Link")})
