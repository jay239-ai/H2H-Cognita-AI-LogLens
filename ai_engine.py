import os
import time
from google import genai  # ✅ NEW SDK


# 🔧 Initialize Gemini
def init_model():
    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        return None, "API key missing. Set GEMINI_API_KEY."

    try:
        client = genai.Client(api_key=api_key)
        return client, None

    except Exception as e:
        return None, f"Client init failed: {str(e)}"


# 🧠 AI Layer
def generate_ai_analysis(
    main_issue,
    severity,
    confidence,
    rule_based_summary,
    rule_based_root_cause,
    logs,
    timeout=10
):
    start_time = time.time()

    client, err = init_model()

    if err:
        return {
            "status": "error",
            "message": f"AI unavailable: {err}"
        }

    message, log_list = main_issue if main_issue else ("No issue detected", [])

    evidence_text = "\n".join([
        f"{log.get('timestamp','N/A')} - {log.get('message','')}"
        for log in log_list[:20]
    ])

    prompt = f"""
You are an expert SRE assistant.

RULES:
- Improve rule-based analysis
- Do not contradict unless clearly wrong

Issue: {message}
Severity: {severity}
Confidence: {confidence}

Summary:
{rule_based_summary}

Root Cause:
{rule_based_root_cause}

Logs:
{evidence_text}

TASK:
1. Refine root cause
2. Explain incident
3. Explain why it happened
4. Suggest actions
5. Evaluate confidence
"""

    try:
        response = client.models.generate_content(
            model="gemini-1.5-flash",
            contents=prompt
        )

        if time.time() - start_time > timeout:
            return {
                "status": "timeout",
                "message": "AI timeout"
            }

        return {
            "status": "success",
            "data": response.text.strip()
        }

    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }