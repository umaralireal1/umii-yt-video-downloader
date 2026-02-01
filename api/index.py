from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
import requests
import urllib.parse
import random
import re

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def extract_youtube_id(url: str):
    regex = r"(?:v=|\/|embed\/|shorts\/|youtu.be\/)([0-9A-Za-z_-]{11})"
    match = re.search(regex, url)
    return match.group(1) if match else None

def process_tiktok_tikwm(url: str):
    try:
        api_url = "https://www.tikwm.com/api/"
        response = requests.post(api_url, data={'url': url, 'hd': 1}, timeout=7)
        data = response.json()
        if data.get("code") == 0:
            res = data["data"]
            return {
                "id": res.get("id"),
                "title": res.get("title") or "TikTok Video",
                "thumbnail": res.get("cover"),
                "duration": res.get("duration"),
                "platform": "TikTok",
                "download_url": res.get("play"),
                "ext": "mp4"
            }
    except: pass
    return None

def process_youtube_piped(url: str):
    video_id = extract_youtube_id(url)
    if not video_id: return None
    
    # Using a reliable Piped instance
    api_endpoint = f"https://pipedapi.kavin.rocks/streams/{video_id}"
    try:
        response = requests.get(api_endpoint, timeout=7)
        data = response.json()
        
        # Find best MP4 stream (video+audio combined)
        streams = data.get("videoStreams", [])
        best_stream = next((s for s in streams if s.get("format") == "MPEG-4" and not s.get("videoOnly")), None)
        
        if not best_stream and streams:
            best_stream = streams[0]
            
        if best_stream:
            return {
                "id": video_id,
                "title": data.get("title") or "YouTube Video",
                "thumbnail": data.get("thumbnailUrl"),
                "duration": data.get("duration"),
                "platform": "YouTube",
                "download_url": best_stream.get("url"),
                "ext": "mp4"
            }
    except: pass
    return None

def process_cobalt(url: str):
    api_url = "https://api.cobalt.tools/api/json"
    headers = {"Accept": "application/json", "Content-Type": "application/json"}
    payload = {"url": url, "vCodec": "h264", "vQuality": "720"}
    try:
        response = requests.post(api_url, json=payload, headers=headers, timeout=8)
        data = response.json()
        if data.get("status") in ["stream", "redirect"] or "url" in data:
            return {
                "id": f"dl-{random.randint(1000, 9999)}",
                "title": data.get("text") or "Downloaded Video",
                "thumbnail": "https://images.unsplash.com/photo-1611162617213-7d7a39e9b1d7?auto=format&fit=crop&w=300",
                "duration": None,
                "platform": "Social Media",
                "download_url": data.get("url"),
                "ext": "mp4"
            }
    except: pass
    return None

@app.get("/api/info")
async def info(url: str = Query(..., description="The URL to process")):
    if not url:
        raise HTTPException(status_code=400, detail="URL is required")
    
    result = None
    
    # 1. TikTok Logic
    if "tiktok.com" in url:
        result = process_tiktok_tikwm(url)
    
    # 2. YouTube Logic
    elif "youtube.com" in url or "youtu.be" in url:
        result = process_youtube_piped(url)
    
    # 3. Fallback / Instagram / Others Logic
    if not result:
        result = process_cobalt(url)
        
    if not result:
        return JSONResponse(status_code=400, content={"detail": "Extraction failed. The platform might be blocking requests or the link is private."})
        
    return result

@app.get("/api/download")
async def download(
    url: str = Query(..., description="Direct video URL"), 
    title: str = Query("video"),
    ext: str = Query("mp4")
):
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
        }
        r = requests.get(url, stream=True, headers=headers, timeout=15)
        r.raise_for_status()
        
        # Clean title for filename
        clean_title = re.sub(r'[^\w\-_\. ]', '_', title)[:100]
        safe_filename = urllib.parse.quote(f"{clean_title}.{ext}")
        
        return StreamingResponse(
            r.iter_content(chunk_size=1024*1024),
            media_type=r.headers.get("Content-Type", "video/mp4"),
            headers={
                "Content-Disposition": f"attachment; filename*=UTF-8''{safe_filename}"
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Proxy Download Error: {str(e)}")