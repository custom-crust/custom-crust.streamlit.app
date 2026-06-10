import streamlit as st
import pandas as pd
import math
import os
import datetime
from streamlit_gsheets import GSheetsConnection
from fpdf import FPDF  

# Try to load the calendar parsers
try:
    import requests
    from ics import Calendar
    import arrow
    HAS_CALENDAR_LIBS = True
except ImportError:
    HAS_CALENDAR_LIBS = False

# --- 1. CONFIGURATION & SECURITY ---
st.set_page_config(page_title="CCK Command Center", layout="wide", page_icon="🍕")
SHEET_URL = "https://docs.google.com/spreadsheets/d/1yqbd35J140KWT7ui8Ggqn68_OfGXb1wofViJRcSgZBU/edit"

# *** YOUR MASTER PIN CODE ***
ACCESS_PIN = "CCK2026!"

# *** OUTLOOK CALENDAR LINK ***
OUTLOOK_CALENDAR_LINK = "https://outlook.live.com/owa/calendar/00000000-0000-0000-0000-000000000000/26efbfea-6ffe-4049-b3dc-4f9ac91ac1fc/cid-2BEC859542F27B9D/calendar.ics"

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
    
    /* Sleek Quoter UI & Login */
    .quote-box, .login-box {
        background-color: #1a1a1a; border: 1px solid rgba(197, 160, 89, 0.3);
        border-radius: 8px; padding: 30px; margin-bottom: 20px;
    }
    .login-box {max-width: 400px; margin: 100px auto; text-align: center;}
    .quote-header {font-family: 'Playfair Display', serif; font-size: 1.8rem; color: #c5a059; border-bottom: 1px solid #333; padding-bottom: 10px; margin-bottom: 20px;}
    .quote-row {display: flex; justify-content: space-between; margin-bottom: 12px; font-size: 1.1rem; color: #e6edf3;}
    .quote-row.total {font-weight: bold; font-size: 1.5rem; color: #c5a059; border-top: 1px solid #333; padding-top: 15px; margin-top: 15px;}
    .quote-row.profit {color: #238636; font-weight: 600; font-size: 1.2rem;}
    
    /* Form Elements */
    div[data-testid="stForm"] {background-color: #1a1a1a; border: 1px solid #333;}
    .stDataFrame {border: 1px solid rgba(197, 160, 89, 0.3) !important; border-radius: 8px !important;}
    </style>
""", unsafe_allow_html=True)

# --- SECURITY GATE ---
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.markdown("""
        <div class="login-box">
            <h2 style="margin-bottom: 10px;">Restricted Access</h2>
            <p style="color: #b0b0b0; font-size: 0.9rem; margin-bottom: 30px;">Custom Crust Kitchen Internal Portal</p>
        </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        pin_input = st.text_input("Enter PIN", type="password", placeholder="••••••••")
        if st.button("Unlock Command Center", use_container_width=True):
            if pin_input == ACCESS_PIN:
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("Invalid PIN. Access Denied.")
    st.stop()

# --- 3. HARDCODED MASTER DATA ENGINE ---
ingredients_data = pd.DataFrame([
    ["10\" Dough Ball", 0.95], ["12\" Dough Ball", 1.25], ["14\" Dough Ball", 1.85],
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
    ["The Plain Jane 14\"", "14\" Dough Ball", 1], ["The Plain Jane 14\"", "House Pizza Sauce", 8], ["The Plain Jane 14\"", "Grande Mozzarella", 13],
    ["The Premium Pepperoni 14\"", "14\" Dough Ball", 1], ["The Premium Pepperoni 14\"", "House Pizza Sauce", 8], ["The Premium Pepperoni 14\"", "Grande Mozzarella", 12], ["The Premium Pepperoni 14\"", "Premium Sliced Pepperoni", 4.5],
    ["The Carnivore 14\"", "14\" Dough Ball", 1], ["The Carnivore 14\"", "House Pizza Sauce", 7], ["The Carnivore 14\"", "Grande Mozzarella", 10], ["The Carnivore 14\"", "Premium Sliced Pepperoni", 3], ["The Carnivore 14\"", "Fontanini Sausage", 4], ["The Carnivore 14\"", "Candied Bacon", 3], ["The Carnivore 14\"", "Mike's Hot Honey", 1],
    ["The Bianco Veggie 14\"", "14\" Dough Ball", 1], ["The Bianco Veggie 14\"", "Sliced Garlic", 1], ["The Bianco Veggie 14\"", "Grande Mozzarella", 8], ["The Bianco Veggie 14\"", "Ricotta Cheese", 5], ["The Bianco Veggie 14\"", "Green Peppers", 4], ["The Bianco Veggie 14\"", "Black Olives", 3],
    ["The Buffalo Soldier 14\"", "14\" Dough Ball", 1], ["The Buffalo Soldier 14\"", "Buffalo Sauce", 5], ["The Buffalo Soldier 14\"", "Grande Mozzarella", 9], ["The Buffalo Soldier 14\"", "Diced Chicken", 7], ["The Buffalo Soldier 14\"", "Blue Cheese Crumbles", 2],
    ["Custom 14\" (Standard Toppings)", "14\" Dough Ball", 1], ["Custom 14\" (Standard Toppings)", "House Pizza Sauce", 8], ["Custom 14\" (Standard Toppings)", "Grande Mozzarella", 12], ["Custom 14\" (Standard Toppings)", "Green Peppers", 3], ["Custom 14\" (Standard Toppings)", "Onion", 3],
    ["Custom 14\" (Premium Toppings)", "14\" Dough Ball", 1], ["Custom 14\" (Premium Toppings)", "House Pizza Sauce", 8], ["Custom 14\" (Premium Toppings)", "Grande Mozzarella", 12], ["Custom 14\" (Premium Toppings)", "Premium Sliced Pepperoni", 3], ["Custom 14\" (Premium Toppings)", "Ricotta Cheese", 3],
    ["Kids Cheese 12\"", "12\" Dough Ball", 1], ["Kids Cheese 12\"", "House Pizza Sauce", 4.5], ["Kids Cheese 12\"", "Grande Mozzarella", 7],
    ["Kids Pepperoni 12\"", "12\" Dough Ball", 1], ["Kids Pepperoni 12\"", "House Pizza Sauce", 4.5], ["Kids Pepperoni 12\"", "Grande Mozzarella", 7], ["Kids Pepperoni 12\"", "Premium Sliced Pepperoni", 1.5],
    ["Kids 2-Topping 12\"", "12\" Dough Ball", 1], ["Kids 2-Topping 12\"", "House Pizza Sauce", 4.5], ["Kids 2-Topping 12\"", "Grande Mozzarella", 7], ["Kids 2-Topping 12\"", "Green Peppers", 1], ["Kids 2-Topping 12\"", "Onion", 1]
], columns=["Recipe", "Ingredient", "Ounces"])

menu_prices = {
    "The Plain Jane 14\"": 17.00, "The Premium Pepperoni 14\"": 23.00, "The Carnivore 14\"": 26.00, 
    "The Bianco Veggie 14\"": 24.00, "The Buffalo Soldier 14\"": 24.00, "Custom 14\" (Standard Toppings)": 24.00,
    "Custom 14\" (Premium Toppings)": 28.00, "Kids Cheese 12\"": 10.00, "Kids Pepperoni 12\"": 12.00, "Kids 2-Topping 12\"": 14.00
}

# --- 4. DATA HELPERS ---
def load_gsheets():
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        return conn.read(spreadsheet=SHEET_URL, worksheet="Vault_Index", ttl=600)
    except: 
        return pd.DataFrame()

# --- 5. PDF GENERATOR ---
def generate_pdf_quote(client_name, event_date, event_address, event_desc, printable_items, event_fee, gross_subtotal, discount_amount, discount_pct, tax_amount, cc_fee_amount, final_quote, adult_pies, kid_pies, adult_tier):
    pdf = FPDF()
    pdf.add_page()
    gold, black, gray = (197, 160, 89), (30, 30, 30), (100, 100, 100)
    
    logo_path = "logo.png" if os.path.exists("logo.png") else ("CCK_Logo.png" if os.path.exists("CCK_Logo.png") else None)
    if logo_path:
        pdf.image(logo_path, x=(pdf.w - 30) / 2, y=10, w=30)
        pdf.ln(35) 
    else:
        pdf.ln(15)
        
    pdf.set_font("Arial", 'B', 24); pdf.set_text_color(*gold); pdf.cell(0, 12, "CUSTOM CRUST KITCHEN", ln=True, align='C')
    pdf.set_font("Arial", 'B', 12); pdf.set_text_color(*gray); pdf.cell(0, 8, "CATERING ESTIMATE", ln=True, align='C')
    pdf.line(10, pdf.get_y() + 5, 200, pdf.get_y() + 5); pdf.ln(10)
    
    pdf.set_font("Arial", 'B', 12); pdf.set_text_color(*black); pdf.cell(0, 8, "EVENT DETAILS", ln=True)
    pdf.set_font("Arial", '', 11); pdf.set_text_color(*gray)
    pdf.cell(0, 6, f"Client: {client_name}", ln=True); pdf.cell(0, 6, f"Date: {event_date}", ln=True)
    pdf.cell(0, 6, f"Location: {event_address}", ln=True); pdf.cell(0, 6, f"Event Notes: {event_desc}", ln=True); pdf.ln(10)
    
    pdf.set_font("Arial", 'B', 14); pdf.set_text_color(*black); pdf.cell(0, 10, "ORDER SUMMARY", ln=True)
    pdf.set_font("Arial", '', 12); pdf.set_text_color(*black)
    for item in printable_items:
        pdf.cell(140, 8, item["desc"], 0, 0); pdf.cell(50, 8, f"${item['total']:,.2f}", 0, 1, 'R')
    pdf.ln(8)
    
    if len(printable_items) > 0:
        pdf.set_font("Arial", 'B', 11); pdf.set_text_color(*black); pdf.cell(0, 8, "PACKAGE DETAILS & EXCLUSIONS:", ln=True)
        pdf.set_font("Arial", '', 10); pdf.set_text_color(*gray)
        if "Classic" in adult_tier: pdf.cell(0, 6, "- Classic Package Includes: The Plain Jane, The Premium Pepperoni, & The Bianco Veggie.", ln=True)
        else: pdf.cell(0, 6, "- Premium Package Includes: Full Signature Pizza Menu.", ln=True)
        pdf.cell(0, 6, "- Exclusions: Calzones are exclusively for retail service and are not included in catering.", ln=True); pdf.ln(8)
    
    pdf.set_font("Arial", 'B', 14); pdf.set_text_color(*black); pdf.cell(0, 10, "FINANCIALS", ln=True); pdf.set_font("Arial", '', 12)
    pdf.cell(140, 8, "Food & Beverage Subtotal", 0, 0); pdf.cell(50, 8, f"${gross_subtotal:,.2f}", 0, 1, 'R')
    if discount_amount > 0:
        pdf.set_text_color(200, 50, 50); pdf.cell(140, 8, f"Discount ({discount_pct}%)", 0, 0); pdf.cell(50, 8, f"-${discount_amount:,.2f}", 0, 1, 'R'); pdf.set_text_color(*black)
    pdf.cell(140, 8, "Setup / Travel Fee", 0, 0); pdf.cell(50, 8, f"${event_fee:,.2f}", 0, 1, 'R')
    if tax_amount > 0: pdf.cell(140, 8, "MA Meals Tax (7.0%)", 0, 0); pdf.cell(50, 8, f"${tax_amount:,.2f}", 0, 1, 'R')
    if cc_fee_amount > 0: pdf.cell(140, 8, "Credit Card Fee (2.29%)", 0, 0); pdf.cell(50, 8, f"${cc_fee_amount:,.2f}", 0, 1, 'R')
    pdf.line(10, pdf.get_y() + 2, 200, pdf.get_y() + 2); pdf.ln(5)
    
    pdf.set_font("Arial", 'B', 16); pdf.set_text_color(*gold)
    pdf.cell(140, 10, "ESTIMATED TOTAL", 0, 0); pdf.cell(50, 10, f"${final_quote:,.2f}", 0, 1, 'R')
    
    pdf.ln(25); pdf.set_font("Arial", 'I', 10); pdf.set_text_color(*gray)
    pdf.multi_cell(0, 6, "Thank you for choosing Custom Crust Kitchen! This document is an estimate to give you an accurate idea of costs. Final pricing may adjust based on exact headcount, menu alterations, or specific event requirements.", align='C')
    try: return bytes(pdf.output()) 
    except: return pdf.output(dest='S').encode('latin-1') 

# --- 6. MAIN APP ---
def main():
    vault_df = load_gsheets()

    c_left, c_logo, c_right = st.columns([5, 1, 5])
    with c_logo:
        if os.path.exists("CCK_Logo.png"): st.image("CCK_Logo.png", use_container_width=True)
        elif os.path.exists("logo.png"): st.image("logo.png", use_container_width=True)
        else: st.markdown("<h1 style='text-align: center; font-size: 3.5rem; margin-bottom: 0;'>CCK</h1>", unsafe_allow_html=True)
            
    st.markdown("<p style='text-align: center; color: #b0b0b0; letter-spacing: 2px; text-transform: uppercase; margin-bottom: 40px;'>Command Center</p>", unsafe_allow_html=True)

    quick_links_html = """<div class="quick-links-container">
<a href="https://www3.usfoods.com/order" target="_blank" class="quick-link-card"><svg width="35" height="35" viewBox="0 0 24 24" fill="none" stroke="#c5a059" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"></path><polyline points="3.27 6.96 12 12.01 20.73 6.96"></polyline><line x1="12" y1="22.08" x2="12" y2="12"></line></svg>US Foods</a>
<a href="https://qbo.intuit.com" target="_blank" class="quick-link-card"><svg width="35" height="35" viewBox="0 0 24 24" fill="none" stroke="#c5a059" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="2" y="3" width="20" height="14" rx="2" ry="2"></rect><line x1="8" y1="21" x2="16" y2="21"></line><line x1="12" y1="17" x2="12" y2="21"></line></svg>QuickBooks</a>
</div>"""
    st.markdown(quick_links_html, unsafe_allow_html=True)

    tabs = st.tabs(["📅 Calendar", "🎫 Event Quoter", "🍕 Pizza Builder", "📖 Recipe Margins", "🗄️ The Vault"])

    # --- TAB 1: CALENDAR ---
    with tabs[0]:
        st.write("##")
        
        if not HAS_CALENDAR_LIBS:
            st.error("⚠️ ACTION REQUIRED: To load the live calendar directly on this page, open your terminal and run: `pip install ics requests arrow`")
        
        ics_link = OUTLOOK_CALENDAR_LINK
        events = []
        is_dummy_data = False
        debug_info = "No events found in the current week."
        
        st.markdown(f"<h3 style='text-align: center; color: #c5a059; margin-bottom: 0;'>Current Week</h3>", unsafe_allow_html=True)
                
        # Get Current Week Dates
        try:
            today = arrow.now('US/Eastern')
            start_of_week = today.shift(days=-today.weekday()).floor('day')
            end_of_week = start_of_week.shift(days=7)
            
            week_days = []
            for i in range(7):
                day_obj = start_of_week.shift(days=i)
                week_days.append({
                    "day_name": day_obj.format("ddd"),
                    "day_num": day_obj.format("D")
                })
        except:
            week_days = [{"day_name": d, "day_num": ""} for d in ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]]
            start_of_week = None
            end_of_week = None
        
        try:
            # Fetch the raw calendar data with a "Fake Browser" User-Agent to bypass Microsoft Blocks
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            }
            req = requests.get(ics_link, headers=headers, timeout=10)
            
            if req.status_code == 200 and start_of_week:
                c = Calendar(req.text)
                for e in list(c.timeline):
                    event_time_naive = arrow.get(e.begin.naive) 
                    
                    if start_of_week.naive <= event_time_naive < end_of_week.naive:
                        events.append({
                            "day": event_time_naive.format("ddd"),
                            "title": e.name,
                            "time": event_time_naive.format("h:mm A"),
                            "type": "major-event" if "open" in e.name.lower() else "product"
                        })
            else:
                is_dummy_data = True
                debug_info = f"Microsoft Server blocked request. HTTP Status Code: {req.status_code}"
        except Exception as e:
            is_dummy_data = True
            debug_info = f"System Error: {str(e)}"

        if is_dummy_data or len(events) == 0:
            if len(events) == 0 and not is_dummy_data:
                pass # The user simply has an empty schedule this week
            else:
                is_dummy_data = True
                events = [
                    {"day": "Mon", "title": "US Foods Delivery", "time": "9:00 AM", "type": "product"},
                    {"day": "Wed", "title": "Adjust Gas Regulator", "time": "11:00 AM", "type": "operational"},
                    {"day": "Wed", "title": "Karaoke Session", "time": "7:00 PM", "type": "entertainment"},
                    {"day": "Thu", "title": "SOFT LUNCH OPENING", "time": "11:00 AM - 4:00 PM", "type": "major-event"},
                ]
                # Force dummy days to look like a realistic week to avoid confusion
                week_days = [
                    {"day_name": "Mon", "day_num": "8"}, {"day_name": "Tue", "day_num": "9"},
                    {"day_name": "Wed", "day_num": "10"}, {"day_name": "Thu", "day_num": "11"},
                    {"day_name": "Fri", "day_num": "12"}, {"day_name": "Sat", "day_num": "13"},
                    {"day_name": "Sun", "day_num": "14"},
                ]

        # NATIVE UI RENDER 
        calendar_html = """
        <style>
        .weekly-calendar-grid { display: grid; grid-template-columns: repeat(7, 1fr); gap: 15px; margin-top: 10px;}
        .calendar-day { background-color: #1a1a1a; border: 1px solid #333; border-radius: 6px; padding: 15px; min-height: 200px; display: flex; flex-direction: column;}
        .calendar-day:hover { border-color: #c5a059; }
        .day-header { font-size: 0.9rem; text-transform: uppercase; color: #b0b0b0; font-weight: 600; margin-bottom: 15px; display: flex; justify-content: space-between; align-items: center;}
        .day-number { font-size: 1.4rem; color: #f5f5f5;}
        .event-card { font-size: 0.8rem; padding: 10px; border-radius: 4px; font-weight: 600; margin-bottom: 8px; line-height: 1.4;}
        .event-card .time { font-size: 0.7rem; font-weight: 400; color: rgba(255, 255, 255, 0.7); display: block; margin-top: 4px;}
        .product { background-color: #2c3e50; border-left: 3px solid #3498db; }
        .operational { background-color: #27ae60; border-left: 3px solid #2ecc71; }
        .entertainment { background-color: #8e44ad; border-left: 3px solid #9b59b6; }
        .major-event { background-color: rgba(197, 160, 89, 0.2); color: #c5a059; border-left: 3px solid #c5a059; }
        </style>
        
        <div style="background-color: #121212; border: 1px solid rgba(197, 160, 89, 0.3); border-radius: 8px; padding: 30px;">
        """
        
        if is_dummy_data:
            calendar_html += f'<div style="background-color: #332b00; color: #ffd700; padding: 10px; border-radius: 4px; font-size: 0.85rem; margin-bottom: 15px;">⚠️ Displaying placeholder schedule. Please verify your active .ics link is valid.<br><span style="color:#aaa; font-size:0.75rem;">Diagnostic Code: {debug_info}</span></div>'

        calendar_html += '<div class="weekly-calendar-grid">'

        for wd in week_days:
            day_name = wd["day_name"]
            day_num = wd["day_num"]
            day_events = [e for e in events if e["day"] == day_name]
            
            calendar_html += f'<div class="calendar-day"><div class="day-header">{day_name} <span class="day-number">{day_num}</span></div>'
            for ev in day_events:
                calendar_html += f'<div class="event-card {ev["type"]}">{ev["title"]}<span class="time">{ev["time"]}</span></div>'
            calendar_html += '</div>'
            
        calendar_html += '</div></div>'
        st.markdown(calendar_html, unsafe_allow_html=True)

    # --- TAB 2: EVENT QUOTER ---
    with tabs[1]:
        st.write("##")
        c_in, c_out = st.columns([1, 1.5], gap="large")
        with c_in:
            st.markdown("<h3 style='margin-bottom: 20px;'>1. Event Details</h3>", unsafe_allow_html=True)
            c_client1, c_client2 = st.columns(2)
            client_name = c_client1.text_input("Client Name *", placeholder="e.g. Bruno Kreusch")
            event_date = c_client2.text_input("Event Date *", placeholder="e.g. June 18th")
            c_client3, c_client4 = st.columns(2)
            event_address = c_client3.text_input("Event Address *", placeholder="e.g. 123 Main St, Saugus, MA")
            event_desc = c_client4.text_input("Event Notes/Type *", placeholder="e.g. Birthday Buffet in Driveway")
            
            st.markdown("<h3 style='margin-bottom: 10px; margin-top: 20px;'>2. Guest Count & Logistics</h3>", unsafe_allow_html=True)
            c_g, c_k, c_f = st.columns(3)
            adults = c_g.number_input("Est. Adults", min_value=1, value=40, step=5)
            kids = c_k.number_input("Est. Kids", min_value=0, value=10, step=5)
            event_fee = c_f.number_input("Setup Fee ($)", min_value=0.0, value=150.0, step=25.0)
            adult_pies, kid_pies = math.ceil((adults * 3) / 6), math.ceil((kids * 2) / 8) if kids > 0 else 0
            st.info(f"💡 **Prep Guide:** You will need to prep ~**{adult_pies} adult pies** (14\") and **{kid_pies} kids pies** (12\").")
            
            st.markdown("<h3 style='margin-bottom: 10px; margin-top: 20px;'>3. Food Packages (Per Person)</h3>", unsafe_allow_html=True)
            c_food1, c_food2 = st.columns(2)
            adult_tier = c_food1.selectbox("Adult Package", ["Classic ($17/head)", "Premium ($22/head)"])
            kid_tier = c_food2.selectbox("Kids Package", ["Standard ($10/head)"])
            
            st.markdown("<h3 style='margin-bottom: 10px; margin-top: 20px;'>4. Beverages & Fees</h3>", unsafe_allow_html=True)
            c_b1, c_b2 = st.columns(2)
            add_adult_bevs = c_b1.checkbox(f"Adult Bev Package ($5.00/adult)", value=True)
            add_kid_bevs = c_b2.checkbox(f"Kids Bev Package ($3.00/kid)", value=True)
            c_t, c_d, c_c = st.columns(3)
            apply_tax = c_t.checkbox("Add MA Meals Tax", value=True)
            apply_cc = c_c.checkbox("Add CC Fee", value=False)
            discount_pct = c_d.number_input("Discount (%)", value=0.0, step=5.0)

        with c_out:
            printable_items, order_lines = [], ""
            adult_food_price = 17.00 if "Classic" in adult_tier else 22.00
            kid_food_price = 10.00
            food_revenue = (adults * adult_food_price) + (kids * kid_food_price)
            
            if adults > 0:
                order_lines += f'<div class="quote-row"><span>Adult Food Pkg</span> <span>${(adults * adult_food_price):,.2f}</span></div>\n'
                printable_items.append({"desc": f"Adult Food Package", "total": (adults * adult_food_price)})
            if kids > 0:
                order_lines += f'<div class="quote-row"><span>Kids Food Pkg</span> <span>${(kids * kid_food_price):,.2f}</span></div>\n'
                printable_items.append({"desc": f"Kids Food Package", "total": (kids * kid_food_price)})

            beverage_revenue, beverage_cost = 0.0, 0.0
            if add_adult_bevs and adults > 0:
                beverage_revenue += adults * 5.00; beverage_cost += adults * 1.50 
                order_lines += f'<div class="quote-row"><span>Adult Bev Pkg</span> <span>${adults * 5.00:,.2f}</span></div>\n'
                printable_items.append({"desc": f"Adult Beverage Package", "total": adults * 5.00})
            if add_kid_bevs and kids > 0:
                beverage_revenue += kids * 3.00; beverage_cost += kids * 1.00 
                order_lines += f'<div class="quote-row"><span>Kids Bev Pkg</span> <span>${kids * 3.00:,.2f}</span></div>\n'
                printable_items.append({"desc": f"Kids Beverage Package", "total": kids * 3.00})

            gross_subtotal = food_revenue + beverage_revenue
            discount_amount = gross_subtotal * (discount_pct / 100.0)
            taxable_amount = (gross_subtotal - discount_amount) + event_fee
            tax_amount = (taxable_amount * 0.07) if apply_tax else 0.0
            cc_fee_amount = ((taxable_amount + tax_amount) * 0.0229) if apply_cc else 0.0
            final_quote = taxable_amount + tax_amount + cc_fee_amount
            total_internal_cost = ((adult_pies * 4.00) + (kid_pies * 2.00)) + beverage_cost
            profit = taxable_amount - total_internal_cost
            margin = (profit / taxable_amount) * 100 if taxable_amount > 0 else 0.0

            quote_html = f"""<div class="quote-box"><div class="quote-header">Custom Catering Proposal</div>
<div style="color: #b0b0b0; margin-bottom: 15px; font-weight: 600;">ORDER SUMMARY</div>{order_lines}
<div class="quote-row"><span>Food & Beverage Subtotal</span> <span>${gross_subtotal:,.2f}</span></div>"""
            if discount_amount > 0: quote_html += f'\n<div class="quote-row" style="color: #da3633;"><span>Discount</span> <span>-${discount_amount:,.2f}</span></div>'
            quote_html += f'\n<div class="quote-row"><span>Setup / Travel Fee</span> <span>${event_fee:,.2f}</span></div>'
            if apply_tax: quote_html += f'\n<div class="quote-row"><span>MA Meals Tax (7.0%)</span> <span>${tax_amount:,.2f}</span></div>'
            if apply_cc: quote_html += f'\n<div class="quote-row"><span>Credit Card Fee (2.29%)</span> <span>${cc_fee_amount:,.2f}</span></div>'
            quote_html += f"""\n<div class="quote-row total"><span>Total Client Quote</span> <span>${final_quote:,.2f}</span></div>
<div style="margin-top: 20px; padding: 15px; background-color: #121212; border-radius: 6px; border-left: 4px solid #c5a059;">
<div class="quote-row profit" style="margin-bottom: 0;"><span>Projected Net Profit</span> <span>${profit:,.2f} ({margin:.1f}%)</span></div></div></div>"""
            st.markdown(quote_html, unsafe_allow_html=True)
            
            if len(printable_items) > 0 and client_name and event_date and event_address:
                pdf_bytes = generate_pdf_quote(client_name, event_date, event_address, event_desc, printable_items, event_fee, gross_subtotal, discount_amount, discount_pct, tax_amount, cc_fee_amount, final_quote, adult_pies, kid_pies, adult_tier)
                st.download_button(label="📄 Download Official PDF", data=pdf_bytes, file_name=f"CCK_Estimate_{client_name}.pdf", mime="application/pdf", use_container_width=True)

    # --- TAB 3: PIZZA BUILDER ---
    with tabs[2]:
        st.write("##")
        c1, c2 = st.columns([1.2, 1], gap="large")
        with c1:
            base = st.selectbox("Crust Base", ["10\" Dough Ball", "12\" Dough Ball", "14\" Dough Ball"])
            sauce = st.selectbox("Sauce", ["None", "House Pizza Sauce", "Buffalo Sauce"])
            sauce_oz = st.number_input("Sauce Amount (oz)", value=8.0, step=0.5) if sauce != "None" else 0.0
            cheeses = st.multiselect("Cheeses", ["Grande Mozzarella", "Fresh Mozzarella", "Ricotta Cheese"])
            cheese_oz = {ch: st.number_input(f"{ch} (oz)", value=10.0, step=0.5) for ch in cheeses}
            toppings = st.multiselect("Toppings", ["Premium Sliced Pepperoni", "Fontanini Sausage", "Candied Bacon", "Mike's Hot Honey"])
            topping_oz = {t: st.number_input(f"{t} (oz)", value=3.0, step=0.5) for t in toppings}
        with c2:
            total_cost = ing_dict.get(base, 0.0)
            if sauce != "None": total_cost += sauce_oz * ing_dict.get(sauce, 0.0)
            for ch, oz in cheese_oz.items(): total_cost += oz * ing_dict.get(ch, 0.0)
            for t, oz in topping_oz.items(): total_cost += oz * ing_dict.get(t, 0.0)
            st.markdown(f"""<div class="quote-box" style="margin-top: 20px;">
<div class="quote-row"><span>Total Raw Food Cost</span> <span>${total_cost:.2f}</span></div>
<div class="quote-row total" style="color: #238636;"><span>Suggested Price (80% Margin)</span> <span>${total_cost / 0.20 if total_cost > 0 else 0.0:.2f}</span></div></div>""", unsafe_allow_html=True)

    # --- TAB 4: RECIPE MARGINS ---
    with tabs[3]:
        st.write("##")
        selected_pie = st.selectbox("Select Menu Item", list(menu_prices.keys()))
        df_recipe = recipes_data[recipes_data['Recipe'] == selected_pie].copy()
        merged_recipe = pd.merge(df_recipe, ingredients_data, on="Ingredient", how="left")
        cost = (merged_recipe['Ounces'] * merged_recipe['Cost']).sum()
        price = menu_prices[selected_pie]
        c1, c2, c3 = st.columns(3)
        c1.markdown(f"<div class='quote-box' style='text-align:center;'><div>RETAIL PRICE</div><div style='font-size: 2rem;'>${price:,.2f}</div></div>", unsafe_allow_html=True)
        c2.markdown(f"<div class='quote-box' style='text-align:center;'><div>FOOD COST</div><div style='font-size: 2rem; color: #da3633;'>${cost:,.2f}</div></div>", unsafe_allow_html=True)
        c3.markdown(f"<div class='quote-box' style='text-align:center;'><div>PROFIT MARGIN</div><div style='font-size: 2rem; color: #238636;'>{((price-cost)/price)*100:.1f}%</div></div>", unsafe_allow_html=True)

    # --- TAB 5: THE VAULT ---
    with tabs[4]:
        st.write("##")
        if not vault_df.empty:
            vault_html = '<div class="vault-grid">'
            for index, row in vault_df.iterrows():
                name, link = row.get('document name') or row.get('name') or "Doc", row.get('link') or row.get('url') or "#"
                vault_html += f'<a href="{link}" target="_blank" class="doc-card"><div class="doc-title">{name}</div></a>'
            st.markdown(vault_html + '</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()
