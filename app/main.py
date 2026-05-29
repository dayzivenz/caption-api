from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import io, hashlib, base64, asyncio
from typing import Optional

app = FastAPI(
    title="CaptionAPI",
    description="Generate high-quality captions/descriptions for AI training datasets. "
                "Powered by Moondream vision model.",
    version="2.0.0",
    docs_url="/docs",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================
# AI Caption Engine
# ============================================================

class CaptionResult(BaseModel):
    caption: str
    tags: list[str]
    model_used: str
    confidence: float
    nsfw_score: Optional[float] = None

class BatchResult(BaseModel):
    filename: str
    result: CaptionResult


def rule_based_caption(image_bytes: bytes, filename: str) -> CaptionResult:
    """Fallback rule-based caption when AI model is unavailable."""
    file_hash = hashlib.md5(image_bytes).hexdigest()[:8]
    size_kb = len(image_bytes) / 1024
    name_lower = filename.lower()
    
    tags = []
    if any(x in name_lower for x in ['anime', 'manga', '2d', 'illustration']):
        tags.extend(['anime', 'illustration'])
    elif any(x in name_lower for x in ['photo', 'realistic', 'real']):
        tags.extend(['photorealistic', 'photo'])
    else:
        tags.append('artwork')
    
    if any(x in name_lower for x in ['nsfw', 'sex', 'nude', 'porn']):
        tags.append('nsfw')
    
    if filename.endswith(('.png', '.jpg', '.jpeg', '.webp')):
        tags.append(filename.split('.')[-1])
    
    caption = f"A high-quality {', '.join(tags)} image. "
    caption += f"File: {filename} ({size_kb:.0f}KB, hash: {file_hash})"
    
    return CaptionResult(
        caption=caption,
        tags=tags,
        model_used="caption-api-v2-rule-based",
        confidence=0.75,
        nsfw_score=0.5 if 'nsfw' in tags else 0.0
    )


class AICaptionEngine:
    """AI-powered captioning via Ollama"""
    
    def __init__(self):
        self.client = None
        self.model = "moondream"  # Lightweight, 1.7GB
        self.available = False
    
    async def ensure_loaded(self):
        if self.available:
            return True
        try:
            import ollama
            self.client = ollama.AsyncClient()
            # Check if model exists
            models = await self.client.list()
            model_names = [m.get("name", "") for m in models.get("models", [])]
            if not any(self.model in n for n in model_names):
                print(f"Model {self.model} not found, falling back to rule-based")
                return False
            self.available = True
            print(f"AI Engine loaded: {self.model}")
            return True
        except Exception as e:
            print(f"AI Engine unavailable: {e}")
            return False
    
    async def generate(self, image_bytes: bytes, filename: str) -> CaptionResult:
        """Generate caption using AI model"""
        if not await self.ensure_loaded():
            return rule_based_caption(image_bytes, filename)
        
        try:
            # Convert to base64 for Ollama
            img_b64 = base64.b64encode(image_bytes).decode("utf-8")
            
            # Generate caption
            response = await self.client.generate(
                model=self.model,
                prompt="Describe this image in detail, suitable for AI training dataset caption.",
                images=[img_b64],
                options={"temperature": 0.3}
            )
            
            caption = response.get("response", "").strip()
            if not caption:
                return rule_based_caption(image_bytes, filename)
            
            # Generate tags from caption
            tags = []
            keywords = {
                "anime": ["anime", "manga", "illustration", "cartoon", "drawing"],
                "photo": ["photo", "photograph", "realistic", "photorealistic"],
                "portrait": ["portrait", "face", "person", "woman", "man", "girl", "boy"],
                "landscape": ["landscape", "mountain", "ocean", "sky", "forest", "nature"],
                "nsfw": ["nsfw", "nude", "sex", "explicit", "erotic"],
            }
            
            caption_lower = caption.lower()
            for category, words in keywords.items():
                if any(w in caption_lower for w in words):
                    tags.append(category)
            
            if not tags:
                tags.append("artwork")
            
            return CaptionResult(
                caption=caption,
                tags=list(set(tags)),
                model_used=f"caption-api-v2-{self.model}",
                confidence=0.85,
                nsfw_score=0.8 if "nsfw" in tags else 0.0
            )
            
        except Exception as e:
            print(f"AI generation error: {e}")
            return rule_based_caption(image_bytes, filename)


# Initialize engine at module level
engine = AICaptionEngine()


# ============================================================
# Routes
# ============================================================

@app.get("/")
async def root():
    ai_status = await engine.ensure_loaded()
    return {
        "service": "CaptionAPI",
        "version": "2.0.0",
        "status": "operational",
        "ai_engine": "moondream" if ai_status else "rule-based (fallback)",
        "endpoints": {
            "caption": "POST /caption - Upload image, get AI caption",
            "batch": "POST /caption/batch - Multiple images",
            "health": "GET /health",
        }
    }


@app.get("/health")
async def health():
    ai_status = await engine.ensure_loaded()
    return {
        "status": "ok",
        "ai_engine": ai_status,
        "model": engine.model if ai_status else "fallback"
    }


@app.post("/caption", response_model=CaptionResult)
async def caption_image(file: UploadFile = File(...)):
    if not file.filename:
        raise HTTPException(400, "No file provided")
    
    allowed = ['png', 'jpg', 'jpeg', 'webp', 'gif']
    ext = file.filename.rsplit('.', 1)[-1].lower() if '.' in file.filename else ''
    if ext not in allowed:
        raise HTTPException(400, f"Unsupported format: {ext}")
    
    contents = await file.read()
    if len(contents) > 10 * 1024 * 1024:
        raise HTTPException(400, "File too large. Max: 10MB")
    
    result = await engine.generate(contents, file.filename)
    return result


@app.post("/caption/batch")
async def caption_batch(files: list[UploadFile] = File(...)):
    if len(files) > 10:
        raise HTTPException(400, "Max 10 files per batch")
    
    results = []
    for f in files:
        contents = await f.read()
        result = await engine.generate(contents, f.filename or "unknown")
        results.append({
            "filename": f.filename,
            "result": result.model_dump()
        })
    
    return {"batch_size": len(results), "results": results}


@app.post("/caption/url")
async def caption_from_url(url: str):
    """Caption an image from URL"""
    import httpx
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(url)
        if resp.status_code != 200:
            raise HTTPException(400, f"Cannot fetch image from URL: {resp.status_code}")
        contents = resp.content
    
    if len(contents) > 10 * 1024 * 1024:
        raise HTTPException(400, "Image too large")
    
    result = await engine.generate(contents, url.split("/")[-1][:50])
    return result


# ============================================================
# Run: uvicorn app.main:app --host 0.0.0.0 --port 8000
# ============================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
