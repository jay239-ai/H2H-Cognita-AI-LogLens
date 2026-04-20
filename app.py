import streamlit as st
from log_analyzer import analyze_log_ai

st.set_page_config(page_title="AI Log Analyzer", layout="centered")

st.title("🔍 AI-Powered Log Analyzer")

st.write("Paste logs below (one per line):")

# User input
user_input = st.text_area("Enter logs", height=200)

if st.button("Analyze Logs"):

    if not user_input.strip():
        st.warning("Please enter at least one log.")
    else:
        logs = user_input.split("\n")

        st.subheader("Results:")

        for log in logs:
            log = log.strip()

            if not log:
                continue

            with st.spinner(f"Analyzing log..."):
                result = analyze_log_ai(log)

            st.markdown(f"### 📄 Log:")
            st.code(log)

            st.markdown("### 🤖 Analysis:")
            st.text(result)

            st.write("---")