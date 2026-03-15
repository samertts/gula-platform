
import requests

def send_result(result):

    url = "http://localhost:8004/results"

    requests.post(url, json=result)
