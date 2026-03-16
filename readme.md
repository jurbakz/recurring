# 🏠 Recurring Expense Tracker & Verifier: Project Plan

## 📋 1. Project Overview
A Python-based financial dashboard to track monthly dues (Rent, Condo, Utilities) and use **OCR (Optical Character Recognition)** to validate payments via receipt uploads.

---

## 🛠️ 2. Technical Stack
* **Frontend:** `Streamlit` (Hosted on Streamlit Community Cloud - $0)
* **Database:** `PostgreSQL` (Supabase or Render Free Tier - $0)
* **Storage:** `Supabase Storage` or `Cloudinary` (To store receipt images permanently for $0)
* **Logic:** `Pandas` (Date-matching & "End of Month" calculations)
* **Vision/OCR:** `EasyOCR` (To read amounts from Gcash/Bank receipts)
* **Image Processing:** `Pillow` (To handle receipt image uploads)

---

## 🗄️ 3. Database Design (PostgreSQL)

### **Table: `properties`**
| Field | Type | Description |
| :--- | :--- | :--- |
| `id` | SERIAL (PK) | Unique Identifier |
| `alias` | TEXT | e.g., "1st House", "Condo" |
| `amount` | FLOAT | The expected payment (e.g., 7300.0) |
| `due_day` | INT | 1-31 (Special Logic: 31 = End of Month) |

### **Table: `payments`**
| Field | Type | Description |
| :--- | :--- | :--- |
| `id` | SERIAL (PK) | Unique Identifier |
| `prop_id` | INT (FK) | Links to Property |
| `date_paid` | TIMESTAMP | Timestamp of upload |
| `month_ref` | TEXT | Format: "YYYY-MM" |
| `receipt_url`| TEXT | Public URL to the stored image (Supabase/Cloudinary) |
| `verified` | BOOL | Result of OCR match (True/False) |

---

## 🎨 4. Functional Design & Flow

### **A. The Dashboard (Home)**
* **Logic:** On load, the app compares `properties.due_day` against the current date.
* **Tile Status Colors:**
    * 🔴 **Red:** Today is ≥ `due_day` AND no record in `payments` for the current month.
    * 🟡 **Yellow:** Due date is within the next 3 days.
    * 🟢 **Green:** A record exists in `payments` for the current month (Verified).



### **B. The Receipt Scanner (OCR)**
When a file is uploaded to a specific tile:
1.  **Extraction:** The app runs `reader.readtext(image)`.
2.  **Validation:** It looks for the target `amount` (e.g., "7300") in the text strings.
3.  **Action:** * **Match:** Update database to `verified = True` and move tile to "Paid" section.
    * **No Match:** Flag for manual review or re-upload.

---

## 📂 5. Project Structure
```text
expense_tracker/
├── app.py              # Main Streamlit UI & Dashboard
├── db_manager.py       # SQL Queries (CRUD operations)
├── ocr_engine.py       # Receipt processing logic
├── requirements.txt    # streamlit, easyocr, pandas, pillow
└── receipts/           # Folder to archive uploaded images