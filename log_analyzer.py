from google import genai
import time

client = genai.Client(api_key="API_KEY")


def detect_log_context(log):
    log_lower = log.lower()

    if "port=22" in log_lower or "ssh" in log_lower:
        return "Possible SSH intrusion attempt"
    elif "login" in log_lower or "auth" in log_lower:
        return "Authentication-related issue"
    elif "timeout" in log_lower:
        return "Network/server timeout issue"
    elif "blocked" in log_lower:
        return "Security rule triggered (blocked traffic)"
    elif "purchase" in log_lower or "product" in log_lower:
        return "E-commerce transaction activity"
    else:
        return "General system activity"


def analyze_log_ai(log, retries=3, delay=2):
    log = log.strip()
    context = detect_log_context(log)

    # ✅ FIXED variable name
    prompt = f"""
Analyze the following log and return:

Issue:
Reason:
Impact:
Action:

Log:
{log}
"""

    for attempt in range(retries):
        try:
            response = client.models.generate_content(
                model="models/gemini-2.5-flash",
                contents=prompt
            )

            if response and response.text:
                return response.text.strip()

        except Exception as e:
            error_msg = str(e).lower()
            print(f"⚠️ Attempt {attempt+1} failed:", error_msg)

            if attempt < retries - 1:
                time.sleep(delay)
                continue

            return f"""Issue: AI Analysis Failure
Reason: {error_msg}
Impact: Log analysis could not be completed
Action: Check API setup"""

    return """Issue: Unknown Failure
Reason: Unexpected execution error
Impact: Analysis not completed
Action: Check system logs"""
