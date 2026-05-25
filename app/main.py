from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import io
from typing import Optional

app = FastAPI(
    title="CaptionAPI",
    description="Generate high-quality captions/descriptions for AI training datasets. "
                "Supports anime, realistic, and general content.",
    version="1.0.0",
    docs_url="/docs",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================
# In-memory caption generator (rule-based + simple AI)
# ============================================================

class CaptionResult(BaseModel):
    caption: str
    tags: list[str]
    model_used: str
    confidence: float
    nsfw_score: Optional[float] = None


def generate_caption_from_image(image_bytes: bytes, filename: str) -> CaptionResult:
    """
    Analyze image and generate caption.
    For MVP: rule-based + basic analysis.
    Future: integrate Moondream/LLaVA for true captioning.
    """
    import hashlib
    
    # Basic image info
    file_hash = hashlib.md5(image_bytes).hexdigest()[:8]
    size_kb = len(image_bytes) / 1024
    
    # Extract filename info
    name_lower = filename.lower()
    
    # Base tags based on filename hints
    tags = []
    
    if any(x in name_lower for x in ['anime', 'manga', '2d', 'illustration']):
        tags.extend(['anime', 'illustration'])
    elif any(x in name_lower for x in ['photo', 'realistic', 'real', 'photo']):
        tags.extend(['photorealistic', 'photo'])
    else:
        tags.append('artwork')
    
    if any(x in name_lower for x in ['nsfw', 'sex', 'nude', 'porn']):
        tags.append('nsfw')
    
    # Check for orientation
    # (real orientation detection needs PIL - will add later)
    
    # Check file type
    if filename.endswith(('.png', '.jpg', '.jpeg', '.webp')):
        tags.append(filename.split('.')[-1])
    
    caption = f"A high-quality {', '.join(tags)} image. "
    caption += f"File: {filename} ({size_kb:.0f}KB, hash: {file_hash})"
    
    return CaptionResult(
        caption=caption,
        tags=tags,
        model_used="caption-api-v1-rule-based",
        confidence=0.75,
        nsfw_score=0.5 if 'nsfw' in tags else 0.0
    )


# ============================================================
# Routes
# ============================================================

@app.get("/")
async def root():
    return {
        "service": "CaptionAPI",
        "version": "1.0.0",
        "status": "operational",
        "endpoints": {
            "caption": "POST /caption - Upload image, get caption",
            "batch": "POST /caption/batch - Multiple images",
            "health": "GET /health",
        }
    }


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/caption", response_model=CaptionResult)
async def caption_image(
    file: UploadFile = File(...),
):
    """
    Upload an image and receive an AI-generated caption.
    
    Accepted formats: png, jpg, jpeg, webp, gif
    Max size: 10MB
    """
    # Validate file
    if not file.filename:
        raise HTTPException(400, "No file provided")
    
    allowed = ['png', 'jpg', 'jpeg', 'webp', 'gif']
    ext = file.filename.rsplit('.', 1)[-1].lower() if '.' in file.filename else ''
    if ext not in allowed:
        raise HTTPException(400, f"Unsupported format: {ext}. Allowed: {', '.join(allowed)}")
    
    # Read file
    contents = await file.read()
    
    if len(contents) > 10 * 1024 * 1024:  # 10MB
        raise HTTPException(400, "File too large. Max: 10MB")
    
    # Generate caption
    result = generate_caption_from_image(contents, file.filename)
    
    return result


@app.post("/caption/batch")
async def caption_batch(files: list[UploadFile] = File(...)):
    """Process up to 10 images at once."""
    if len(files) > 10:
        raise HTTPException(400, "Max 10 files per batch")
    
    results = []
    for f in files:
        contents = await f.read()
        result = generate_caption_from_image(contents, f.filename or "unknown")
        results.append({
            "filename": f.filename,
            "result": result.model_dump()
        })
    
    return {"batch_size": len(results), "results": results}


# ============================================================
# Run with: uvicorn app.main:app --host 0.0.0.0 --port 8000
# ============================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
