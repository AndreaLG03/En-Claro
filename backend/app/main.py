import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pathlib import Path

from .api.routes import router
from .services.claude_client import close_client
from .utils.logging_config import setup_logging

# Professional logging setup
setup_logging()
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic
    logger.info("Starting En Claro API...")
    yield
    # Shutdown logic
    logger.info("Shutting down En Claro API...")
    await close_client()

app = FastAPI(
    title="En Claro",
    description="App de apoyo cognitivo para personas autistas",
    version="0.1.0",
    lifespan=lifespan
)

# Configure CORS
# Note: allow_credentials=False for wildcard origins as per standard security
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API routes
app.include_router(router, prefix="/api")

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Ocurrió un error inesperado en el servidor. Por favor, inténtalo de nuevo más tarde."}
    )

# Define paths
BASE_DIR = Path(__file__).resolve().parent.parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"

# Serve Frontend Static Files
if FRONTEND_DIR.exists():
    # Mount specific directories to specific paths
    app.mount("/css", StaticFiles(directory=FRONTEND_DIR / "css"), name="css")
    app.mount("/js", StaticFiles(directory=FRONTEND_DIR / "js"), name="js")
    
    # Mount assets if they exist (newly added for logo)
    assets_dir = FRONTEND_DIR / "assets"
    if assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

    @app.get("/")
    async def serve_index():
        return FileResponse(FRONTEND_DIR / "index.html")

    # Catch-all for other static files or client-side routing
    @app.get("/{full_path:path}")
    async def catch_all(full_path: str):
        file_path = FRONTEND_DIR / full_path
        if file_path.is_file():
            return FileResponse(file_path)
        # Fallback to index.html for SPA routing (if we had any), or 404
        # For a simple site, returning index.html for everything might be confusing if assets are missing
        # But for now changing to only return index if it's not a file
        return FileResponse(FRONTEND_DIR / "index.html")
else:
    logger.warning(f"Frontend directory not found at {FRONTEND_DIR}")
    @app.get("/")
    async def root():
        return {"message": "API running, but frontend files not found."}
