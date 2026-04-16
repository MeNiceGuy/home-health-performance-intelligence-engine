import json
from pathlib import Path

FILE = Path("data/billing_state.json")

def load():
    if FILE.exists():
        return json.loads(FILE.read_text())
    return {}

def save(data):
    FILE.parent.mkdir(exist_ok=True)
    FILE.write_text(json.dumps(data, indent=2))

def get_user(username):
    data = load()
    return data.get(username, {
        "plan": "free",
        "reports_used": 0,
        "limit": 2,
        "customer_id": "",
        "subscription_id": ""
    })

def update_user(username, updates):
    data = load()
    record = get_user(username)
    record.update(updates)
    data[username] = record
    save(data)
    return record
