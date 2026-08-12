from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.telegram_bot import send_telegram_message, notify_critical_alert
from app.services.telegram_bot_commands import handle_telegram_command

router = APIRouter(prefix="/telegram", tags=["telegram"])

@router.post("/webhook")
async def telegram_webhook(request: Request, db: Session = Depends(get_db)):
    """Receive updates from Telegram Bot and process commands."""
    try:
        body = await request.json()
        message = body.get("message")
        if not message:
            return {"status": "ignored"}

        chat_id = str(message.get("chat", {}).get("id"))
        text = message.get("text", "")

        if text.startswith("/"):
            response_text = handle_telegram_command(text, chat_id, db)
            send_telegram_message(response_text, chat_id=chat_id)

        return {"status": "ok"}
    except Exception as e:
        return {"status": "error", "detail": str(e)}

@router.post("/test-alert")
def test_telegram_alert():
    """Test sending a platform status notification via Telegram."""
    success = notify_critical_alert(
        alert_title="System Integration Test",
        patient_name="Demo Patient",
        details="All tenant isolation, AI fabric, and Telegram monitoring checks are operating normally."
    )
    if not success:
        raise HTTPException(
            status_code=500,
            detail="Failed to send Telegram message. Verify TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID."
        )
    return {"status": "success", "message": "Telegram monitoring notification sent successfully."}
