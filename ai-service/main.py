import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
try:
    from .config import MODEL_NAME, GEMINI_API_KEY
    from .routes import document_route, classify_route, literature_route
except ImportError:
    from config import MODEL_NAME, GEMINI_API_KEY
    from routes import document_route, classify_route, literature_route

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("ai-service")

app = FastAPI(
    title="Smart Inbox Assistant - AI Service",
    description="Stateless GenAI document understanding, classification and fact extraction service powered by Gemini.",
    version="1.0.0"
)

# CORS configuration for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(document_route.router)
app.include_router(classify_route.router)
app.include_router(literature_route.router)

@app.get("/health", tags=["System"])
@app.get("/ai/health", tags=["System"])
async def health_check():
    has_key = bool(GEMINI_API_KEY and GEMINI_API_KEY != "your_gemini_api_key_here")
    return {
        "status": "ok",
        "service": "ai-service",
        "model": MODEL_NAME,
        "apiKeyConfigured": has_key
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

