import requests
import json







def send(ip,message,node_id):
    url = "https://api.wemessenger.ir/v2/9icwJq1SNWyWlWOUegXX3DrRpCqsC4eivkC5GdwscMGo7pMfOVFdjtwQRtPwoGrk6yWnciNjUxyJhv3wraljrg==/sendMessage"

    headers = {
    'Content-Type': 'application/json'
}
    payload = json.dumps({
    "to": {
    "category": "CHANNEL",
    "node": node_id,
    "session_id": "*"
    },
    "text": {
    "text": ip + " " + message
    }
})
    response = requests.request("POST", url, headers=headers, data=payload)