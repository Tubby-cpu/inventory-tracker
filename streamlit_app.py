import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import hashlib

# ====================== PROFESSIONAL DESIGN ======================
st.set_page_config(page_title="Your Clinic Group • Inventory", layout="centered", page_icon="Cross")

# Beautiful clinical styling
st.markdown("""
<style>
    .big-title {font-size: 48px !important; font-weight: bold; color: #0066cc; text-align: center; margin-bottom: 0px;}
    .subtitle {font-size: 22px !important; color: #555; text-align: center; margin-bottom: 40px;}
    .login-box {max-width: 420px; margin: 0 auto; padding: 40px; background: white; 
                border-radius: 16px; box-shadow: 0 12px 40px rgba(0,0,0,0.12); border: 1px solid #e0e0e0;}
    .stButton>button {width: 100%; background: #0066cc; color: white; font-size: 18px; 
                      padding: 14px; border-radius: 12px; font-weight: bold;}
    .stButton>button:hover {background: #0052a3;}
    header {visibility: hidden;}
    .css-1d391kg {padding: 1rem;}
    .footer {text-align: center; margin-top: 80px; color: #888; font-size: 15px;}
    .report-table {font-size: 16px;}
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
    st.markdown('<p class="subtitle">Smart Pharmacy Inventory • Live Across All Sites</p>', unsafe_allow_html=True)
    
    with st.container():
        st.markdown('<div class="login-box">', unsafe_allow_html=True)
        st.markdown("### Secure Access")
        username = st.text_input("Username", placeholder="e.g. capetown")
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
    
    st.markdown('<div class="footer">© 2025 Your Clinic Group • Professional Healthcare Management</div>', unsafe_allow_html=True)
    st.stop()

# ====================== AFTER LOGIN — FULL APP ======================
st.set_page_config(layout="wide")  # Switch to wide after login
st.markdown('<p style="font-size: 42px; color: #0066cc; text-align: center; font-weight: bold;">Your Clinic Group</p>', unsafe_allow_html=True)
st.markdown('<p style="text-align: center; color: #555; font-size: 20px; margin-bottom: 30px;">Pharmacy Inventory System • Live Across All Sites</p>', unsafe_allow_html=True)

# Sidebar
st.sidebar.success(f"Welcome: {st.session_state.user}")
st.sidebar.write(f"**{st.session_state.clinic}**")
if st.sidebar.button("Logout"):
    st.session_state.clear()
    st.rerun()

# ====================== HELPERS ======================
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

# Clinic selector
role = st.session_state.role
user_clinic = st.session_state.clinic
if role == "admin":
    clinic_options = ["All", "Cape Town", "Sandton", "Marshall Town", "Gqberha", "Sandton 2", "Pretoria"]
    selected_clinic = st.selectbox("View Clinic", clinic_options, key="admin_view")
else:
    selected_clinic = user_clinic

df = get_df("All" if (role == "admin" and selected_clinic == "All") else selected_clinic)
tab1, tab2, tab3, tab4 = st.tabs(["Current Stock", "Receive Stock", "Issue Stock", "Full Report"])

# Keep your existing working tabs 1–3 here (Current Stock, Receive, Issue) — they are perfect

# ====================== TAB 4: FULL REPORT WITH PATIENTS & REMARKS ======================
with tab4:
    st.subheader(f"Transaction History — {selected_clinic}")
    conn = sqlite3.connect(DB_PATH)
    history = pd.read_sql_query("""
        SELECT t.timestamp, t.type, m.drug_name, m.batch_no, t.quantity, t.patient_name, t.remarks
        FROM transactions t
        JOIN medicines m ON t.drug_id = m.id
        WHERE t.clinic = ?
        ORDER BY t.timestamp DESC
    """, conn, params=(selected_clinic,))
    conn.close()

    if history.empty:
        st.info("No transactions recorded yet.")
    else:
        history["timestamp"] = pd.to_datetime(history["timestamp"]).dt.strftime("%Y-%m-%d %H:%M")
        history["type"] = history["type"].map({"in": "Received", "out": "Issued"})
        history.rename(columns={
            "timestamp": "Date & Time", "type": "Action", "drug_name": "Medicine",
            "batch_no": "Batch", "quantity": "Qty", "patient_name": "Patient", "remarks": "Remarks"
        }, inplace=True)

        st.dataframe(history[["Date & Time", "Action", "Medicine", "Batch", "Qty", "Patient", "Remarks"]], 
                     use_container_width=True)

        csv = history.to_csv(index=False).encode()
        st.download_button("Download Full Report", csv, 
                          f"Report_{selected_clinic.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.csv", "text/csv")

st.sidebar.markdown("---")
st.sidebar.markdown("**Your Clinic Group** • 2025")
