import os
import logging
from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import time
from typing import Callable

# Import routers
from routes.ai_router import router as ai_router
from routes.openevals_router import router as openevals_router
from routes.openevals_runtime_router import router as openevals_runtime_router
from routes.dataset_router import router as dataset_router
from routes.project_eval_router import router as project_eval_router
from routes.dashboard_router import router as dashboard_router
from routes.analytics_router import router as analytics_router
from routes.conversation_analytics_router import router as conversation_analytics_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("api")

# Create FastAPI app
app = FastAPI(
    title="Insight Forge Analytics Hub API",
    description="API for Insight Forge Analytics Hub with AI capabilities",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Middleware for request logging and timing
@app.middleware("http")
async def log_requests(request: Request, call_next: Callable):
    start_time = time.time()
    
    # Process the request
    try:
        response = await call_next(request)
    except Exception as e:
        logger.error(f"Request error: {str(e)}")
        raise
    
    # Calculate processing time
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    
    # Log request details
    logger.info(
        f"Request: {request.method} {request.url.path} "
        f"- Status: {response.status_code} "
        f"- Time: {process_time:.4f}s"
    )
    
    return response

# Error handler
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": exc.detail,
            "status": exc.status_code
        }
    )

# Root endpoint
@app.get("/")
async def root():
    return {
        "success": True,
        "message": "Welcome to Insight Forge Analytics Hub API",
        "version": "1.0.0"
    }

# Health check endpoint
@app.get("/health")
async def health_check():
    return {
        "success": True,
        "status": "healthy",
        "timestamp": time.time()
    }

# Include routers
app.include_router(ai_router)
app.include_router(openevals_router)
app.include_router(openevals_runtime_router)
app.include_router(dataset_router, prefix="/datasets")
app.include_router(project_eval_router, prefix="/project-eval")
app.include_router(dashboard_router, prefix="/dashboard")
app.include_router(conversation_analytics_router, prefix="/conversation-analytics")
app.include_router(analytics_router, prefix="/analytics")

# Add startup event
@app.on_event("startup")
async def startup_event():
    logger.info("Starting up API server")
    
    # Initialize services and check connections
    try:
        # Import here to avoid circular imports
        from services.vector_service import vector_service
        from services.cache_service import cache_service
        from services.ai_service import ai_service
        from services.project_evaluator import project_evaluator
        from config.openevals_config import openevals_config
        
        # Initialize services
        await vector_service.initialize()
        cache_service.initialize()
        await ai_service.initialize()
        
        # Create logs directory for project evaluations
        os.makedirs(os.path.join(os.path.dirname(__file__), "logs", "project_evaluations"), exist_ok=True)
        
        logger.info("All services initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing services: {str(e)}")
        # Continue running even if some services fail

# Add shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down Insight Forge Analytics Hub API")
    
    # Save cache
    from services.cache_service import save_cache
    save_cache()
    
    # Save vector database
    from services.vector_service import save_vector_db
    save_vector_db()
    
    logger.info("Shutdown complete")

# Run the application
if __name__ == "__main__":
    import uvicorn
    
    # Get port from environment or use default
    port = int(os.environ.get("PORT", 8000))
    
    # Run server
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
