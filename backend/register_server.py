# backend/register_server.py

from fastapi import FastAPI
from pydantic import BaseModel
from server_registry import set_active_server

app = FastAPI()

class RegisterRequest(BaseModel):
    server_id: str

@app.post("/register_server")
def register_server(req: RegisterRequest):
    set_active_server(req.server_id)
    return {"status": "registered", "server": req.server_id}
