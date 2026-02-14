from fastapi import FastAPI
import os

app = FastAPI()

@app.get("/")
def read_root():
    return {
        "status": "alive", 
        "env_render": os.environ.get("RENDER"), 
        "port": os.environ.get("PORT") 
    }

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/debug-system")
def debug():
    return {"status": "minimal-mode"}
