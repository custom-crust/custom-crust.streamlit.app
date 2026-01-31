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

# --- CUSTOM CSS (FULL TEXTURE) ---
st.markdown("""
<style>
    /* 1. Main Background: Dark Mesh/Leather Texture */
    .stApp {
        background-color: #0e0e0e;
        background-image: radial-gradient(#262626 1px, transparent 0);
        background-size: 20px 20px;
    }
    
    /* 2. Sidebar: Same Texture, Subtle Border */
    [data-testid="stSidebar"] {
        background-color: #0e0e0e;
        background-image: radial-gradient(#262626 1px, transparent 0);
        background-size: 20px 20px;
        border-right: 1px solid #333;
    }
    /* 3. Metric Cards (Floating Effect) */
    [data-testid="stMetric"] {
        background: linear-gradient(145deg, #1e1e1e, #141414);
        padding: 15px 20px;
        border-radius: 12px;
        border: 1px solid #333;
        box-shadow: 4px 4px 10px rgba(0,0,0,0.5);
    }
    /* 4. Remove default Plotly white/black backgrounds */
    .js-plotly-plot .plotly .main-svg {
        background-color: rgba(0,0,0,0) !important;
    }
    /* 5. Custom Font Styling */ h1, h2, h3, p, div, span { color: #E0E0E0 !important; }

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
        except Exception:
            ws = sheet.add_worksheet(title=name, rows="100", cols="10")
            ws.append_row(headers)
            return ws

    ledger_sheet = get_worksheet("Ledger", ["Item", "Category", "Cost", "Date"])
    sales_sheet = get_worksheet("Sales", ["Event", "Type", "Revenue", "Date"])
    menu_sheet = get_worksheet("Menu", ["Item Name", "Description", "Price"])
    vault_sheet = get_worksheet("Vault_Index", ["Document Name", "Type", "Link", "Upload Date"])
except Exception as e:
    st.error(f"📉 Sheet Connection Failed: {e}")
    st.stop()

# --- 4. SIDEBAR NAVIGATION ---
st.sidebar.title("🍕 Custom Crust HQ")
st.sidebar.markdown("---")
menu_choice = st.sidebar.radio(
    "Command Center",
    ["📊 Dashboard", "📝 Log Expenses", "💰 Sales & Revenue", "🍕 Menu Editor", "🗄️ Document Vault"],
)
st.sidebar.markdown("---")

# --- 5. PAGE LOGIC ---

# 📊 DASHBOARD (Upgraded)
if menu_choice == "📊 Dashboard":
    st.header("Business Health Overview")
    
    # Load Data
    expenses = pd.DataFrame(ledger_sheet.get_all_records())
    sales = pd.DataFrame(sales_sheet.get_all_records())
    
    # Clean Data
    total_exp = 0.0
    total_rev = 0.0
    
    if not expenses.empty:
        expenses['Cost'] = pd.to_numeric(expenses['Cost'], errors='coerce').fillna(0)
        total_exp = expenses['Cost'].sum()
        
    if not sales.empty:
        sales['Revenue'] = pd.to_numeric(sales['Revenue'], errors='coerce').fillna(0)
        total_rev = sales['Revenue'].sum()
    
    # Top Metrics
    c1, c2, c3 = st.columns(3)
    c1.metric("Total Sales", f"${total_rev:,.2f}")
    c2.metric("Total Expenses", f"${total_exp:,.2f}")
    net_color = "normal" if (total_rev - total_exp) >= 0 else "inverse"
    c3.metric("Net Profit", f"${total_rev - total_exp:,.2f}", delta_color=net_color)
    
    st.divider()
    
    # Charts Area
    col_charts1, col_charts2 = st.columns(2)
    
    with col_charts1:
        st.subheader("💸 Expense Breakdown")
        if not expenses.empty and total_exp > 0:
            fig_exp = px.pie(expenses, values='Cost', names='Category', hole=0.4)
            st.plotly_chart(fig_exp, use_container_width=True)
        else:
            st.info("Log expenses to see the breakdown.")
            
    with col_charts2:
        st.subheader("💰 Revenue Sources")
        if not sales.empty and total_rev > 0:
            fig_rev = px.pie(sales, values='Revenue', names='Type', hole=0.4)
            st.plotly_chart(fig_rev, use_container_width=True)
        else:
            st.info("Log sales to see the breakdown.")

# 📝 LOG EXPENSES (Updated Categories)
elif menu_choice == "📝 Log Expenses":
    st.header("Log New Expense")
    with st.form("expense_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        item = col1.text_input("Description")
        amount = col2.number_input("Cost ($)", min_value=0.01)
        
        # Expanded Categories for Mobile Pizzeria
        category = st.selectbox("Category", [
            "Inventory (Food & Drink)",
            "Equipment & Supplies", 
            "Vehicle & Fuel",             # Gas for trailer/truck
            "POS & Technology",           # Toast subscription, Website
            "Transaction Fees",           # Credit Card processing fees
            "Legal & Admin Fees",         # LLC reg, Bank fees, Permits
            "Insurance",
            "Labor & Wages",
            "Marketing & Ads",
            "Event Fees & Rent",          # Cost to park at a venue
            "Repairs & Maintenance",
            "Utilities (Propane/Electric)",
            "Other"
        ])
        
        date = st.date_input("Date")
        
        if st.form_submit_button("Save Expense"):
            ledger_sheet.append_row([item, category, amount, str(date)])
            st.success(f"Saved: ${amount} for {item} ({category})")

# 💰 SALES
elif menu_choice == "💰 Sales & Revenue":
    st.header("Track Sales")
    tab1, tab2 = st.tabs(["Log Sale", "View History"])

    with tab1:
        with st.form("sales_form", clear_on_submit=True):
            event = st.text_input("Event Name / Location")
            rev = st.number_input("Total Revenue ($)", min_value=0.01)
            sType = st.selectbox("Type", ["Daily Service", "Catering Event", "Online Order"])
            sDate = st.date_input("Date")

            if st.form_submit_button("Log Revenue"):
                sales_sheet.append_row([event, sType, rev, str(sDate)])
                st.success(f"💰 Cha-ching! Logged ${rev}")

    with tab2:
        df_sales = pd.DataFrame(sales_sheet.get_all_records())
        if not df_sales.empty:
            st.dataframe(df_sales, use_container_width=True)
        else:
            st.info("No sales history found.")

# 🍕 MENU EDITOR (Fixed)
elif menu_choice == "🍕 Menu Editor":
    st.header("Manage Pizza Menu")

    # 1. Load Data with Safety Check
    try:
        existing_data = menu_sheet.get_all_records()
        menu_df = pd.DataFrame(existing_data)
    except Exception:
        # Auto-fix empty sheet
        menu_sheet.append_row(["Item Name", "Description", "Price"])
        menu_df = pd.DataFrame(columns=["Item Name", "Description", "Price"])
        st.rerun()

    # 2. Editable Table
    edited_menu = st.data_editor(
        menu_df, 
        num_rows="dynamic",
        use_container_width=True,
        key="menu_editor"
    )

    # 3. Save Button
    if st.button("Update Live Menu"):
        with st.spinner("Saving changes..."):
            menu_sheet.clear()
            # Add headers back
            menu_sheet.append_row(["Item Name", "Description", "Price"])
            # Write the new data
            if not edited_menu.empty:
                menu_sheet.append_rows(edited_menu.values.tolist())
            st.success("✅ Menu updated on website!")

# 🗄️ VAULT (Clean & Robust)
elif menu_choice == "🗄️ Document Vault":
    st.header("Secure Document Vault")
    
    # 1. VIEW EXISTING DOCS (With Crash Protection)
    try:
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
