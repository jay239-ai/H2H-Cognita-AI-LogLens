from datetime import datetime


# 🧠 Main function
def analyze_incident(main_issue, severity, confidence, evidence_logs):
    message, logs = main_issue if main_issue else ("No issue detected", [])

    timeline = build_timeline(logs)
    root_cause = guess_root_cause(message, logs)
    summary = generate_summary(message, severity, len(logs))
    expected = generate_expected_behavior(message)
    action = suggest_action(message, severity)
    reasoning = build_reasoning(severity, confidence, logs)
    evidence_score = calculate_evidence_score(logs)

    return {
        "summary": summary,
        "timeline": timeline,
        "root_cause": root_cause,
        "expected": expected,
        "action": action,
        "reasoning": reasoning,
        "evidence_score": evidence_score
    }


# ⏱️ Timeline builder (FIXED: sorted)
def build_timeline(logs):
    events = []

    # Try sorting by timestamp
    try:
        sorted_logs = sorted(
            logs,
            key=lambda x: parse_time(x.get("timestamp"))
        )
    except:
        sorted_logs = logs

    for log in sorted_logs[:10]:
        events.append({
            "time": log.get("timestamp", "unknown"),
            "event": log.get("message", "")
        })

    return events


def parse_time(ts):
    try:
        return datetime.strptime(ts, "%b %d %H:%M:%S")
    except:
        return datetime.min


# 📌 Summary (IMPROVED)
def generate_summary(message, severity, count):
    return f"""
An incident related to '{message}' was detected with {count} occurrences.
The issue is classified as {severity} severity based on frequency and log patterns,
indicating a measurable impact on system behavior.
""".strip()


# ⚠️ Root cause (IMPROVED: uses logs too)
def guess_root_cause(message, logs):
    combined_text = message.lower() + " " + " ".join(
        [log.get("message", "").lower() for log in logs[:10]]
    )

    if "login" in combined_text or "auth" in combined_text:
        return {
            "cause": "Authentication failure detected (possible invalid credentials or auth service disruption)",
            "confidence": "High"
        }

    if "timeout" in combined_text:
        return {
            "cause": "Service timeout observed, likely due to network latency or overloaded service",
            "confidence": "Medium"
        }

    if "database" in combined_text or "db" in combined_text:
        return {
            "cause": "Database connectivity or query execution issue detected",
            "confidence": "Medium"
        }

    if "exception" in combined_text or "error" in combined_text:
        return {
            "cause": "Unhandled exception or system error detected, requiring deeper inspection",
            "confidence": "Low"
        }

    return {
        "cause": "No clear root cause identified from available evidence",
        "confidence": "Low"
    }


# 📊 Expected behavior
def generate_expected_behavior(message):
    return f"""
Under normal conditions, '{message}' should not occur and system operations should complete successfully without errors.
""".strip()


# 🛠️ Suggested action
def suggest_action(message, severity):
    if severity == "Critical":
        return "Immediately investigate logs, restart affected services, and validate system health and dependencies."

    if severity == "High":
        return "Check service dependencies, recent deployments, and monitor system performance closely."

    if severity == "Medium":
        return "Monitor logs for recurring patterns and verify system stability."

    return "No immediate action required. Continue monitoring."


# 🧠 Reasoning (cleaner)
def build_reasoning(severity, confidence, logs):
    return f"""
This conclusion is derived from repeated log patterns and frequency analysis.

Severity: {severity}
Confidence Level: {confidence}
Logs analyzed: {len(logs)}

The system prioritizes recurring issues over isolated events.
""".strip()


# 📊 Evidence scoring (slightly improved)
def calculate_evidence_score(logs):
    if not logs:
        return 0

    score = 0

    for log in logs:
        msg = log.get("message", "").lower()

        if "error" in msg:
            score += 2
        if "timeout" in msg:
            score += 3
        if "fail" in msg:
            score += 2
        if "exception" in msg:
            score += 3
        if "crash" in msg:
            score += 4

    # Normalize slightly
    return min(score, 100)