# CaptionAPI — AI Caption Generator
# 
# FastAPI-based microservice for generating image captions.
# Designed for AI dataset creators, LoRA trainers, and content managers.
#
# Quick start:
#   pip install -e .
#   uvicorn app.main:app --reload
#   Open http://localhost:8000/docs
#
# Deploy:
#   Railway:   `railway up`
#   Render:    Add as Web Service, start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
#   Vercel:    Use vercel.json with ASGI adapter
#
# API Usage:
#   curl -X POST -F "file=@image.png" http://localhost:8000/caption
