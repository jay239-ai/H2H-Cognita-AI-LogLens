import streamlit as st
from log_analyzer import analyze_log

st.title("AI-Powered Log Analyzer")

st.write("Paste logs below (one per line):")

# User input
user_input = st.text_area("Enter logs")

if st.button("Analyze Logs"):

    logs = user_input.split("\n")

    st.subheader("Results:")

    for log in logs:
        if log.strip() == "":
            continue

        result = analyze_log(log)

        st.markdown(f"### Log: {log}")
        st.write(f"**Issue:** {result['Issue']}")
        st.write(f"**Reason:** {result['Reason']}")
        st.write(f"**Impact:** {result['Impact']}")
        st.write(f"**Action:** {result['Action']}")
        st.write("---")