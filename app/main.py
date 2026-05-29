from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn, httpx, base64
from typing import Optional

app = FastAPI(title="CaptionAPI", version="2.2.0", docs_url="/docs")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

LOCAL_AI = "http://localhost:8887"

class CaptionResult(BaseModel):
    caption: str
    tags: list[str]
    model_used: str
    confidence: float
    nsfw_score: float = 0.0

@app.get("/")
async def root():
    ai_ok = False
    try:
        async with httpx.AsyncClient(timeout=3) as c:
            r = await c.get(f"{LOCAL_AI}/")
            ai_ok = r.status_code == 200
    except:
        pass
    return {
        "service": "CaptionAPI",
        "version": "2.2.0",
        "status": "operational",
        "ai_engine": "dayzi-qwen-vision" if ai_ok else "rule-based (fallback)",
        "endpoints": {
            "caption": "POST /caption",
            "batch": "POST /caption/batch",
            "url": "POST /caption/url",
            "health": "GET /health",
        }
    }

@app.get("/health")
async def health():
    ai_ok = False
    try:
        async with httpx.AsyncClient(timeout=3) as c:
            r = await c.get(f"{LOCAL_AI}/health")
            ai_ok = r.status_code == 200
    except:
        pass
    return {"status": "ok", "ai_engine": ai_ok, "model": "dayzi-qwen-vision" if ai_ok else "fallback"}

def rule_caption(contents: bytes, filename: str) -> CaptionResult:
    import hashlib
    h = hashlib.md5(contents).hexdigest()[:8]
    name = filename.lower()
    tags = []
    if any(x in name for x in ['anime','manga','2d']): tags.append('anime')
    if any(x in name for x in ['photo','realistic']): tags.append('realistic')
    if any(x in name for x in ['nsfw','sex','nude']): tags.append('nsfw')
    if not tags: tags.append('artwork')
    return CaptionResult(
        caption=f"A high-quality {', '.join(tags)} image. File: {filename} (hash: {h})",
        tags=tags, model_used="caption-api-rule", confidence=0.75,
        nsfw_score=0.8 if 'nsfw' in tags else 0.0)

@app.post("/caption", response_model=CaptionResult)
async def caption_image(file: UploadFile = File(...)):
    if not file.filename:
        raise HTTPException(400, "No file")
    ext = file.filename.rsplit('.',1)[-1].lower() if '.' in file.filename else ''
    if ext not in ['png','jpg','jpeg','webp','gif']:
        raise HTTPException(400, f"Unsupported format: {ext}")
    contents = await file.read()
    if len(contents) > 10*1024*1024:
        raise HTTPException(400, "File too large")
    # Try AI first
    try:
        async with httpx.AsyncClient(timeout=30) as c:
            r = await c.post(f"{LOCAL_AI}/caption",
                files={"file": (file.filename, contents, f"image/{ext}")})
            if r.status_code == 200:
                return CaptionResult(**r.json())
    except:
        pass
    return rule_caption(contents, file.filename)

@app.post("/caption/url", response_model=CaptionResult)
async def caption_url(url: str):
    async with httpx.AsyncClient(timeout=15) as c:
        resp = await c.get(url)
        if resp.status_code != 200:
            raise HTTPException(400, f"Cannot fetch: {resp.status_code}")
        contents = resp.content
    if len(contents) > 10*1024*1024:
        raise HTTPException(400, "Image too large")
    filename = url.split("/")[-1][:50] or "image.png"
    try:
        async with httpx.AsyncClient(timeout=30) as c:
            async with httpx.AsyncClient(timeout=30) as c2:
                r = await c2.post(f"{LOCAL_AI}/caption",
                    files={"file": (filename, contents, "image/png")})
                if r.status_code == 200:
                    return CaptionResult(**r.json())
    except:
        pass
    return rule_caption(contents, filename)

@app.post("/caption/batch")
async def caption_batch(files: list[UploadFile] = File(...)):
    if len(files) > 10:
        raise HTTPException(400, "Max 10 files")
    results = []
    for f in files:
        contents = await f.read()
        try:
            async with httpx.AsyncClient(timeout=30) as c:
                r = await c.post(f"{LOCAL_AI}/caption",
                    files={"file": (f.filename or "img.png", contents, "image/png")})
                if r.status_code == 200:
                    results.append({"filename": f.filename, "result": r.json()})
                    continue
        except:
            pass
        rc = rule_caption(contents, f.filename or "unknown")
        results.append({"filename": f.filename, "result": rc.model_dump()})
    return {"batch_size": len(results), "results": results}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
