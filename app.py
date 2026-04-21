import streamlit as st
import plotly.express as px

from parse import parse_logs
from incident_analyzer import analyze_incident
from log_analyzer import (
    clean_logs,
    group_logs,
    get_top_issues,
    get_main_issue,
    detect_severity,
    calculate_confidence
)
from ai_engine import generate_ai_analysis


# 🔹 PAGE CONFIG (MUST FIRST)
st.set_page_config(page_title="LogLens", layout="wide")


# 🎨 LOAD CSS
def load_css():
    try:
        with open("main.css", encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    except:
        pass

load_css()


# 🔹 HEADER
st.markdown("<h1 class='accent'>LogLens</h1>", unsafe_allow_html=True)
st.markdown("<p class='subtle'>AI-powered log intelligence platform</p>", unsafe_allow_html=True)

st.divider()


# 🔹 INPUT SECTION (TABS = PREMIUM UX)
tab1, tab2 = st.tabs(["Upload Logs", "Paste Logs"])

logs = None

with tab1:
    uploaded_file = st.file_uploader("Upload log file", type=["log", "txt", "json", "csv"])
    if uploaded_file:
        try:
            logs = uploaded_file.read().decode("utf-8", errors="ignore")
        except:
            st.error("Failed to read file")

with tab2:
    text_input = st.text_area("Paste logs here", height=200)
    if text_input:
        logs = text_input


# 🔹 ANALYZE BUTTON (CONTROLLED FLOW)
analyze_clicked = st.button("Analyze Logs")


# 🔹 PROCESS ONLY AFTER BUTTON
if logs and analyze_clicked:

    with st.spinner("Analyzing logs..."):

        parsed_logs = parse_logs(logs, uploaded_file.name if 'uploaded_file' in locals() and uploaded_file else None)
        cleaned_logs = clean_logs(parsed_logs)
        grouped_logs = group_logs(cleaned_logs)

        top_issues = get_top_issues(grouped_logs)
        main_issue = get_main_issue(grouped_logs)

        severity = detect_severity(grouped_logs)
        confidence = calculate_confidence(grouped_logs)

        confidence_map = {"Low": 30, "Medium": 60, "High": 90}
        confidence_value = confidence_map.get(confidence, 50)


    # 🔹 METRICS ROW
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Total Logs", len(cleaned_logs))

    with col2:
        st.metric("Severity", severity)

    with col3:
        st.metric("Confidence", f"{confidence_value}%")


    # 🔹 MAIN INCIDENT CARD
    if main_issue:
        st.markdown("### Main Incident")

        st.markdown(f"""
        <div class='card'>
        <b>{main_issue[0]}</b><br>
        {len(main_issue[1])} occurrences
        </div>
        """, unsafe_allow_html=True)


        # 🔹 RULE-BASED ANALYSIS
        ai_result = analyze_incident(
            main_issue,
            severity,
            confidence,
            main_issue[1]
        )

        root = ai_result["root_cause"]
        root_text = f"{root['cause']} (Confidence: {root['confidence']})" if isinstance(root, dict) else root


        # 🔹 CLEAN SECTIONS
        st.subheader("Summary")
        st.write(ai_result["summary"])

        st.subheader("Timeline")
        for step in ai_result["timeline"]:
            st.write(f"{step['time']} → {step['event']}")

        st.subheader("Root Cause")
        st.warning(root_text)

        st.subheader("Reliability")
        st.progress(confidence_value / 100)
        st.write(f"{confidence_value}% confidence")

        st.subheader("Expected Behavior")
        st.info(ai_result["expected"])

        st.subheader("Recommended Action")
        st.success(ai_result["action"])


        # 🔹 AI SECTION (COLLAPSIBLE = PREMIUM FEEL)
        with st.expander("AI Deep Analysis"):

            try:
                with st.spinner("Running AI analysis..."):
                    ai_output = generate_ai_analysis(
                        main_issue,
                        severity,
                        confidence,
                        ai_result["summary"],
                        root_text,
                        main_issue[1]
                    )

                if ai_output["status"] == "success":
                    st.write(ai_output["data"])

                elif ai_output["status"] == "timeout":
                    st.warning(ai_output["message"])

                else:
                    st.error(ai_output["message"])

            except Exception as e:
                st.error(f"AI error: {str(e)}")
                