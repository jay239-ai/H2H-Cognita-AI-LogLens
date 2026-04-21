import json
import pandas as pd
import re


# 🔹 Main function
def parse_logs(raw_logs, file_name=None):
    if file_name:
        if file_name.endswith(".json"):
            return parse_json(raw_logs)
        elif file_name.endswith(".csv"):
            return parse_csv(raw_logs)

    return parse_text(raw_logs)


# 🔹 JSON parser
def parse_json(raw_logs):
    logs = []

    for line in raw_logs.split("\n"):
        try:
            data = json.loads(line)

            logs.append({
                "timestamp": str(data.get("timestamp", "N/A")),
                "level": str(data.get("level", "UNKNOWN")),
                "service": str(data.get("service", "GENERAL")),
                "message": str(data.get("message", "")).strip()
            })

        except:
            continue

    return logs


# 🔹 CSV parser
def parse_csv(raw_logs):
    try:
        from io import StringIO
        df = pd.read_csv(StringIO(raw_logs))

        logs = []
        for _, row in df.iterrows():
            logs.append({
                "timestamp": str(row.get("timestamp", "N/A")),
                "level": str(row.get("level", "UNKNOWN")),
                "service": str(row.get("service", "GENERAL")),
                "message": str(row.get("message", "")).strip()
            })

        return logs

    except:
        return []


# 🔹 TEXT / SYSLOG parser (FIXED)
def parse_text(raw_logs):
    logs = []

    # ✅ Strict pattern (only real logs)
    pattern = re.compile(
        r'^(?P<timestamp>\w{3}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2})\s+'
        r'(?P<level>INFO|ERROR|WARN|DEBUG|FATAL)\s+'
        r'(?P<service>[\w\-]+)\s+'
        r'(?P<message>.+)$'
    )

    for line in raw_logs.split("\n"):
        line = line.strip()

        # 🔴 Skip empty or non-log lines
        if not line or len(line) < 10:
            continue

        match = pattern.match(line)

        if match:
            data = match.groupdict()

            logs.append({
                "timestamp": data["timestamp"],
                "level": data["level"],
                "service": data["service"],  # ✅ keeps auth-service intact
                "message": data["message"].strip()
            })

        else:
            # 🟡 Fallback: treat as generic log (but clean)
            logs.append({
                "timestamp": "N/A",
                "level": "UNKNOWN",
                "service": "GENERAL",
                "message": line
            })

    return logs