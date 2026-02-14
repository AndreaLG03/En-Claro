import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pathlib import Path
import os


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
        from .config import settings
        logger.info(f"Database URL Configured: {'postgres' in settings.DATABASE_URL if settings.DATABASE_URL else 'sqlite (default)'}")
        
        # TEMPORARY: Commented out to debug deployment hang
        # init_db()
        logger.info("Database initialized successfully (SKIPPED).")
    except Exception as e:
        logger.exception(f"CRITICAL: Database initialization failed: {e}")
        # We continue letting the app start so we can at least serve the frontend/debug endpoints
        # This prevents the "No open HTTP ports" error if DB is the cause of the hang
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
def find_frontend_dir():
    # 1. Check if on Render and use absolute path
    if os.environ.get("RENDER"):
        render_path = Path("/opt/render/project/src/frontend")
        if render_path.exists():
            return render_path
            
    # 2. Walk up tree for local dev or if absolute path failed
    current = Path(__file__).resolve().parent
    for _ in range(5):
        if (current / "frontend").exists() and (current / "frontend").is_dir():
            return current / "frontend"
        current = current.parent
        if current == current.parent: # Reached root
            break
            
    return None

frontend_path = find_frontend_dir()

if not frontend_path:
    # Last ditch effort for Render: maybe it's just 'frontend'?
    if Path("frontend").exists():
        frontend_path = Path("frontend").resolve()
    else:
        logger.error(f"CRITICAL: Frontend directory NOT found. CWD: {os.getcwd()}")
else:
    logger.info(f"Frontend found at: {frontend_path}")

logger.info(f"Serving frontend from: {frontend_path}")

from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware

# ... (rest of imports)

# ...

app = FastAPI(
    title="En Claro API",
    description="Backend for En Claro cognitive support app",
    version="1.0.0",
    # lifespan=lifespan # DISABLED TO DEBUG HANG
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
# Define paths
BASE_DIR = Path(__file__).resolve().parent.parent.parent
# Use the robustly found path, or fallback to relative for local dev if find_frontend_dir failed (which shouldn't happen if structure is right)
FRONTEND_DIR = frontend_path if frontend_path else (BASE_DIR / "frontend")

# Serve Frontend Static Files
if FRONTEND_DIR and FRONTEND_DIR.exists():
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
    # catch_all moved to end

else:
    logger.warning(f"Frontend directory not found at {FRONTEND_DIR}")
    @app.get("/")
    async def root():
        return {"message": "API running, but frontend files not found. Check server logs."}

@app.get("/debug-system")
async def debug_system():
    """Diagnostic endpoint to find where files are hidden"""
    import os
    cwd = os.getcwd()
    
    # List files in CWD
    files_in_cwd = []
    try:
        files_in_cwd = os.listdir(cwd)
    except Exception as e:
        files_in_cwd = [str(e)]
        
    # Walk up to find 'frontend'
    walk_up = []
    current = Path(cwd)
    for _ in range(4):
        items = []
        try:
            items = [p.name for p in current.iterdir()]
        except:
            items = ["error"]
        walk_up.append({str(current): items})
        current = current.parent
        
    # Check specific paths
    check_paths = [
        "/opt/render/project/src",
        "/opt/render/project/src/frontend",
        "/opt/render/project/src/backend",
        str(Path(__file__).resolve().parent), # app dir
        str(Path(__file__).resolve().parent.parent), # backend dir
        str(Path(__file__).resolve().parent.parent.parent), # root dir
    ]
    
    path_status = {}
    for p in check_paths:
        path_obj = Path(p)
        status = "missing"
        if path_obj.exists():
            status = "exists"
            if path_obj.is_dir():
                try:
                    status += f" (contents: {os.listdir(p)})"
                except:
                    status += " (dir, list failed)"
        path_status[p] = status

    return {
        "cwd": cwd,
        "files_in_cwd": files_in_cwd,
        "walk_up": walk_up,
        "path_status": path_status,
        "env_render": os.environ.get("RENDER"),
        "frontend_dir_variable": str(FRONTEND_DIR),
        "frontend_dir_exists": FRONTEND_DIR.exists() if FRONTEND_DIR else False
    }

# Catch-all for other static files or client-side routing
# MUST BE LAST
@app.get("/{full_path:path}")
async def catch_all(full_path: str):
    file_path = FRONTEND_DIR / full_path
    if file_path and file_path.is_file():
        return FileResponse(file_path)
        
    # If accessing a specific static file (js, css, png) and it's missing, return 404
    if "." in full_path and not full_path.endswith(".html"):
        return JSONResponse(status_code=404, content={"detail": "File not found"})

    # Fallback to index.html for SPA routing
    if FRONTEND_DIR:
        return FileResponse(FRONTEND_DIR / "index.html")
    return JSONResponse(status_code=404, content={"detail": "Frontend not found"})
