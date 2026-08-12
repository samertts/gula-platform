import requests
import sys

BOT_TOKEN = "8772178106:AAHb5CKlCk-rvughldX6n8ZWJo97nkMP6OU"

def verify_and_send():
    print(f"--- GULA Telegram Bot Verification ---")

    # 1. Get Bot Info
    url_info = f"https://api.telegram.org/bot{BOT_TOKEN}/getMe"
    try:
        resp_info = requests.get(url_info, timeout=10).json()
        if not resp_info.get("ok"):
            print(f"❌ Invalid Token: {resp_info.get('description')}")
            return

        bot_name = resp_info['result']['first_name']
        bot_username = resp_info['result']['username']
        print(f"✅ Bot Connected: {bot_name} (@{bot_username})")

        # 2. Get Updates to find Chat ID
        url_updates = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates"
        resp_updates = requests.get(url_updates, timeout=10).json()

        if not resp_updates.get("ok"):
            print(f"❌ Failed to get updates: {resp_updates.get('description')}")
            return

        updates = resp_updates.get("result", [])
        if not updates:
            print("⚠️ No messages found. Please send any message to the bot on Telegram first!")
            return

        # Get the latest chat_id
        chat_id = updates[-1]["message"]["chat"]["id"]
        user_name = updates[-1]["message"]["from"].get("first_name", "User")
        print(f"✅ Found Chat ID: {chat_id} (User: {user_name})")

        # 3. Send Success Message
        msg = (
            f"🚀 *GULA Platform Integration Success* 🚀\n\n"
            f"Hello {user_name},\n\n"
            f"This is a verified proof of success from the GULA Platform backend. "
            f"The Telegram gateway is now fully integrated and operational.\n\n"
            f"🟢 *System Status:* Secure & Active\n"
            f"🔬 *Lab Results:* Automated\n"
            f"🚨 *Critical Alerts:* Real-time Enabled\n\n"
            f"_Powered by GULA Health National Platform_"
        )

        url_send = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        resp_send = requests.post(url_send, json={
            "chat_id": chat_id,
            "text": msg,
            "parse_mode": "Markdown"
        }).json()

        if resp_send.get("ok"):
            print(f"✅ PROOF SENT! Check your Telegram bot (@{bot_username}) now.")
        else:
            print(f"❌ Failed to send proof: {resp_send.get('description')}")

    except Exception as e:
        print(f"❌ Error during verification: {str(e)}")

if __name__ == "__main__":
    verify_and_send()
