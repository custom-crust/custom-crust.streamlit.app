import streamlit as st
import pandas as pd
import plotly.express as px
import gspread
from google.oauth2.service_account import Credentials
import json
import io
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload

# 1. SETUP GOOGLE CONNECTION
def get_gspread_client():
    try:
        # --- THE FIX: Direct assignment (No json.loads needed) ---
        info = st.secrets["GCP_SERVICE_ACCOUNT"]
        # ---------------------------------------------------------

        scope = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
        creds = Credentials.from_service_account_info(info, scopes=scope)
        return gspread.authorize(creds)
    except Exception as e:
        st.error(f"Connection Error: {e}")
        st.stop()

# Drive service helper
@st.cache_resource
def get_drive_service():
    try:
        raw = st.secrets.get("GCP_SERVICE_ACCOUNT")
        if raw is None:
            return None
        if isinstance(raw, str):
            info = st.secrets["GCP_SERVICE_ACCOUNT"]
        else:
            info = raw
        # normalize private_key like above
        if isinstance(info, dict) and "private_key" in info and isinstance(info["private_key"], str):
            pk = info["private_key"]
            while "\\\\n" in pk:
                pk = pk.replace("\\\\n", "\\n")
            pk = pk.replace("\\n", "\n")
            pk = pk.replace("\\r\\n", "\n").replace("\\r", "\n")
            pk = pk.replace("\r\n", "\n").replace("\r", "\n")
            info["private_key"] = pk.strip()
        creds = Credentials.from_service_account_info(
            info, scopes=['https://www.googleapis.com/auth/drive']
        )
        return build("drive", "v3", credentials=creds)
    except Exception as e:
        st.error("Drive Connection Offline: Please check Secrets and Drive sharing.")
        return None

# Connect to your specific sheet
client = get_gspread_client()
try:
    sheet = client.open("Custom Crust Kitchen - Master Ledger")
    ledger_sheet = sheet.worksheet("Ledger")
    menu_sheet = sheet.worksheet("Menu")
    sales_sheet = sheet.worksheet("Sales")
    vault_sheet = sheet.worksheet("Vault")
except Exception as e:
    st.error(
        f"Sheet Error: {e}. Ensure the Google Sheet is shared with your Service Account email."
    )
    st.stop()

# 2. BRANDING
st.set_page_config(page_title="Custom Crust Kitchen LLC", layout="wide", page_icon="🍕")
st.title("🍕 Custom Crust Kitchen LLC: Command Center")

# 3. NAVIGATION
menu_choice = st.sidebar.radio("Go To:", ["Dashboard", "Log Expenses", "Sales & Catering", "Menu Management", "Vault"])

# 4. DASHBOARD
if menu_choice == "Dashboard":
    st.header("Financial Overview")
    ledger_data = pd.DataFrame(ledger_sheet.get_all_records())
    sales_data = pd.DataFrame(sales_sheet.get_all_records())
    
    c1, c2, c3 = st.columns(3)
    total_exp = ledger_data["Cost"].sum() if not ledger_data.empty else 0
    total_rev = sales_data["Revenue"].sum() if not sales_data.empty else 0
    
    c1.metric("Total Expenses", f"${total_exp:,.2f}")
    c2.metric("Total Revenue", f"${total_rev:,.2f}")
    c3.metric("Net Cash Flow", f"${total_rev - total_exp:,.2f}")

    st.divider()
    if not ledger_data.empty:
        fig_pie = px.pie(ledger_data, values='Cost', names='Category', hole=0.5, title="Expense Distribution")
        st.plotly_chart(fig_pie, use_container_width=True)

# 5. LOG EXPENSES
elif menu_choice == "Log Expenses":
    st.header("Log Business Expenses")
    with st.form("exp_form", clear_on_submit=True):
        name = st.text_input("Item")
        val = st.number_input("Cost ($)", min_value=0.0)
        cat = st.selectbox("Category", ["Supplies", "Equipment", "Asset", "Maintenance", "Marketing", "Legal"])
        dt = st.date_input("Date")
        if st.form_submit_button("Log to Google"):
            ledger_sheet.append_row([name, cat, val, str(dt)])
            st.success("Saved!")

# 6. SALES & CATERING
if menu_choice == "Sales & Catering":
    st.header("Revenue Tracking")
    # Log New Sales
    with st.form("sales_log", clear_on_submit=True):
        evt = st.text_input("Event/Location Name")
        rev_amt = st.number_input("Revenue ($)", min_value=0.0)
        stype = st.selectbox("Type", ["Daily Sales", "Catering (Flat Rate)"])
        sdate = st.date_input("Date")
        if st.form_submit_button("Log Revenue to Google"):
            sales_sheet.append_row([evt, stype, rev_amt, str(sdate)])
            st.success(f"Logged ${rev_amt} for {evt}")
    
    st.divider()
    st.subheader("Recent Sales History")
    sales_data = pd.DataFrame(sales_sheet.get_all_records())
    if not sales_data.empty:
        st.dataframe(sales_data, use_container_width=True)
    else:
        st.info("No sales recorded yet. Use the form above to log your first sale!")

# 7. MENU MANAGEMENT
elif menu_choice == "Menu Management":
    st.header("Menu Editor")
    menu_data = pd.DataFrame(menu_sheet.get_all_records())
    edited_menu = st.data_editor(menu_data, num_rows="dynamic")
    if st.button("Save Menu Changes"):
        menu_sheet.update([edited_menu.columns.values.tolist()] + edited_menu.values.tolist())
        st.success("Menu Updated!")

# 8. THE VAULT
elif menu_choice == "Vault":
    st.header("The Vault")
    st.write("Secure access to business documents.")
    try:
        vault_data = pd.DataFrame(vault_sheet.get_all_records())

        # File uploader + Drive upload
        uploaded_file = st.file_uploader("Choose a file to upload to Drive")
        if uploaded_file is not None:
            service = get_drive_service()
            if service is None:
                st.error("Drive service not available.")
            else:
                try:
                    file_bytes = uploaded_file.getvalue()
                    mime = uploaded_file.type or "application/octet-stream"
                    media = MediaIoBaseUpload(
                        io.BytesIO(file_bytes), mimetype=mime, resumable=False
                    )
                    metadata = {"name": uploaded_file.name}
                    folder_id = st.secrets.get("DRIVE_FOLDER_ID")
                    if folder_id:
                        metadata["parents"] = [folder_id]
                    f = (
                        service.files()
                        .create(body=metadata, media_body=media, fields="id,webViewLink")
                        .execute()
                    )
                    file_id = f.get("id")
                    view_link = f.get("webViewLink") or f"https://drive.google.com/file/d/{file_id}/view"
                    # Append to the Vault sheet: [Document Name, Link]
                    vault_sheet.append_row([uploaded_file.name, view_link])
                    st.success("Upload complete ✅")
                    st.markdown(f"[Open in Drive]({view_link})", unsafe_allow_html=True)
                except Exception as e:
                    st.error(f"Upload failed: {e}")

        if not vault_data.empty:
            # Render list of documents
            for index, row in vault_data.iterrows():
                name = row.get('Document Name') if 'Document Name' in row else None
                link = row.get('Link') if 'Link' in row else None
                if name and link:
                    st.markdown(f"- [{name}]({link})")
        else:
            st.warning("The Vault is empty. Add 'Document Name' and 'Link' to your Google Sheet.")
    except Exception as e:
        st.error(f"Error loading Vault: {e}")
