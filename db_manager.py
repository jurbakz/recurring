import os
import sqlite3
import psycopg2
from psycopg2 import sql
from datetime import datetime

class DBManager:
    def __init__(self):
        # Check Streamlit secrets first, then environment variables
        self.db_url = None
        try:
            import streamlit as st
            if "DATABASE_URL" in st.secrets:
                self.db_url = st.secrets["DATABASE_URL"]
        except:
            pass
            
        if not self.db_url:
            self.db_url = os.getenv("DATABASE_URL")
            
        self.is_postgres = self.db_url is not None
        self.setup_db()

    def get_connection(self):
        if self.is_postgres:
            # For Supabase/Render, we often need to handle the connection string carefully
            # and sometimes force SSL.
            return psycopg2.connect(self.db_url, sslmode='prefer')
        else:
            return sqlite3.connect("database.db")

    def setup_db(self):
        conn = self.get_connection()
        cur = conn.cursor()
        
        # Create properties table
        if self.is_postgres:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS properties (
                    id SERIAL PRIMARY KEY,
                    alias TEXT NOT NULL,
                    amount FLOAT NOT NULL,
                    due_day INTEGER NOT NULL
                )
            """)
        else:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS properties (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    alias TEXT NOT NULL,
                    amount FLOAT NOT NULL,
                    due_day INTEGER NOT NULL
                )
            """)

        # Create payments table
        if self.is_postgres:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS payments (
                    id SERIAL PRIMARY KEY,
                    prop_id INTEGER REFERENCES properties(id),
                    date_paid TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    month_ref TEXT NOT NULL,
                    receipt_url TEXT,
                    verified BOOLEAN DEFAULT FALSE
                )
            """)
        else:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS payments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    prop_id INTEGER,
                    date_paid TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    month_ref TEXT NOT NULL,
                    receipt_url TEXT,
                    verified BOOLEAN DEFAULT FALSE,
                    FOREIGN KEY (prop_id) REFERENCES properties(id)
                )
            """)
        
        conn.commit()
        conn.close()

    def get_properties(self):
        conn = self.get_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM properties")
        rows = cur.fetchall()
        conn.close()
        return rows

    def add_property(self, alias, amount, due_day):
        conn = self.get_connection()
        cur = conn.cursor()
        cur.execute("INSERT INTO properties (alias, amount, due_day) VALUES (%s, %s, %s)" if self.is_postgres else "INSERT INTO properties (alias, amount, due_day) VALUES (?, ?, ?)", (alias, amount, due_day))
        conn.commit()
        conn.close()

    def get_payment_for_month(self, prop_id, month_ref):
        conn = self.get_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM payments WHERE prop_id = %s AND month_ref = %s" if self.is_postgres else "SELECT * FROM payments WHERE prop_id = ? AND month_ref = ?", (prop_id, month_ref))
        row = cur.fetchone()
        conn.close()
        return row

    def record_payment(self, prop_id, month_ref, receipt_url, verified):
        conn = self.get_connection()
        cur = conn.cursor()
        cur.execute("INSERT INTO payments (prop_id, month_ref, receipt_url, verified) VALUES (%s, %s, %s, %s)" if self.is_postgres else "INSERT INTO payments (prop_id, month_ref, receipt_url, verified) VALUES (?, ?, ?, ?)", (prop_id, month_ref, receipt_url, verified))
        conn.commit()
        conn.close()

    def get_payment_history(self):
        conn = self.get_connection()
        cur = conn.cursor()
        # Use a JOIN to get aliases instead of IDs
        query = """
            SELECT p.alias, pay.date_paid, pay.month_ref, pay.verified, p.amount
            FROM payments pay
            INNER JOIN properties p ON pay.prop_id = p.id
            ORDER BY pay.date_paid DESC
        """
        cur.execute(query)
        rows = cur.fetchall()
        conn.close()
        return rows
