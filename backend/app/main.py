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
from .models.db import init_db

from starlette.middleware.sessions import SessionMiddleware
from .api.auth import router as auth_router
from .config import settings

# Professional logging setup
setup_logging()
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic
    logger.info("Starting En Claro API...")
    try:
        init_db()
        logger.info("Database initialized successfully.")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        
    yield
    # Shutdown logic
    logger.info("Shutting down En Claro API...")
    await close_client()

# Use relative path for production (Render) - Backend serves Frontend
# We need to know where the frontend files are.
# In production structure: /opt/render/project/src/frontend
# Local structure: ../frontend (relative to backend/app/main.py)

# Robustly find the frontend directory
current_dir = Path(__file__).resolve().parent # backend/app
backend_dir = current_dir.parent # backend
project_root = backend_dir.parent # Antigravity (or root in Render)

# Try standard location first
frontend_path = project_root / "frontend"

if not frontend_path.exists():
    # Fallback for different structures or Docker
    logger.warning(f"Frontend not found at {frontend_path}, trying alternative...")
    # Check if we are in 'src' (Render sometimes)
    frontend_path = Path("/opt/render/project/src/frontend")

logger.info(f"Serving frontend from: {frontend_path}")

from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware

# ... (rest of imports)

# ...

app = FastAPI(
    title="En Claro API",
    description="App de apoyo cognitivo para personas autistas",
    version="0.1.0",
    lifespan=lifespan
)

# Trust Proxy Headers (for Render SSL termination)
app.add_middleware(ProxyHeadersMiddleware, trusted_hosts="*")

# Add Session Middleware for OAuth
# https_only=True ensures cookies are only sent over HTTPS (critical for Production)
app.add_middleware(SessionMiddleware, secret_key=settings.SECRET_KEY, https_only=settings.RENDER)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Allow all origins for dev/production flexibility
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API routes
app.include_router(router, prefix="/api")
app.include_router(auth_router, prefix="/auth")

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
    
    # Mount images/assets if they exist
    if (FRONTEND_DIR / "assets").exists():
        app.mount("/assets", StaticFiles(directory=FRONTEND_DIR / "assets"), name="assets")

    @app.get("/")
    async def read_root():
        index_path = FRONTEND_DIR / "index.html"
        if index_path.exists():
            return FileResponse(index_path)
        return {"status": "ok", "message": "Backend is running, but frontend not found."}

    @app.get("/health")
    async def health_check():
        return {"status": "ok"}
    
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
