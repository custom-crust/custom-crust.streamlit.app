import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
from streamlit_gsheets import GSheetsConnection
import os

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
    .block-container {padding-top: 2rem; padding-bottom: 5rem;}
    
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
    df.columns = [col.strip().title() for col in df.columns]
    money_cols = ['Cost', 'Amount', 'Price', 'Revenue', 'Total', 'Debit', 'Credit', 'Balance', 'Value', 'Unit Cost', 'Recipe Cost', 'Profit', 'Menu Price', 'Line Total']
    for col in df.columns:
        if col in money_cols: df[col] = df[col].apply(clean_currency)
    for col in df.columns:
        if 'date' in col.lower() or 'updated' in col.lower():
            try: df[col] = pd.to_datetime(df[col]).dt.strftime('%m/%d/%Y')
            except: pass
    return df

def style_df(df):
    if df.empty: return df
    money_cols = ['Cost', 'Amount', 'Price', 'Revenue', 'Total', 'Debit', 'Credit', 'Balance', 'Value', 'Unit Cost', 'Recipe Cost', 'Profit', 'Menu Price', 'Line Total']
    pct_cols = ['Margin (%)', 'Margin']
    format_dict = {c: "${:,.2f}" for c in df.columns if c in money_cols}
    format_dict.update({c: "{:.1f}%" for c in df.columns if c in pct_cols})
    return df.style.format(format_dict)

def load_data():
    data = {}
    tabs = {
        "assets": "Assets", "expenses": "Ledger", "sales": "Sales", 
        "menu": "Menu", "vault": "Vault_Index", "debt": "Debt_Log",
        "ingredients": "Ingredients", "recipes": "Recipes", "vendors": "Vendors",
        "bank_log": "Transfers" 
    }
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        for key, sheet_name in tabs.items():
            try:
                df = conn.read(spreadsheet=SHEET_URL, worksheet=sheet_name, ttl=0)
                df.columns = [str(c).strip().lower() for c in df.columns]
                if 'date' in df.columns: df['date'] = pd.to_datetime(df['date'], errors='coerce')
                data[key] = df.to_dict('records')
            except: data[key] = []
        return data, None
    except Exception as e:
        return {k:[] for k in tabs}, str(e)

# --- 4. MAIN APP ---
def main():
    if 'quote_cart' not in st.session_state: st.session_state.quote_cart = []
    data, error = load_data()
    assets, expenses, sales = data['assets'], data['expenses'], data['sales']
    menu, vault, debt = data['menu'], data['vault'], data['debt']
    ingredients, recipes, vendors = data['ingredients'], data['recipes'], data['vendors']
    bank_log = data['bank_log']

    # --- LOGO (CENTERED & ROBUST) ---
    c1, c2, c3 = st.columns([1, 2, 1]) # Middle column is wider
    with c2: 
        if os.path.exists("logo.png"):
            st.image("logo.png", use_container_width=True)
        else:
            st.markdown("<h1 style='text-align: center; font-size: 80px;'>🍕 CCK</h1>", unsafe_allow_html=True)
    
    if error: st.error(f"🚨 Connection Error: {error}")

    tabs = st.tabs(["📊 Dashboard", "🏦 Banking", "💰 Sales", "📝 Expenses", "📉 Debt", "📅 Event Quote", "🍕 Menu", "📂 Tools"])

    # --- MATH ---
    liquid = 0.0
    northern_bank_bal = 0.0
    for a in assets:
        if "northern" in str(a.get('account name','')).lower():
            northern_bank_bal = clean_currency(a.get('balance', 0))

    for e in expenses:
        pay_method = str(e.get('paid via') or '').lower()
        val = clean_currency(e.get('cost') or e.get('amount') or 0)
        if "northern" in pay_method or "bank" in pay_method:
            northern_bank_bal -= val

    if bank_log:
        for b in bank_log:
            b_type = str(b.get('type') or b.get('transaction type') or b.get('from account') or '').lower()
            val = clean_currency(b.get('amount', 0))
            if "deposit" in b_type: northern_bank_bal += val
            elif "withdraw" in b_type: northern_bank_bal -= val

    borrowed, repaid = 0.0, 0.0
    if debt:
        for d in debt:
            t_type = str(d.get('transaction type','')).lower()
            amt = clean_currency(d.get('amount') or 0)
            if "borrow" in t_type: borrowed += amt
            elif "repay" in t_type: repaid += amt
    current_debt = borrowed - repaid
    
    tot_exp = sum(clean_currency(e.get('cost') or e.get('amount') or 0) for e in expenses)
    tot_sale = sum(clean_currency(s.get('revenue') or s.get('amount') or 0) for s in sales)

    # --- UI ---
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
            if expenses:
                df = pd.DataFrame(expenses)
                cost_col = next((c for c in ['cost','amount'] if c in df.columns), None)
                if cost_col:
                    df['clean'] = df[cost_col].apply(clean_currency)
                    if df['clean'].sum() > 0:
                        fig = px.pie(df, values='clean', names='category', hole=0.6, color_discrete_sequence=px.colors.qualitative.Pastel)
                        fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="#b0b0b0", height=300, margin=dict(t=0, b=0, l=0, r=0))
                        st.plotly_chart(fig, use_container_width=True)
        with c2:
            st.markdown("#### 💰 Sales Source")
            if sales:
                df_s = pd.DataFrame(sales)
                rev_col = next((c for c in ['revenue','amount'] if c in df_s.columns), None)
                cat_col = 'category' if 'category' in df_s.columns else 'event'
                if rev_col:
                    df_s['clean_rev'] = df_s[rev_col].apply(clean_currency)
                    if df_s['clean_rev'].sum() > 0:
                        figS = px.pie(df_s, values='clean_rev', names=cat_col, hole=0.6, color_discrete_sequence=px.colors.qualitative.Set3)
                        figS.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="#b0b0b0", height=300, margin=dict(t=0, b=0, l=0, r=0))
                        st.plotly_chart(figS, use_container_width=True)
            else: st.info("No sales data.")

    with tabs[1]:
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
                if st.form_submit_button("Submit"): st.success(f"Recorded: {b_type} of ${b_amt}")
        with c2:
            st.markdown("#### Activity Log")
            if bank_log: st.dataframe(style_df(format_df(pd.DataFrame(bank_log))), use_container_width=True, hide_index=True)
            else: st.caption("No activity.")

    with tabs[2]:
        st.write("##")
        c1, c2 = st.columns([1, 2])
        with c1:
            st.markdown("### Log Sale")
            with st.form("sale"):
                cat = st.selectbox("Category", ["Catering", "Food Festival", "Street Service / Truck", "Online Order", "Other"])
                desc = st.text_input("Event Name")
                amt = st.number_input("Revenue ($)", 0.0)
                date = st.date_input("Date", datetime.today(), format="MM/DD/YYYY")
                if st.form_submit_button("Log Sale"): st.success("Logged!")
        with c2:
            ytd, mtd, wk, last_wk = 0.0, 0.0, 0.0, 0.0
            if sales:
                df_s = pd.DataFrame(sales)
                rev = next((c for c in ['revenue','amount'] if c in df_s.columns), None)
                if rev:
                    df_s['cl'] = df_s[rev].apply(clean_currency)
                    now = datetime.now()
                    st_wk = (now - timedelta(days=now.weekday())).replace(hour=0,minute=0,second=0,microsecond=0)
                    ytd = df_s[df_s['date'] >= datetime(now.year,1,1)]['cl'].sum()
                    mtd = df_s[df_s['date'] >= datetime(now.year,now.month,1)]['cl'].sum()
                    wk = df_s[df_s['date'] >= st_wk]['cl'].sum()
                    last_wk = df_s[(df_s['date'] >= st_wk-timedelta(7)) & (df_s['date'] < st_wk)]['cl'].sum()
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("📅 YTD", f"${ytd:,.0f}"); m2.metric("🗓️ MTD", f"${mtd:,.0f}"); m3.metric("🟢 This Wk", f"${wk:,.0f}"); m4.metric("🟡 Last Wk", f"${last_wk:,.0f}")
            st.write("---")
            if sales: st.dataframe(style_df(format_df(pd.DataFrame(sales))), use_container_width=True, hide_index=True)

    with tabs[3]:
        st.write("##")
        with st.form("exp"):
            c1, c2, c3, c4 = st.columns(4)
            item = c1.text_input("Item"); cost = c2.number_input("Cost ($)", 0.0)
            cat = c3.selectbox("Category", ["Ingredients & Supplies", "Fuel & Propane", "Smallwares & Utensils", "Equipment", "Equipment Maintenance", "Licensing & Legal", "Rent", "Labor", "Startup Asset / Initial Investment", "Other"])
            pay = c4.selectbox("Paid Via", ["Northern Bank Debit Card", "Cash / Undeposited", "Owner Personal Funds / Equity"])
            if st.form_submit_button("Save"): st.success("Saved!")
        if expenses: st.dataframe(style_df(format_df(pd.DataFrame(expenses))), use_container_width=True, hide_index=True)

    with tabs[4]:
        st.write("##")
        c1, c2, c3 = st.columns(3)
        c1.metric("🔴 Borrowed", f"${borrowed:,.2f}"); c2.metric("🟢 Paid Off", f"${repaid:,.2f}"); c3.metric("🟡 Remaining", f"${current_debt:,.2f}")
        st.write("---")
        with st.form("debt"):
            c1, c2, c3, c4 = st.columns(4)
            name = c1.text_input("Name"); dtype = c2.selectbox("Type", ["Repay", "Borrow"]); amt = c3.number_input("Amount ($)", 0.0); dt = c4.date_input("Date", datetime.today(), format="MM/DD/YYYY")
            if st.form_submit_button("Log"): st.success("Logged!")
        if debt: st.dataframe(style_df(format_df(pd.DataFrame(debt))), use_container_width=True, hide_index=True)

    with tabs[5]:
        st.write("##")
        st.markdown("### 📝 Event Quote Builder")
        c1, c2 = st.columns(2)
        with c1:
            fee_amt = st.number_input("Flat Event Fee ($)", 0.0)
            if st.button("Add Event Fee"): st.session_state.quote_cart.append({"Item": "Event Fee", "Price": fee_amt, "Qty": 1, "Line Total": fee_amt}); st.rerun()
        with c2:
            trav_amt = st.number_input("Travel Fee ($)", 0.0)
            if st.button("Add Travel Fee"): st.session_state.quote_cart.append({"Item": "Travel Fee", "Price": trav_amt, "Qty": 1, "Line Total": trav_amt}); st.rerun()
        st.write("---")
        c_add1, c_add2, c_add3 = st.columns([3, 1, 1])
        df_menu = pd.DataFrame(menu) if menu else pd.DataFrame()
        if not df_menu.empty:
            m_name = next((c for c in df_menu.columns if 'item' in c or 'name' in c), None)
            m_price = next((c for c in df_menu.columns if 'price' in c or 'cost' in c), None)
            sel = c_add1.selectbox("Item", df_menu[m_name].tolist() if m_name else [])
            qty = c_add2.number_input("Qty", 1, 500, 10)
            row = df_menu[df_menu[m_name] == sel].iloc[0]
            pr = clean_currency(row[m_price]) if m_price else 0.0
            if c_add3.button("Add"): st.session_state.quote_cart.append({"Item": sel, "Price": pr, "Qty": qty, "Line Total": pr*qty}); st.rerun()
        if st.session_state.quote_cart:
            cart = pd.DataFrame(st.session_state.quote_cart)
            st.dataframe(style_df(format_df(cart)), use_container_width=True, hide_index=True)
            st.metric("⭐ TOTAL QUOTE", f"${cart['Line Total'].sum():,.2f}")
            if st.button("Clear"): st.session_state.quote_cart = []; st.rerun()

    with tabs[6]:
        st.write("##")
        if menu: st.dataframe(style_df(format_df(pd.DataFrame(menu))), use_container_width=True, hide_index=True)
        with st.expander("Add Item"):
            with st.form("menu"):
                name = st.text_input("Name"); price = st.number_input("Price", 0.0)
                if st.form_submit_button("Add"): st.success("Added!")

    with tabs[7]:
        st.write("##")
        sub1, sub2, sub3, sub4 = st.tabs(["💰 Profit", "🤝 Vendors", "🏦 Assets", "🗄️ Vault"])
        with sub1:
            if ingredients and recipes and menu:
                df_ing = pd.DataFrame(ingredients)
                col_map = {}
                for col in df_ing.columns:
                    if 'cost' in col or 'price' in col: col_map['unit_cost'] = col
                    if 'yield' in col or 'weight' in col: col_map['yield'] = col
                    if 'item' in col or 'name' in col: col_map['item'] = col
                if 'unit_cost' in col_map and 'yield' in col_map:
                    df_ing['clean_cost'] = df_ing[col_map['unit_cost']].apply(clean_currency)
                    df_ing['clean_yield'] = df_ing[col_map['yield']].apply(clean_currency)
                    df_ing['item_name'] = df_ing[col_map.get('item', df_ing.columns[0])]
                    df_ing['cost_per_oz'] = df_ing.apply(lambda x: x['clean_cost'] / x['clean_yield'] if x['clean_yield'] > 0 else 0, axis=1)
                    
                    df_rec = pd.DataFrame(recipes)
                    r_name = next((c for c in df_rec.columns if 'recipe' in c or 'name' in c), None)
                    r_ing = next((c for c in df_rec.columns if 'ingredient' in c or 'item' in c), None)
                    r_qty = next((c for c in df_rec.columns if 'quantity' in c or 'qty' in c), None)

                    if r_name and r_ing and r_qty:
                        merged = pd.merge(df_rec, df_ing, left_on=r_ing, right_on='item_name', how='left')
                        merged['line_cost'] = merged[r_qty].apply(clean_currency) * merged['cost_per_oz']
                        master = merged.groupby(r_name)['line_cost'].sum().reset_index()
                        master.rename(columns={'line_cost': 'Recipe Cost', r_name: 'Item Name'}, inplace=True)
                        
                        df_menu = pd.DataFrame(menu)
                        m_name = next((c for c in df_menu.columns if 'item' in c or 'name' in c), None)
                        m_price = next((c for c in df_menu.columns if 'price' in c or 'cost' in c), None)
                        
                        if m_name and m_price:
                            df_menu['clean_price'] = df_menu[m_price].apply(clean_currency)
                            df_menu['match_name'] = df_menu[m_name].astype(str).str.replace(r"\s*\(.*?\)", "", regex=True).str.strip()
                            final = pd.merge(master, df_menu[['match_name', 'clean_price']], left_on='Item Name', right_on='match_name', how='left')
                            final['Profit'] = final['clean_price'] - final['Recipe Cost']
                            final['Margin (%)'] = (final['Profit'] / final['clean_price']) * 100
                            final.rename(columns={'clean_price': 'Menu Price'}, inplace=True)
                            st.dataframe(style_df(format_df(final[['Item Name', 'Recipe Cost', 'Menu Price', 'Profit', 'Margin (%)']])), use_container_width=True, hide_index=True)
            else: st.info("Waiting for data.")
        
        with sub2:
            with st.expander("➕ Add"):
                with st.form("v"):
                    n = st.text_input("Name"); c = st.text_input("Cat"); p = st.text_input("Prod"); ph = st.text_input("Phone"); em = st.text_input("Email")
                    if st.form_submit_button("Save"): st.success("Saved!")
            st.write("---")
            q = st.text_input("🔍 Search Vendors", "").lower()
            if vendors:
                df_v = pd.DataFrame(vendors)
                mask = df_v.apply(lambda x: x.astype(str).str.lower().str.contains(q).any(), axis=1)
                st.dataframe(format_df(df_v[mask]), use_container_width=True, hide_index=True)
        
        with sub3:
            if assets: st.dataframe(style_df(format_df(pd.DataFrame(assets))), use_container_width=True, hide_index=True)
        with sub4:
            with st.expander("➕ Add Doc"):
                with st.form("d"):
                    n = st.text_input("Name"); l = st.text_input("Link"); 
                    if st.form_submit_button("Save"): st.success("Saved!")
            st.write("---")
            q = st.text_input("🔍 Search Docs", "").lower()
            if vault:
                for v in vault:
                    if q in str(v).lower(): st.info(f"📄 **[{v.get('document name') or v.get('name')}]({v.get('link') or v.get('url')})**")

if __name__ == "__main__":
    main()
