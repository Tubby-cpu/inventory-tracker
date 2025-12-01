import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import hashlib

# ====================== CLEAN PROFESSIONAL DESIGN ======================
st.set_page_config(page_title="Your Clinic Group • Inventory", layout="centered", page_icon="⚕️")

# Custom CSS — modern, clinical, beautiful
st.markdown("""
<style>
    .big-font {font-size: 50px !important; font-weight: bold; color: #0066cc; text-align: center;}
    .medium-font {font-size: 22px !important; color: #555; text-align: center; margin-bottom: 40px;}
    .login-box {max-width: 400px; margin: 0 auto; padding: 40px; background: white; 
                border-radius: 15px; box-shadow: 0 10px 30px rgba(0,0,0,0.1);}
    .stButton>button {width: 100%; background: #0066cc; color: white; font-size: 18px; 
                      padding: 12px; border-radius: 10px;}
    .stButton>button:hover {background: #0052a3;}
    header {visibility: hidden;}
    .css-1d391kg {padding: 2rem 1rem;}
    .css-1v0mbdj a {color: #0066cc;}
    .footer {text-align: center; margin-top: 60px; color: #888; font-size: 14px;}
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

# ====================== DATABASE INIT ======================
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS medicines (...)''')  # your full table code
    c.execute('''CREATE TABLE IF NOT EXISTS transactions (...)''')
    conn.commit()
    conn.close()
init_db()

# ====================== CENTERED LOGIN SCREEN ======================
if "user" not in st.session_state:
    st.markdown('<p class="big-font">Your Clinic Group</p>', unsafe_allow_html=True)
    st.markdown('<p class="medium-font">Smart Pharmacy Inventory System</p>', unsafe_allow_html=True)
    
    with st.container():
        st.markdown('<div class="login-box">', unsafe_allow_html=True)
        st.markdown("### Secure Login")
        username = st.text_input("Username", placeholder="e.g. capetown or admin")
        password = st.text_input("Password", type="password", placeholder="Enter your password")
        
        if st.button("Login to Inventory"):
            hashed = hashlib.sha256(password.encode()).hexdigest()
            if username in USERS and USERS[username]["password"] == hashed:
                st.session_state.user = username
                st.session_state.role = USERS[username]["role"]
                st.session_state.clinic = USERS[username]["clinic"]
                st.success("Login successful! Loading...")
                st.rerun()
            else:
                st.error("Incorrect username or password")
        st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown('<div class="footer">© 2025 Your Clinic Group • Professional Pharmacy Management</div>', unsafe_allow_html=True)
    st.stop()

# ====================== AFTER LOGIN — FULL APP ======================
st.sidebar.success(f"Logged in: {st.session_state.user}")
st.sidebar.write(f"**{st.session_state.clinic}**")
if st.sidebar.button("Logout"):
    st.session_state.clear()
    st.rerun()

# Title after login
st.markdown('<p style="font-size: 40px; color: #0066cc; text-align: center; font-weight: bold;">Your Clinic Group</p>', unsafe_allow_html=True)
st.markdown('<p style="text-align: center; color: #555; font-size: 20px;">Pharmacy Inventory • Live Across All Sites</p>', unsafe_allow_html=True)

# Rest of your working code (clinic selector, tabs, etc.) goes here exactly as before
role = st.session_state.role
user_clinic = st.session_state.clinic

if role == "admin":
    clinic_options = ["All", "Cape Town", "Sandton", "Marshall Town", "Gqberha", "Sandton 2", "Pretoria"]
    selected_clinic = st.selectbox("View Clinic", clinic_options, key="admin_select")
else:
    selected_clinic = user_clinic

df = get_df("All" if (role == "admin" and selected_clinic == "All") else selected_clinic)

tab1, tab2, tab3, tab4 = st.tabs(["Current Stock", "Receive Stock", "Issue Stock", "Reports"])

# Paste your four working tab blocks here exactly as they are now
# (Current Stock, Receive, Issue, Reports — no changes needed)

# At the very end
st.sidebar.markdown("---")
st.sidebar.markdown("**Your Clinic Group** • 2025")
