import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
from db_manager import DBManager
from ocr_engine import OCREngine
from PIL import Image
import os

# Page Config
st.set_page_config(page_title="Recurring Tracker", layout="wide")

# Initialize DB & OCR
@st.cache_resource
def get_db():
    return DBManager()

@st.cache_resource
def get_ocr():
    return OCREngine()

db = get_db()
ocr = get_ocr()

# --- Helper Functions ---
def get_status_info(due_day):
    """Calculates days left and returns color + status."""
    today = date.today()
    # Handle end of month (31 logic)
    actual_due_day = min(due_day, 28)
    due_date = date(today.year, today.month, actual_due_day)
    
    days_left = (due_date - today).days
    
    # Logic: 3 days = Green, 2 days = Yellow, 1 day/Today/Past = Red
    if days_left == 3:
        return "#E8F5E9", f"Upcoming (3 days left)", True
    elif days_left == 2:
        return "#FFF9C4", f"Due in 2 days", True
    elif days_left <= 1:
        return "#FFCDD2", f"DUE SOON / PAST DUE", True
    else:
        return "#F5F5F5", "Future", False # Not showing yet

# --- Navigation Menu ---
with st.sidebar:
    st.title("💸 Tracker Menu")
    menu = st.radio("Go to:", ["🏠 Home", "➕ Add New", "📜 History"])
    st.divider()

# --- Page: Add New ---
if menu == "➕ Add New":
    st.title("Manage Recurring Items")
    with st.form("add_property", clear_on_submit=True):
        st.subheader("Add New Bill/Property")
        new_alias = st.text_input("Alias (e.g., Rent, Meralco)")
        new_amount = st.number_input("Expected Amount (₱)", min_value=0.0)
        new_due_day = st.number_input("Due Day (1-31)", min_value=1, max_value=31)
        if st.form_submit_button("Add Recurring Item"):
            if new_alias and new_amount > 0:
                db.add_property(new_alias, new_amount, new_due_day)
                st.success(f"Added {new_alias} to list!")
            else:
                st.warning("Please fill up all fields.")

# --- Page: History ---
elif menu == "📜 History":
    st.title("Payment History")
    history = db.get_payment_history()
    if not history:
        st.info("No payments recorded yet.")
    else:
        df = pd.DataFrame(history, columns=["Property", "Date Paid", "Month Reference", "Verified", "Amount"])
        st.dataframe(df, use_container_width=True)

# --- Page: Home (Dashboard) ---
else:
    st.title("🏠 Action Dashboard")
    current_month = datetime.now().strftime("%Y-%m")
    properties = db.get_properties()
    
    active_tiles = 0
    cols = st.columns(3)
    
    for prop in properties:
        prop_id, alias, amount, due_day = prop
        payment = db.get_payment_for_month(prop_id, current_month)
        is_paid = payment is not None and payment[5] # verified = True
        
        # Calculate visibility
        bg_color, status_text, should_show = get_status_info(due_day)
        
        # IF not paid AND (newly added OR due soon)
        if not is_paid and should_show:
            with cols[active_tiles % 3]:
                st.markdown(f"""
                    <div style="background-color: {bg_color}; padding: 20px; border-radius: 12px; border-left: 10px solid rgba(0,0,0,0.1); color: #333;">
                        <h2 style="margin: 0;">{alias}</h2>
                        <h3 style="margin: 0; color: #555;">₱{amount:,.2f}</h3>
                        <p style="margin: 10px 0 0 0; font-weight: bold;">{status_text}</p>
                    </div>
                """, unsafe_allow_html=True)
                
                uploaded_file = st.file_uploader(f"Scan Receipt", key=f"file_{prop_id}")
                if uploaded_file is not None:
                    with st.spinner("Analyzing Receipt..."):
                        img = Image.open(uploaded_file)
                        text = ocr.extract_text(img)
                        verified = ocr.verify_amount(text, amount)
                        db.record_payment(prop_id, current_month, "CLOUD", verified)
                        if verified:
                            st.balloons()
                            st.success("Verified! Moving to history...")
                            st.rerun()
                        else:
                            st.error("Amount mismatch! Try again.")
                st.divider()
                active_tiles += 1

    if active_tiles == 0:
        st.success("Everything is paid! Your home is empty. ☕")
        st.image("https://cdn-icons-png.flaticon.com/512/3063/3063822.png", width=150)
