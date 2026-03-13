
import requests

def send_telegram(bot_token,chat_id,message):

    url=f"https://api.telegram.org/bot{bot_token}/sendMessage"

    requests.post(url,json={

        "chat_id":chat_id,

        "text":message

    })

