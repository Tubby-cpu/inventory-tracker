import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import hashlib

# ====================== PROFESSIONAL DESIGN ======================
st.set_page_config(page_title="Your Clinic Group • Inventory", layout="centered", page_icon="Cross")

st.markdown("""
<style>
    .big-title {font-size: 48px !important; font-weight: bold; color: #0066cc; text-align: center;}
    .subtitle {font-size: 22px !important; color: #555; text-align: center; margin-bottom: 40px;}
    .login-box {max-width: 420px; margin: 0 auto; padding: 40px; background: white; 
                border-radius: 16px; box-shadow: 0 12px 40px rgba(0,0,0,0.12); border: 1px solid #e0e0e0;}
    .stButton>button {width: 100%; background: #0066cc; color: white; font-size: 18px; padding: 14px; border-radius: 12px;}
    .stButton>button:hover {background: #0052a3;}
    header {visibility: hidden;}
    .footer {text-align: center; margin-top: 80px; color: #888; font-size: 15px;}
    .stTabs [data-baseweb="tab"] {font-size: 18px; font-weight: 600;}
</style>
""", unsafe_allow_html=True)

DB_PATH = "inventory.db"

# ====================== USERS ======================
USERS = {
    "capetown": {"password": hashlib.sha256("capetown".encode()).hexdigest(), "role": "user", "clinic": "Cape Town"},
    "sandton": {"password": hashlib.sha256("sandton".encode()).hexdigest(), "role": "user", "clinic": "Sandton"},
    "marshall": {"password": hashlib.sha256("marshall".encode()).hexdigest(), "role": "user", "clinic": "Marshall Town"},
    "gqberha": {"password": hashlib.sha256("gqberha".encode()).hexdigest(), "role": "user", "clinic": "Gqberha"},
    "sandton2": {"password": hashlib.sha256("sandton2".encode()).hexdigest(), "role": "user", "clinic": "Sandton 2"},
    "pretoria": {"password": hashlib.sha256("pretoria".encode()).hexdigest(), "role": "user", "clinic": "Pretoria"},
    "admin": {"password": hashlib.sha256("admin123".encode()).hexdigest(), "role": "admin", "clinic": "All"},
}

# ====================== DATABASE ======================
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS medicines (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, clinic TEXT NOT NULL, drug_name TEXT NOT NULL,
                    generic_name TEXT, strength TEXT, batch_no TEXT, expiry_date DATE,
                    quantity INTEGER, low_stock_threshold INTEGER DEFAULT 20,
                    date_added TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    c.execute('''CREATE TABLE IF NOT EXISTS transactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, clinic TEXT, drug_id INTEGER,
                    type TEXT, quantity INTEGER, patient_name TEXT, remarks TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    conn.commit()
    conn.close()
init_db()

# ====================== CENTERED LOGIN ======================
if "user" not in st.session_state:
    st.markdown('<p class="big-title">Your Clinic Group</p>', unsafe_allow_html=True)
    st.markdown('<p class="subtitle">Smart Pharmacy Inventory System</p>', unsafe_allow_html=True)
    
    with st.container():
        st.markdown('<div class="login-box">', unsafe_allow_html=True)
        st.markdown("### Secure Access")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.button("Login to Inventory"):
            hashed = hashlib.sha256(password.encode()).hexdigest()
            if username in USERS and USERS[username]["password"] == hashed:
                st.session_state.user = username
                st.session_state.role = USERS[username]["role"]
                st.session_state.clinic = USERS[username]["clinic"]
                st.rerun()
            else:
                st.error("Incorrect credentials")
        st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown('<div class="footer">© 2025 Your Clinic Group</div>', unsafe_allow_html=True)
    st.stop()

# ====================== AFTER LOGIN ======================
st.set_page_config(layout="wide")
st.markdown('<p style="font-size: 42px; color: #0066cc; text-align: center; font-weight: bold;">Your Clinic Group</p>', unsafe_allow_html=True)
st.markdown('<p style="text-align: center; color: #555; font-size: 20px; margin-bottom: 30px;">Pharmacy Inventory • Live Across All Sites</p>', unsafe_allow_html=True)

st.sidebar.success(f"Welcome: {st.session_state.user}")
st.sidebar.write(f"**{st.session_state.clinic}**")
if st.sidebar.button("Logout"):
    st.session_state.clear()
    st.rerun()

# ====================== CLINIC SELECTION WITH SECURITY ======================
role = st.session_state.role
user_clinic = st.session_state.clinic

if role == "admin":
    clinic_options = ["All", "Cape Town", "Sandton", "Marshall Town", "Gqberha", "Sandton 2", "Pretoria"]
    selected_clinic = st.selectbox("Select Clinic (Admin Mode)", clinic_options)
    st.sidebar.warning("ADMIN MODE: You can edit any clinic")
else:
    selected_clinic = user_clinic
    st.sidebar.info(f"You are locked to: {selected_clinic}")

# ====================== DATA & HELPERS ======================
def get_df(clinic_filter=None):
    conn = sqlite3.connect(DB_PATH)
    if clinic_filter and clinic_filter != "All":
        df = pd.read_sql_query("SELECT * FROM medicines WHERE clinic = ?", conn, params=(clinic_filter,))
    else:
        df = pd.read_sql_query("SELECT * FROM medicines", conn)
    conn.close()
    if not df.empty:
        df["expiry_date"] = pd.to_datetime(df["expiry_date"])
    return df

def add_transaction(clinic, drug_id, type_, qty, patient="", remarks=""):
    conn = sqlite3.connect(DB_PATH)
    conn.execute("INSERT INTO transactions (clinic, drug_id, type, quantity, patient_name, remarks) VALUES (?,?,?,?,?,?)",
                 (clinic, drug_id, type_, qty, patient, remarks))
    conn.commit()
    conn.close()

df = get_df("All" if (role == "admin" and selected_clinic == "All") else selected_clinic)
tab1, tab2, tab3, tab4 = st.tabs(["Current Stock", "Receive Stock", "Issue Stock", "Full Report"])

# ====================== ALL TABS (WORKING & SECURE) ======================
# [All your working tab code from before goes here — Current Stock, Receive, Issue, Full Report]
# I'm including them fully so you don't lose anything:

# TAB 1: CURRENT STOCK
with tab1:
    st.subheader(f"Stock – {selected_clinic}")
    if df.empty:
        st.info("No stock yet")
    else:
        today = pd.to_datetime("today").normalize()
        df["days_to_expiry"] = (df["expiry_date"] - today).dt.days
        df["status"] = "normal"
        df.loc[df["quantity"] <= df["low_stock_threshold"], "status"] = "low_stock"
        df.loc[df["days_to_expiry"] <= 90, "status"] = "near_expiry"
        df.loc[df["days_to_expiry"] <= 0, "status"] = "expired"

        c1, c2, c3 = st.columns(3)
        c1.metric("Expired", len(df[df["status"] == "expired"]))
        c2.metric("Near Expiry", len(df[df["status"] == "near_expiry"]))
        c3.metric("Low Stock", len(df[df["status"] == "low_stock"]))

        display = df[["drug_name", "generic_name", "strength", "batch_no", "expiry_date", "quantity"]].copy()
        display["expiry_date"] = display["expiry_date"].dt.strftime("%Y-%m-%d")
        status_list = df["status"].tolist()

        def highlight_row(row):
            status = status_list[row.name]
            if status == "expired": return ["background: #ffcccc"] * len(row)
            if status == "near_expiry": return ["background: #ffffcc"] * len(row)
            if status == "low_stock": return ["background: #ffcc99"] * len(row)
            return [""] * len(row)

        st.dataframe(display.style.apply(highlight_row, axis=1), use_container_width=True)

# TAB 2 & 3: ONLY WORK ON SELECTED CLINIC
with tab2:
    st.subheader(f"Receive Stock — {selected_clinic}")
    with st.form("receive"):
        drug_name = st.text_input("Drug Name *")
        generic = st.text_input("Generic Name")
        strength = st.text_input("Strength")
        batch = st.text_input("Batch Number *")
        expiry = st.date_input("Expiry Date", min_value=datetime.today())
        qty = st.number_input("Quantity", min_value=1)
        threshold = st.number_input("Low-stock alert", value=20)
        if st.form_submit_button("Add Stock"):
            conn = sqlite3.connect(DB_PATH)
            conn.execute("""INSERT INTO medicines 
                (clinic, drug_name, generic_name, strength, batch_no, expiry_date, quantity, low_stock_threshold)
                VALUES (?,?,?,?,?,?,?,?)""",
                (selected_clinic, drug_name, generic, strength, batch, expiry, qty, threshold))
            drug_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
            conn.commit()
            conn.close()
            add_transaction(selected_clinic, drug_id, "in", qty)
            st.success("Stock received!")
            st.rerun()

with tab3:
    st.subheader(f"Issue Medicine — {selected_clinic}")
    if df.empty:
        st.info("No stock")
    else:
        df["option"] = df["drug_name"] + " | " + df["batch_no"] + " | Stock: " + df["quantity"].astype(str)
        choice = st.selectbox("Select medicine", df["option"])
        row_idx = df[df["option"] == choice].index[0]
        current_qty = int(df.loc[row_idx, "quantity"])
        drug_id = int(df.loc[row_idx, "id"])

        col1, col2 = st.columns(2)
        col1.write(f"Available: {current_qty}")
        issue_qty = col2.number_input("Qty", min_value=1, max_value=current_qty)

        patient = st.text_input("Patient name")
        remarks = st.text_input("Remarks")

        if st.button("Issue Medicine", type="primary"):
            new_qty = current_qty - issue_qty
            conn = sqlite3.connect(DB_PATH)
            conn.execute("UPDATE medicines SET quantity = ? WHERE id = ?", (new_qty, drug_id))
            conn.commit()
            conn.close()
            add_transaction(selected_clinic, drug_id, "out", issue_qty, patient, remarks)
            st.success(f"Issued {issue_qty} → Stock now: {new_qty}")
            st.rerun()

# TAB 4: FULL REPORT
with tab4:
    st.subheader(f"History — {selected_clinic}")
    conn = sqlite3.connect(DB_PATH)
    history = pd.read_sql_query("""
        SELECT t.timestamp, t.type, m.drug_name, t.quantity, t.patient_name, t.remarks
        FROM transactions t JOIN medicines m ON t.drug_id = m.id
        WHERE t.clinic = ? ORDER BY t.timestamp DESC
    """, conn, params=(selected_clinic,))
    conn.close()
    if not history.empty:
        history["timestamp"] = pd.to_datetime(history["timestamp"]).dt.strftime("%Y-%m-%d %H:%M")
        history["type"] = history["type"].map({"in": "Received", "out": "Issued"})
        st.dataframe(history, use_container_width=True)

st.sidebar.markdown("---")
st.sidebar.markdown("**Your Clinic Group** • 2025")
