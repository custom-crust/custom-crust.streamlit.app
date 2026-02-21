import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from streamlit_gsheets import GSheetsConnection
import os
import re

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="CCK Dashboard", layout="wide", page_icon="🍕")
SHEET_URL = "https://docs.google.com/spreadsheets/d/1yqbd35J140KWT7ui8Ggqn68_OfGXb1wofViJRcSgZBU/edit"

# --- 2. STYLING ---
st.markdown("""
    <style>
    .stApp {
        background-color: #0E1117;
        background-image: url("https://www.transparenttextures.com/patterns/cubes.png");
        background-blend-mode: overlay;
        background-attachment: fixed;
    }
    section[data-testid="stSidebar"] {display: none;}
    .block-container {padding-top: 3rem; padding-bottom: 5rem;}

    .stTabs [data-baseweb="tab-list"] {justify-content: center; gap: 20px; border-bottom: 1px solid #333;}
    .stTabs [data-baseweb="tab"] {background-color: transparent; color: #888; font-weight: 600; font-size: 1rem;}
    .stTabs [aria-selected="true"] {color: #4CAF50 !important; border-bottom: 2px solid #4CAF50 !important;}

    div.stMetric, div.stDataFrame, div[data-testid="stForm"] {
        background-color: #161b22; border: 1px solid #30363d;
        padding: 20px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    }
    div.stButton > button {
        background-color: #238636; color: white; border-radius: 6px;
        font-weight: bold; height: 45px; width: 100%; text-transform: uppercase;
    }
    h1, h3, h4, p, label {color: #e6edf3; font-family: 'Segoe UI', sans-serif;}
    div[data-testid="stMetricValue"] {color: #ffffff !important;}

    [data-testid="stElementToolbar"] {display: none;}
    
    /* --- HIDE STREAMLIT HEADER ANCHORS --- */
    [data-testid="stHeaderAction"] {
        display: none !important;
        visibility: hidden !important;
    }

    .vault-link {
        font-size: 18px; color: #58a6ff; text-decoration: none;
        padding: 10px; display: block; border-bottom: 1px solid #30363d;
    }
    .vault-link:hover {color: #4CAF50; background-color: #1c2128;}
    </style>
""", unsafe_allow_html=True)

# --- 3. DATA HELPERS ---
def clean_currency(value):
    if pd.isna(value) or value == "": return 0.0
    if isinstance(value, (int, float)): return float(value)
    s = str(value).replace('$', '').replace(',', '').strip()
    try: return float(s) if s else 0.0
    except: return 0.0

def format_df(df):
    if df.empty: return df
    display_df = df.copy()
    
    # Capitalize Headers
    display_df.columns = [col.strip().title() for col in display_df.columns]

    # --- CLEANING: REMOVE REPEATED HEADER ROWS ---
    # This checks if the first column's value matches the header name (case-insensitive)
    if not display_df.empty:
        first_col = display_df.columns[0]
        display_df = display_df[display_df[first_col].astype(str).str.strip().str.lower() != first_col.strip().lower()]

    money_cols = ['Cost', 'Amount', 'Price', 'Revenue', 'Total', 'Debit', 'Credit', 'Balance', 'Value', 'Unit Cost', 'Recipe Cost', 'Profit', 'Menu Price', 'Line Total']
    for col in display_df.columns:
        if col in money_cols: display_df[col] = display_df[col].apply(clean_currency)

    for col in display_df.columns:
        if 'Date' in col or 'Updated' in col:
            display_df[col] = pd.to_datetime(display_df[col], errors='coerce')

    return display_df

def show_table(df):
    if df.empty: return
    
    # Create a copy for display
    df_display = df.copy()
    col_config = {}

    # 1. Format Dates
    for col in df_display.columns:
        if "Date" in col or "Updated" in col:
            col_config[col] = st.column_config.DateColumn(col, format="MM/DD/YYYY")
    
    # 2. STRING FORMATTING FOR MONEY
    money_cols = ['Cost', 'Price', 'Amount', 'Revenue', 'Total', 'Balance', 'Profit', 'Debit', 'Credit']
    for col in df_display.columns:
        if any(x in col for x in money_cols):
            df_display[col] = df_display[col].apply(lambda x: f"${x:,.2f}" if isinstance(x, (int, float)) else x)
        elif "Margin" in col or "%" in col:
             df_display[col] = df_display[col].apply(lambda x: f"{x:.1f}%" if isinstance(x, (int, float)) else x)

    st.dataframe(df_display, use_container_width=True, hide_index=True, column_config=col_config)

# --- 4. GOOGLE SHEETS FUNCTIONS ---
def get_connection():
    return st.connection("gsheets", type=GSheetsConnection)

def load_data():
    data = {}
    tabs = {
        "assets": "Assets", "expenses": "Ledger", "sales": "Sales",
        "menu": "Menu", "vault": "Vault_Index", "debt": "Debt_Log",
        "ingredients": "Ingredients", "recipes": "Recipes", "vendors": "Vendors",
        "bank_log": "Bank_Log"
    }
    
    conn = get_connection()
    
    for key, sheet_name in tabs.items():
        try:
            df = conn.read(spreadsheet=SHEET_URL, worksheet=sheet_name, ttl=5)
            df.columns = [str(c).strip().lower() for c in df.columns]
            if 'date' in df.columns:
                df['date'] = pd.to_datetime(df['date'], errors='coerce')
            data[key] = df
        except Exception as e:
            st.error(f"⚠️ Error loading tab '{sheet_name}': {e}")
            data[key] = pd.DataFrame()
            
    return data, None

def update_sheet(sheet_name, df):
    try:
        conn = get_connection()
        conn.update(spreadsheet=SHEET_URL, worksheet=sheet_name, data=df)
        return True
    except Exception as e:
        st.error(f"Error saving to {sheet_name}: {e}")
        return False

# --- 5. MAIN APP ---
def main():
    if 'quote_cart' not in st.session_state: st.session_state.quote_cart = []

    data, error = load_data()
    assets, expenses, sales = data['assets'], data['expenses'], data['sales']
    menu, vault, debt = data['menu'], data['vault'], data['debt']
    ingredients, recipes, vendors = data['ingredients'], data['recipes'], data['vendors']
    bank_log = data['bank_log']

    c1, c2, c3 = st.columns([3, 1, 3])
    with c2:
        if os.path.exists("logo.png"): st.image("logo.png", width=200)
        else: st.markdown("<h1 style='text-align: center; font-size: 80px;'>🍕 CCK</h1>", unsafe_allow_html=True)

    if error: st.error(f"🚨 Connection Error: {error}")

    tabs = st.tabs(["📊 Dashboard", "📉 P&L", "🏦 Banking", "💰 Sales", "📝 Expenses", "📉 Debt", "📅 Quote", "🍕 Menu", "📂 Tools"])

    # --- SHARED CALCS ---
    northern_bank_bal = 0.0
    if not assets.empty:
        for index, row in assets.iterrows():
            if "northern" in str(row.get('account name','')).lower():
                northern_bank_bal += clean_currency(row.get('balance', 0))

    if not expenses.empty:
        for index, row in expenses.iterrows():
            pay_method = str(row.get('paid via', '')).lower()
            val = clean_currency(row.get('cost') or row.get('amount') or 0)
            if "northern" in pay_method or "bank" in pay_method:
                northern_bank_bal -= val

    if not bank_log.empty:
        for index, row in bank_log.iterrows():
            b_type = str(row.get('type') or row.get('transaction type') or row.get('from account') or '').lower()
            val = clean_currency(row.get('amount', 0))
            if "deposit" in b_type: northern_bank_bal += val
            elif "withdraw" in b_type: northern_bank_bal -= val

    borrowed, repaid = 0.0, 0.0
    if not debt.empty:
        for index, row in debt.iterrows():
            t_type = str(row.get('transaction type','')).lower()
            amt = clean_currency(row.get('amount') or 0)
            if "borrow" in t_type: borrowed += amt
            elif "repay" in t_type: repaid += amt
    current_debt = borrowed - repaid

    tot_exp = sum(clean_currency(row.get('cost') or row.get('amount') or 0) for i, row in expenses.iterrows()) if not expenses.empty else 0
    tot_sale = sum(clean_currency(row.get('revenue') or row.get('amount') or 0) for i, row in sales.iterrows()) if not sales.empty else 0

    # Net Position
    net_position = northern_bank_bal - current_debt

    # Weekly P&L Logic
    now = datetime.now()
    start_wk = (now - timedelta(days=now.weekday())).replace(hour=0,minute=0,second=0,microsecond=0)

    wk_sales, wk_exp = 0.0, 0.0
    if not sales.empty:
        df_s = sales.copy()
        if 'date' in df_s.columns:
            rev_col = next((c for c in ['revenue','amount'] if c in df_s.columns), None)
            if rev_col:
                wk_sales = df_s[df_s['date'] >= start_wk][rev_col].apply(clean_currency).sum()

    if not expenses.empty:
        df_e = expenses.copy()
        if 'date' in df_e.columns:
            cost_col = next((c for c in ['cost','amount'] if c in df_e.columns), None)
            if cost_col:
                wk_exp = df_e[df_e['date'] >= start_wk][cost_col].apply(clean_currency).sum()

    wk_profit = wk_sales - wk_exp

    # --- TAB 1: DASHBOARD ---
    with tabs[0]:
        st.write("##")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("🏦 Northern Bank", f"${northern_bank_bal:,.2f}")
        c2.metric("🔴 Current Debt", f"${current_debt:,.2f}")
        c3.metric("💵 Total Sales", f"${tot_sale:,.2f}")
        c4.metric("💸 Total Expenses", f"${tot_exp:,.2f}")
        st.write("---")

        c1, c2 = st.columns(2)
        with c1:
            st.markdown("#### 💸 Expenses")
            if not expenses.empty:
                df = expenses.copy()
                cost_col = next((c for c in ['cost','amount'] if c in df.columns), None)
                if cost_col:
                    df['clean'] = df[cost_col].apply(clean_currency)
                    if df['clean'].sum() > 0:
                        fig = px.pie(df, values='clean', names='category', hole=0.6, color_discrete_sequence=px.colors.qualitative.Pastel)
                        # CLEAN HOVER & FIX PADDING
                        fig.update_traces(hovertemplate="<b>%{label}</b><br>Amount: $%{value:,.2f}<br>%{percent}")
                        fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="#b0b0b0", height=300, margin=dict(t=20, b=20, l=20, r=20))
                        st.plotly_chart(fig, use_container_width=True)
        with c2:
            st.markdown("#### 💰 Sales Source")
            if not sales.empty:
                df_s = sales.copy()
                rev_col = next((c for c in ['revenue','amount'] if c in df_s.columns), None)
                cat_col = 'category' if 'category' in df_s.columns else 'event'
                if rev_col:
                    df_s['clean_rev'] = df_s[rev_col].apply(clean_currency)
                    if df_s['clean_rev'].sum() > 0:
                        figS = px.pie(df_s, values='clean_rev', names=cat_col, hole=0.6, color_discrete_sequence=px.colors.qualitative.Set3)
                        # CLEAN HOVER & FIX PADDING
                        figS.update_traces(hovertemplate="<b>%{label}</b><br>Amount: $%{value:,.2f}<br>%{percent}")
                        figS.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="#b0b0b0", height=300, margin=dict(t=20, b=20, l=20, r=20))
                        st.plotly_chart(figS, use_container_width=True)

    # --- TAB 2: P&L ---
    with tabs[1]:
        st.write("##")
        st.markdown(f"""
        <div style="text-align: center; padding: 20px; background-color: #161b22; border-radius: 10px; border: 1px solid #30363d; margin-bottom: 20px;">
            <h3 style="margin:0; color: #8b949e;">Net Position (Liquid Assets - Debt)</h3>
            <div style="margin:0; font-size: 3rem; font-weight: bold; color: {'#da3633' if net_position < 0 else '#238636'};">
                ${net_position:,.2f}
            </div>
            <p style="color: #8b949e;">Goal: Get this number to $0.00 (Debt Free)</p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("### 📅 This Week's Performance (Mon-Sun)")
        c1, c2, c3 = st.columns(3)
        c1.metric("Incoming (Sales)", f"${wk_sales:,.2f}")
        c2.metric("Outgoing (Expenses)", f"${wk_exp:,.2f}")
        c3.metric("Weekly Net Profit", f"${wk_profit:,.2f}", delta_color="normal")

        if wk_sales > 0 or wk_exp > 0:
            chart_data = pd.DataFrame({
                "Type": ["Sales (In)", "Expenses (Out)"],
                "Amount": [wk_sales, wk_exp]
            })
            fig = px.bar(chart_data, x="Type", y="Amount", color="Type",
                         color_discrete_map={"Sales (In)": "#238636", "Expenses (Out)": "#da3633"},
                         title="This Week: Money In vs. Money Out")
            fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="#b0b0b0")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No activity recorded for this week yet. Go sell some pizza!")

    # --- TAB 3: BANKING ---
    with tabs[2]:
        st.write("##")
        st.markdown(f"### 🏦 Northern Bank Balance: **${northern_bank_bal:,.2f}**")
        c1, c2 = st.columns(2)
        with c1:
            with st.form("bank_op"):
                st.markdown("#### Transaction")
                b_type = st.selectbox("Type", ["Deposit", "Withdrawal"])
                b_amt = st.number_input("Amount ($)", 0.0)
                b_desc = st.text_input("Description")
                b_date = st.date_input("Date", datetime.today(), format="MM/DD/YYYY")
                if st.form_submit_button("Submit"):
                    new_row = pd.DataFrame([{"type": b_type, "amount": b_amt, "description": b_desc, "date": b_date.strftime("%Y-%m-%d")}])
                    updated_df = pd.concat([bank_log, new_row], ignore_index=True)
                    if update_sheet("Bank_Log", updated_df): st.success("Logged!"); st.rerun()
        with c2:
            st.markdown("#### Activity Log")
            if not bank_log.empty:
                df_display = format_df(bank_log)
                # --- HIDE UNWANTED COLUMNS ---
                unwanted = ["From Account", "To Account", "Notes"]
                df_display = df_display.drop(columns=[c for c in unwanted if c in df_display.columns])
                show_table(df_display)

    # --- TAB 4: SALES (RESTORED METRICS) ---
    with tabs[3]:
        st.write("##")
        c1, c2 = st.columns([1, 2])
        with c1:
            st.markdown("### Log Sale")
            with st.form("sale"):
                cat = st.selectbox("Category", ["Catering", "Food Festival", "Street Service / Truck", "Online Order", "Other"])
                desc = st.text_input("Event Name")
                amt = st.number_input("Revenue ($)", 0.0)
                date = st.date_input("Date", datetime.today(), format="MM/DD/YYYY")
                if st.form_submit_button("Log Sale"):
                    new_row = pd.DataFrame([{"category": cat, "event": desc, "revenue": amt, "date": date.strftime("%Y-%m-%d")}])
                    updated_df = pd.concat([sales, new_row], ignore_index=True)
                    if update_sheet("Sales", updated_df): st.success("Logged!"); st.rerun()

        with c2:
            # --- SALES DASHBOARD LOGIC ---
            ytd_val, mtd_val, week_val, last_week_val = 0.0, 0.0, 0.0, 0.0
            if not sales.empty:
                df_s = sales.copy()
                rev = next((c for c in ['revenue','amount'] if c in df_s.columns), None)
                if rev:
                    df_s['cl'] = df_s[rev].apply(clean_currency)
                    now = datetime.now()
                    start_wk = (now - timedelta(days=now.weekday())).replace(hour=0,minute=0,second=0,microsecond=0)
                    
                    ytd_val = df_s[df_s['date'] >= datetime(now.year,1,1)]['cl'].sum()
                    mtd_val = df_s[df_s['date'] >= datetime(now.year,now.month,1)]['cl'].sum()
                    week_val = df_s[df_s['date'] >= start_wk]['cl'].sum()
                    last_week_val = df_s[(df_s['date'] >= start_wk-timedelta(7)) & (df_s['date'] < start_wk)]['cl'].sum()
            
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("📅 YTD Sales", f"${ytd_val:,.0f}")
            m2.metric("🗓️ MTD Sales", f"${mtd_val:,.0f}")
            m3.metric("🟢 This Week", f"${week_val:,.0f}")
            m4.metric("🟡 Last Week", f"${last_week_val:,.0f}")
            st.write("---")
            if not sales.empty: show_table(format_df(sales))

    # --- TAB 5: EXPENSES ---
    with tabs[4]:
        st.write("##")
        with st.form("exp"):
            c1, c2, c3, c4, c5 = st.columns(5)
            item = c1.text_input("Item")
            cost = c2.number_input("Cost ($)", 0.0)
            cat = c3.selectbox("Category", ["Ingredients & Supplies", "Fuel & Propane", "Smallwares & Utensils", "Equipment", "Equipment Maintenance", "Licensing & Legal", "Rent", "Labor", "Startup Asset / Initial Investment", "Other"])
            pay = c4.selectbox("Paid Via", ["Northern Bank Debit Card", "Cash / Undeposited", "Owner Personal Funds / Equity"])
            dt = c5.date_input("Date", datetime.today(), format="MM/DD/YYYY")
            if st.form_submit_button("Save"):
                new_row = pd.DataFrame([{"item": item, "cost": cost, "category": cat, "paid via": pay, "date": dt.strftime("%Y-%m-%d")}])
                updated_df = pd.concat([expenses, new_row], ignore_index=True)
                if update_sheet("Ledger", updated_df): st.success("Saved!"); st.rerun()
        if not expenses.empty: show_table(format_df(expenses))

    # --- TAB 6: DEBT ---
    with tabs[5]:
        st.write("##")
        c1, c2, c3 = st.columns(3)
        c1.metric("🔴 Borrowed", f"${borrowed:,.2f}")
        c2.metric("🟢 Paid Off", f"${repaid:,.2f}")
        c3.metric("🟡 Remaining", f"${current_debt:,.2f}")
        st.write("---")
        with st.form("debt"):
            c1, c2, c3, c4 = st.columns(4)
            name = c1.text_input("Name")
            dtype = c2.selectbox("Type", ["Repay", "Borrow"])
            amt = c3.number_input("Amount ($)", 0.0)
            dt = c4.date_input("Date", datetime.today(), format="MM/DD/YYYY")
            if st.form_submit_button("Log"):
                new_row = pd.DataFrame([{"loan name": name, "transaction type": dtype, "amount": amt, "date": dt.strftime("%Y-%m-%d")}])
                updated_df = pd.concat([debt, new_row], ignore_index=True)
                if update_sheet("Debt_Log", updated_df): st.success("Logged!"); st.rerun()
        if not debt.empty: show_table(format_df(debt))

    # --- TAB 7: QUOTE BUILDER ---
    with tabs[6]:
        st.write("##")
        st.markdown("### 📝 Event Quote Builder")
        c1, c2 = st.columns(2)
        with c1:
            fee_amt = st.number_input("Flat Event Fee ($)", 0.0)
            if st.button("Add Event Fee"):
                st.session_state.quote_cart.append({"Item": "Event Fee", "Price": fee_amt, "Qty": 1, "Line Total": fee_amt})
                st.rerun()
        with c2:
            trav_amt = st.number_input("Travel Fee ($)", 0.0)
            if st.button("Add Travel Fee"):
                st.session_state.quote_cart.append({"Item": "Travel Fee", "Price": trav_amt, "Qty": 1, "Line Total": trav_amt})
                st.rerun()
        st.write("---")
        c_add1, c_add2, c_add3 = st.columns([3, 1, 1])
        if not menu.empty:
            m_name = next((c for c in menu.columns if 'item' in c or 'name' in c), None)
            m_price = next((c for c in menu.columns if 'price' in c or 'cost' in c), None)
            sel = c_add1.selectbox("Item", menu[m_name].tolist() if m_name else [])
            qty = c_add2.number_input("Qty", 1, 500, 10)
            if c_add3.button("Add"):
                row = menu[menu[m_name] == sel].iloc[0]
                pr = clean_currency(row[m_price]) if m_price else 0.0
                st.session_state.quote_cart.append({"Item": sel, "Price": pr, "Qty": qty, "Line Total": pr*qty})
                st.rerun()

        if st.session_state.quote_cart:
            cart = pd.DataFrame(st.session_state.quote_cart)
            show_table(format_df(cart))
            st.metric("⭐ TOTAL QUOTE", f"${cart['Line Total'].sum():,.2f}")
            if st.button("Clear"): st.session_state.quote_cart = []; st.rerun()

    # --- TAB 8: MENU ---
    with tabs[7]:
        st.write("##")
        if not menu.empty: show_table(format_df(menu))
        with st.expander("Add Item"):
            with st.form("menu"):
                name = st.text_input("Name"); price = st.number_input("Price", 0.0)
                if st.form_submit_button("Add"):
                    new_row = pd.DataFrame([{"item name": name, "price": price}])
                    updated_df = pd.concat([menu, new_row], ignore_index=True)
                    if update_sheet("Menu", updated_df): st.success("Added!"); st.rerun()

    # --- TAB 9: TOOLS ---
    with tabs[8]:
        st.write("##")
        sub1, sub2, sub3, sub4 = st.tabs(["💰 Profit", "🤝 Vendors", "🏦 Assets", "🗄️ Vault"])

        with sub1:
            if ingredients.empty or recipes.empty or menu.empty:
                st.info("⚠️ Need Ingredients, Recipes, and Menu data to calculate profit.")
            else:
                try:
                    # 1. Calculate Ingredient Unit Costs
                    df_ing = ingredients.copy()
                    c_cost = next((c for c in df_ing.columns if 'cost' in c), 'cost')
                    c_yield = next((c for c in df_ing.columns if 'yield' in c), 'yield')
                    c_item = next((c for c in df_ing.columns if 'item' in c), 'item')

                    df_ing['unit_cost'] = df_ing[c_cost].apply(clean_currency) / df_ing[c_yield].apply(clean_currency).replace(0, 1)
                    df_ing['match_item'] = df_ing[c_item].str.lower().str.strip()

                    # 2. Calculate Recipe Costs
                    df_rec = recipes.copy()
                    r_name = next((c for c in df_rec.columns if 'recipe' in c), 'recipe')
                    r_ing = next((c for c in df_rec.columns if 'ingredient' in c), 'ingredient')
                    r_qty = next((c for c in df_rec.columns if 'quantity' in c or 'qty' in c), 'quantity')

                    df_rec['match_ing'] = df_rec[r_ing].str.lower().str.strip()
                    df_rec['qty_clean'] = df_rec[r_qty].apply(clean_currency)

                    merged = pd.merge(df_rec, df_ing, left_on='match_ing', right_on='match_item', how='left')
                    
                    # FILL MISSING COSTS WITH 0
                    merged['unit_cost'] = merged['unit_cost'].fillna(0.0)
                    
                    # WARNINGS (Collapsible)
                    unmatched_ingredients = merged[merged['unit_cost'] == 0]['match_ing'].unique()
                    if len(unmatched_ingredients) > 0:
                        with st.expander("⚠️ Missing Cost Data (Click to View)"):
                            st.warning(f"The following ingredients have $0.00 cost (Check spelling in 'Ingredients' sheet): {', '.join(unmatched_ingredients)}")

                    merged['line_cost'] = merged['qty_clean'] * merged['unit_cost']

                    recipe_costs = merged.groupby(r_name)['line_cost'].sum().reset_index()
                    recipe_costs.rename(columns={'line_cost': 'Recipe Cost', r_name: 'Recipe Name'}, inplace=True)
                    recipe_costs['match_recipe'] = recipe_costs['Recipe Name'].str.lower().str.strip()

                    # 3. Compare with Menu Price
                    df_menu = menu.copy()
                    m_name = next((c for c in df_menu.columns if 'item' in c or 'name' in c), 'item name')
                    m_price = next((c for c in df_menu.columns if 'price' in c), 'price')

                    df_menu['match_menu'] = df_menu[m_name].astype(str).str.replace(r"\s*\(.*?\)", "", regex=True).str.strip().str.lower()
                    df_menu['clean_price'] = df_menu[m_price].apply(clean_currency)

                    final = pd.merge(df_menu, recipe_costs, left_on='match_menu', right_on='match_recipe', how='left')
                    final['Recipe Cost'] = final['Recipe Cost'].fillna(0)
                    final['Profit'] = final['clean_price'] - final['Recipe Cost']
                    final['Margin %'] = ((final['Profit'] / final['clean_price']) * 100).fillna(0)

                    # ROUNDING
                    final = final.round(2)
                    
                    # --- WRAPPED IN FORMAT_DF TO FIX HEADER/DUPLICATE ROW ---
                    display_profit = final[[m_name, 'clean_price', 'Recipe Cost', 'Profit', 'Margin %']].rename(columns={'clean_price':'Menu Price'})
                    show_table(format_df(display_profit))
                    
                except Exception as e:
                    st.error(f"Calculation Error: {e}")

        with sub2:
            with st.expander("➕ Add Vendor"):
                with st.form("v"):
                    n = st.text_input("Name"); c = st.text_input("Cat"); p = st.text_input("Prod"); ph = st.text_input("Phone"); em = st.text_input("Email")
                    if st.form_submit_button("Save"):
                        new_row = pd.DataFrame([{"vendor name": n, "category": c, "products": p, "phone": ph, "email": em}])
                        updated_df = pd.concat([vendors, new_row], ignore_index=True)
                        if update_sheet("Vendors", updated_df): st.success("Saved!"); st.rerun()
            st.write("---")
            q = st.text_input("🔍 Search Vendors", "").lower()
            if not vendors.empty:
                mask = vendors.apply(lambda x: x.astype(str).str.lower().str.contains(q).any(), axis=1)
                show_table(format_df(vendors[mask]))

        with sub3:
            if not assets.empty: show_table(format_df(assets))

        with sub4:
            with st.expander("➕ Add Document"):
                with st.form("d"):
                    n = st.text_input("Document Name"); l = st.text_input("Link (URL)");
                    if st.form_submit_button("Save"):
                         new_row = pd.DataFrame([{"document name": n, "link": l}])
                         updated_df = pd.concat([vault, new_row], ignore_index=True)
                         if update_sheet("Vault_Index", updated_df): st.success("Saved!"); st.rerun()
            st.write("---")
            if not vault.empty:
                for index, row in vault.iterrows():
                    name = row.get('document name') or row.get('name') or "Unnamed Doc"
                    link = row.get('link') or row.get('url') or "#"
                    if link and str(link).startswith('http'):
                        st.markdown(f'<a href="{link}" target="_blank" class="vault-link">📄 {name}</a>', unsafe_allow_html=True)
                    else:
                        st.markdown(f'<div class="vault-link">📄 {name} (No Link)</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()
