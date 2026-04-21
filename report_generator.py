from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from datetime import datetime


# 🧠 Main PDF generator
def generate_pdf(report_data, filename="incident_report.pdf"):
    c = canvas.Canvas(filename, pagesize=letter)
    width, height = letter

    y = height - 50

    # Title
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, y, "LogLens Incident Report")
    y -= 25

    # Timestamp (FIXED FORMAT)
    c.setFont("Helvetica", 10)
    c.drawString(50, y, f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    y -= 30

    # 🔹 Summary
    y = write_section(c, "Summary", report_data.get("summary", ""), y)

    # 🔹 Metrics
    severity = report_data.get("severity", "Unknown")
    confidence = report_data.get("confidence", "Unknown")

    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y, "System Metrics")
    y -= 20

    c.setFont("Helvetica", 10)
    c.drawString(50, y, f"Severity: {severity}")
    y -= 15
    c.drawString(50, y, f"Confidence: {confidence}")
    y -= 25

    # 🔹 Timeline
    timeline = report_data.get("timeline", [])
    if timeline:
        c.setFont("Helvetica-Bold", 12)
        c.drawString(50, y, "Timeline")
        y -= 20

        c.setFont("Helvetica", 10)
        for step in timeline[:8]:
            line = f"{step.get('time')} → {step.get('event')}"
            for wrapped in wrap_text(line):
                if y < 50:
                    c.showPage()
                    y = 750
                    c.setFont("Helvetica", 10)
                c.drawString(50, y, wrapped)
                y -= 12

        y -= 20

    # 🔹 Root Cause
    root = report_data.get("root_cause", "")
    if isinstance(root, dict):
        root_text = f"{root.get('cause','')} (Confidence: {root.get('confidence','')})"
    else:
        root_text = str(root)

    y = write_section(c, "Root Cause Analysis", root_text, y)

    # 🔹 Expected Behavior
    y = write_section(c, "Expected Behavior", report_data.get("expected", ""), y)

    # 🔹 Suggested Action
    y = write_section(c, "Recommended Action", report_data.get("action", ""), y)

    # 🔹 Reasoning
    y = write_section(c, "Analysis Reasoning", report_data.get("reasoning", ""), y)

    # 🔹 Evidence Score
    evidence_score = report_data.get("evidence_score", 0)
    y = write_section(c, "Evidence Score", f"{evidence_score}/100", y)

    c.save()
    return filename


# 🧩 Helper: safe text writer
def write_section(canvas_obj, title, text, y):
    canvas_obj.setFont("Helvetica-Bold", 12)
    canvas_obj.drawString(50, y, title)
    y -= 18

    canvas_obj.setFont("Helvetica", 10)

    for line in wrap_text(text):
        if y < 50:
            canvas_obj.showPage()
            y = 750
            canvas_obj.setFont("Helvetica", 10)

        canvas_obj.drawString(50, y, line)
        y -= 14

    y -= 15
    return y


# 🧠 Helper: text wrapping
def wrap_text(text, limit=90):
    words = str(text).split()
    lines = []
    line = ""

    for w in words:
        if len(line + w) < limit:
            line += w + " "
        else:
            lines.append(line)
            line = w + " "

    if line:
        lines.append(line)

    return lines