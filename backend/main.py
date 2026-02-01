import uvicorn
import requests
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import urllib.parse

app = FastAPI()

# Configure CORS
origins = [
    "*"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def home():
    return {"status": "Legacy backend active. Please use /api/ endpoints."}

@app.get("/api/info")
async def info(url: str = Query(...)):
    # Redirecting logic or simple error as we moved to api/index.py
    raise HTTPException(status_code=400, detail="Please use the Vercel API route /api/info")

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)