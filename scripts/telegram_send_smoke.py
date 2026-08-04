#!/usr/bin/env python3
"""Telegram Bot runtime send verification — GULA Platform
=========================================================
Verifies end-to-end delivery through the production provider
(``shared.notifications.telegram.TelegramNotificationService``) against the
official Telegram Bot API.

Security contract:
  - TELEGRAM_BOT_TOKEN is read ONLY from the environment (never an argument).
  - chat_id is supplied DYNAMICALLY via ``--chat-id`` (or discovered from
    pending updates with ``--discover``) — never read from configuration.
  - The token is never printed, logged, or written to any file.

Usage:
    TELEGRAM_BOT_TOKEN=<token> python scripts/telegram_send_smoke.py --chat-id 123456789
    TELEGRAM_BOT_TOKEN=<token> python scripts/telegram_send_smoke.py --discover
    TELEGRAM_BOT_TOKEN=<token> python scripts/telegram_send_smoke.py \
        --chat-id @ops_channel --html --text "<b>GULA</b> startup verified"
    TELEGRAM_BOT_TOKEN=<token> python scripts/telegram_send_smoke.py \
        --chat-id 123 --photo report.png --text "Lab report"

Exit codes: 0 delivered, 1 failed, 2 bot not configured.
"""

from __future__ import annotations

import argparse
import os
import sys


def _load_service():
    """Import the production provider (backend/.venv + PYTHONPATH=..)."""
    try:
        from shared.notifications.telegram import TelegramNotificationService
    except ImportError:
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
        from shared.notifications.telegram import TelegramNotificationService
    return TelegramNotificationService()


def _discover_chat_id(service) -> int | None:
    """Find the most recent chat that interacted with the bot (getUpdates).

    The chat_id comes from live API data — still fully dynamic, never
    configured. Returns None when there is nothing to target yet.
    """
    result = service.poll_updates(limit=5)
    if not result.ok:
        print(f"discover: getUpdates failed: {result.error}")
        return None
    updates = result.data or []
    chat_ids: list = []
    for update in updates:
        for key in ("message", "edited_message", "channel_post", "callback_query"):
            payload = update.get(key)
            if not payload:
                continue
            chat = payload.get("chat") or {}
            if chat.get("id") is not None:
                chat_ids.append(chat["id"])
    return chat_ids[-1] if chat_ids else None


def main() -> int:
    parser = argparse.ArgumentParser(description="Telegram runtime send verification")
    mode = parser.add_mutually_exclusive_group(required=False)
    mode.add_argument("--chat-id", help="Target chat/group/channel id (dynamic per call)")
    mode.add_argument(
        "--discover",
        action="store_true",
        help="Target the most recent chat found via getUpdates",
    )
    parser.add_argument("--text", default="GULA Platform — Telegram send verification OK")
    parser.add_argument("--html", action="store_true", help="Send with parse_mode=HTML")
    parser.add_argument(
        "--markdown-v2",
        action="store_true",
        help="Send with parse_mode=MarkdownV2",
    )
    parser.add_argument("--photo", help="Path to an image to attach (sendPhoto)")
    parser.add_argument("--document", help="Path to a file to attach (sendDocument)")
    parser.add_argument("--alert", choices=["info", "warning", "critical"], help="Send as alert")
    parser.add_argument("--monitoring", action="store_true", help="Send as monitoring message")
    args = parser.parse_args()

    service = _load_service()
    if not service.is_configured:
        print("FAIL: TELEGRAM_BOT_TOKEN is not set in the environment")
        return 2

    me = service.get_me()
    if not me.ok:
        print(f"FAIL: token rejected by Bot API (getMe): {me.error}")
        return 1
    bot_username = (me.data or {}).get("username", "unknown")
    print(f"ok: authenticated as @{bot_username} (token from environment only)")

    chat_id = args.chat_id
    if not chat_id:
        chat_id = _discover_chat_id(service)
    if not chat_id:
        print(
            "FAIL: no --chat-id given and getUpdates returned no chats. "
            "Message the bot first, or pass --chat-id <id>.",
        )
        return 1

    print(f"send: chat_id={chat_id} (supplied dynamically at runtime)")

    result = None
    if args.photo:
        with open(args.photo, "rb") as fh:
            result = service.send_photo(chat_id, fh.read(), caption=args.text)
    elif args.document:
        result = service.send_file(chat_id, file_path=args.document, caption=args.text)
    elif args.alert:
        result = service.send_alert(chat_id, args.text, level=args.alert)
    elif args.monitoring:
        result = service.send_monitoring(chat_id, args.text, service="gula-platform")
    elif args.html:
        result = service.send_html(chat_id, args.text)
    elif args.markdown_v2:
        result = service.send_markdown_v2(chat_id, args.text)
    else:
        result = service.send_text(chat_id, args.text)

    if result.success:
        print(f"ok: delivered message_id={result.message_id}")
        return 0
    print(f"FAIL: {result.error}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
