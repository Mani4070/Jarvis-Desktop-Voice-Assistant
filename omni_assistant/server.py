from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os
from engine import process_query

app = FastAPI(title="Omni Assistant API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from pydantic import BaseModel

class CommandRequest(BaseModel):
    query: str

@app.post("/api/command")
async def handle_command(command: CommandRequest):
    query = command.query
    response_text = process_query(query)
    return JSONResponse({"status": "success", "response": response_text})

@app.get("/api/status")
async def get_status():
    return JSONResponse({"status": "online", "assistant_name": "Omni Assistant"})

# Serve static files for the Web UI
static_dir = os.path.join(os.path.dirname(__file__), "static")
if not os.path.exists(static_dir):
    os.makedirs(static_dir)

app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")

if __name__ == "__main__":
    print("Starting Omni Assistant Web Server...")
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)
