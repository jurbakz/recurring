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
def get_status_color(due_day, is_paid):
    if is_paid:
        return "green"
    
    today = date.today()
    # Handle end of month (31 logic)
    actual_due_day = min(due_day, 28) # Simple logic for now
    due_date = date(today.year, today.month, actual_due_day)
    
    if today >= due_date:
        return "red"
    elif (due_date - today).days <= 3:
        return "yellow"
    else:
        return "blue" # Far from due

# --- Sidebar Management ---
with st.sidebar:
    st.title("🏠 Prop Management")
    with st.form("add_property"):
        new_alias = st.text_input("Alias (e.g. Condo)")
        new_amount = st.number_input("Amount", min_value=0.0)
        new_due_day = st.number_input("Due Day (1-31)", min_value=1, max_value=31)
        if st.form_submit_button("Add Property"):
            db.add_property(new_alias, new_amount, new_due_day)
            st.success("Property added!")

# --- Main Dashboard ---
st.title("💸 Recurring Expense Dashboard")

current_month = datetime.now().strftime("%Y-%m")
properties = db.get_properties()

if not properties:
    st.info("Add a property in the sidebar to get started!")
else:
    cols = st.columns(3)
    for idx, prop in enumerate(properties):
        prop_id, alias, amount, due_day = prop
        payment = db.get_payment_for_month(prop_id, current_month)
        is_paid = payment is not None and payment[5] # verified = True
        
        color = get_status_color(due_day, is_paid)
        
        with cols[idx % 3]:
            # Simple Tile UI
            status_emoji = "✅" if is_paid else "🔔"
            st.markdown(f"""
                <div style="background-color: {color}; padding: 20px; border-radius: 10px; color: white;">
                    <h3>{status_emoji} {alias}</h3>
                    <p>Amount: ₱{amount:,.2f}</p>
                    <p>Due Day: {due_day}</p>
                    <p>Status: {'PAID' if is_paid else 'PENDING'}</p>
                </div>
            """, unsafe_allow_html=True)
            
            # Action for non-paid tiles
            if not is_paid:
                uploaded_file = st.file_uploader(f"Upload Receipt for {alias}", key=f"file_{prop_id}")
                if uploaded_file is not None:
                    with st.spinner("Processing OCR..."):
                        img = Image.open(uploaded_file)
                        text = ocr.extract_text(img)
                        verified = ocr.verify_amount(text, amount)
                        
                        # In a real cloud app, you'd upload this to Supabase/S3 first
                        # For local testing, we just save the status
                        db.record_payment(prop_id, current_month, "LOCAL_UPLOAD", verified)
                        
                        if verified:
                            st.success(f"Matched ₱{amount}! Verified.")
                            st.rerun()
                        else:
                            st.error("Amount mismatch! Manual review needed.")
                            st.write("Detected Text:", text)
            st.divider()
