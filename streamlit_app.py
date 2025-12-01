import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import hashlib

# ====================== AT THE VERY TOP (after imports) ======================
# Replace your current st.set_page_config with this upgraded version
st.set_page_config(
    page_title="Your Clinic Group • Inventory Pro",
    page_icon="⚕️",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://www.yourwebsite.co.za',
        'Report a bug': 'mailto:your.email@domain.com',
        'About': "# Your Clinic Group Inventory System\nProfessional pharmacy management • Built in-house 2025"
    }
)

# Add this CSS for a clean, modern look (paste right after st.set_page_config)
st.markdown("""
<style>
    .css-1d391kg {padding-top: 1rem; padding-bottom: 1rem;}
    .css-1v0mbdj {font-size: 1.1rem !important;}
    .stButton>button {background-color: #0066cc; color: white; border-radius: 8px; padding: 0.5rem 1rem;}
    .stButton>button:hover {background-color: #0052a3;}
    .stSuccess {background-color: #d4edda; border-color: #c3e6cb; color: #155724;}
    header {visibility: hidden;}  /* hides the default Streamlit header */
    .css-18e3th9 {padding-top: 1rem;}
    .css-1y0t9h1 {font-family: 'Segoe UI', sans-serif;}
    h1 {color: #0066cc; text-align: center;}
    .stTabs [data-baseweb="tab"] {font-size: 1.1rem; font-weight: 600;}
</style>
""", unsafe_allow_html=True)

# ====================== REPLACE YOUR CURRENT st.title LINE ======================
st.markdown("""
<div style="text-align: center; padding: 2rem 0;">
    <h1 style="color: #0066cc; margin:0;">Your Clinic Group</h1>
    <p style="color: #555; font-size: 1.3rem; margin:5px;">Smart Pharmacy Inventory • Live Across All Sites</p>
</div>
""", unsafe_allow_html=True)

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
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    clinic TEXT NOT NULL,
                    drug_name TEXT NOT NULL,
                    generic_name TEXT,
                    strength TEXT,
                    batch_no TEXT,
                    expiry_date DATE,
                    quantity INTEGER,
                    low_stock_threshold INTEGER DEFAULT 20,
                    date_added TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    c.execute('''CREATE TABLE IF NOT EXISTS transactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    clinic TEXT,
                    drug_id INTEGER,
                    type TEXT,
                    quantity INTEGER,
                    patient_name TEXT,
                    remarks TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    conn.commit()
    conn.close()
init_db()

# ====================== AUTH ======================
def login():
    if "user" not in st.session_state:
        st.sidebar.title("Login")
        username = st.sidebar.text_input("Username")
        password = st.sidebar.text_input("Password", type="password")
        if st.sidebar.button("Login"):
            hashed = hashlib.sha256(password.encode()).hexdigest()
            if username in USERS and USERS[username]["password"] == hashed:
                st.session_state.user = username
                st.session_state.role = USERS[username]["role"]
                st.session_state.clinic = USERS[username]["clinic"]
                st.rerun()
            else:
                st.sidebar.error("Wrong credentials")
        st.stop()

login()
st.sidebar.success(f"Logged in: {st.session_state.user}")
st.sidebar.write(f"**{st.session_state.clinic}**")
if st.sidebar.button("Logout"):
    st.session_state.clear()
    st.rerun()

# ====================== ALWAYS FRESH DATA ======================
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

# ====================== MAIN ======================
st.title("Clinic Inventory Pro")

role = st.session_state.role
user_clinic = st.session_state.clinic

if role == "admin":
    clinic_options = ["All", "Cape Town", "Sandton", "Marshall Town", "Gqberha", "Sandton 2", "Pretoria"]
    selected_clinic = st.selectbox("View Clinic", clinic_options)
else:
    selected_clinic = user_clinic

# This line forces fresh data every single time
df = get_df("All" if (role == "admin" and selected_clinic == "All") else selected_clinic)

tab1, tab2, tab3, tab4 = st.tabs(["Current Stock", "Receive Stock", "Issue Stock", "Reports"])

# ───── TAB 1: CURRENT STOCK ─────
with tab1:
    st.subheader(f"Stock – {selected_clinic}")
    if df.empty:
        col1, col2, col3 = st.columns(3)
        col1.metric("Expired", 0); col2.metric("Near Expiry", 0); col3.metric("Low Stock", 0)
        st.info("No medicines yet — go to 'Receive Stock' to add some")
    else:
        today = pd.to_datetime("today").normalize()
        df["days_to_expiry"] = (df["expiry_date"] - today).dt.days
        df["status"] = "normal"
        df.loc[df["quantity"] <= df["low_stock_threshold"], "status"] = "low_stock"
        df.loc[df["days_to_expiry"] <= 90, "status"] = "near_expiry"
        df.loc[df["days_to_expiry"] <= 0, "status"] = "expired"

        c1, c2, c3 = st.columns(3)
        c1.metric("Expired", len(df[df["status"] == "expired"]))
        c2.metric("Near Expiry (<90 days)", len(df[df["status"] == "near_expiry"]))
        c3.metric("Low Stock", len(df[df["status"] == "low_stock"]))

        display = df[["drug_name", "generic_name", "strength", "batch_no", "expiry_date", "quantity", "low_stock_threshold"]].copy()
        display["expiry_date"] = display["expiry_date"].dt.strftime("%Y-%m-%d")
        status_list = df["status"].tolist()

        def highlight_row(row):
            status = status_list[row.name]
            if status == "expired": return ["background: #ffcccc"] * len(row)
            if status == "near_expiry": return ["background: #ffffcc"] * len(row)
            if status == "low_stock": return ["background: #ffcc99"] * len(row)
            return [""] * len(row)

        st.dataframe(display.style.apply(highlight_row, axis=1), use_container_width=True)

# ───── TAB 2: RECEIVE STOCK ─────
with tab2:
    st.subheader("Receive New Stock")
    with st.form("receive"):
        drug_name = st.text_input("Drug Name *")
        generic = st.text_input("Generic Name (optional)")
        strength = st.text_input("Strength e.g. 500mg")
        batch = st.text_input("Batch Number *")
        expiry = st.date_input("Expiry Date", min_value=datetime.today())
        qty = st.number_input("Quantity", min_value=1)
        threshold = st.number_input("Low-stock alert", value=20)
        submitted = st.form_submit_button("Add Stock")
        if submitted:
            if not drug_name or not batch:
                st.error("Drug name and batch number required")
            else:
                conn = sqlite3.connect(DB_PATH)
                conn.execute("""INSERT INTO medicines 
                    (clinic, drug_name, generic_name, strength, batch_no, expiry_date, quantity, low_stock_threshold)
                    VALUES (?,?,?,?,?,?,?,?)""",
                    (selected_clinic, drug_name, generic, strength, batch, expiry, qty, threshold))
                drug_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
                conn.commit()
                conn.close()
                add_transaction(selected_clinic, drug_id, "in", qty, remarks=f"Received {batch}")
                st.success(f"Added {qty} × {drug_name}")
                st.balloons()
                st.rerun()

# ——— TAB 3: ISSUE STOCK – 100 % WORKING INSTANT UPDATE ———
with tab3:
    st.subheader("Issue Medicine")
    if df.empty:
        st.info("No stock available")
    else:
        # Build the dropdown options
        df["option"] = (df["drug_name"] + " | " + df["batch_no"] +
                        " | Exp: " + df["expiry_date"].dt.strftime("%b %Y") +
                        " | Stock: " + df["quantity"].astype(str))
        choice = st.selectbox("Select medicine", df["option"], key="issue_select")

        # Get the actual row index in df (this is the key!)
        row_idx = df[df["option"] == choice].index[0]
        current_qty = int(df.loc[row_idx, "quantity"])
        drug_id = int(df.loc[row_idx, "id"])

        col1, col2 = st.columns(2)
        col1.write(f"**Available:** {current_qty}")
        issue_qty = col2.number_input("Qty to issue", min_value=1, max_value=current_qty, key="issue_qty")

        patient = st.text_input("Patient name (optional)")
        remarks = st.text_input("Remarks")

        if st.button("Issue Medicine", type="primary"):
            new_qty = current_qty - issue_qty

            # Direct database update using the real ID
            conn = sqlite3.connect(DB_PATH)
            conn.execute("UPDATE medicines SET quantity = ? WHERE id = ?", (new_qty, drug_id))
            conn.commit()
            conn.close()

            add_transaction(selected_clinic, drug_id, "out", issue_qty, patient, remarks)
            st.success(f"Issued {issue_qty} → New stock: {new_qty}")
            st.rerun()        # instant refresh

# ───── TAB 4: FULL TRANSACTION REPORT (ISSUED + RECEIVED + PATIENT NAMES) ─────
with tab4:
    st.subheader("Full Transaction History")

    # Load all transactions for the selected clinic
    conn = sqlite3.connect(DB_PATH)
    query = """
        SELECT t.timestamp, t.type, m.drug_name, m.batch_no, t.quantity, 
               t.patient_name, t.remarks, t.clinic
        FROM transactions t
        JOIN medicines m ON t.drug_id = m.id
        WHERE t.clinic = ?
        ORDER BY t.timestamp DESC
    """
    history = pd.read_sql_query(query, conn, params=(selected_clinic,))
    conn.close()

    if history.empty:
        st.info("No transactions yet. Start receiving and issuing stock!")
    else:
        # Clean up display
        history["timestamp"] = pd.to_datetime(history["timestamp"]).dt.strftime("%Y-%m-%d %H:%M")
        history["type"] = history["type"].map({"in": "RECEIVED", "out": "ISSUED"})
        history.rename(columns={
            "timestamp": "Date & Time",
            "type": "Action",
            "drug_name": "Medicine",
            "batch_no": "Batch",
            "quantity": "Qty",
            "patient_name": "Patient",
            "remarks": "Remarks",
            "clinic": "Clinic"
        }, inplace=True)

        # Reorder columns
        display_history = history[["Date & Time", "Action", "Medicine", "Batch", "Qty", "Patient", "Remarks"]]

        st.dataframe(display_history, use_container_width=True)

        # Export button
        csv = display_history.to_csv(index=False).encode()
        st.download_button(
            "Download Full Report (CSV)",
            csv,
            f"transaction_report_{selected_clinic.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.csv",
            "text/csv"
        )

        # Quick stats
        st.markdown("---")
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Received", history[history["Action"] == "RECEIVED"]["Qty"].sum())
        col2.metric("Total Issued", history[history["Action"] == "ISSUED"]["Qty"].sum())
        col3.metric("Total Transactions", len(history))

st.sidebar.caption("Clinic Inventory • Built with Streamlit")
