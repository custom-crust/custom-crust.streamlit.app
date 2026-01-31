import streamlit as st
import pandas as pd
import plotly.express as px
import gspread
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
import io

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="Custom Crust HQ", layout="wide", page_icon="🍕")

# --- CUSTOM CSS (PROFESSIONAL LEFT ALIGN) ---
st.markdown("""
<style>
    /* 1. Main Background: Dark Mesh/Leather Texture */
    .stApp {
        background-color: #0e0e0e;
        background-image: radial-gradient(#262626 1px, transparent 0);
        background-size: 20px 20px;
    }
    
    /* 2. Sidebar: Robust Border & Texture */
    [data-testid="stSidebar"] {
        background-color: #0e0e0e;
        background-image: radial-gradient(#262626 1px, transparent 0);
        background-size: 20px 20px;
        border-right: 3px solid #333;
        padding-left: 10px;
        padding-right: 10px; /* Add padding on right for the buttons */
    }
    
    /* 3. Sidebar Menu Items -> "Navigation Cards" */
    [data-testid="stSidebar"] div[role="radiogroup"] {
        display: flex;
        flex-direction: column;
        gap: 8px; /* Space between buttons */
    }
    
    [data-testid="stSidebar"] label[data-baseweb="radio"] {
        background: linear-gradient(145deg, #1e1e1e, #141414); /* Card Background */
        border: 1px solid #444;       /* Card Border */
        border-radius: 10px;          /* Rounded Corners */
        padding: 10px 15px;           /* Inner Spacing */
        width: 100%;                  /* Fill Sidebar Width */
        margin-bottom: 0px !important;
        transition: all 0.2s ease-in-out;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.3); /* Subtle Shadow */
    }
    
    /* Hover Effect for Buttons */
    [data-testid="stSidebar"] label[data-baseweb="radio"]:hover {
        border-color: #FF4B4B;        /* Highlight Color */
        transform: translateX(5px);   /* Slide Right */
        box-shadow: 4px 4px 8px rgba(0,0,0,0.5);
    }
/* 4. Metric Cards: Dashboard Boxes */
[data-testid="stMetric"] {
    background: linear-gradient(145deg, #1e1e1e, #141414);
    padding: 15px 20px;
    border-radius: 15px;
    border: 2px solid #444;
    box-shadow: 4px 4px 10px rgba(0,0,0,0.5);
}
/* 5. Horizontal Dividers: The "Capsule" Look */
hr {
    margin-top: 30px;
    margin-bottom: 30px;
    border: 0;
    height: 5px;
    background: #333;
    border-radius: 5px;
}
/* 6. General Text Styling */
h1, h2, h3, p, div, span {
    color: #E0E0E0 !important;
}
/* 7. Specific Style for 'Command Center' Label */ .st-emotion-cache-16idsys p { font-size: 12px; text-transform: uppercase; color: #888 !important; letter-spacing: 1.5px; font-weight: 600; margin-left: 5px; }

</style>
""", unsafe_allow_html=True)

# Hardcoded IDs (from provided links / configuration)
SHEET_ID = "1yqbd35J140KWT7ui8Ggqn68_OfGXb1wofViJRcSgZBU"
VAULT_FOLDER_ID = "15YYxQXXAk9zuJ6wpRUZbUg6Qsmmyjcd2"

# --- 2. AUTHENTICATION (single helper) ---
@st.cache_resource
def get_manager():
    try:
        info = st.secrets["GCP_SERVICE_ACCOUNT"]
        # Accept either a dict (Option B in Streamlit secrets) or a JSON string
        if isinstance(info, str):
            import json
            try:
                info = json.loads(info)
            except Exception:
                st.error("🔐 GCP_SERVICE_ACCOUNT secret is a string but not valid JSON. Please store the service account JSON or the parsed dictionary in Streamlit secrets.")
                st.stop()

        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive",
        ]

        # Normalize private_key newlines (handle escaped newlines safely)
        if isinstance(info, dict) and "private_key" in info and isinstance(info["private_key"], str):
            pk = info["private_key"]
            pk = pk.replace("\\n", "\n").replace("\\r\\n", "\n").replace("\\r", "\n")
            info["private_key"] = pk.strip()

        try:
            creds = Credentials.from_service_account_info(info, scopes=scopes)
        except Exception as err:
            st.error(f"🔐 Failed to create credentials: {err}. Check your service account secret shape.")
            st.stop()

        gs_client = gspread.authorize(creds)
        drive_client = build("drive", "v3", credentials=creds)
        return gs_client, drive_client
    except Exception as e:
        st.error(f"🔐 Authentication Error: {e}")
        st.stop()

client, drive_service = get_manager()

# --- 3. CONNECT TO SHEETS ---
try:
    sheet = client.open_by_key(SHEET_ID)
    
    def get_worksheet(name, headers):
        try:
            return sheet.worksheet(name)
        except:
            ws = sheet.add_worksheet(title=name, rows="100", cols="10")
            ws.append_row(headers)
            return ws
    ledger_sheet = get_worksheet("Ledger", ["Item", "Category", "Cost", "Date"])
    sales_sheet = get_worksheet("Sales", ["Event", "Type", "Revenue", "Date"])
    menu_sheet = get_worksheet("Menu", ["Item Name", "Description", "Price"])
    vault_sheet = get_worksheet("Vault_Index", ["Document Name", "Type", "Link", "Date"])
    assets_sheet = get_worksheet("Assets", ["Account Name", "Type", "Balance", "Last Updated"])
    debt_sheet = get_worksheet("Debt_Log", ["Loan Name", "Transaction Type", "Amount", "Date"])
    # NEW: Ingredients Tab
    ing_sheet = get_worksheet("Ingredients", ["Item Name", "Bulk Unit (e.g. 50lb)", "Bulk Cost", "Unit Cost"])
    # NEW TABS
    assets_sheet = get_worksheet("Assets", ["Account Name", "Type", "Balance", "Last Updated"])
    debt_sheet = get_worksheet("Debt_Log", ["Loan Name", "Transaction Type", "Amount", "Date"])
    # NEW: Ingredients Tab
    ing_sheet = get_worksheet("Ingredients", ["Item Name", "Bulk Unit (e.g. 50lb)", "Bulk Cost", "Unit Cost"])

except Exception as e:
    st.error(f"📉 Sheet Connection Failed: {e}")
    st.stop()

# --- 4. SIDEBAR NAVIGATION ---
st.sidebar.title("🍕 Custom Crust HQ")
st.sidebar.markdown("---")
st.sidebar.markdown("**COMMAND CENTER**") 
menu_choice = st.sidebar.radio("Navigation", 
    ["📊 Dashboard", "🏦 Assets & Debt", "🍳 Recipe Costing", "📝 Log Expenses", "💰 Sales & Revenue", "🍕 Menu Editor", "🗄️ Document Vault"], label_visibility="collapsed")
st.sidebar.markdown("---")


# --- 5. PAGE LOGIC ---

# 📊 DASHBOARD (Crash-Proof Logic)

# 📊 DASHBOARD (Smart & Diagnostic)

# 📊 DASHBOARD (X-RAY DIAGNOSTIC MODE)

# 📊 DASHBOARD (The Bulldozer Fix)

# 📊 DASHBOARD (Hard-Coded Fix)
    # 📊 DASHBOARD (Clean & Robust)
    if menu_choice == "📊 Dashboard":
        st.header("Business Health Overview")
        
        # 1. Helper: Currency Cleaner (Handles $17,000.00)
        def clean_money(val):
            if isinstance(val, (int, float)): return float(val)
            if isinstance(val, str):
                # Remove $ and , and spaces
                clean = val.replace('$', '').replace(',', '').strip()
                if not clean: return 0.0
                try: return float(clean)
                except: return 0.0
            return 0.0

        # 2. Helper: Robust Data Loader
        def get_df(sheet):
            try:
                data = sheet.get_all_values()
                if len(data) < 2: return pd.DataFrame()
                # Normalize headers: Title Case and Strip (e.g. "transaction type " -> "Transaction Type")
                headers = [str(h).strip().title() for h in data[0]]
                return pd.DataFrame(data[1:], columns=headers)
            except:
                return pd.DataFrame()

        # 3. Load Data
        df_exp = get_df(ledger_sheet)
        df_sales = get_df(sales_sheet)
        df_assets = get_df(assets_sheet)
        df_debt = get_df(debt_sheet)

        # 4. Calculate Expenses
        total_exp = 0.0
        if not df_exp.empty and "Cost" in df_exp.columns:
            df_exp["Clean_Cost"] = df_exp["Cost"].apply(clean_money)
            total_exp = df_exp["Clean_Cost"].sum()

        # 5. Calculate Sales
        total_rev = 0.0
        if not df_sales.empty and "Revenue" in df_sales.columns:
            df_sales["Clean_Rev"] = df_sales["Revenue"].apply(clean_money)
            total_rev = df_sales["Clean_Rev"].sum()

        # 6. Calculate Assets
        total_assets = 0.0
        if not df_assets.empty and "Balance" in df_assets.columns:
            df_assets["Clean_Bal"] = df_assets["Balance"].apply(clean_money)
            total_assets = df_assets["Clean_Bal"].sum()

        # 7. Calculate Debt (The Fix)
        total_debt = 0.0
        if not df_debt.empty and "Amount" in df_debt.columns:
            df_debt["Clean_Amt"] = df_debt["Amount"].apply(clean_money)
            
            # Identify Transaction Type column (fuzzy match)
            type_col = next((c for c in df_debt.columns if "Type" in c), None)
            
            if type_col:
                # Normalize to lowercase for easy matching (borrow vs Borrow)
                df_debt["Norm_Type"] = df_debt[type_col].astype(str).str.lower()
                
                borrowed = df_debt[df_debt["Norm_Type"].str.contains("borrow")]["Clean_Amt"].sum()
                repaid = df_debt[df_debt["Norm_Type"].str.contains("repay")]["Clean_Amt"].sum()
                total_debt = borrowed - repaid

        # 8. Display Metrics
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total Sales", f"${total_rev:,.0f}")
        c2.metric("Total Expenses", f"${total_exp:,.0f}")
        c3.metric("Net Profit", f"${total_rev - total_exp:,.0f}", delta=total_rev - total_exp)
        
        # Net Worth = Assets - Debt
        net_worth = total_assets - total_debt
        c4.metric("Business Equity", f"${net_worth:,.0f}", delta=f"Debt: ${total_debt:,.0f}", delta_color="off")

        st.divider()

        # 9. Charts
        col_charts1, col_charts2 = st.columns(2)
        
        with col_charts1:
            st.subheader("💸 Spending Breakdown")
            if total_exp > 0 and "Category" in df_exp.columns:
                fig_exp = px.pie(df_exp, values="Clean_Cost", names="Category", hole=0.4)
                st.plotly_chart(fig_exp, use_container_width=True)
            else:
                st.info("No expenses logged yet.")

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
                st.info("No assets or debt logged yet.")

# 🏦 ASSETS & DEBT MANAGER
elif menu_choice == "🏦 Assets & Debt":
    st.header("Assets & Liability Tracker")
    
    tab_debt, tab_assets = st.tabs(["📉 Manage Debt", "💵 Manage Assets"])
    
    # --- DEBT TRACKER ---
    with tab_debt:
        st.subheader("Loan Repayment Tracker")
        
        # Form to Log Borrowing or Payment
        with st.form("debt_form", clear_on_submit=True):
            c1, c2 = st.columns(2)
            # UPDATED: Default value is now generic
            loan_name = c1.text_input("Creditor Name", value="Business Loan")
            trans_type = c2.selectbox("Action", ["Repayment", "Borrow"])
            amount = st.number_input("Amount ($)", min_value=0.01)
            date = st.date_input("Date")
            
            if st.form_submit_button("Update Loan Balance"):
                debt_sheet.append_row([loan_name, trans_type, amount, str(date)])
                st.success("Transaction Logged!")
                st.rerun()
        
        # Show Balances
        debts = pd.DataFrame(debt_sheet.get_all_records())
        if not debts.empty:
            debts['Amount'] = pd.to_numeric(debts['Amount'], errors='coerce')
            # Group by Loan Name
            for loan in debts['Loan Name'].unique():
                subset = debts[debts['Loan Name'] == loan]
                borrowed = subset[subset['Transaction Type'] == 'Borrow']['Amount'].sum()
                repaid = subset[subset['Transaction Type'] == 'Repayment']['Amount'].sum()
                balance = borrowed - repaid
                
                st.divider()
                st.write(f"**{loan}**")
                k1, k2, k3 = st.columns(3)
                k1.metric("Original Loan", f"${borrowed:,.0f}")
                k2.metric("Paid Off", f"${repaid:,.0f}")
                k3.metric("Remaining Balance", f"${balance:,.0f}", delta=-balance)
                
                # Progress Bar
                if borrowed > 0:
                    progress = min(repaid / borrowed, 1.0)
                    st.progress(progress, text=f"{int(progress*100)}% Paid Off")
    # --- ASSET TRACKER ---
    with tab_assets:
        st.subheader("Bank Accounts & Credit Limits")
        st.info("📝 Tip: Edit the balances below and click 'Save'.")
        
        # 1. Load Data
        try:
            assets_data = assets_sheet.get_all_records()
            assets_df = pd.DataFrame(assets_data)
        except:
            assets_df = pd.DataFrame()
    # 2. Self-Healing: If empty, create default template
    if assets_df.empty:
        default_data = [
            {"Account Name": "Business Checking", "Type": "Cash", "Balance": 0, "Last Updated": str(pd.Timestamp.now().date())},
            {"Account Name": "Savings / Reserve", "Type": "Cash", "Balance": 0, "Last Updated": str(pd.Timestamp.now().date())},
            {"Account Name": "Credit Card Limit", "Type": "Credit", "Balance": 10000, "Last Updated": str(pd.Timestamp.now().date())}
        ]
        assets_df = pd.DataFrame(default_data)
    # 3. Editable Table
    edited_assets = st.data_editor(
        assets_df, 

        # 🏦 ASSETS & DEBT MANAGER
        elif menu_choice == "🏦 Assets & Debt":
            st.header("Assets & Liability Tracker")
    
            tab_debt, tab_assets = st.tabs(["📉 Manage Debt", "💵 Manage Assets"])
    
            # Helper: Clean Money
            def clean_money(val):
                if isinstance(val, (int, float)): return float(val)
                if isinstance(val, str):
                    clean = val.replace('$', '').replace(',', '').strip()
                    if not clean: return 0.0
                    try: return float(clean)
                    except: return 0.0
                return 0.0

            # --- DEBT TRACKER ---
            with tab_debt:
                st.subheader("Loan Repayment Tracker")
        
                # Form
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
        
                # Show Balances (The Fix)
                try:
                    data = debt_sheet.get_all_values()
                    if len(data) > 1:
                        # Use clean headers
                        headers = [str(h).strip().title() for h in data[0]]
                        debts = pd.DataFrame(data[1:], columns=headers)
                
                        # Clean Amount
                        debts['Clean_Amt'] = debts['Amount'].apply(clean_money)
                
                        # Group by Loan Name
                        unique_loans = debts['Loan Name'].unique()
                
                        for loan in unique_loans:
                            subset = debts[debts['Loan Name'] == loan]
                    
                            # Fuzzy match 'Borrow' and 'Repayment'
                            # Convert type to lower case for comparison
                            subset['Norm_Type'] = subset['Transaction Type'].astype(str).str.lower()
                    
                            borrowed = subset[subset['Norm_Type'].str.contains('borrow')]['Clean_Amt'].sum()
                            repaid = subset[subset['Norm_Type'].str.contains('repay')]['Clean_Amt'].sum()
                            balance = borrowed - repaid
                    
                            st.divider()
                            st.write(f"**{loan}**")
                            k1, k2, k3 = st.columns(3)
                            k1.metric("Original Loan", f"${borrowed:,.0f}")
                            k2.metric("Paid Off", f"${repaid:,.0f}")
                            k3.metric("Remaining Balance", f"${balance:,.0f}", delta=-balance)
                    
                            if borrowed > 0:
                                progress = min(repaid / borrowed, 1.0)
                                st.progress(progress, text=f"{int(progress*100)}% Paid Off")
                    else:
                        st.info("No debt records found.")
                except Exception as e:
                    st.error(f"Error loading debt data: {e}")

            # --- ASSET TRACKER ---
            with tab_assets:
                st.subheader("Bank Accounts & Credit Limits")
                st.info("📝 Tip: Edit the balances below and click 'Save'.")
        
                # Load Data
                try:
                    assets_data = assets_sheet.get_all_records()
                    assets_df = pd.DataFrame(assets_data)
                except:
                    assets_df = pd.DataFrame()

                # Defaults
                if assets_df.empty:
                    default_data = [
                        {"Account Name": "Business Checking", "Type": "Cash", "Balance": 0, "Last Updated": str(pd.Timestamp.now().date())},
                        {"Account Name": "Savings / Reserve", "Type": "Cash", "Balance": 0, "Last Updated": str(pd.Timestamp.now().date())},
                        {"Account Name": "Credit Card Limit", "Type": "Credit", "Balance": 10000, "Last Updated": str(pd.Timestamp.now().date())}
                    ]
                    assets_df = pd.DataFrame(default_data)

                # Editor
                edited_assets = st.data_editor(
                    assets_df, 
                    num_rows="dynamic",
                    use_container_width=True,
                    column_config={
                        "Balance": st.column_config.NumberColumn("Balance ($)", format="$%d"),
                        "Type": st.column_config.SelectboxColumn("Type", options=["Cash", "Credit", "Investment", "Fixed Asset (Trailer/Oven)"])
                    }
                )
        
                # Save
                if st.button("Save Asset Balances"):
                    assets_sheet.clear()
                    assets_sheet.append_row(["Account Name", "Type", "Balance", "Last Updated"])
                    if not edited_assets.empty:
                        assets_sheet.append_rows(edited_assets.values.tolist())
                    st.success("✅ Balances Updated!")
                    st.rerun()
        existing_data = vault_sheet.get_all_records()
        vault_df = pd.DataFrame(existing_data)
    except Exception:
        # If the sheet is empty or headers are missing, auto-fix it
        vault_sheet.append_row(["Document Name", "Type", "Link", "Date"])
        vault_df = pd.DataFrame(columns=["Document Name", "Type", "Link", "Date"])
        st.rerun()

    if not vault_df.empty:
        cols_config = {}
        if "Link" in vault_df.columns:
            cols_config["Link"] = st.column_config.LinkColumn("Document Link")
            
        st.dataframe(
            vault_df, 
            column_config=cols_config,
            use_container_width=True
        )
    else:
        st.write("No documents logged yet.")
    st.divider()
    # 2. LOG NEW DOCUMENT
    st.subheader("Log New Document")
    with st.form("vault_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        doc_name = col1.text_input("Document Name (e.g. Health Permit)")
        doc_type = col2.selectbox("Type", ["License", "Permit", "Receipt", "Tax Doc", "Contract", "Other"])
        
        doc_link = st.text_input("Paste Google Drive Link Here")
        
        if st.form_submit_button("Log to Vault"):
            if doc_name and doc_link:
                vault_sheet.append_row([
                    doc_name, 
                    doc_type, 
                    doc_link, 
                    str(pd.Timestamp.now())
                ])
                st.success(f"✅ Logged: {doc_name}")
            else:
                st.warning("Please enter a Name and a Link.")

# 🍳 RECIPE COSTING
elif menu_choice == "🍳 Recipe Costing":
    st.header("Recipe & Food Cost Calculator")
    
    tab_pantry, tab_calc = st.tabs(["🥕 Ingredient Pantry", "🧮 Pizza Builder"])
    
    # --- TAB 1: PANTRY (Manage Bulk Costs) ---
    with tab_pantry:
        st.subheader("Manage Raw Ingredients")
        st.info("💡 Enter your bulk items here. Example: 'Flour (50lb Bag)', Cost: $25.00.")
        
        # Form to add ingredient
        with st.form("ing_form", clear_on_submit=True):
            c1, c2, c3 = st.columns(3)
            name = c1.text_input("Ingredient Name (e.g. Mozzarella)")
            unit = c2.text_input("Unit Size (e.g. 1 lb, 1 oz, 1 can)")
            cost = c3.number_input("Bulk Cost ($)", min_value=0.01)
            
            if st.form_submit_button("Add to Pantry"):
                unit_cost = cost # Placeholder, in V2 we can add conversion logic
                ing_sheet.append_row([name, unit, cost, cost]) # Simple Append
                st.success(f"Added {name}")
                st.rerun()
        
        # Editable Table
        try:
            ing_data = ing_sheet.get_all_records()
            ing_df = pd.DataFrame(ing_data)
            
            if not ing_df.empty:
                edited_ing = st.data_editor(
                    ing_df, 
                    num_rows="dynamic",
                    use_container_width=True,
                    column_config={
                        "Bulk Cost": st.column_config.NumberColumn(format="$%.2f"),
                        "Unit Cost": st.column_config.NumberColumn("Calculated Unit Cost ($)", format="$%.4f")
                    }
                )
                
                if st.button("Save Pantry Changes"):
                    ing_sheet.clear()
                    ing_sheet.append_row(["Item Name", "Bulk Unit (e.g. 50lb)", "Bulk Cost", "Unit Cost"])
                    ing_sheet.append_rows(edited_ing.values.tolist())
                    st.success("Pantry Updated!")
        except:
            st.write("No ingredients yet.")
    # --- TAB 2: CALCULATOR (Build a Pizza) ---
    with tab_calc:
        st.subheader("Price Your Pizza")
        
        # 1. Select Ingredients
        st.markdown("#### Step 1: Add Components")
        
        # Fetch ingredients for dropdown
        try:
            ing_list = pd.DataFrame(ing_sheet.get_all_records())
            options = ing_list["Item Name"].tolist() if not ing_list.empty else []
        except:
            options = []
        
        if not options:
            st.warning("Go to the Pantry tab and add ingredients first!")
        else:
            if "recipe_items" not in st.session_state:
                st.session_state.recipe_items = []
            c1, c2, c3 = st.columns([2, 1, 1])
            sel_ing = c1.selectbox("Select Ingredient", options)
            sel_cost = 0.0
            if not ing_list.empty:
                row = ing_list[ing_list["Item Name"] == sel_ing].iloc[0]
                raw_cost = row.get("Unit Cost") if row.get("Unit Cost") else row.get("Bulk Cost")
                sel_cost = float(raw_cost) if raw_cost else 0.0
            qty = c2.number_input("Quantity Used", min_value=0.1, value=1.0, step=0.1)
            st.write(f"Unit Cost: ${sel_cost:.2f}")
            if c3.button("Add to Recipe"):
                line_cost = sel_cost * qty
                st.session_state.recipe_items.append({
                    "Ingredient": sel_ing,
                    "Qty": qty,
                    "Cost": line_cost
                })
            st.divider()
            st.markdown("#### Step 2: Cost Analysis")
            if st.session_state.recipe_items:
                recipe_df = pd.DataFrame(st.session_state.recipe_items)
                st.dataframe(recipe_df, use_container_width=True)
                total_food_cost = recipe_df["Cost"].sum()
                if st.button("Clear Recipe"):
                    st.session_state.recipe_items = []
                    st.rerun()
                st.divider()
                k1, k2, k3 = st.columns(3)
                k1.metric("🥗 Total Food Cost", f"${total_food_cost:.2f}")
                target_price = k2.number_input("Target Selling Price ($)", value=15.00)
                if target_price > 0:
                    fc_percent = (total_food_cost / target_price) * 100
                    profit = target_price - total_food_cost
                    color = "normal"
                    if fc_percent < 25: color = "normal"
                    elif fc_percent < 35: color = "off"
                    else: color = "inverse"
                    k3.metric("Profit Margin", f"${profit:.2f} ({int(100-fc_percent)}%)", delta_color=color)
                    st.progress(min(fc_percent/100, 1.0), text=f"Food Cost: {fc_percent:.1f}% (Aim for <30%)")
