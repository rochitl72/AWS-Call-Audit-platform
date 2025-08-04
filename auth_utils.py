import streamlit as st
import bcrypt
import pymongo

client = pymongo.MongoClient("mongodb://localhost:27017/")
db = client["call_audit_db"]
users_collection = db["users"]

# ---------------- Helper Functions ----------------
def hash_password(password):
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())

def check_password(password, hashed):
    return bcrypt.checkpw(password.encode("utf-8"), hashed)

# ---------------- Session Check ----------------
def check_login():
    return "agent_name" in st.session_state

def logout():
    st.session_state.clear()
    st.success("Logged out successfully.")

# ---------------- Login Form ----------------
def login():
    st.title("🔐 Agent Login")
    agent_id = st.text_input("👤 Agent Name")
    password = st.text_input("🔑 Password", type="password")

    if st.button("Login"):
        user = users_collection.find_one({"agent_name": agent_id})
        if user and check_password(password, user["password_hash"]):
            st.session_state["agent_name"] = agent_id
            st.success("Login successful!")
            st.rerun()
        else:
            st.error("Invalid credentials. Try again or sign up.")

    st.markdown("Don't have an account? [Click to Sign Up](#signup)")

# ---------------- Signup Form ----------------
def signup():
    st.title("🆕 Agent Signup")
    new_name = st.text_input("👤 Choose Agent Name")
    new_pass = st.text_input("🔑 Choose Password", type="password")

    if st.button("Sign Up"):
        if users_collection.find_one({"agent_name": new_name}):
            st.error("Agent already exists. Please login.")
        else:
            hashed = hash_password(new_pass)
            users_collection.insert_one({"agent_name": new_name, "password_hash": hashed})
            st.success("Signup successful! Please go to login page.")
            st.balloons()