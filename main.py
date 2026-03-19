import streamlit as st
import pandas as pd
import math
from datetime import datetime
from streamlit_gsheets import GSheetsConnection
import os

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="CCK Command Center", layout="wide", page_icon="🍕")
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
    .stTabs [data-baseweb="tab"] {background-color: transparent; color: #888; font-weight: 600; font-size: 1.1rem;}
    .stTabs [aria-selected="true"] {color: #c5a059 !important; border-bottom: 2px solid #c5a059 !important;}
    div.stMetric, div.stDataFrame, div[data-testid="stForm"] {
        background-color: #161b22; border: 1px solid #30363d;
        padding: 20px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    }
    div.stButton > button {
        background-color: #c5a059; color: #121212; border-radius: 6px;
        font-weight: bold; height: 45px; width: 100%; text-transform: uppercase;
    }
    h1, h2, h3, h4, p, label {color: #e6edf3; font-family: 'Segoe UI', sans-serif;}
    div[data-testid="stMetricValue"] {color: #ffffff !important;}
    [data-testid="stHeaderAction"] {display: none !important;}
    
    /* --- CUSTOM COMMAND CENTER CSS --- */
    .quick-links-container {
        display: flex; justify-content: center; align-items: center;
        gap: 40px; padding-bottom: 25px; border-bottom: 1px solid #333;
        margin-bottom: 25px; margin-top: -10px; flex-wrap: wrap;
    }
    .quick-link-card {
        background-color: #161b22; border: 1px solid #30363d;
        border-radius: 10px; padding: 15px 25px; text-align: center;
        text-decoration: none; color: #e6edf3; font-weight: bold;
        transition: transform 0.2s, border-color 0.2s;
        display: flex; flex-direction: column; align-items: center; gap: 10px;
    }
    .quick-link-card:hover {
        transform: translateY(-5px); border-color: #c5a059; color: #c5a059;
    }
    .quick-link-icon {width: 45px; height: 45px; object-fit: contain;}
    .vault-link {
        font-size: 18px; color: #58a6ff; text-decoration: none;
        padding: 12px; display: block; border-bottom: 1px solid #30363d;
    }
    .vault-link:hover {color: #c5a059; background-color: #1c2128;}
    </style>
""", unsafe_allow_html=True)

# --- 3. HARDCODED MASTER DATA ENGINE ---
ingredients_data = pd.DataFrame([
    ["10\" Dough Ball", 0.95], ["12\" Dough Ball", 1.25], ["16\" Dough Ball", 1.85],
    ["House Pizza Sauce", 0.04], ["Buffalo Sauce", 0.13], ["Mike's Hot Honey", 0.61],
    ["Grande Mozzarella", 0.23], ["Fresh Mozzarella", 0.38], ["Ricotta Cheese", 0.28],
    ["Premium Sliced Pepperoni", 0.36], ["Fontanini Sausage", 0.37], ["Candied Bacon", 0.25],
    ["Diced Ham", 0.22], ["Fresh Tomatoes", 0.09], ["Green Peppers", 0.05],
    ["Black Olives", 0.06], ["Sliced Garlic", 0.19], ["Drained Pineapple", 0.05]
], columns=["Ingredient", "Cost Per Oz"])

recipes_data = pd.DataFrame([
    ["The Plain Jane 16\"", "16\" Dough Ball", 1], ["The Plain Jane 16\"", "House Pizza Sauce", 8], ["The Plain Jane 16\"", "Grande Mozzarella", 13],
    ["The Premium Pepperoni 16\"", "16\" Dough Ball", 1], ["The Premium Pepperoni 16\"", "House Pizza Sauce", 8], ["The Premium Pepperoni 16\"", "Grande Mozzarella", 12], ["The Premium Pepperoni 16\"", "Premium Sliced Pepperoni", 4.5],
    ["The Carnivore 16\"", "16\" Dough Ball", 1], ["The Carnivore 16\"", "House Pizza Sauce", 7], ["The Carnivore 16\"", "Grande Mozzarella", 10], ["The Carnivore 16\"", "Premium Sliced Pepperoni", 3], ["The Carnivore 16\"", "Fontanini Sausage", 4], ["The Carnivore 16\"", "Candied Bacon", 3], ["The Carnivore 16\"", "Mike's Hot Honey", 1],
    ["The Bianco Veggie 16\"", "16\" Dough Ball", 1], ["The Bianco Veggie 16\"", "Sliced Garlic", 1], ["The Bianco Veggie 16\"", "Grande Mozzarella", 8], ["The Bianco Veggie 16\"", "Ricotta Cheese", 5], ["The Bianco Veggie 16\"", "Green Peppers", 4], ["The Bianco Veggie 16\"", "Black Olives", 3],
    ["Large Calzone", "16\" Dough Ball", 1], ["Large Calzone", "Grande Mozzarella", 10], ["Large Calzone", "Ricotta Cheese", 7]
], columns=["Recipe", "Ingredient", "Ounces"])

menu_prices = {
    "The Plain Jane 16\"": 19.00, "The Premium Pepperoni 16\"": 23.00, 
    "The Carnivore 16\"": 28.00, "The Bianco Veggie 16\"": 28.00, "Large Calzone": 22.00
}

# --- 4. DATA HELPERS ---
def get_recipe_cost(recipe_name):
    df = recipes_data[recipes_data['Recipe'] == recipe_name]
    merged = pd.merge(df, ingredients_data, on="Ingredient", how="left")
    merged['Line Cost'] = merged['Ounces'] * merged['Cost Per Oz']
    return merged['Line Cost'].sum()

def get_connection():
    return st.connection("gsheets", type=GSheetsConnection)

def load_gsheets():
    conn = get_connection()
    try:
        vault = conn.read(spreadsheet=SHEET_URL, worksheet="Vault_Index", ttl=600)
    except: vault = pd.DataFrame()
    return vault

# --- 5. MAIN APP ---
def main():
    vault_df = load_gsheets()

    c1, c2, c3 = st.columns([3, 1, 3])
    with c2:
        st.markdown("<h1 style='text-align: center; font-size: 50px; color: #c5a059;'>CCK</h1>", unsafe_allow_html=True)

    # --- QUICK LINKS COMMAND CENTER ---
    # The Gemini Marketing link includes a pre-written prompt via URL parameters!
    gemini_marketing_url = "https://gemini.google.com/?prompt=Act+as+the+Chief+Marketing+Officer+for+Custom+Crust+Kitchen,+a+premium+mobile+artisan+pizza+catering+company.+Write+me+an+engaging+Instagram+caption+about+our+new+menu."
    
    st.markdown(f"""
        <div class="quick-links-container">
            <a href="https://www3.usfoods.com/order" target="_blank" class="quick-link-card">
                <img class="quick-link-icon" src="https://img.icons8.com/color/96/food-truck.png" alt="US Foods">
                US Foods Portal
            </a>
            <a href="{gemini_marketing_url}" target="_blank" class="quick-link-card">
                <img class="quick-link-icon" src="https://www.gstatic.com/lamda/images/gemini_sparkle_v002_d4735304ff6292a690345.svg" alt="Gemini">
                CMO Marketing AI
            </a>
            <a href="https://qbo.intuit.com" target="_blank" class="quick-link-card">
                <img class="quick-link-icon" src="https://img.icons8.com/color/96/quickbooks.png" alt="QuickBooks">
                QuickBooks
            </a>
            <a href="https://www.instagram.com/customcrustkitchen/" target="_blank" class="quick-link-card">
                <img class="quick-link-icon" src="https://img.icons8.com/fluency/96/instagram-new.png" alt="Instagram">
                Instagram
            </a>
        </div>
    """, unsafe_allow_html=True)

    tabs = st.tabs(["📋 Event Quoter", "🍕 Recipe Book", "⚖️ Dough Prep Calc", "🗄️ The Vault"])

    # --- TAB 1: EVENT QUOTER ---
    with tabs[0]:
        st.write("##")
        st.markdown("### 🎫 Automatic Event Quoter")
        st.markdown("<p style='color: #888;'>Enter the guest count. The app assumes 2.5 slices per adult to calculate the required 16\" pies.</p>", unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        guests = col1.number_input("Number of Guests", min_value=1, value=50)
        event_fee = col2.number_input("Flat Travel/Setup Fee ($)", value=150.0)
        
        slices_needed = guests * 2.5
        pies_needed = math.ceil(slices_needed / 8)
        
        st.write("---")
        st.markdown(f"#### 🍕 Requires: {pies_needed} Large (16\") Pizzas")
        
        # Simple distribution: 40% Cheese, 40% Pepperoni, 20% Specialty
        cheese_pies = math.ceil(pies_needed * 0.40)
        pep_pies = math.ceil(pies_needed * 0.40)
        spec_pies = pies_needed - cheese_pies - pep_pies
        
        cost_cheese = cheese_pies * get_recipe_cost("The Plain Jane 16\"")
        cost_pep = pep_pies * get_recipe_cost("The Premium Pepperoni 16\"")
        cost_spec = spec_pies * get_recipe_cost("The Carnivore 16\"")
        total_food_cost = cost_cheese + cost_pep + cost_spec
        
        retail_cheese = cheese_pies * menu_prices["The Plain Jane 16\""]
        retail_pep = pep_pies * menu_prices["The Premium Pepperoni 16\""]
        retail_spec = spec_pies * menu_prices["The Carnivore 16\""]
        total_retail = retail_cheese + retail_pep + retail_spec + event_fee
        
        profit = total_retail - total_food_cost
        margin = (profit / total_retail) * 100 if total_retail > 0 else 0

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Recommended Cheese", f"{cheese_pies} Pies")
        m2.metric("Recommended Pepperoni", f"{pep_pies} Pies")
        m3.metric("Recommended Specialty", f"{spec_pies} Pies")
        m4.metric("Raw Food Cost", f"${total_food_cost:,.2f}")
        
        st.markdown(f"""
        <div style="text-align: center; padding: 20px; background-color: #1a1a1a; border-radius: 10px; border: 1px solid #c5a059; margin-top: 20px;">
            <h3 style="margin:0; color: #8b949e;">Suggested Quote to Client</h3>
            <div style="margin:0; font-size: 3rem; font-weight: bold; color: #c5a059;">${total_retail:,.2f}</div>
            <p style="color: #238636; font-weight: bold;">Estimated Profit: ${profit:,.2f} ({margin:.1f}% Margin)</p>
        </div>
        """, unsafe_allow_html=True)

    # --- TAB 2: RECIPE BOOK ---
    with tabs[1]:
        st.write("##")
        st.markdown("### 📖 Standardized Build Sheets")
        selected_pie = st.selectbox("Select Menu Item", list(menu_prices.keys()))
        
        df_recipe = recipes_data[recipes_data['Recipe'] == selected_pie]
        cost = get_recipe_cost(selected_pie)
        price = menu_prices[selected_pie]
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Retail Price", f"${price:,.2f}")
        c2.metric("Food Cost", f"${cost:,.2f}")
        c3.metric("Margin", f"{((price-cost)/price)*100:.1f}%")
        
        st.dataframe(df_recipe[['Ingredient', 'Ounces']], use_container_width=True, hide_index=True)

    # --- TAB 3: DOUGH PREP CALC ---
    with tabs[2]:
        st.write("##")
        st.markdown("### ⚖️ Master Dough Batch Calculator")
        st.markdown("<p style='color: #888;'>Based on 60% Hydration, 2.5% Salt, 0.5% Yeast.</p>", unsafe_allow_html=True)
        
        c1, c2 = st.columns(2)
        qty_12 = c1.number_input("How many 12\" Dough Balls? (9 oz each)", min_value=0, value=0)
        qty_16 = c2.number_input("How many 16\" Dough Balls? (16 oz each)", min_value=0, value=20)
        
        total_ounces = (qty_12 * 9) + (qty_16 * 16)
        total_grams = total_ounces * 28.3495 # Convert oz to grams
        
        # Baker's Math (Total % = 100 + 60 + 2.5 + 0.5 = 163%)
        flour_g = total_grams / 1.63
        water_g = flour_g * 0.60
        salt_g = flour_g * 0.025
        yeast_g = flour_g * 0.005
        
        st.write("---")
        st.markdown("#### 🥣 Scale Weights (Grams)")
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("🌾 Flour (100%)", f"{flour_g:,.0f} g")
        m2.metric("💧 Water (60%)", f"{water_g:,.0f} g")
        m3.metric("🧂 Salt (2.5%)", f"{salt_g:,.0f} g")
        m4.metric("🦠 Yeast (0.5%)", f"{yeast_g:,.1f} g")

    # --- TAB 4: THE VAULT ---
    with tabs[3]:
        st.write("##")
        st.markdown("### 🗄️ Document Vault")
        st.markdown("<p style='color: #888;'>Important business documents synced from your Google Sheet.</p>", unsafe_allow_html=True)
        if not vault_df.empty:
            for index, row in vault_df.iterrows():
                name = row.get('document name') or row.get('name') or "Unnamed Doc"
                link = row.get('link') or row.get('url') or "#"
                if link and str(link).startswith('http'):
                    st.markdown(f'<a href="{link}" target="_blank" class="vault-link">📄 {name}</a>', unsafe_allow_html=True)
                else:
                    st.markdown(f'<div class="vault-link">📄 {name} (No Link)</div>', unsafe_allow_html=True)
        else:
            st.info("Vault is currently empty. Add links to your Google Sheet 'Vault_Index' tab.")

if __name__ == "__main__":
    main()
