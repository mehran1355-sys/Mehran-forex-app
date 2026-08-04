# backend/server_registry.py

import json
from pathlib import Path

REGISTRY_FILE = Path("server_registry.json")

def set_active_server(server_id):
    data = {"active_server": server_id}
    REGISTRY_FILE.write_text(json.dumps(data))

def get_active_server():
    if not REGISTRY_FILE.exists():
        return None
    data = json.loads(REGISTRY_FILE.read_text())
    return data.get("active_server")
