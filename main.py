
import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import plotly.express as px
from datetime import datetime

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

# --- MAIN APP ---
def main():
    st.set_page_config(page_title="Custom Crust HQ", layout="wide", page_icon="🍕")

    # 1. Load Data (Simple Call - No Try/Except needed here)
    assets, expenses_data = load_data()

    # 2. Process Liquid Assets (Global Bridge)
    liquid_assets = []
    if assets:
        for a in assets:
            atype = str(a.get('Type') or a.get('type') or '').strip().lower()
            if atype == 'liquid':
                liquid_assets.append(a)

    # 3. Sidebar Navigation
elif menu_choice == "🧾 Invoice Generator":
    st.sidebar.title("Navigation")
    
    # 1. Define Menu Options
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
    
    # 2. Create Sidebar Radio
    selected = st.sidebar.radio("Go to", options)

    # --- TAB 1: DASHBOARD ---
    if selected == "📊 Dashboard":
        st.markdown("## 🚀 Business Command Center")

        # A. Get Data
        # 'assets' and 'expenses_data' come from the load_data() function we added earlier
        safe_assets = locals().get('assets', []) or []
        safe_expenses = locals().get('expenses_data', []) or []

        # B. Filter Liquid Assets
        liquid_assets = []
        for a in safe_assets:
            atype = str(a.get('Type') or a.get('type') or '').strip().lower()
            if atype == 'liquid':
                liquid_assets.append(a)

        # C. Calculate Live Balances
    st.header("Invoice Builder")
    
    # Init Invoice Items List
    if "invoice_items" not in st.session_state: st.session_state.invoice_items = []
    
    # Top Section: Info
    c1, c2 = st.columns(2)
    client = c1.text_input("Client Name", placeholder="e.g. Corporate Event")
    inv_date = c2.date_input("Invoice Date")
    inv_id = f"INV-{random.randint(1000,9999)}"
    
    st.divider()
    
    # Middle Section: Add Items
    st.subheader("Add Items")
    menu_df = load_data(menu_sheet)
    
    tab_menu, tab_custom = st.tabs(["Select from Menu", "Custom Item"])
    
    with tab_menu:
        if not menu_df.empty:
            c_m1, c_m2, c_m3 = st.columns([3, 1, 1])
            sel_item = c_m1.selectbox("Menu Item", menu_df["Item Name"], key="inv_menu_sel")
            # Get default price
            price_row = menu_df[menu_df["Item Name"] == sel_item]["Price"].values
            def_price = clean_money(price_row[0]) if len(price_row) > 0 else 0.0
            
            sel_price = c_m2.number_input("Price ($)", value=def_price, key="inv_menu_price")
            sel_qty = c_m3.number_input("Qty", value=1, key="inv_menu_qty")
            
            if st.button("Add Menu Item", key="btn_add_menu"):
                st.session_state.invoice_items.append({
                    "Description": sel_item, "Qty": sel_qty, "Price": sel_price, "Total": sel_qty * sel_price
                })
                st.success(f"Added {sel_item}")
        else:
            st.warning("Menu sheet is empty.")

    with tab_custom:
        c_c1, c_c2, c_c3 = st.columns([3, 1, 1])
        cust_desc = c_c1.text_input("Description", placeholder="e.g. Catering Fee", key="inv_cust_desc")
        cust_price = c_c2.number_input("Price ($)", value=0.0, key="inv_cust_price")
        cust_qty = c_c3.number_input("Qty", value=1, key="inv_cust_qty")
        
        if st.button("Add Custom Item", key="btn_add_cust"):
            st.session_state.invoice_items.append({
                "Description": cust_desc, "Qty": cust_qty, "Price": cust_price, "Total": cust_qty * cust_price
            })
            st.success(f"Added {cust_desc}")

    # Bottom Section: Review & Save
    st.divider()
    st.subheader(f"Invoice Summary: {inv_id}")
    st.caption(f"Bill To: {client} | Date: {inv_date}")

    if st.session_state.invoice_items:
        # Show clean table instead of HTML
        inv_df = pd.DataFrame(st.session_state.invoice_items)
        st.dataframe(inv_df, use_container_width=True, hide_index=True)
        
        # Calculate Totals
        subtotal = inv_df["Total"].sum()
        tax = subtotal * 0.07 # 7% Tax
        grand_total = subtotal + tax
        
        # Totals Display
        c_t1, c_t2, c_t3 = st.columns(3)
        c_t1.metric("Subtotal", f"${subtotal:,.2f}")
        c_t2.metric("Tax (7%)", f"${tax:,.2f}")
        c_t3.metric("TOTAL DUE", f"${grand_total:,.2f}")
        
        c_act1, c_act2 = st.columns(2)
        if c_act1.button("💾 Save Invoice to Database", type="primary"):
            if client:
                try:
                    invoice_sheet.append_row([inv_id, client, str(inv_date), grand_total, "Unpaid"])
                    st.balloons()
                    st.success("Invoice Saved Successfully!")
                except Exception as e:
                    st.error(f"Error saving: {e}")
            else:
                st.error("Please enter a Client Name.")
        
        if c_act2.button("Clear Invoice"):
            st.session_state.invoice_items = []
            st.rerun()
    else:
        st.info("No items added yet.")

elif menu_choice == "📅 Planner & Projections":
    st.header("Future Event Planner")
    
    df_plan = load_data(planner_sheet)
    df_sales = load_data(sales_sheet)
    
    with st.expander("➕ Add Event", expanded=True):
        with st.form("planner_form", clear_on_submit=True):
            c1, c2, c3 = st.columns(3)
            name = c1.text_input("Event Name")
            date = c2.date_input("Date")
            rev = c3.number_input("Projected Revenue ($)", min_value=0.0)
            status = st.selectbox("Status", ["Confirmed", "Tentative", "Lead"])
            if st.form_submit_button("Save Event"):
                planner_sheet.append_row([name, str(date), rev, status])
                st.success("Saved!")
                st.rerun()
    
    st.divider()
    
    # Projections Chart
    if not df_plan.empty:
        df_plan["Amount"] = df_plan["Projected Revenue"].apply(clean_money)
        df_plan["Date"] = pd.to_datetime(df_plan["Date"], errors="coerce")
        df_plan["Month"] = df_plan["Date"].dt.strftime("%Y-%m")
        
        # Group by month
        proj_grp = df_plan.groupby("Month")["Amount"].sum().reset_index()
        proj_grp["Type"] = "Projected"
        
        # Get Actuals if available
        final_df = proj_grp
        if not df_sales.empty:
            df_sales["Amount"] = df_sales["Revenue"].apply(clean_money)
            df_sales["Date"] = pd.to_datetime(df_sales["Date"], errors="coerce")
            df_sales["Month"] = df_sales["Date"].dt.strftime("%Y-%m")
            act_grp = df_sales.groupby("Month")["Amount"].sum().reset_index()
            act_grp["Type"] = "Actual"
            final_df = pd.concat([proj_grp, act_grp])
            
        fig = px.bar(final_df, x="Month", y="Amount", color="Type", barmode="group",
                     color_discrete_map={"Actual": "#00CC96", "Projected": "#636EFA"})
        fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font=dict(color="white"))
        st.plotly_chart(fig, use_container_width=True)
        
        st.caption("Upcoming Events List:")
        st.dataframe(df_plan[["Event Name", "Date", "Projected Revenue", "Status"]], use_container_width=True)
    else:
        st.info("No events planned yet.")

elif menu_choice == "💰 Sales & Revenue":
    st.header("Log Sales Revenue")
    df_sales = load_data(sales_sheet)
    
    # MTD/YTD Logic
    mtd, ytd = 0.0, 0.0
    if not df_sales.empty:
        df_sales["Clean_Rev"] = df_sales["Revenue"].apply(clean_money)
        df_sales["Date_Obj"] = pd.to_datetime(df_sales["Date"], errors="coerce")
        now = pd.Timestamp.now()
        mtd = df_sales[(df_sales["Date_Obj"].dt.month == now.month) & (df_sales["Date_Obj"].dt.year == now.year)]["Clean_Rev"].sum()
        ytd = df_sales[df_sales["Date_Obj"].dt.year == now.year]["Clean_Rev"].sum()

    c1, c2 = st.columns(2)
    c1.metric("💰 MTD Sales", f"${mtd:,.2f}")
    c2.metric("🚀 YTD Sales", f"${ytd:,.2f}")
    st.divider()

    with st.form("sales_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        event = c1.text_input("Event Name")
        s_type = c2.selectbox("Type", ["Festival/Event", "Catering", "Private Party", "Daily Service"])
        rev = st.number_input("Revenue ($)", min_value=0.01)
        date = st.date_input("Date")
        if st.form_submit_button("Log Sales"):
            sales_sheet.append_row([event, s_type, rev, str(date)])
            st.success("Sales Logged!")
            st.rerun()
            
    if not df_sales.empty:
        st.subheader("Recent Sales")
        st.dataframe(df_sales.tail(5).iloc[::-1][["Event", "Type", "Revenue", "Date"]], use_container_width=True, hide_index=True)

elif menu_choice == "📝 Log Expenses":
    st.header("Log Business Expenses")
    df_exp = load_data(ledger_sheet)
    
    mtd, ytd = 0.0, 0.0
    if not df_exp.empty:
        df_exp["Clean_Cost"] = df_exp["Cost"].apply(clean_money)
        df_exp["Date_Obj"] = pd.to_datetime(df_exp["Date"], errors="coerce")
        now = pd.Timestamp.now()
        mtd = df_exp[(df_exp["Date_Obj"].dt.month == now.month) & (df_exp["Date_Obj"].dt.year == now.year)]["Clean_Cost"].sum()
        ytd = df_exp[df_exp["Date_Obj"].dt.year == now.year]["Clean_Cost"].sum()

    c1, c2 = st.columns(2)
    c1.metric("📅 MTD Expenses", f"${mtd:,.2f}")
    c2.metric("📆 YTD Expenses", f"${ytd:,.2f}")
    st.divider()


    # Load assets for payment method dropdown
    df_assets_list = load_data(assets_sheet)
    liquid_assets = []
    if not df_assets_list.empty:
        # Filter for Liquid by classification or type (case-insensitive)
        for _, row in df_assets_list.iterrows():
            class_val = str(row.get("Classification", "")).strip().lower()
            type_val = str(row.get("Type", "")).strip().lower()
            if class_val == "liquid" or type_val == "liquid":
                liquid_assets.append(row["Account Name"])
    payment_options = liquid_assets if liquid_assets else []
    payment_options.append("Other/External")

    with st.form("expense_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        item = c1.text_input("Item Name")
        cat = c2.selectbox("Category", ["Startup & Assets", "Inventory", "Equipment", "Vehicle", "Marketing", "Utilities", "Other"])
        cost = st.number_input("Cost ($)", min_value=0.01)
        date = st.date_input("Date")
        payment_source = st.selectbox("Payment Method", payment_options)
        if st.form_submit_button("Log Expense"):
            ledger_sheet.append_row([item, cat, cost, str(date), payment_source])
            st.success("Expense Logged!")
            st.rerun()

    if not df_exp.empty:
        st.subheader("Recent Expenses")
        st.dataframe(df_exp.tail(5).iloc[::-1][["Item", "Category", "Cost", "Date"]], use_container_width=True, hide_index=True)

elif menu_choice == "🏦 Assets & Debt":
    st.header("Assets & Liability Tracker")
    tab_debt, tab_assets = st.tabs(["📉 Manage Debt", "💵 Manage Assets"])
    
    with tab_debt:
        st.subheader("Debt Tracker")
        with st.form("debt_form"):
            c1, c2 = st.columns(2)
            name = c1.text_input("Creditor")
            action = c2.selectbox("Action", ["Repayment", "Borrow"])
            amt = st.number_input("Amount ($)", min_value=0.01)
            date = st.date_input("Date")
            if st.form_submit_button("Update"):
                debt_sheet.append_row([name, action, amt, str(date)])
                st.success("Updated!")
                st.rerun()
        
        df_d = load_data(debt_sheet)
        if not df_d.empty and "Amount" in df_d.columns:
            df_d['Clean'] = df_d['Amount'].apply(clean_money)
            for loan in df_d['Loan Name'].unique():
                sub = df_d[df_d['Loan Name'] == loan]
                # Fuzzy match type
                t_col = next((c for c in sub.columns if "Type" in c), None)
                if t_col:
                    sub['Norm'] = sub[t_col].astype(str).str.lower()
                    bor = sub[sub['Norm'].str.contains('borrow')]['Clean'].sum()
                    rep = sub[sub['Norm'].str.contains('repay')]['Clean'].sum()
                    bal = bor - rep
                    st.divider()
                    st.write(f"**{loan}**")
                    k1, k2, k3 = st.columns(3)
                    k1.metric("Original", f"${bor:,.0f}")
                    k2.metric("Paid", f"${rep:,.0f}")
                    k3.metric("Balance", f"${bal:,.0f}", delta=-bal)

    with tab_assets:
        st.subheader("Asset Balances")
        df_a = load_data(assets_sheet)
        if df_a.empty:
            df_a = pd.DataFrame([{"Account Name": "Checking", "Type": "Cash", "Initial Balance": 0, "Balance": 0, "Last Updated": str(pd.Timestamp.now().date())}])

        # Show asset table and allow editing
        edited = st.data_editor(df_a, num_rows="dynamic", use_container_width=True, column_order=["Account Name", "Type", "Classification", "Initial Balance", "Balance", "Last Updated"])
        if st.button("Save Assets"):
            assets_sheet.clear()
            assets_sheet.append_row(["Account Name", "Type", "Classification", "Initial Balance", "Balance", "Last Updated"])
            if not edited.empty: assets_sheet.append_rows(edited.values.tolist())
            st.success("Assets Saved!")
            st.rerun()

        st.markdown("---")
        st.subheader("Add Deposit to Asset")
        # Only show Liquid assets in deposit dropdown
        # --- Robust Liquid Asset Dropdown ---
        liquid_assets = []
        for idx, row in df_a.iterrows():
            asset_type = str(row.get('Type') or row.get('type') or row.get('Classification') or '').strip().lower()
            if asset_type == 'liquid':
                liquid_assets.append(row.get('Account Name') or row.get('name'))
        deposit_col1, deposit_col2 = st.columns(2)
        deposit_options = liquid_assets
        deposit_asset = deposit_col1.selectbox("Select Asset to Deposit Into", options=deposit_options if deposit_options else ["No Liquid Assets Found"])
        deposit_amt = deposit_col2.number_input("Deposit Amount ($)", min_value=0.01, value=0.01, step=0.01)
        deposit_notes = st.text_input("Notes (optional)")
        deposit_date = st.date_input("Deposit Date", value=pd.Timestamp.now().date())
        if st.button("Add Deposit") and deposit_asset:
            deposits_sheet.append_row([str(deposit_date), deposit_amt, deposit_asset, deposit_notes])
            st.success(f"Deposit of ${deposit_amt:,.2f} added to {deposit_asset}.")
            st.rerun()

elif menu_choice == "🤝 Vendor Network":
    st.header("Vendor Directory")
    with st.expander("➕ Add Vendor"):
        with st.form("vendor_form", clear_on_submit=True):
            c1, c2 = st.columns(2)
            name = c1.text_input("Company Name")
            contact = c2.text_input("Contact Person")
            phone = st.text_input("Phone")
            email = st.text_input("Email")
            cat = st.selectbox("Category", ["Food", "Equipment", "Maintenance", "Marketing", "Other"])
            if st.form_submit_button("Save Vendor"):
                vendor_sheet.append_row([name, contact, phone, email, "", cat])
                st.success("Saved!")
                st.rerun()
    
    df_v = load_data(vendor_sheet)
    if not df_v.empty: st.dataframe(df_v, use_container_width=True)
    else: st.info("No vendors yet.")

elif menu_choice == "🍕 Menu Editor":
    st.header("Menu Manager")
    df_m = load_data(menu_sheet)
    edited = st.data_editor(df_m, num_rows="dynamic", use_container_width=True)
    if st.button("Save Menu"):
        menu_sheet.clear()
        menu_sheet.append_row(["Item Name", "Description", "Price", "Category"])
        menu_sheet.append_rows(edited.values.tolist())
        st.success("Menu Saved!")

elif menu_choice == "🍳 Recipe Costing":
    st.header("Recipe Calculator")
    df_i = load_data(ing_sheet)
    
    tab1, tab2 = st.tabs(["Ingredients", "Calculator"])
    with tab1:
        st.subheader("Pantry")
        with st.form("ing_form", clear_on_submit=True):
            c1, c2, c3 = st.columns(3)
            n = c1.text_input("Ingredient")
            u = c2.text_input("Unit")
            c = c3.number_input("Cost ($)", min_value=0.01)
            if st.form_submit_button("Add"):
                ing_sheet.append_row([n, u, c, c])
                st.success("Added!")
                st.rerun()
        if not df_i.empty: st.dataframe(df_i, use_container_width=True)
        else: st.info("Add ingredients first.")
        
    with tab2:
        st.subheader("Build Recipe")
        if not df_i.empty:
            if "recipe" not in st.session_state: st.session_state.recipe = []
            c1, c2, c3 = st.columns([2,1,1])
            sel = c1.selectbox("Ingredient", df_i["Item Name"])
            qty = c2.number_input("Qty", 1.0)
            if c3.button("Add to Recipe"):
                row = df_i[df_i["Item Name"] == sel].iloc[0]
                u_cost = clean_money(row.get("Unit Cost", row.get("Cost", 0)))
                st.session_state.recipe.append({"Item": sel, "Qty": qty, "Cost": u_cost * qty})
            
            if st.session_state.recipe:
                rdf = pd.DataFrame(st.session_state.recipe)
                st.dataframe(rdf)
                st.metric("Total Cost", f"${rdf['Cost'].sum():.2f}")
                if st.button("Clear"):
                    st.session_state.recipe = []
                    st.rerun()
        else: st.warning("Pantry is empty.")

elif menu_choice == "🗄️ Document Vault":
    st.header("Document Vault")
    with st.form("doc_form"):
        c1, c2 = st.columns(2)
        name = c1.text_input("Name")
        link = c2.text_input("Link")
        # Document categories constant
        VAULT_CATEGORIES = [
            "Legal & Formation",      # Cert of Org, Operating Agreement, EIN
            "Licenses & Permits",     # Health Inspection, ServSafe
            "Assets & Vehicles",      # Trailer Title, Truck Purchase, Bill of Sale
            "Contracts & Agreements", # Event Contracts, Vendor Agreements
            "Banking & Financial",    # Bank Letters, Tax Forms
            "Insurance",              # Liability Policy, Car Insurance
            "Receipts & Expenses",    # Gas, Home Depot, Supplies
            "Brand & Marketing",      # Logos, Social Media Assets
            "Recipes & Menus",        # Food Specs, Prep Sheets
            "Employee & HR",          # Staff Contracts (Future)
            "Other"
        ]
        dtype = st.selectbox("Type", VAULT_CATEGORIES)
        if st.form_submit_button("Save Doc"):
            vault_sheet.append_row([name, dtype, link, str(pd.Timestamp.now().date())])
            st.success("Saved!")
    st.dataframe(load_data(vault_sheet), column_config={"Link": st.column_config.LinkColumn("Link")})
    