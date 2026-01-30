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
    vault_sheet = get_worksheet("Vault_Index", ["Document Name", "Type", "File ID", "Upload Date"])
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

# 📊 DASHBOARD
if menu_choice == "📊 Dashboard":
    st.header("Business Health Overview")
    expenses = pd.DataFrame(ledger_sheet.get_all_records())
    sales = pd.DataFrame(sales_sheet.get_all_records())

    total_exp = 0.0
    total_rev = 0.0

    if not expenses.empty:
        expenses["Cost"] = pd.to_numeric(expenses["Cost"], errors="coerce").fillna(0)
        total_exp = expenses["Cost"].sum()

    if not sales.empty:
        sales["Revenue"] = pd.to_numeric(sales["Revenue"], errors="coerce").fillna(0)
        total_rev = sales["Revenue"].sum()

    c1, c2, c3 = st.columns(3)
    c1.metric("Total Sales", f"${total_rev:,.2f}")
    c2.metric("Total Expenses", f"${total_exp:,.2f}")
    c3.metric("Net Profit", f"${total_rev - total_exp:,.2f}")

    st.divider()
    if not expenses.empty:
        fig = px.pie(expenses, values="Cost", names="Category", title="Expense Breakdown", hole=0.4)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Log some expenses to see charts!")

# 📝 LOG EXPENSES
elif menu_choice == "📝 Log Expenses":
    st.header("Log New Expense")
    with st.form("expense_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        item = col1.text_input("Description")
        amount = col2.number_input("Cost ($)", min_value=0.01)
        category = st.selectbox(
            "Category", ["Inventory (Food)", "Equipment", "Labor", "Marketing", "Utilities", "Other"]
        )
        date = st.date_input("Date")

        if st.form_submit_button("Save Expense"):
            ledger_sheet.append_row([item, category, amount, str(date)])
            st.success(f"Saved: ${amount} for {item}")

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

# 🍕 MENU
elif menu_choice == "🍕 Menu Editor":
    st.header("Manage Pizza Menu")
    menu_df = pd.DataFrame(menu_sheet.get_all_records())
    edited_menu = st.data_editor(menu_df, num_rows="dynamic")

    if st.button("Update Live Menu"):
        menu_sheet.clear()
        menu_sheet.append_row(["Item Name", "Description", "Price"])
        if not edited_menu.empty:
            menu_sheet.append_rows(edited_menu.values.tolist())
        st.success("Menu updated on website!")

# 🗄️ VAULT (Direct to Drive)
elif menu_choice == "🗄️ Document Vault":
    st.header("Secure Document Vault")
    st.write("Uploads go directly to your Google Drive folder.")

    uploaded_file = st.file_uploader("Upload Permit, License, or Receipt")
    doc_type = st.selectbox(
        "Document Type", ["Health Permit", "Business License", "Tax Document", "Insurance", "Receipt"]
    )

    if st.button("Upload to Drive"):
        if uploaded_file:
            with st.spinner("Encrypting and Uploading..."):
                try:
                    file_metadata = {"name": f"[{doc_type}] {uploaded_file.name}", "parents": [VAULT_FOLDER_ID]}
                    media = MediaIoBaseUpload(io.BytesIO(uploaded_file.getvalue()), mimetype=uploaded_file.type)
                    file = drive_service.files().create(body=file_metadata, media_body=media, fields="id").execute()
                    vault_sheet.append_row(
                        [uploaded_file.name, doc_type, file.get("id"), str(pd.Timestamp.now())]
                    )
                    st.success("✅ File uploaded successfully!")
                except Exception as e:
                    st.error(f"Upload failed: {e}")
        else:
            st.warning("Please choose a file first.")
