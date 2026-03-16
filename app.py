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
    try:
        return DBManager()
    except Exception as e:
        st.error(f"Failed to connect to Database: {e}")
        return None

@st.cache_resource
def get_ocr():
    return OCREngine()

db = get_db()
ocr = get_ocr()

# --- Helper Functions ---
def get_status_info(due_day):
    """Calculates days left and returns color + status."""
    today = date.today()
    actual_due_day = min(due_day, 28)
    due_date = date(today.year, today.month, actual_due_day)
    
    days_left = (due_date - today).days
    
    if days_left == 3:
        return "#E8F5E9", f"Upcoming (3 days left)", True
    elif days_left == 2:
        return "#FFF9C4", f"Due in 2 days", True
    elif days_left <= 1:
        return "#FFCDD2", f"DUE SOON / PAST DUE", True
    else:
        return "#F5F5F5", "Future", False

# --- Modal (Dialog) for Payment ---
@st.dialog("Complete Your Payment")
def pay_modal(prop_id, alias, amount):
    st.write(f"#### Paying for: **{alias}**")
    st.write(f"Expected Amount: **₱{amount:,.2f}**")
    st.divider()
    
    uploaded_file = st.file_uploader("📸 Upload or Take a Picture of Receipt", key=f"upload_{prop_id}")
    
    if uploaded_file:
        with st.spinner("Analyzing Receipt..."):
            img = Image.open(uploaded_file)
            # Display preview
            st.image(img, caption="Preview", use_container_width=True)
            
            text = ocr.extract_text(img)
            verified = ocr.verify_amount(text, amount)
            
            if st.button("Confirm & Verify", use_container_width=True, type="primary"):
                current_month = datetime.now().strftime("%Y-%m")
                db.record_payment(prop_id, current_month, "CLOUD", verified)
                
                if verified:
                    st.success("✅ Match Found! Payment Verified.")
                    st.balloons()
                    st.rerun()
                else:
                    st.error("❌ Amount mismatch! Manual review required.")
                    st.write(f"Detected Text: {text}")

# --- Navigation Menu ---
with st.sidebar:
    st.title("💸 Tracker Menu")
    menu = st.radio("Go to:", ["🏠 Home", "📋 All Bills", "➕ Add New", "📜 History"])
    st.divider()

if db is None:
    st.warning("Database is not connected.")
else:
    # --- Page: Add New ---
    if menu == "➕ Add New":
        st.title("Manage Recurring Items")
        with st.form("add_property", clear_on_submit=True):
            st.subheader("Add New Bill/Property")
            new_alias = st.text_input("Alias (e.g., Rent, Meralco)")
            new_amount = st.number_input("Expected Amount (₱)", min_value=0.0)
            new_due_day = st.number_input("Due Day (1-31)", min_value=1, max_value=31)
            if st.form_submit_button("Add Recurring Item", use_container_width=True):
                if new_alias and new_amount > 0:
                    try:
                        db.add_property(new_alias, new_amount, new_due_day)
                        st.success(f"Added {new_alias} to list!")
                    except Exception as e:
                        st.error(f"Error: {e}")
                else:
                    st.warning("Please fill up all fields.")

    # --- Page: All Bills ---
    elif menu == "📋 All Bills":
        st.title("All Registered Bills")
        try:
            properties = db.get_properties()
            if not properties:
                st.info("No bills registered yet.")
            else:
                cols = st.columns(3)
                for idx, prop in enumerate(properties):
                    prop_id, alias, amount, due_day = prop
                    with cols[idx % 3]:
                        st.markdown(f"""
                            <div style="background-color: #ffffff; padding: 20px; border-radius: 15px; border: 1px solid #eee; box-shadow: 2px 2px 10px rgba(0,0,0,0.05); color: #333;">
                                <h3 style="margin: 0; color: #2C3E50;">{alias}</h3>
                                <h4 style="margin: 0; color: #7F8C8D;">₱{amount:,.2f}</h4>
                                <p style="margin: 10px 0 0 0; font-size: 0.9em;">📅 <b>Due Day:</b> {due_day}</p>
                            </div>
                        """, unsafe_allow_html=True)
                        st.write("") # Spacer
        except Exception as e:
            st.error(f"Error: {e}")

    # --- Page: History ---
    elif menu == "📜 History":
        st.title("Payment History")
        try:
            history = db.get_payment_history()
            if not history:
                st.info("No payments recorded yet.")
            else:
                df = pd.DataFrame(history, columns=["Property", "Date Paid", "Month Reference", "Verified", "Amount"])
                st.dataframe(df, use_container_width=True)
        except Exception as e:
            st.error(f"Error: {e}")

    # --- Page: Home (Dashboard) ---
    else:
        st.title("🏠 Action Dashboard")
        current_month = datetime.now().strftime("%Y-%m")
        try:
            properties = db.get_properties()
            active_tiles = 0
            cols = st.columns(3)
            
            for prop in properties:
                prop_id, alias, amount, due_day = prop
                payment = db.get_payment_for_month(prop_id, current_month)
                is_paid = payment is not None and payment[5]
                
                bg_color, status_text, should_show = get_status_info(due_day)
                
                if not is_paid and should_show:
                    with cols[active_tiles % 3]:
                        # Main Tile
                        st.markdown(f"""
                            <div style="background-color: {bg_color}; padding: 25px; border-radius: 20px; border-bottom: 5px solid rgba(0,0,0,0.1); color: #333; text-align: center;">
                                <h2 style="margin: 0; font-size: 1.5em;">{alias}</h2>
                                <h1 style="margin: 5px 0; font-size: 2em; color: #222;">₱{amount:,.0f}</h1>
                                <p style="margin: 10px 0 0 0; font-weight: bold; opacity: 0.7;">{status_text}</p>
                            </div>
                        """, unsafe_allow_html=True)
                        
                        # Cute Pay Button
                        if st.button(f"Pay {alias} 💸", key=f"btn_{prop_id}", use_container_width=True):
                            pay_modal(prop_id, alias, amount)
                        
                        st.write("") # Spacer
                        active_tiles += 1

            if active_tiles == 0:
                st.success("Everything is paid! Enjoy your coffee. ☕")
                st.image("https://cdn-icons-png.flaticon.com/512/3063/3063822.png", width=150)
        except Exception as e:
            st.error(f"Error: {e}")
