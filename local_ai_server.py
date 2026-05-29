"""CaptionAPI Local Proxy — talks to Ollama via its own REST API"""
import httpx, base64
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

app = FastAPI(title="CaptionAPI Local AI", version="2.1.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

OLLAMA = "http://localhost:11434"
MODEL = "dayzi-qwen-vision:latest"  # qwen2vl, works with images

class CaptionResult(BaseModel):
    caption: str
    tags: list[str]
    model_used: str
    confidence: float
    nsfw_score: float = 0.0

@app.get("/")
async def root():
    return {"service":"CaptionAPI Local AI","version":"2.1.0","model":MODEL,"status":"operational"}

@app.get("/health")
async def health():
    async with httpx.AsyncClient(timeout=5) as c:
        r = await c.get(f"{OLLAMA}/api/tags")
        models = [m["name"] for m in r.json().get("models",[])]
    return {"status":"ok","model":MODEL,"ollama_models":models}

@app.post("/caption", response_model=CaptionResult)
async def caption_image(file: UploadFile = File(...)):
    if not file.filename:
        raise HTTPException(400,"No file")
    contents = await file.read()
    if len(contents) > 20*1024*1024:
        raise HTTPException(400,"File too large")
    
    img_b64 = base64.b64encode(contents).decode("utf-8")
    
    async with httpx.AsyncClient(timeout=60) as c:
        r = await c.post(f"{OLLAMA}/api/generate", json={
            "model": MODEL,
            "prompt": "Describe this image in detail, suitable for AI training dataset caption.",
            "images": [img_b64],
            "options": {"temperature": 0.3}
        })
        if r.status_code != 200:
            raise HTTPException(502, f"Ollama error: {r.text[:200]}")
        
        # Ollama returns NDJSON — first line has response
        lines = r.text.strip().split("\n")
        caption = ""
        for line in lines:
            try:
                data = __import__("json").loads(line)
                if data.get("response"):
                    caption += data["response"]
            except:
                pass
        
        caption = caption.strip()
        if not caption:
            caption = "No description generated."
    
    # Auto-tag
    cl = caption.lower()
    tags = []
    if any(w in cl for w in ["anime","manga","illustration","drawing","cartoon"]): tags.append("anime")
    if any(w in cl for w in ["photo","realistic","photograph","photorealistic"]): tags.append("realistic")
    if any(w in cl for w in ["person","woman","man","girl","boy","portrait","human"]): tags.append("portrait")
    if any(w in cl for w in ["landscape","mountain","ocean","sky","nature","forest"]): tags.append("landscape")
    if any(w in cl for w in ["nsfw","nude","explicit","sex","erotic","pornographic"]): tags.append("nsfw")
    if not tags: tags.append("image")
    
    return CaptionResult(
        caption=caption, tags=tags,
        model_used=f"caption-api-local-{MODEL.split(':')[0]}", confidence=0.85,
        nsfw_score=0.8 if "nsfw" in tags else 0.0
    )

if __name__ == "__main__":
    print(f"Starting Local AI Proxy on :8887 (Ollama -> {MODEL})")
    uvicorn.run(app, host="0.0.0.0", port=8887, log_level="info")
