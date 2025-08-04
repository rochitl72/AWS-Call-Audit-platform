import streamlit as st
import base64
import json
import datetime
import os
import pandas as pd
import plotly.express as px
import numpy as np

# ---------------- Local Imports ----------------
from auth_utils import login, check_login, logout, signup
from mongo_connector import save_report, get_reports_for_agent

# ---------------- Streamlit Config ----------------
st.set_page_config(
    page_title="Call Audit Portal",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---------------- Background Image Setup ----------------
def get_base64_image(path):
    with open(path, "rb") as f:
        data = f.read()
    return base64.b64encode(data).decode()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
bg_image_path = os.path.join(BASE_DIR, "static", "tiger.JPG")
bg_image = get_base64_image(bg_image_path)

st.markdown(f"""
    <style>
    .stApp {{
        background-image: url("data:image/jpg;base64,{bg_image}");
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
        background-repeat: no-repeat;
    }}
    .block-container {{
        background-color: rgba(0, 0, 0, 0.6);
        padding: 2rem;
        border-radius: 10px;
    }}
    section[data-testid="stSidebar"] {{
        background-color: black !important;
    }}
    h1, h2, h3, h4, p, span, div, label {{
        color: white !important;
    }}
    .stTextInput > div > div > input {{
        color: white !important;
    }}
    </style>
""", unsafe_allow_html=True)

# ---------------- Authentication ----------------
if not check_login():
    option = st.sidebar.radio("🔐 Authentication", ["Login", "Signup"])
    if option == "Login":
        login()
    else:
        signup()
    st.stop()

# ---------------- Sidebar ----------------
st.sidebar.success(f"👤 Logged in as: {st.session_state['agent_name']}")
page = st.sidebar.selectbox("📂 Navigation", [
    "Upload & Analyze", "📊 View Reports", "📤 Logout"
])

if page == "📤 Logout":
    logout()

# ---------------- Upload & Analyze ----------------
elif page == "Upload & Analyze":
    st.title("📞 Upload New Call Recording")
    date_str = st.date_input("📅 Select Call Date", value=datetime.date.today())
    uploaded_file = st.file_uploader("🎧 Upload MP3/WAV/M4A Call Recording", type=["mp3", "wav", "m4a"])

    if uploaded_file:
        # Save file locally
        audio_dir = "uploaded_calls"
        os.makedirs(audio_dir, exist_ok=True)
        file_path = os.path.join(audio_dir, uploaded_file.name)
        with open(file_path, "wb") as f:
            f.write(uploaded_file.read())
        st.success(f"Uploaded: {uploaded_file.name}")

        # Run call audit pipeline
        st.info("Running call analysis...")
        from aws_call_audit import generate_full_audit
        generate_full_audit(audio_path=file_path)

        if not os.path.exists("report.json"):
            st.error("❌ Failed to generate report.")
        else:
            with open("report.json") as f:
                report = json.load(f)

            save_report(
                agent_name=st.session_state["agent_name"],
                date=str(date_str),
                file_name=uploaded_file.name,
                report_data=report
            )
            st.success("✅ Report saved to MongoDB.")
            st.json(report)

# ---------------- View Reports ----------------
elif page == "📊 View Reports":
    st.title("📈 View Past Call Reports")
    reports = get_reports_for_agent(st.session_state["agent_name"])

    if not reports:
        st.warning("No reports found.")
    else:
        # --- Date selection
        date_options = sorted(set(r["date"] for r in reports))
        selected_date = st.selectbox("📆 Select Date", date_options)

        # --- File selection
        files_for_date = sorted(set(r["file_name"] for r in reports if r["date"] == selected_date))
        selected_file = st.selectbox("🎧 Select Call File", files_for_date)

        # --- Get matching report
        report = next(
            (r["report"] for r in reports if r["date"] == selected_date and r["file_name"] == selected_file),
            None
        )

        if report:
            st.subheader("📋 Compliance Summary")
            compliance = report.get("classification", {})
            status = compliance.get("status", "Unknown")
            conf = compliance.get("confidence", 0)
            st.metric("Status", status)
            st.metric("Confidence", f"{conf * 100:.2f} %")

            # --- Classification probability bar
            prob_df = pd.DataFrame({
                "Class": ["Compliant", "Non-Compliant"],
                "Probability": [conf if status == "Compliant" else 1 - conf,
                                 1 - conf if status == "Compliant" else conf]
            })
            fig_prob = px.bar(prob_df, x="Class", y="Probability", color="Class", text="Probability",
                              title="📊 Classification Probabilities")
            fig_prob.update_traces(texttemplate='%{y:.2f}', textposition='outside')
            st.plotly_chart(fig_prob, use_container_width=True)

            # --- Voice Feature Profile (normalized)
            audio_features = report.get("audio_features", {})
            feature_names = ["pitch", "pitch_range", "tempo", "jitter", "zero_crossing_rate", "rms_energy"]
            values = [audio_features.get(f, 0) for f in feature_names]
            max_val = max(values) if max(values) != 0 else 1
            norm_values = [v / max_val for v in values]

            radar_data = pd.DataFrame({"Feature": feature_names, "Value": norm_values})
            fig_radar = px.line_polar(radar_data, r='Value', theta='Feature',
                                      line_close=True, title="🎙️ Voice Feature Profile (Normalized)",
                                      markers=True)
            st.plotly_chart(fig_radar, use_container_width=True)

            # --- Sentiment Pie Chart
            tone_scores = report.get("tone_scores", {})
            if tone_scores:
                pie_df = pd.DataFrame(tone_scores.items(), columns=["Sentiment", "Score"])
                fig_pie = px.pie(pie_df, names="Sentiment", values="Score", title="🗣️ Sentiment Distribution")
                st.plotly_chart(fig_pie, use_container_width=True)

            # --- MFCC Top Components
            mfcc = audio_features.get("mfcc", [])
            if mfcc:
                top_n = min(len(mfcc), 5)
                mfcc_df = pd.DataFrame({"MFCC Index": list(range(top_n)), "Value": mfcc[:top_n]})
                fig_mfcc = px.bar(mfcc_df, x="MFCC Index", y="Value", title="🎵 Top MFCC Components")
                st.plotly_chart(fig_mfcc, use_container_width=True)

            # --- Rule Violations
            violations = report.get("bedrock_analysis", {}).get("violations", [])
            st.subheader("🚫 Rule Violations")
            if violations:
                st.write(f"Total Violations: {len(violations)}")
                st.dataframe(pd.DataFrame(violations))
            else:
                st.success("🎉 No rule violations detected.")