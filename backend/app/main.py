"""Main FastAPI application."""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.utils.logger import logger
from app.api.routes import router as api_router
from app.api.websocket import handle_websocket
import uuid

# Create FastAPI app
app = FastAPI(
    title="AI Murder Mystery API",
    description="Multi-agent detective game backend",
    version="0.1.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173", "http://127.0.0.1:3000", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(api_router, prefix="/api")


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "status": "healthy",
        "service": "AI Murder Mystery",
        "version": "0.1.0"
    }


@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str = None):
    """WebSocket endpoint for real-time communication."""
    if client_id is None:
        client_id = str(uuid.uuid4())
    await handle_websocket(websocket, client_id)


if __name__ == "__main__":
    import uvicorn
    logger.info(f"Starting server on {settings.host}:{settings.port}")
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=True
    )