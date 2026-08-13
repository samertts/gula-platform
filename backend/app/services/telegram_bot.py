import os
import requests
from typing import Optional

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

def send_telegram_message(message: str, chat_id: Optional[str] = None) -> bool:
    """Send a message to a Telegram chat using the configured Bot Token."""
    token = TELEGRAM_BOT_TOKEN
    target_chat = chat_id or TELEGRAM_CHAT_ID

    if not token or not target_chat:
        print("Telegram Bot Token or Chat ID not configured.")
        return False

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": target_chat,
        "text": message,
        "parse_mode": "Markdown"
    }

    try:
        response = requests.post(url, json=payload, timeout=10)
        if response.status_code == 200:
            return True
        else:
            print(f"Failed to send Telegram message: {response.text}")
            return False
    except Exception as e:
        print(f"Error sending Telegram notification: {e}")
        return False

def notify_critical_alert(alert_title: str, patient_name: str, details: str):
    """Send a critical medical alert to the admin/doctor Telegram channel."""
    msg = (
        f"🚨 *GULA Critical Clinical Alert* 🚨\n\n"
        f"• *Alert:* {alert_title}\n"
        f"• *Patient:* {patient_name}\n"
        f"• *Details:* {details}\n\n"
        f"_Please check GULA Dashboard immediately._"
    )
    return send_telegram_message(msg)

def notify_lab_result_ready(patient_name: str, phone: str, result_url: str):
    """Notify when lab results are ready for automated free delivery."""
    msg = (
        f"🔬 *GULA Lab Result Ready*\n\n"
        f"• *Patient:* {patient_name}\n"
        f"• *Phone:* {phone}\n"
        f"• *Secure Link:* {result_url}\n\n"
        f"_Automated delivery via GULA Telegram Gateway_"
    )
    return send_telegram_message(msg)
