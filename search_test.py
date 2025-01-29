import requests
import json

conversation_history = [
    {"user": "質問内容"}
]

url = "http://127.0.0.1:8000/conversation_history"
parameters = {
    'messages': conversation_history
}
response = requests.post(url, json=parameters)
res = json.loads(response.text)
print('res:', res)