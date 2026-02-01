from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
import requests
import urllib.parse
import random
import re
import json

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def extract_youtube_id(url: str):
    # Robust regex for all YT link types
    patterns = [
        r'(?:v=|\/)([0-9A-Za-z_-]{11}).*',
        r'(?:v=|\/)([0-9A-Za-z_-]{11})',
        r'youtu\.be\/([0-9A-Za-z_-]{11})',
        r'shorts\/([0-9A-Za-z_-]{11})'
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None

def process_tiktok_tikwm(url: str):
    try:
        api_url = "https://www.tikwm.com/api/"
        response = requests.post(api_url, data={'url': url, 'hd': 1}, timeout=10)
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
    except Exception as e:
        print(f"TikTok Error: {e}")
    return None

def process_youtube_piped(url: str):
    video_id = extract_youtube_id(url)
    if not video_id: return None
    
    # List of Piped instances to rotate through
    instances = [
        "https://pipedapi.kavin.rocks",
        "https://api.piped.privacy.com.de",
        "https://pipedapi.drgns.space",
        "https://api.piped.kavin.rocks",
        "https://piped-api.lunar.icu"
    ]
    
    for base_url in instances:
        try:
            print(f"Trying Piped Instance: {base_url}")
            api_endpoint = f"{base_url}/streams/{video_id}"
            response = requests.get(api_endpoint, timeout=6)
            
            if response.status_code == 200:
                data = response.json()
                
                # Check for errors in response body
                if "error" in data:
                    continue

                streams = data.get("videoStreams", [])
                
                # Find best MP4 stream (video+audio combined)
                best_stream = next((s for s in streams if s.get("format") == "MPEG-4" and not s.get("videoOnly")), None)
                
                if not best_stream and streams:
                    best_stream = streams[0] # Fallback
                    
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
        except Exception as e:
            print(f"Instance {base_url} failed: {str(e)}")
            continue
            
    return None

def process_cobalt(url: str):
    api_url = "https://api.cobalt.tools/api/json"
    headers = {
        "Accept": "application/json", 
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    payload = {
        "url": url, 
        "vCodec": "h264", 
        "vQuality": "720",
        "filenamePattern": "basic"
    }
    try:
        print("Trying Cobalt Fallback...")
        response = requests.post(api_url, json=payload, headers=headers, timeout=12)
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
        else:
            print(f"Cobalt returned non-success: {data}")
    except Exception as e:
        print(f"Cobalt Error: {e}")
    return None

@app.get("/api/info")
async def info(url: str = Query(..., description="The URL to process")):
    if not url:
        raise HTTPException(status_code=400, detail="URL is required")
    
    print(f"Processing URL: {url}")
    result = None
    
    # 1. TikTok Logic
    if "tiktok.com" in url:
        result = process_tiktok_tikwm(url)
    
    # 2. YouTube Logic
    elif "youtube.com" in url or "youtu.be" in url:
        result = process_youtube_piped(url)
    
    # 3. Fallback / Instagram / Others Logic (or if Piped failed)
    if not result:
        result = process_cobalt(url)
        
    if not result:
        return JSONResponse(status_code=400, content={
            "detail": "Extraction failed. The servers are busy or the link is restricted. Please try again in a few seconds."
        })
        
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
        r = requests.get(url, stream=True, headers=headers, timeout=20)
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
        raise HTTPException(status_code=500, detail=f"Proxy Download Error: {str(e)}")from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
import requests
import urllib.parse
import random
import re
import json

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def extract_youtube_id(url: str):
    # Robust regex for all YT link types
    patterns = [
        r'(?:v=|\/)([0-9A-Za-z_-]{11}).*',
        r'(?:v=|\/)([0-9A-Za-z_-]{11})',
        r'youtu\.be\/([0-9A-Za-z_-]{11})',
        r'shorts\/([0-9A-Za-z_-]{11})'
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None

def process_tiktok_tikwm(url: str):
    try:
        api_url = "https://www.tikwm.com/api/"
        response = requests.post(api_url, data={'url': url, 'hd': 1}, timeout=10)
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
    except Exception as e:
        print(f"TikTok Error: {e}")
    return None

def process_youtube_piped(url: str):
    video_id = extract_youtube_id(url)
    if not video_id: return None
    
    # List of Piped instances to rotate through
    instances = [
        "https://pipedapi.kavin.rocks",
        "https://api.piped.privacy.com.de",
        "https://pipedapi.drgns.space",
        "https://api.piped.kavin.rocks",
        "https://piped-api.lunar.icu"
    ]
    
    for base_url in instances:
        try:
            print(f"Trying Piped Instance: {base_url}")
            api_endpoint = f"{base_url}/streams/{video_id}"
            response = requests.get(api_endpoint, timeout=6)
            
            if response.status_code == 200:
                data = response.json()
                
                # Check for errors in response body
                if "error" in data:
                    continue

                streams = data.get("videoStreams", [])
                
                # Find best MP4 stream (video+audio combined)
                best_stream = next((s for s in streams if s.get("format") == "MPEG-4" and not s.get("videoOnly")), None)
                
                if not best_stream and streams:
                    best_stream = streams[0] # Fallback
                    
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
        except Exception as e:
            print(f"Instance {base_url} failed: {str(e)}")
            continue
            
    return None

def process_cobalt(url: str):
    api_url = "https://api.cobalt.tools/api/json"
    headers = {
        "Accept": "application/json", 
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    payload = {
        "url": url, 
        "vCodec": "h264", 
        "vQuality": "720",
        "filenamePattern": "basic"
    }
    try:
        print("Trying Cobalt Fallback...")
        response = requests.post(api_url, json=payload, headers=headers, timeout=12)
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
        else:
            print(f"Cobalt returned non-success: {data}")
    except Exception as e:
        print(f"Cobalt Error: {e}")
    return None

@app.get("/api/info")
async def info(url: str = Query(..., description="The URL to process")):
    if not url:
        raise HTTPException(status_code=400, detail="URL is required")
    
    print(f"Processing URL: {url}")
    result = None
    
    # 1. TikTok Logic
    if "tiktok.com" in url:
        result = process_tiktok_tikwm(url)
    
    # 2. YouTube Logic
    elif "youtube.com" in url or "youtu.be" in url:
        result = process_youtube_piped(url)
    
    # 3. Fallback / Instagram / Others Logic (or if Piped failed)
    if not result:
        result = process_cobalt(url)
        
    if not result:
        return JSONResponse(status_code=400, content={
            "detail": "Extraction failed. The servers are busy or the link is restricted. Please try again in a few seconds."
        })
        
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
        r = requests.get(url, stream=True, headers=headers, timeout=20)
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
