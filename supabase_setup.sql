-- STEP 1: Go to Supabase SQL Editor
-- STEP 2: Paste this code and click "Run"

-- 1. Create the properties table
CREATE TABLE IF NOT EXISTS properties (
    id SERIAL PRIMARY KEY,
    alias TEXT NOT NULL,
    amount FLOAT NOT NULL,
    due_day INTEGER NOT NULL
);

-- 2. Create the payments table
CREATE TABLE IF NOT EXISTS payments (
    id SERIAL PRIMARY KEY,
    prop_id INTEGER REFERENCES properties(id),
    date_paid TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    month_ref TEXT NOT NULL,
    receipt_url TEXT,
    verified BOOLEAN DEFAULT FALSE
);

-- 3. Verify: Check the "Table Editor" on the left to see your new tables!
