import re

# Rule-based (fast + reliable)
def analyze_log_rule_based(log):
    log_lower = log.lower()

    rules = [
        {
            "pattern": r"failed password",
            "output": {
                "Issue": "Unauthorized login attempt",
                "Reason": "Failed password detected",
                "Impact": "Possible security threat",
                "Action": "Check IP and secure authentication"
            }
        },
        {
            "pattern": r"\b500\b",
            "output": {
                "Issue": "Server error",
                "Reason": "HTTP 500 status code",
                "Impact": "Website or API may be down",
                "Action": "Check backend server"
            }
        },
        {
            "pattern": r"timeout",
            "output": {
                "Issue": "Timeout issue",
                "Reason": "Request exceeded time limit",
                "Impact": "Slow or failed operations",
                "Action": "Check network or database"
            }
        },
        {
            "pattern": r"connection refused",
            "output": {
                "Issue": "Connection failure",
                "Reason": "Service refused connection",
                "Impact": "Service unavailable",
                "Action": "Ensure service is running"
            }
        },
        {
            "pattern": r"down|link-3",
            "output": {
                "Issue": "Network/system down",
                "Reason": "Component inactive",
                "Impact": "Loss of connectivity",
                "Action": "Check network device"
            }
        }
    ]

    for rule in rules:
        if re.search(rule["pattern"], log_lower):
            return rule["output"]

    return None  # important


# AI-based (placeholder now, real API later)
def analyze_log_ai(log):
    return {
        "Issue": "AI Analysis",
        "Reason": f"AI interpretation of log: {log}",
        "Impact": "May affect system functionality",
        "Action": "Further investigation required"
    }


# Final function (hybrid)
def analyze_log(log):
    result = analyze_log_rule_based(log)

    if result:
        return result
    
    # fallback to AI
    return analyze_log_ai(log)