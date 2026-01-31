# FORCE UPDATE: V5.0 (Nuclear Reset)
import streamlit as st
import pandas as pd
import plotly.express as px
import gspread
from google.oauth2.service_account import Credentials
import datetime

# --- 1. SETUP PAGE CONFIGURATION ---
st.set_page_config(page_title="Custom Crust HQ", page_icon="🍕", layout="wide")


# --- 2. CONNECT TO GOOGLE SHEETS (Smart Auth) ---
@st.cache_resource
def connect_to_gsheets():
    scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    
    # Try multiple secret keys (Lowercase vs Uppercase)
    if "GCP_SERVICE_ACCOUNT" in st.secrets:
        creds_dict = st.secrets["GCP_SERVICE_ACCOUNT"]
    elif "gcp_service_account" in st.secrets:
        creds_dict = st.secrets["gcp_service_account"]
    elif "gsheets" in st.secrets:
        creds_dict = st.secrets["gsheets"]
    else:
        st.error("🚨 Secrets Error: Could not find 'GCP_SERVICE_ACCOUNT' in secrets.")
        st.stop()
    
    creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
    client = gspread.authorize(creds)
    
    try:
        sheet = client.open("Custom Crust Kitchen - Master Ledger")
        return sheet
    except Exception as e:
        st.error(f"🚨 Connection Error: {e}")
        st.stop()

sheet = connect_to_gsheets()

# Helper: Get Worksheet
def get_worksheet(name, headers):
    try:
        return sheet.worksheet(name)
    except:
        ws = sheet.add_worksheet(title=name, rows=100, cols=20)
        ws.append_row(headers)
        return ws

# Load Tabs (Added 'Planner')
ledger_sheet = get_worksheet("Ledger", ["Item", "Category", "Cost", "Date"])
sales_sheet = get_worksheet("Sales", ["Event", "Type", "Revenue", "Date"])
assets_sheet = get_worksheet("Assets", ["Account Name", "Type", "Balance", "Last Updated"])
debt_sheet = get_worksheet("Debt_Log", ["Loan Name", "Transaction Type", "Amount", "Date"])
planner_sheet = get_worksheet("Planner", ["Event Name", "Date", "Projected Revenue", "Status"])
vendor_sheet = get_worksheet("Vendors", ["Company Name", "Contact Person", "Phone", "Email", "Address", "Category"])
menu_sheet = get_worksheet("Menu", ["Item Name", "Description", "Price", "Category"])
ing_sheet = get_worksheet("Ingredients", ["Item Name", "Bulk Unit", "Bulk Cost", "Unit Cost"])
vault_sheet = get_worksheet("Vault_Index", ["Document Name", "Type", "Link", "Date"])

# --- 3. CUSTOM CSS (FINAL EXECUTIVE THEME) ---
st.markdown("""
<style>
    /* Main Background */
    .stApp, [data-testid="stSidebar"] {
        background-color: #0e0e0e;
        background-image: radial-gradient(#262626 1px, transparent 0);
        background-size: 20px 20px;
    }
    [data-testid="stSidebar"] { border-right: 1px solid #333; }

    /* NEON LOGO */
    .sidebar-logo {
        font-family: 'Arial Black', sans-serif;
        font-size: 24px !important;
        line-height: 1.2;
        text-transform: uppercase;
        color: #fff;
        text-align: center;
        margin-bottom: 25px;
        margin-top: 10px;
        text-shadow: 0 0 10px rgba(255, 75, 75, 0.9), 0 0 20px rgba(255, 75, 75, 0.6);
        letter-spacing: 1px;
    }
    
    /* BOXY BUTTONS */
    [data-testid="stSidebar"] div[role="radiogroup"] { display: flex; flex-direction: column; gap: 12px; }
    [data-testid="stSidebar"] label[data-baseweb="radio"] {
        background: rgba(22, 22, 22, 0.8);
        backdrop-filter: blur(5px);
        border: 1px solid #333;
        border-radius: 8px;
        padding: 15px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.2);
        color: #aaa;
        margin-bottom: 0px !important;
        transition: all 0.2s ease;
    }
    [data-testid="stSidebar"] label[data-baseweb="radio"]:hover {
        border-color: #FF4B4B; background: #1e1e1e; color: #fff; transform: scale(1.02);
    }

    /* METRIC CARDS */
    [data-testid="stMetric"] {
        background: rgba(22, 22, 22, 0.8);
        backdrop-filter: blur(5px);
        border: 1px solid #333;
        border-radius: 8px;
        padding: 20px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.3);
    }
    [data-testid="stMetric"]:hover { border-color: #FF4B4B; }
    [data-testid="stMetricLabel"] { color: #888 !important; font-size: 11px; text-transform: uppercase; letter-spacing: 1px; }
    [data-testid="stMetricValue"] { color: #fff !important; font-size: 26px; font-weight: 700; }
    
    h1, h2, h3 { color: #fff !important; }
    p, span, div { color: #ccc; }
    hr { border: 0; height: 1px; background: #333; margin: 20px 0; }
    .st-emotion-cache-16idsys p { text-align: center; width: 100%; color: #666 !important; font-size: 10px; letter-spacing: 2px; font-weight: 700; margin-bottom: 10px; }
</style>
""", unsafe_allow_html=True)

# --- 4. GLOBAL HELPERS ---
def clean_money(val):
    if isinstance(val, (int, float)): return float(val)
    if isinstance(val, str):
        clean = val.replace('$', '').replace(',', '').strip()
        if not clean: return 0.0
        try: return float(clean)
        except: return 0.0
    return 0.0

def get_df_robust(sheet_obj):
    try:
        data = sheet_obj.get_all_values()
        if len(data) < 2: return pd.DataFrame()
        headers = [str(h).strip().title() for h in data[0]]
        return pd.DataFrame(data[1:], columns=headers)
    except: return pd.DataFrame()

# --- 5. SIDEBAR NAVIGATION ---
st.sidebar.markdown('<p class="sidebar-logo">🍕 CUSTOM CRUST<br>HQ 🍕</p>', unsafe_allow_html=True)
st.sidebar.markdown("---")
st.sidebar.markdown("**COMMAND CENTER**") 
menu_choice = st.sidebar.radio("Navigation", 
    [
        "📊 Dashboard", 
        "📅 Planner & Projections",
        "💰 Sales & Revenue", 
        "📝 Log Expenses", 
        "🏦 Assets & Debt", 
        "🤝 Vendor Network",
        "🍕 Menu Editor",
        "🍳 Recipe Costing", 
        "🗄️ Document Vault"
    ], label_visibility="collapsed"
)
st.sidebar.markdown("---")

# --- 6. PAGE LOGIC ---

# 📊 DASHBOARD
if menu_choice == "📊 Dashboard":
    st.title("🚀 Business Command Center")
    st.markdown("###")
    
    # Load All Data
    df_exp = get_df_robust(ledger_sheet)
    df_sales = get_df_robust(sales_sheet)
    df_assets = get_df_robust(assets_sheet)
    df_debt = get_df_robust(debt_sheet)

    # Calculate Totals
    total_exp = 0.0
    if not df_exp.empty and "Cost" in df_exp.columns:
        df_exp["Clean_Cost"] = df_exp["Cost"].apply(clean_money)
        total_exp = df_exp["Clean_Cost"].sum()

    total_rev = 0.0
    if not df_sales.empty and "Revenue" in df_sales.columns:
        df_sales["Clean_Rev"] = df_sales["Revenue"].apply(clean_money)
        total_rev = df_sales["Clean_Rev"].sum()

    total_assets = 0.0
    if not df_assets.empty and "Balance" in df_assets.columns:
        df_assets["Clean_Bal"] = df_assets["Balance"].apply(clean_money)
        total_assets = df_assets["Clean_Bal"].sum()

    total_debt = 0.0
    if not df_debt.empty and "Amount" in df_debt.columns:
        df_debt["Clean_Amt"] = df_debt["Amount"].apply(clean_money)
        type_col = next((c for c in df_debt.columns if "Type" in c), None)
        if type_col:
            df_debt["Norm_Type"] = df_debt[type_col].astype(str).str.lower()
            borrowed = df_debt[df_debt["Norm_Type"].str.contains("borrow")]["Clean_Amt"].sum()
            repaid = df_debt[df_debt["Norm_Type"].str.contains("repay")]["Clean_Amt"].sum()
            total_debt = borrowed - repaid

    # Top Metrics
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("💰 Total Revenue", f"${total_rev:,.0f}")
    c2.metric("💸 Total Expenses", f"${total_exp:,.0f}")
    c3.metric("📈 Net Profit", f"${total_rev - total_exp:,.0f}", delta=total_rev - total_exp)
    c4.metric("🏛️ Business Equity", f"${total_assets - total_debt:,.0f}", delta=f"Debt: ${total_debt:,.0f}", delta_color="off")

    st.markdown("---")

    # Middle Zone: Operations
    st.subheader("📊 Operational Performance")
    c_op1, c_op2 = st.columns(2)
    
    with c_op1:
        st.caption("Revenue Sources")
        if total_rev > 0 and "Type" in df_sales.columns:
            fig = px.pie(df_sales, values="Clean_Rev", names="Type", hole=0.5, color_discrete_sequence=px.colors.qualitative.Pastel)
            fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font=dict(color="white"))
            st.plotly_chart(fig, use_container_width=True)
        else: st.info("No sales data.")

    with c_op2:
        st.caption("Expense Breakdown")
        if total_exp > 0 and "Category" in df_exp.columns:
            fig = px.pie(df_exp, values="Clean_Cost", names="Category", hole=0.5, color_discrete_sequence=px.colors.qualitative.Vivid)
            fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font=dict(color="white"))
            st.plotly_chart(fig, use_container_width=True)
        else: st.info("No expense data.")

# 📅 PLANNER & PROJECTIONS (NEW)
elif menu_choice == "📅 Planner & Projections":
    st.header("Future Event Planner")
    
    # 1. Load Data
    df_plan = get_df_robust(planner_sheet)
    df_sales = get_df_robust(sales_sheet) # Needed for "Actuals"
    
    # 2. Input Form
    with st.expander("➕ Add Upcoming Event / Catering Gig", expanded=True):
        with st.form("planner_form", clear_on_submit=True):
            c1, c2, c3 = st.columns(3)
            evt_name = c1.text_input("Event Name")
            evt_date = c2.date_input("Date")
            evt_rev = c3.number_input("Projected Revenue ($)", min_value=0.0)
            status = st.selectbox("Status", ["Confirmed", "Tentative", "Lead"])
            
            if st.form_submit_button("Add Event"):
                planner_sheet.append_row([evt_name, str(evt_date), evt_rev, status])
                st.success("Event Added!")
                st.rerun()
    
    # 3. Process Data for Charting
    total_proj = 0.0
    combined_data = []

    # Get Projected
    if not df_plan.empty:
        df_plan["Projected Revenue"] = df_plan["Projected Revenue"].apply(clean_money)
        df_plan["Date"] = pd.to_datetime(df_plan["Date"], errors="coerce")
        df_plan["Month"] = df_plan["Date"].dt.strftime("%Y-%m")
        total_proj = df_plan["Projected Revenue"].sum()
        
        # Group by Month
        proj_grouped = df_plan.groupby("Month")["Projected Revenue"].sum().reset_index()
        proj_grouped["Type"] = "Projected"
        proj_grouped.rename(columns={"Projected Revenue": "Amount"}, inplace=True)
        combined_data.append(proj_grouped)

    # Get Actuals (from Sales)
    if not df_sales.empty:
        df_sales["Revenue"] = df_sales["Revenue"].apply(clean_money)
        df_sales["Date"] = pd.to_datetime(df_sales["Date"], errors="coerce")
        df_sales["Month"] = df_sales["Date"].dt.strftime("%Y-%m")
        
        act_grouped = df_sales.groupby("Month")["Revenue"].sum().reset_index()
        act_grouped["Type"] = "Actual Sales"
        act_grouped.rename(columns={"Revenue": "Amount"}, inplace=True)
        combined_data.append(act_grouped)

    # 4. Metrics & Chart
    st.divider()
    c1, c2 = st.columns([1, 2])
    
    with c1:
        st.metric("🔮 Total Pipeline (Projected)", f"${total_proj:,.0f}")
        st.caption("Upcoming Events:")
        if not df_plan.empty:
            st.dataframe(df_plan[["Event Name", "Date", "Projected Revenue", "Status"]], hide_index=True)
        else:
            st.info("No upcoming events logged.")

    with c2:
        st.subheader("📊 Actual vs. Projected Sales")
        if combined_data:
            final_df = pd.concat(combined_data)
            fig = px.bar(final_df, x="Month", y="Amount", color="Type", barmode="group",
                         color_discrete_map={"Actual Sales": "#00CC96", "Projected": "#636EFA"})
            fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font=dict(color="white"))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Log sales or events to see projections.")

# 💰 SALES & REVENUE (Updated)
elif menu_choice == "💰 Sales & Revenue":
    st.header("Log Sales Revenue")
    
    df_sales = get_df_robust(sales_sheet)
    mtd_rev, ytd_rev = 0.0, 0.0
    
    if not df_sales.empty:
        df_sales["Clean_Rev"] = df_sales["Revenue"].apply(clean_money)
        df_sales["Date_Obj"] = pd.to_datetime(df_sales["Date"], errors="coerce")
        now = pd.Timestamp.now()
        mtd_rev = df_sales[(df_sales["Date_Obj"].dt.month == now.month) & (df_sales["Date_Obj"].dt.year == now.year)]["Clean_Rev"].sum()
        ytd_rev = df_sales[df_sales["Date_Obj"].dt.year == now.year]["Clean_Rev"].sum()

    c1, c2 = st.columns(2)
    c1.metric("💰 MTD Sales", f"${mtd_rev:,.2f}")
    c2.metric("🚀 YTD Sales", f"${ytd_rev:,.2f}")
    st.markdown("---")

    with st.form("sales_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        event = c1.text_input("Event Name")
        s_type = c2.selectbox("Type", ["Festival/Event", "Catering", "Private Party", "Daily Service"])
        rev = st.number_input("Total Revenue ($)", min_value=0.01)
        date = st.date_input("Date")
        if st.form_submit_button("Log Sales"):
            sales_sheet.append_row([event, s_type, rev, str(date)])
            st.success("✅ Sales Logged!")
            st.rerun()
            
    if not df_sales.empty:
        st.subheader("🕒 Recent Sales")
        st.dataframe(df_sales.tail(5).iloc[::-1][["Event", "Type", "Revenue", "Date"]], use_container_width=True, hide_index=True)

# 📝 LOG EXPENSES (Updated)
elif menu_choice == "📝 Log Expenses":
    st.header("Log Business Expenses")
    
    df_exp = get_df_robust(ledger_sheet)
    mtd_exp, ytd_exp = 0.0, 0.0
    
    if not df_exp.empty:
        df_exp["Clean_Cost"] = df_exp["Cost"].apply(clean_money)
        df_exp["Date_Obj"] = pd.to_datetime(df_exp["Date"], errors="coerce")
        now = pd.Timestamp.now()
        mtd_exp = df_exp[(df_exp["Date_Obj"].dt.month == now.month) & (df_exp["Date_Obj"].dt.year == now.year)]["Clean_Cost"].sum()
        ytd_exp = df_exp[df_exp["Date_Obj"].dt.year == now.year]["Clean_Cost"].sum()

    c1, c2 = st.columns(2)
    c1.metric("📅 MTD Expenses", f"${mtd_exp:,.2f}")
    c2.metric("📆 YTD Expenses", f"${ytd_exp:,.2f}")
    st.markdown("---")

    with st.form("expense_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        item_name = col1.text_input("Item Name")
        category = col2.selectbox("Category", [
            "Startup & Assets (Trailer, Truck, Ovens)", "Inventory (Food & Drink)", 
            "Equipment & Supplies", "Vehicle & Fuel", "Marketing & Ads", "Utilities", "Other"
        ])
        cost = st.number_input("Cost ($)", min_value=0.01)
        date = st.date_input("Date")
        if st.form_submit_button("Add Expense"):
            ledger_sheet.append_row([item_name, category, cost, str(date)])
            st.success("✅ Expense Logged!")
            st.rerun()

    if not df_exp.empty:
        st.subheader("🕒 Recent Expenses")
        st.dataframe(df_exp.tail(5).iloc[::-1][["Item", "Category", "Cost", "Date"]], use_container_width=True, hide_index=True)

# 🏦 ASSETS & DEBT
elif menu_choice == "🏦 Assets & Debt":
    st.header("Assets & Liability Tracker")
    tab_debt, tab_assets = st.tabs(["📉 Manage Debt", "💵 Manage Assets"])
    
    with tab_debt:
        st.subheader("Loan Repayment Tracker")
        with st.form("debt_form"):
            c1, c2 = st.columns(2)
            loan_name = c1.text_input("Creditor Name", "Business Loan")
            trans_type = c2.selectbox("Action", ["Repayment", "Borrow"])
            amount = st.number_input("Amount ($)", min_value=0.01)
            date = st.date_input("Date")
            if st.form_submit_button("Update Loan"):
                debt_sheet.append_row([loan_name, trans_type, amount, str(date)])
                st.success("Logged!")
                st.rerun()
        
        debts = get_df_robust(debt_sheet)
        if not debts.empty and "Amount" in debts.columns:
            debts['Clean_Amt'] = debts['Amount'].apply(clean_money)
            for loan in debts['Loan Name'].unique():
                sub = debts[debts['Loan Name'] == loan]
                t_col = next((c for c in sub.columns if "Type" in c), None)
                if t_col:
                    sub['Norm_Type'] = sub[t_col].astype(str).str.lower()
                    bor = sub[sub['Norm_Type'].str.contains('borrow')]['Clean_Amt'].sum()
                    rep = sub[sub['Norm_Type'].str.contains('repay')]['Clean_Amt'].sum()
                    bal = bor - rep
                    st.divider()
                    st.write(f"**{loan}**")
                    k1, k2, k3 = st.columns(3)
                    k1.metric("Original", f"${bor:,.0f}")
                    k2.metric("Paid", f"${rep:,.0f}")
                    k3.metric("Remaining", f"${bal:,.0f}", delta=-bal)

    with tab_assets:
        st.subheader("Asset Balances")
        assets_df = get_df_robust(assets_sheet)
        if assets_df.empty: assets_df = pd.DataFrame([{"Account Name": "Biz Checking", "Type": "Cash", "Balance": 0, "Last Updated": str(pd.Timestamp.now().date())}])
        
        edited = st.data_editor(assets_df, num_rows="dynamic", use_container_width=True)
        if st.button("Save Assets"):
            assets_sheet.clear()
            assets_sheet.append_row(["Account Name", "Type", "Balance", "Last Updated"])
            if not edited.empty: assets_sheet.append_rows(edited.values.tolist())
            st.success("Saved!")
            st.rerun()

# 🤝 VENDOR NETWORK (NEW)
elif menu_choice == "🤝 Vendor Network":
    st.header("Vendor & Supplier Directory")
    
    # Input Form
    with st.expander("➕ Add New Vendor"):
        with st.form("vendor_form", clear_on_submit=True):
            c1, c2 = st.columns(2)
            comp_name = c1.text_input("Company Name")
            contact = c2.text_input("Contact Person")
            
            c3, c4 = st.columns(2)
            phone = c3.text_input("Phone Number")
            email = c4.text_input("Email")
            
            address = st.text_area("Address / Notes")
            category = st.selectbox("Category", ["Food Supplier", "Equipment", "Maintenance", "Marketing", "Other"])
            
            if st.form_submit_button("Save Vendor"):
                vendor_sheet.append_row([comp_name, contact, phone, email, address, category])
                st.success("Vendor Saved!")
                st.rerun()

    # Display Directory
    st.subheader("📋 Vendor List")
    df_vendors = get_df_robust(vendor_sheet)
    if not df_vendors.empty:
        st.dataframe(df_vendors, use_container_width=True)
    else:
        st.info("No vendors added yet.")

# 🍕 MENU EDITOR
elif menu_choice == "🍕 Menu Editor":
    st.header("Menu Management")
    menu_df = get_df_robust(menu_sheet)
    edited_menu = st.data_editor(menu_df, num_rows="dynamic", use_container_width=True)
    if st.button("Save Menu"):
        menu_sheet.clear()
        menu_sheet.append_row(["Item Name", "Description", "Price", "Category"])
        menu_sheet.append_rows(edited_menu.values.tolist())
        st.success("Menu Updated!")

# 🍳 RECIPE COSTING
elif menu_choice == "🍳 Recipe Costing":
    st.header("Recipe Calculator")
    tab_pantry, tab_calc = st.tabs(["🥕 Ingredients", "🧮 Calculator"])
    with tab_pantry:
        with st.form("ing_form"):
            c1, c2, c3 = st.columns(3)
            name = c1.text_input("Name")
            unit = c2.text_input("Unit")
            cost = c3.number_input("Cost", min_value=0.01)
            if st.form_submit_button("Add"):
                ing_sheet.append_row([name, unit, cost, cost])
                st.success("Added!")
                st.rerun()
        st.dataframe(get_df_robust(ing_sheet), use_container_width=True)
    
    with tab_calc:
        ing_df = get_df_robust(ing_sheet)
        if not ing_df.empty:
            if "recipe" not in st.session_state: st.session_state.recipe = []
            c1, c2, c3 = st.columns([2,1,1])
            sel = c1.selectbox("Ingredient", ing_df["Item Name"])
            qty = c2.number_input("Qty", 1.0)
            if c3.button("Add"):
                cost = clean_money(ing_df[ing_df["Item Name"] == sel].iloc[0].get("Unit Cost", 0))
                st.session_state.recipe.append({"Item": sel, "Qty": qty, "Cost": cost * qty})
            
            if st.session_state.recipe:
                rdf = pd.DataFrame(st.session_state.recipe)
                st.dataframe(rdf)
                st.metric("Total Cost", f"${rdf['Cost'].sum():.2f}")
                if st.button("Clear"):
                    st.session_state.recipe = []
                    st.rerun()

# 🗄️ DOCUMENT VAULT
elif menu_choice == "🗄️ Document Vault":
    st.header("Document Vault")
    with st.form("vault"):
        c1, c2 = st.columns(2)
        name = c1.text_input("Doc Name")
        link = c2.text_input("Drive Link")
        dtype = st.selectbox("Type", ["License", "Invoice", "Contract", "Other"])
        if st.form_submit_button("Save"):
            vault_sheet.append_row([name, dtype, link, str(pd.Timestamp.now().date())])
            st.success("Saved!")
    st.dataframe(get_df_robust(vault_sheet), column_config={"Link": st.column_config.LinkColumn("Link")})
