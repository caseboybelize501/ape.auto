"""
APE - Autonomous Production Engineer
FastAPI Application

Main application entry point with:
- CORS configuration
- Middleware setup
- Route registration
- Health checks
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from datetime import datetime
import time

from server.api import (
    requirements_router,
    plans_router,
    generations_router,
    critic_router,
    prs_router,
    deployments_router,
    incidents_router,
    repos_router,
    analytics_router,
    auth_router,
)


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    
    app = FastAPI(
        title="APE - Autonomous Production Engineer",
        description="""
## APE API

Autonomous Production Engineer takes requirements through:
1. Codebase understanding
2. Architecture planning  
3. Dependency-aware code generation
4. Critic-validated implementation
5. Test generation & execution
6. PR creation & deployment
7. Production monitoring & self-repair

### Human Gates
- **GATE-1**: Plan approval (architecture + contracts)
- **GATE-2**: PR review approval
- **GATE-3**: Production deploy approval
- **GATE-4**: Halt resolution
        """,
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )
    
    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure per environment
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Request timing middleware
    @app.middleware("http")
    async def add_process_time_header(request: Request, call_next):
        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time
        response.headers["X-Process-Time"] = str(process_time)
        return response
    
    # Exception handlers
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        return JSONResponse(
            status_code=500,
            content={
                "error": "internal_error",
                "message": str(exc),
                "path": request.url.path,
            }
        )
    
    # Health check
    @app.get("/health", tags=["health"])
    async def health_check():
        return {
            "status": "healthy",
            "version": "1.0.0",
            "timestamp": datetime.utcnow().isoformat(),
        }
    
    # Root endpoint
    @app.get("/", tags=["root"])
    async def root():
        return {
            "name": "APE - Autonomous Production Engineer",
            "version": "1.0.0",
            "docs": "/docs",
            "health": "/health",
        }
    
    # Register routers
    app.include_router(auth_router, prefix="/api", tags=["authentication"])
    app.include_router(requirements_router, prefix="/api", tags=["requirements"])
    app.include_router(plans_router, prefix="/api", tags=["plans"])
    app.include_router(generations_router, prefix="/api", tags=["generations"])
    app.include_router(critic_router, prefix="/api", tags=["critic"])
    app.include_router(prs_router, prefix="/api", tags=["prs"])
    app.include_router(deployments_router, prefix="/api", tags=["deployments"])
    app.include_router(incidents_router, prefix="/api", tags=["incidents"])
    app.include_router(repos_router, prefix="/api", tags=["repos"])
    app.include_router(analytics_router, prefix="/api", tags=["analytics"])
    
    return app


# Create app instance
app = create_app()

# App config for workers
app_config = {
    "host": "0.0.0.0",
    "port": 8000,
    "reload": True,
    "log_level": "info",
}
