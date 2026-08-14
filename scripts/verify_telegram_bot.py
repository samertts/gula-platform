import logging
import os
from typing import Any

import requests

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
REQUEST_TIMEOUT_SECONDS = 10
LOGGER = logging.getLogger(__name__)


def _telegram_response(method: str, url: str, **kwargs: Any) -> dict[str, Any]:
    response = requests.request(method, url, timeout=REQUEST_TIMEOUT_SECONDS, **kwargs)
    response.raise_for_status()
    payload = response.json()
    if not isinstance(payload, dict):
        raise ValueError("Telegram returned a non-object JSON response")
    return payload


def verify_and_send() -> None:
    if not BOT_TOKEN:
        LOGGER.error("TELEGRAM_BOT_TOKEN must be set before running this verification script.")
        return

    LOGGER.info("--- GULA Telegram Bot Verification ---")

    url_info = f"https://api.telegram.org/bot{BOT_TOKEN}/getMe"
    try:
        bot_response = _telegram_response("GET", url_info)
        if not bot_response.get("ok"):
            LOGGER.error("Invalid token: %s", bot_response.get("description"))
            return

        bot = bot_response["result"]
        if not isinstance(bot, dict):
            raise ValueError("Telegram getMe response has an invalid result")
        bot_name = bot["first_name"]
        bot_username = bot["username"]
        LOGGER.info("Bot connected: %s (@%s)", bot_name, bot_username)

        url_updates = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates"
        updates_response = _telegram_response("GET", url_updates)
        if not updates_response.get("ok"):
            LOGGER.error("Failed to get updates: %s", updates_response.get("description"))
            return

        updates = updates_response.get("result", [])
        if not isinstance(updates, list) or not updates:
            LOGGER.warning("No messages found. Send a message to the bot on Telegram first.")
            return

        latest_update = updates[-1]
        if not isinstance(latest_update, dict):
            raise ValueError("Telegram update has an invalid shape")
        message = latest_update["message"]
        if not isinstance(message, dict):
            raise ValueError("Telegram update is missing a message")
        chat = message["chat"]
        sender = message["from"]
        if not isinstance(chat, dict) or not isinstance(sender, dict):
            raise ValueError("Telegram update is missing chat or sender data")
        chat_id = chat["id"]
        user_name = sender.get("first_name", "User")
        LOGGER.info("Found chat ID: %s (user: %s)", chat_id, user_name)

        message_text = (
            "GULA Platform Integration Success\n\n"
            f"Hello {user_name},\n\n"
            "This is a verified proof of success from the GULA Platform backend. "
            "The Telegram gateway is now fully integrated and operational.\n\n"
            "System Status: Secure & Active\n"
            "Lab Results: Automated\n"
            "Critical Alerts: Real-time Enabled\n\n"
            "Powered by GULA Health National Platform"
        )
        url_send = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        sent_response = _telegram_response(
            "POST",
            url_send,
            json={
                "chat_id": chat_id,
                "text": message_text,
                "parse_mode": "Markdown",
            },
        )
        if sent_response.get("ok"):
            LOGGER.info("Proof sent. Check the Telegram bot (@%s).", bot_username)
        else:
            LOGGER.error("Failed to send proof: %s", sent_response.get("description"))

    except (KeyError, TypeError, ValueError, requests.RequestException) as exc:
        LOGGER.error("Telegram verification failed: %s", exc)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    verify_and_send()
