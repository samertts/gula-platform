from ai_assistant import analyze_logs, log_event

log_event("Device connected")
log_event("Result saved")
log_event("Error reading device")

print(analyze_logs())
