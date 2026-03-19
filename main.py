import streamlit as st
import pandas as pd
import math
import os
from streamlit_gsheets import GSheetsConnection

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="CCK Command Center", layout="wide", page_icon="🍕")
SHEET_URL = "https://docs.google.com/spreadsheets/d/1yqbd35J140KWT7ui8Ggqn68_OfGXb1wofViJRcSgZBU/edit"

# --- 2. LUXURY CSS (Matching the CCK Website) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@300;400;600&family=Playfair+Display:ital,wght@0,400;0,600;1,400&display=swap');

    .stApp {
        background-color: #121212;
        font-family: 'Montserrat', sans-serif;
        color: #f5f5f5;
    }
    
    /* Hide Streamlit junk */
    section[data-testid="stSidebar"], [data-testid="stHeaderAction"] {display: none !important;}
    .block-container {padding-top: 2rem; padding-bottom: 5rem;}
    
    /* Typography */
    h1, h2, h3 {font-family: 'Playfair Display', serif; color: #c5a059;}
    h4, h5, p, label {font-family: 'Montserrat', sans-serif; color: #e6edf3;}
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {justify-content: center; gap: 30px; border-bottom: 1px solid rgba(197, 160, 89, 0.2);}
    .stTabs [data-baseweb="tab"] {background-color: transparent; color: #b0b0b0; font-weight: 600; font-size: 1.1rem;}
    .stTabs [aria-selected="true"] {color: #c5a059 !important; border-bottom: 2px solid #c5a059 !important;}
    
    /* Quick Links Container */
    .quick-links-container {
        display: flex; justify-content: center; align-items: center;
        gap: 30px; padding-bottom: 30px; border-bottom: 1px solid rgba(197, 160, 89, 0.2);
        margin-bottom: 30px; margin-top: -10px; flex-wrap: wrap;
    }
    .quick-link-card {
        background-color: #1a1a1a; border: 1px solid rgba(197, 160, 89, 0.3);
        border-radius: 8px; padding: 15px 30px; text-align: center;
        text-decoration: none; color: #f5f5f5; font-weight: 600; letter-spacing: 1px;
        transition: all 0.3s ease; display: flex; flex-direction: column; align-items: center; gap: 10px;
        min-width: 160px;
    }
    .quick-link-card:hover {
        transform: translateY(-4px); border-color: #c5a059; color: #c5a059;
        box-shadow: 0 4px 15px rgba(197, 160, 89, 0.15);
    }
    
    /* The Vault Grid */
    .vault-grid {
        display: grid; grid-template-columns: repeat(auto-fill, minmax(220px, 1fr)); gap: 20px; padding-top: 20px;
    }
    .doc-card {
        background-color: #1a1a1a; border: 1px solid #333; border-radius: 8px;
        padding: 30px 20px; text-align: center; text-decoration: none; color: #f5f5f5;
        transition: all 0.3s ease; display: flex; flex-direction: column; align-items: center; gap: 15px;
    }
    .doc-card:hover {
        border-color: #c5a059; transform: translateY(-3px); background-color: #1e1e1e;
    }
    .doc-card svg {fill: none; stroke: #c5a059; width: 45px; height: 45px; stroke-width: 1.5;}
    .doc-title {font-family: 'Montserrat', sans-serif; font-weight: 600; font-size: 1rem; color: #f5f5f5;}
    
    /* Sleek Quoter UI */
    .quote-box {
        background-color: #1a1a1a; border: 1px solid rgba(197, 160, 89, 0.3);
        border-radius: 8px; padding: 30px; margin-bottom: 20px;
    }
    .quote-header {font-family: 'Playfair Display', serif; font-size: 1.8rem; color: #c5a059; border-bottom: 1px solid #333; padding-bottom: 10px; margin-bottom: 20px;}
    .quote-row {display: flex; justify-content: space-between; margin-bottom: 12px; font-size: 1.1rem; color: #e6edf3;}
    .quote-row.total {font-weight: bold; font-size: 1.5rem; color: #c5a059; border-top: 1px solid #333; padding-top: 15px; margin-top: 15px;}
    .quote-row.profit {color: #238636; font-weight: 600; font-size: 1.2rem;}
    
    /* Form Elements */
    div[data-testid="stForm"] {background-color: #1a1a1a; border: 1px solid #333;}
    
    /* Hide empty dataframe index */
    .stDataFrame {border: 1px solid rgba(197, 160, 89, 0.3) !important; border-radius: 8px !important;}
    </style>
""", unsafe_allow_html=True)

# --- 3. HARDCODED MASTER DATA ENGINE ---
ingredients_data = pd.DataFrame([
    ["10\" Dough Ball", 0.95], ["12\" Dough Ball", 1.25], ["16\" Dough Ball", 1.85],
    ["House Pizza Sauce", 0.04], ["Buffalo Sauce", 0.13], ["Mike's Hot Honey", 0.61],
    ["Grande Mozzarella", 0.23], ["Fresh Mozzarella", 0.38], ["Ricotta Cheese", 0.28],
    ["Blue Cheese Crumbles", 0.25],
    ["Premium Sliced Pepperoni", 0.36], ["Fontanini Sausage", 0.37], ["Candied Bacon", 0.25],
    ["Diced Ham", 0.22], ["Diced Chicken", 0.28], 
    ["Fresh Tomatoes", 0.09], ["Green Peppers", 0.05], ["Onion", 0.02],
    ["Black Olives", 0.06], ["Sliced Garlic", 0.19], ["Drained Pineapple", 0.05]
], columns=["Ingredient", "Cost"])

ing_dict = {row['Ingredient'].strip(): float(row['Cost']) for index, row in ingredients_data.iterrows()}

recipes_data = pd.DataFrame([
    ["The Plain Jane 16\"", "16\" Dough Ball", 1], ["The Plain Jane 16\"", "House Pizza Sauce", 8], ["The Plain Jane 16\"", "Grande Mozzarella", 13],
    ["The Premium Pepperoni 16\"", "16\" Dough Ball", 1], ["The Premium Pepperoni 16\"", "House Pizza Sauce", 8], ["The Premium Pepperoni 16\"", "Grande Mozzarella", 12], ["The Premium Pepperoni 16\"", "Premium Sliced Pepperoni", 4.5],
    ["The Carnivore 16\"", "16\" Dough Ball", 1], ["The Carnivore 16\"", "House Pizza Sauce", 7], ["The Carnivore 16\"", "Grande Mozzarella", 10], ["The Carnivore 16\"", "Premium Sliced Pepperoni", 3], ["The Carnivore 16\"", "Fontanini Sausage", 4], ["The Carnivore 16\"", "Candied Bacon", 3], ["The Carnivore 16\"", "Mike's Hot Honey", 1],
    ["The Bianco Veggie 16\"", "16\" Dough Ball", 1], ["The Bianco Veggie 16\"", "Sliced Garlic", 1], ["The Bianco Veggie 16\"", "Grande Mozzarella", 8], ["The Bianco Veggie 16\"", "Ricotta Cheese", 5], ["The Bianco Veggie 16\"", "Green Peppers", 4], ["The Bianco Veggie 16\"", "Black Olives", 3],
    ["The Buffalo Soldier 16\"", "16\" Dough Ball", 1], ["The Buffalo Soldier 16\"", "Buffalo Sauce", 5], ["The Buffalo Soldier 16\"", "Grande Mozzarella", 9], ["The Buffalo Soldier 16\"", "Diced Chicken", 7], ["The Buffalo Soldier 16\"", "Blue Cheese Crumbles", 2],
    ["Custom 16\" (Standard Toppings)", "16\" Dough Ball", 1], ["Custom 16\" (Standard Toppings)", "House Pizza Sauce", 8], ["Custom 16\" (Standard Toppings)", "Grande Mozzarella", 12], ["Custom 16\" (Standard Toppings)", "Green Peppers", 3], ["Custom 16\" (Standard Toppings)", "Onion", 3],
    ["Custom 16\" (Premium Toppings)", "16\" Dough Ball", 1], ["Custom 16\" (Premium Toppings)", "House Pizza Sauce", 8], ["Custom 16\" (Premium Toppings)", "Grande Mozzarella", 12], ["Custom 16\" (Premium Toppings)", "Premium Sliced Pepperoni", 3], ["Custom 16\" (Premium Toppings)", "Ricotta Cheese", 3]
], columns=["Recipe", "Ingredient", "Ounces"])

menu_prices = {
    "The Plain Jane 16\"": 19.00, 
    "The Premium Pepperoni 16\"": 23.00, 
    "The Carnivore 16\"": 28.00, 
    "The Bianco Veggie 16\"": 28.00, 
    "The Buffalo Soldier 16\"": 28.00,
    "Custom 16\" (Standard Toppings)": 24.00,
    "Custom 16\" (Premium Toppings)": 28.00
}

# --- 4. DATA HELPERS ---
def get_recipe_cost(recipe_name):
    df = recipes_data[recipes_data['Recipe'] == recipe_name].copy()
    df['match_ing'] = df['Ingredient'].str.strip()
    safe_ing_df = ingredients_data.copy()
    safe_ing_df['match_ing'] = safe_ing_df['Ingredient'].str.strip()
    merged = pd.merge(df, safe_ing_df[['match_ing', 'Cost']], on="match_ing", how="left")
    merged['Cost'] = merged['Cost'].fillna(0.0)
    merged['Line Cost'] = merged['Ounces'] * merged['Cost']
    return merged['Line Cost'].sum()

def load_gsheets():
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        vault = conn.read(spreadsheet=SHEET_URL, worksheet="Vault_Index", ttl=600)
        return vault
    except: 
        return pd.DataFrame()

# --- 5. MAIN APP ---
def main():
    vault_df = load_gsheets()

    # Dynamic Centered Logo (Column sizing adjusted to 4-1-4 to make logo 40% smaller)
    c_left, c_logo, c_right = st.columns([4, 1, 4])
    with c_logo:
        if os.path.exists("CCK_Logo.png"):
            st.image("CCK_Logo.png", use_container_width=True)
        elif os.path.exists("logo.png"):
            st.image("logo.png", use_container_width=True)
        else:
            st.markdown("<h1 style='text-align: center; font-size: 3.5rem; margin-bottom: 0;'>CCK</h1>", unsafe_allow_html=True)
            
    st.markdown("<p style='text-align: center; color: #b0b0b0; letter-spacing: 2px; text-transform: uppercase; margin-bottom: 40px;'>Command Center</p>", unsafe_allow_html=True)

    quick_links_html = """<div class="quick-links-container">
<a href="https://www3.usfoods.com/order" target="_blank" class="quick-link-card">
<svg width="35" height="35" viewBox="0 0 24 24" fill="none" stroke="#c5a059" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
<path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"></path>
<polyline points="3.27 6.96 12 12.01 20.73 6.96"></polyline>
<line x1="12" y1="22.08" x2="12" y2="12"></line>
</svg>
US Foods
</a>
<a href="https://gemini.google.com/app/7e448fe20a7cd3a5" target="_blank" class="quick-link-card">
<svg width="35" height="35" viewBox="0 0 24 24" fill="none" stroke="#c5a059" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
<path d="M12 2v20M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"></path>
</svg>
CMO Persona
</a>
<a href="https://qbo.intuit.com" target="_blank" class="quick-link-card">
<svg width="35" height="35" viewBox="0 0 24 24" fill="none" stroke="#c5a059" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
<rect x="2" y="3" width="20" height="14" rx="2" ry="2"></rect>
<line x1="8" y1="21" x2="16" y2="21"></line>
<line x1="12" y1="17" x2="12" y2="21"></line>
</svg>
QuickBooks
</a>
</div>"""
    st.markdown(quick_links_html, unsafe_allow_html=True)

    tabs = st.tabs(["🎫 Event Quoter", "🍕 Pizza Builder", "📖 Recipe Margins", "🗄️ The Vault"])

    # --- TAB 1: EVENT QUOTER ---
    with tabs[0]:
        st.write("##")
        c_in, c_out = st.columns([1, 1.5], gap="large")
        
        with c_in:
            st.markdown("<h3 style='margin-bottom: 20px;'>1. Event Parameters</h3>", unsafe_allow_html=True)
            c_g, c_f = st.columns(2)
            guests = c_g.number_input("Est. Guests (For reference)", min_value=1, value=50, step=5)
            event_fee = c_f.number_input("Flat Travel/Setup Fee ($)", min_value=0.0, value=150.0, step=25.0)
            
            pies_needed = math.ceil((guests * 2.5) / 8)
            st.info(f"💡 **Rule of Thumb:** For {guests} guests, you will need about **{pies_needed} large pies**.")
            
            st.markdown("<h3 style='margin-bottom: 10px; margin-top: 20px;'>2. Build the Order</h3>", unsafe_allow_html=True)
            order_qtys = {}
            for item, price in menu_prices.items():
                order_qtys[item] = st.number_input(f"{item} (${price:.2f})", min_value=0, value=0, step=1)
                
            st.markdown("<h3 style='margin-bottom: 10px; margin-top: 20px;'>3. Taxes & Fees</h3>", unsafe_allow_html=True)
            c_t, c_c = st.columns(2)
            apply_tax = c_t.checkbox("Add MA Meals Tax (7.0%)", value=True)
            apply_cc = c_c.checkbox("Add CC Fee (2.29%)", value=False)

        with c_out:
            pizza_subtotal = 0.0
            total_food_cost = 0.0
            total_pies = 0
            order_lines = ""
            
            for item, qty in order_qtys.items():
                if qty > 0:
                    item_price = menu_prices[item]
                    item_cost = get_recipe_cost(item)
                    
                    pizza_subtotal += (item_price * qty)
                    total_food_cost += (item_cost * qty)
                    total_pies += qty
                    order_lines += f'<div class="quote-row"><span>{qty}x {item}</span> <span>${(item_price * qty):,.2f}</span></div>\n'
            
            if total_pies == 0:
                order_lines = '<div class="quote-row"><span style="color: #666; font-style: italic;">No items added to order yet.</span> <span>$0.00</span></div>\n'
                
            taxable_amount = pizza_subtotal + event_fee
            tax_amount = (taxable_amount * 0.07) if apply_tax else 0.0
            
            subtotal_with_tax = taxable_amount + tax_amount
            cc_fee_amount = (subtotal_with_tax * 0.0229) if apply_cc else 0.0
            
            final_quote = subtotal_with_tax + cc_fee_amount
            
            net_revenue = pizza_subtotal + event_fee
            profit = net_revenue - total_food_cost
            margin = (profit / net_revenue) * 100 if net_revenue > 0 else 0.0

            quote_html = f"""<div class="quote-box">
<div class="quote-header">Custom Catering Proposal</div>
<div style="color: #b0b0b0; margin-bottom: 15px; font-weight: 600; font-family: 'Montserrat';">ORDER SUMMARY ({total_pies} ITEMS TOTAL)</div>
{order_lines}
<div style="color: #b0b0b0; margin-top: 25px; margin-bottom: 15px; font-weight: 600; font-family: 'Montserrat';">FINANCIALS</div>
<div class="quote-row"><span>Pizza Subtotal</span> <span>${pizza_subtotal:,.2f}</span></div>
<div class="quote-row"><span>Setup / Travel Fee</span> <span>${event_fee:,.2f}</span></div>"""

            if apply_tax:
                quote_html += f'\n<div class="quote-row"><span>MA Meals Tax (7.0%)</span> <span>${tax_amount:,.2f}</span></div>'
            if apply_cc:
                quote_html += f'\n<div class="quote-row"><span>Credit Card Fee (2.29%)</span> <span>${cc_fee_amount:,.2f}</span></div>'

            quote_html += f"""\n<div class="quote-row total"><span>Total Client Quote</span> <span>${final_quote:,.2f}</span></div>
<div style="margin-top: 20px; padding: 15px; background-color: #121212; border-radius: 6px; border-left: 4px solid #c5a059;">
<div class="quote-row" style="margin-bottom: 5px;"><span>Internal Raw Food Cost</span> <span>${total_food_cost:,.2f}</span></div>
<div class="quote-row profit" style="margin-bottom: 0;"><span>Projected Net Profit</span> <span>${profit:,.2f} ({margin:.1f}%)</span></div>
</div>
</div>"""
            st.markdown(quote_html, unsafe_allow_html=True)

    # --- TAB 2: PIZZA BUILDER ---
    with tabs[1]:
        st.write("##")
        st.markdown("<p style='color: #b0b0b0; margin-bottom: 30px;'>Select your crust and layer on ingredients by the ounce to engineer your target 80% margin.</p>", unsafe_allow_html=True)
        
        c1, c2 = st.columns([1.2, 1], gap="large")
        
        with c1:
            st.markdown("### The Canvas")
            base = st.selectbox("Crust Base", ["10\" Dough Ball", "12\" Dough Ball", "16\" Dough Ball"])
            base_cost = ing_dict.get(base, 0.0)
            
            st.markdown("### The Sauce")
            sauce = st.selectbox("Sauce Type", ["None", "House Pizza Sauce", "Buffalo Sauce"])
            sauce_oz = st.number_input("Sauce Amount (oz)", min_value=0.0, value=8.0, step=0.5) if sauce != "None" else 0.0
            
            st.markdown("### The Cheese")
            cheeses = st.multiselect("Select Cheeses", ["Grande Mozzarella", "Fresh Mozzarella", "Ricotta Cheese", "Blue Cheese Crumbles"])
            cheese_oz = {}
            for ch in cheeses:
                cheese_oz[ch] = st.number_input(f"{ch} (oz)", min_value=0.0, value=10.0, step=0.5, key=f"ch_{ch}")
                
            st.markdown("### The Toppings")
            toppings = st.multiselect("Select Meats & Veggies", ["Premium Sliced Pepperoni", "Fontanini Sausage", "Candied Bacon", "Diced Ham", "Diced Chicken", "Fresh Tomatoes", "Green Peppers", "Onion", "Black Olives", "Sliced Garlic", "Drained Pineapple", "Mike's Hot Honey"])
            topping_oz = {}
            for t in toppings:
                topping_oz[t] = st.number_input(f"{t} (oz)", min_value=0.0, value=3.0, step=0.5, key=f"t_{t}")
                
        with c2:
            st.markdown("### Cost Breakdown")
            total_cost = base_cost
            breakdown = [{"Ingredient": base, "Ounces": 1.0, "Line Cost": base_cost}]
            
            if sauce != "None" and sauce_oz > 0:
                sc = sauce_oz * ing_dict.get(sauce, 0.0)
                total_cost += sc
                breakdown.append({"Ingredient": sauce, "Ounces": sauce_oz, "Line Cost": sc})
                
            for ch, oz in cheese_oz.items():
                c = oz * ing_dict.get(ch, 0.0)
                total_cost += c
                breakdown.append({"Ingredient": ch, "Ounces": oz, "Line Cost": c})
                
            for t, oz in topping_oz.items():
                c = oz * ing_dict.get(t, 0.0)
                total_cost += c
                breakdown.append({"Ingredient": t, "Ounces": oz, "Line Cost": c})
                
            bd_df = pd.DataFrame(breakdown)
            if not bd_df.empty:
                bd_df['Line Cost'] = bd_df['Line Cost'].apply(lambda x: f"${x:.2f}")
                st.dataframe(bd_df, use_container_width=True, hide_index=True)
                
            target_price = total_cost / 0.20 if total_cost > 0 else 0.0
            
            builder_html = f"""<div class="quote-box" style="margin-top: 20px;">
<div class="quote-row"><span>Total Raw Food Cost</span> <span>${total_cost:.2f}</span></div>
<div class="quote-row total" style="color: #238636;"><span>Suggested Menu Price (80% Margin)</span> <span>${target_price:.2f}</span></div>
</div>"""
            st.markdown(builder_html, unsafe_allow_html=True)

    # --- TAB 3: RECIPE MARGINS ---
    with tabs[2]:
        st.write("##")
        col_sel, col_blank = st.columns([1, 2])
        with col_sel:
            selected_pie = st.selectbox("Select Menu Item", list(menu_prices.keys()), key="margin_pie")
        
        df_recipe = recipes_data[recipes_data['Recipe'] == selected_pie].copy()
        df_recipe['match_ing'] = df_recipe['Ingredient'].str.strip()
        safe_ing_df = ingredients_data.copy()
        safe_ing_df['match_ing'] = safe_ing_df['Ingredient'].str.strip()
        merged_recipe = pd.merge(df_recipe, safe_ing_df[['match_ing', 'Cost']], on="match_ing", how="left")
        merged_recipe['Cost'] = merged_recipe['Cost'].fillna(0.0)
        merged_recipe['Line Cost'] = merged_recipe['Ounces'] * merged_recipe['Cost']
        
        cost = merged_recipe['Line Cost'].sum()
        price = menu_prices[selected_pie]
        
        c1, c2, c3 = st.columns(3)
        c1.markdown(f"<div class='quote-box' style='text-align:center;'><div style='color:#b0b0b0; font-size: 0.9rem;'>RETAIL PRICE</div><div style='font-size: 2rem; color: #f5f5f5;'>${price:,.2f}</div></div>", unsafe_allow_html=True)
        c2.markdown(f"<div class='quote-box' style='text-align:center;'><div style='color:#b0b0b0; font-size: 0.9rem;'>FOOD COST</div><div style='font-size: 2rem; color: #da3633;'>${cost:,.2f}</div></div>", unsafe_allow_html=True)
        c3.markdown(f"<div class='quote-box' style='text-align:center;'><div style='color:#b0b0b0; font-size: 0.9rem;'>PROFIT MARGIN</div><div style='font-size: 2rem; color: #238636;'>{((price-cost)/price)*100:.1f}%</div></div>", unsafe_allow_html=True)
        
        st.markdown("#### Recipe Breakdown")
        display_df = merged_recipe[['Ingredient', 'Ounces', 'Line Cost']].copy()
        display_df['Line Cost'] = display_df['Line Cost'].apply(lambda x: f"${x:.2f}")
        st.dataframe(display_df, use_container_width=True, hide_index=True)

    # --- TAB 4: THE VAULT ---
    with tabs[3]:
        st.write("##")
        if not vault_df.empty:
            vault_html = '<div class="vault-grid">'
            for index, row in vault_df.iterrows():
                name = row.get('document name') or row.get('name') or "Unnamed Doc"
                link = row.get('link') or row.get('url') or "#"
                href = link if str(link).startswith('http') else '#'
                
                svg_icon = '''<svg viewBox="0 0 24 24">
<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
<polyline points="14 2 14 8 20 8"></polyline>
<line x1="16" y1="13" x2="8" y2="13"></line>
<line x1="16" y1="17" x2="8" y2="17"></line>
<polyline points="10 9 9 9 8 9"></polyline>
</svg>'''
                
                vault_html += f'''<a href="{href}" target="_blank" class="doc-card">
{svg_icon}
<div class="doc-title">{name}</div>
</a>'''
            vault_html += '</div>'
            st.markdown(vault_html, unsafe_allow_html=True)
        else:
            st.info("Vault is empty or Google Sheets connection failed. Add links to your 'Vault_Index' tab.")

if __name__ == "__main__":
    main()
