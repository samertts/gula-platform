import logging
import requests

logger = logging.getLogger("gula.telegram")


def send_telegram(bot_token: str, chat_id: str, message: str) -> bool:
    """Send a message via Telegram Bot API.

    Returns True on success, False on failure.
    """
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    try:
        resp = requests.post(
            url,
            json={"chat_id": chat_id, "text": message},
            timeout=10,
        )
        if resp.status_code != 200:
            logger.warning(f"Telegram send failed: {resp.status_code}")
            return False
        return True
    except requests.RequestException as e:
        logger.error(f"Telegram send error: {e}")
        return False
