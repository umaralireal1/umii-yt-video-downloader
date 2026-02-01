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
    """
    Extracts the YouTube Video ID from various URL formats.
    """
    url = url.strip()
    patterns = [
        r'(?:v=|\/)([0-9A-Za-z_-]{11}).*',
        r'(?:v=|\/)([0-9A-Za-z_-]{11})',
        r'youtu\.be\/([0-9A-Za-z_-]{11})',
        r'shorts\/([0-9A-Za-z_-]{11})',
        r'^([0-9A-Za-z_-]{11})$'
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None

def process_tiktok_tikwm(url: str):
    try:
        api_url = "https://www.tikwm.com/api/"
        response = requests.post(api_url, data={'url': url, 'hd': 1}, timeout=5)
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
    if not video_id: 
        return None
    
    # Prioritize faster/less blocked instances
    instances = [
        "https://pipedapi.kavin.rocks",
        "https://api.piped.kotnn.me",
        "https://piped-api.lunar.icu",
        "https://pipedapi.drgns.space",
        "https://api.piped.privacy.com.de"
    ]
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    }

    for base_url in instances:
        try:
            print(f"Trying Piped Instance: {base_url}")
            # Reduced timeout to 2.5s to fail fast and try next
            api_endpoint = f"{base_url}/streams/{video_id}"
            response = requests.get(api_endpoint, headers=headers, timeout=2.5)
            
            if response.status_code == 200:
                data = response.json()
                if "error" in data: continue

                streams = data.get("videoStreams", [])
                # Prefer mp4, non-videoOnly
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
        except Exception as e:
            print(f"Instance {base_url} failed: {str(e)}")
            continue
            
    return None

def process_cobalt(url: str, backup=False):
    # Primary and Backup Cobalt instances
    api_url = "https://co.wuk.sh/api/json" if backup else "https://api.cobalt.tools/api/json"
    
    headers = {
        "Accept": "application/json", 
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
    }
    
    payload = {
        "url": url, 
        "vCodec": "h264", 
        "vQuality": "720",
        "filenamePattern": "basic",
        "isAudioOnly": False
    }
    
    try:
        print(f"Trying Cobalt ({'Backup' if backup else 'Primary'})...")
        response = requests.post(api_url, json=payload, headers=headers, timeout=8)
        data = response.json()
        
        # Cobalt success check
        if data.get("status") in ["stream", "redirect"] or "url" in data:
            return {
                "id": f"dl-{random.randint(1000, 9999)}",
                "title": data.get("text") or data.get("filename") or "Downloaded Video",
                "thumbnail": "https://images.unsplash.com/photo-1611162617213-7d7a39e9b1d7?auto=format&fit=crop&w=300",
                "duration": None,
                "platform": "Social Media",
                "download_url": data.get("url"),
                "ext": "mp4"
            }
    except Exception as e:
        print(f"Cobalt {'Backup' if backup else 'Primary'} Error: {e}")
        
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
        if not result:
            result = process_cobalt(url) # Fallback to Cobalt for TikTok
    
    # 2. YouTube Logic
    elif "youtube.com" in url or "youtu.be" in url:
        # Try Piped first
        result = process_youtube_piped(url)
        # If Piped fails, try Cobalt Primary
        if not result:
            result = process_cobalt(url, backup=False)
        # If Cobalt Primary fails, try Cobalt Backup
        if not result:
            result = process_cobalt(url, backup=True)
    
    # 3. General Fallback (Instagram, Twitter, etc.)
    else:
        result = process_cobalt(url, backup=False)
        if not result:
            result = process_cobalt(url, backup=True)

    if not result:
        # Return 400 with detail so frontend displays the error message
        return JSONResponse(status_code=400, content={
            "detail": "Extraction failed. The platform might be blocking requests or the link is private."
        })
        
    return result

@app.get("/api/download")
async def download(
    url: str = Query(..., description="Direct video URL"), 
    title: str = Query("video"),
    ext: str = Query("mp4")
):
    try:
        # Some CDNs reject requests without a User-Agent
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
            'Referer': 'https://www.youtube.com/'
        }
        
        # Increase timeout for large files
        r = requests.get(url, stream=True, headers=headers, timeout=30)
        r.raise_for_status()
        
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
        print(f"Download Proxy Error: {e}")
        raise HTTPException(status_code=500, detail="Failed to proxy download. Source link might have expired.")from fastapi import FastAPI, HTTPException, Query
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
    """
    Extracts the YouTube Video ID from various URL formats.
    """
    url = url.strip()
    patterns = [
        r'(?:v=|\/)([0-9A-Za-z_-]{11}).*',
        r'(?:v=|\/)([0-9A-Za-z_-]{11})',
        r'youtu\.be\/([0-9A-Za-z_-]{11})',
        r'shorts\/([0-9A-Za-z_-]{11})',
        r'^([0-9A-Za-z_-]{11})$'
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None

def process_tiktok_tikwm(url: str):
    try:
        api_url = "https://www.tikwm.com/api/"
        response = requests.post(api_url, data={'url': url, 'hd': 1}, timeout=5)
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
    if not video_id: 
        return None
    
    # Prioritize faster/less blocked instances
    instances = [
        "https://pipedapi.kavin.rocks",
        "https://api.piped.kotnn.me",
        "https://piped-api.lunar.icu",
        "https://pipedapi.drgns.space",
        "https://api.piped.privacy.com.de"
    ]
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    }

    for base_url in instances:
        try:
            print(f"Trying Piped Instance: {base_url}")
            # Reduced timeout to 2.5s to fail fast and try next
            api_endpoint = f"{base_url}/streams/{video_id}"
            response = requests.get(api_endpoint, headers=headers, timeout=2.5)
            
            if response.status_code == 200:
                data = response.json()
                if "error" in data: continue

                streams = data.get("videoStreams", [])
                # Prefer mp4, non-videoOnly
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
        except Exception as e:
            print(f"Instance {base_url} failed: {str(e)}")
            continue
            
    return None

def process_cobalt(url: str, backup=False):
    # Primary and Backup Cobalt instances
    api_url = "https://co.wuk.sh/api/json" if backup else "https://api.cobalt.tools/api/json"
    
    headers = {
        "Accept": "application/json", 
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
    }
    
    payload = {
        "url": url, 
        "vCodec": "h264", 
        "vQuality": "720",
        "filenamePattern": "basic",
        "isAudioOnly": False
    }
    
    try:
        print(f"Trying Cobalt ({'Backup' if backup else 'Primary'})...")
        response = requests.post(api_url, json=payload, headers=headers, timeout=8)
        data = response.json()
        
        # Cobalt success check
        if data.get("status") in ["stream", "redirect"] or "url" in data:
            return {
                "id": f"dl-{random.randint(1000, 9999)}",
                "title": data.get("text") or data.get("filename") or "Downloaded Video",
                "thumbnail": "https://images.unsplash.com/photo-1611162617213-7d7a39e9b1d7?auto=format&fit=crop&w=300",
                "duration": None,
                "platform": "Social Media",
                "download_url": data.get("url"),
                "ext": "mp4"
            }
    except Exception as e:
        print(f"Cobalt {'Backup' if backup else 'Primary'} Error: {e}")
        
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
        if not result:
            result = process_cobalt(url) # Fallback to Cobalt for TikTok
    
    # 2. YouTube Logic
    elif "youtube.com" in url or "youtu.be" in url:
        # Try Piped first
        result = process_youtube_piped(url)
        # If Piped fails, try Cobalt Primary
        if not result:
            result = process_cobalt(url, backup=False)
        # If Cobalt Primary fails, try Cobalt Backup
        if not result:
            result = process_cobalt(url, backup=True)
    
    # 3. General Fallback (Instagram, Twitter, etc.)
    else:
        result = process_cobalt(url, backup=False)
        if not result:
            result = process_cobalt(url, backup=True)

    if not result:
        # Return 400 with detail so frontend displays the error message
        return JSONResponse(status_code=400, content={
            "detail": "Extraction failed. The platform might be blocking requests or the link is private."
        })
        
    return result

@app.get("/api/download")
async def download(
    url: str = Query(..., description="Direct video URL"), 
    title: str = Query("video"),
    ext: str = Query("mp4")
):
    try:
        # Some CDNs reject requests without a User-Agent
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
            'Referer': 'https://www.youtube.com/'
        }
        
        # Increase timeout for large files
        r = requests.get(url, stream=True, headers=headers, timeout=30)
        r.raise_for_status()
        
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
        print(f"Download Proxy Error: {e}")
        raise HTTPException(status_code=500, detail="Failed to proxy download. Source link might have expired.")from fastapi import FastAPI, HTTPException, Query
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
    """
    Extracts the YouTube Video ID from various URL formats.
    """
    url = url.strip()
    patterns = [
        r'(?:v=|\/)([0-9A-Za-z_-]{11}).*',
        r'(?:v=|\/)([0-9A-Za-z_-]{11})',
        r'youtu\.be\/([0-9A-Za-z_-]{11})',
        r'shorts\/([0-9A-Za-z_-]{11})',
        r'^([0-9A-Za-z_-]{11})$'
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None

def process_tiktok_tikwm(url: str):
    try:
        api_url = "https://www.tikwm.com/api/"
        response = requests.post(api_url, data={'url': url, 'hd': 1}, timeout=5)
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
    if not video_id: 
        return None
    
    # Prioritize faster/less blocked instances
    instances = [
        "https://pipedapi.kavin.rocks",
        "https://api.piped.kotnn.me",
        "https://piped-api.lunar.icu",
        "https://pipedapi.drgns.space",
        "https://api.piped.privacy.com.de"
    ]
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    }

    for base_url in instances:
        try:
            print(f"Trying Piped Instance: {base_url}")
            # Reduced timeout to 2.5s to fail fast and try next
            api_endpoint = f"{base_url}/streams/{video_id}"
            response = requests.get(api_endpoint, headers=headers, timeout=2.5)
            
            if response.status_code == 200:
                data = response.json()
                if "error" in data: continue

                streams = data.get("videoStreams", [])
                # Prefer mp4, non-videoOnly
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
        except Exception as e:
            print(f"Instance {base_url} failed: {str(e)}")
            continue
            
    return None

def process_cobalt(url: str, backup=False):
    # Primary and Backup Cobalt instances
    api_url = "https://co.wuk.sh/api/json" if backup else "https://api.cobalt.tools/api/json"
    
    headers = {
        "Accept": "application/json", 
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
    }
    
    payload = {
        "url": url, 
        "vCodec": "h264", 
        "vQuality": "720",
        "filenamePattern": "basic",
        "isAudioOnly": False
    }
    
    try:
        print(f"Trying Cobalt ({'Backup' if backup else 'Primary'})...")
        response = requests.post(api_url, json=payload, headers=headers, timeout=8)
        data = response.json()
        
        # Cobalt success check
        if data.get("status") in ["stream", "redirect"] or "url" in data:
            return {
                "id": f"dl-{random.randint(1000, 9999)}",
                "title": data.get("text") or data.get("filename") or "Downloaded Video",
                "thumbnail": "https://images.unsplash.com/photo-1611162617213-7d7a39e9b1d7?auto=format&fit=crop&w=300",
                "duration": None,
                "platform": "Social Media",
                "download_url": data.get("url"),
                "ext": "mp4"
            }
    except Exception as e:
        print(f"Cobalt {'Backup' if backup else 'Primary'} Error: {e}")
        
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
        if not result:
            result = process_cobalt(url) # Fallback to Cobalt for TikTok
    
    # 2. YouTube Logic
    elif "youtube.com" in url or "youtu.be" in url:
        # Try Piped first
        result = process_youtube_piped(url)
        # If Piped fails, try Cobalt Primary
        if not result:
            result = process_cobalt(url, backup=False)
        # If Cobalt Primary fails, try Cobalt Backup
        if not result:
            result = process_cobalt(url, backup=True)
    
    # 3. General Fallback (Instagram, Twitter, etc.)
    else:
        result = process_cobalt(url, backup=False)
        if not result:
            result = process_cobalt(url, backup=True)

    if not result:
        # Return 400 with detail so frontend displays the error message
        return JSONResponse(status_code=400, content={
            "detail": "Extraction failed. The platform might be blocking requests or the link is private."
        })
        
    return result

@app.get("/api/download")
async def download(
    url: str = Query(..., description="Direct video URL"), 
    title: str = Query("video"),
    ext: str = Query("mp4")
):
    try:
        # Some CDNs reject requests without a User-Agent
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
            'Referer': 'https://www.youtube.com/'
        }
        
        # Increase timeout for large files
        r = requests.get(url, stream=True, headers=headers, timeout=30)
        r.raise_for_status()
        
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
        print(f"Download Proxy Error: {e}")
        raise HTTPException(status_code=500, detail="Failed to proxy download. Source link might have expired.")from fastapi import FastAPI, HTTPException, Query
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
    """
    Extracts the YouTube Video ID from various URL formats.
    """
    url = url.strip()
    patterns = [
        r'(?:v=|\/)([0-9A-Za-z_-]{11}).*',
        r'(?:v=|\/)([0-9A-Za-z_-]{11})',
        r'youtu\.be\/([0-9A-Za-z_-]{11})',
        r'shorts\/([0-9A-Za-z_-]{11})',
        r'^([0-9A-Za-z_-]{11})$'
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None

def process_tiktok_tikwm(url: str):
    try:
        api_url = "https://www.tikwm.com/api/"
        response = requests.post(api_url, data={'url': url, 'hd': 1}, timeout=5)
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
    if not video_id: 
        return None
    
    # Prioritize faster/less blocked instances
    instances = [
        "https://pipedapi.kavin.rocks",
        "https://api.piped.kotnn.me",
        "https://piped-api.lunar.icu",
        "https://pipedapi.drgns.space",
        "https://api.piped.privacy.com.de"
    ]
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    }

    for base_url in instances:
        try:
            print(f"Trying Piped Instance: {base_url}")
            # Reduced timeout to 2.5s to fail fast and try next
            api_endpoint = f"{base_url}/streams/{video_id}"
            response = requests.get(api_endpoint, headers=headers, timeout=2.5)
            
            if response.status_code == 200:
                data = response.json()
                if "error" in data: continue

                streams = data.get("videoStreams", [])
                # Prefer mp4, non-videoOnly
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
        except Exception as e:
            print(f"Instance {base_url} failed: {str(e)}")
            continue
            
    return None

def process_cobalt(url: str, backup=False):
    # Primary and Backup Cobalt instances
    api_url = "https://co.wuk.sh/api/json" if backup else "https://api.cobalt.tools/api/json"
    
    headers = {
        "Accept": "application/json", 
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
    }
    
    payload = {
        "url": url, 
        "vCodec": "h264", 
        "vQuality": "720",
        "filenamePattern": "basic",
        "isAudioOnly": False
    }
    
    try:
        print(f"Trying Cobalt ({'Backup' if backup else 'Primary'})...")
        response = requests.post(api_url, json=payload, headers=headers, timeout=8)
        data = response.json()
        
        # Cobalt success check
        if data.get("status") in ["stream", "redirect"] or "url" in data:
            return {
                "id": f"dl-{random.randint(1000, 9999)}",
                "title": data.get("text") or data.get("filename") or "Downloaded Video",
                "thumbnail": "https://images.unsplash.com/photo-1611162617213-7d7a39e9b1d7?auto=format&fit=crop&w=300",
                "duration": None,
                "platform": "Social Media",
                "download_url": data.get("url"),
                "ext": "mp4"
            }
    except Exception as e:
        print(f"Cobalt {'Backup' if backup else 'Primary'} Error: {e}")
        
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
        if not result:
            result = process_cobalt(url) # Fallback to Cobalt for TikTok
    
    # 2. YouTube Logic
    elif "youtube.com" in url or "youtu.be" in url:
        # Try Piped first
        result = process_youtube_piped(url)
        # If Piped fails, try Cobalt Primary
        if not result:
            result = process_cobalt(url, backup=False)
        # If Cobalt Primary fails, try Cobalt Backup
        if not result:
            result = process_cobalt(url, backup=True)
    
    # 3. General Fallback (Instagram, Twitter, etc.)
    else:
        result = process_cobalt(url, backup=False)
        if not result:
            result = process_cobalt(url, backup=True)

    if not result:
        # Return 400 with detail so frontend displays the error message
        return JSONResponse(status_code=400, content={
            "detail": "Extraction failed. The platform might be blocking requests or the link is private."
        })
        
    return result

@app.get("/api/download")
async def download(
    url: str = Query(..., description="Direct video URL"), 
    title: str = Query("video"),
    ext: str = Query("mp4")
):
    try:
        # Some CDNs reject requests without a User-Agent
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
            'Referer': 'https://www.youtube.com/'
        }
        
        # Increase timeout for large files
        r = requests.get(url, stream=True, headers=headers, timeout=30)
        r.raise_for_status()
        
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
        print(f"Download Proxy Error: {e}")
        raise HTTPException(status_code=500, detail="Failed to proxy download. Source link might have expired.")
