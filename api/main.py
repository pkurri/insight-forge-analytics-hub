from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
from dotenv import load_dotenv
from db.connection import init_db_pool, close_db_pool
from routes import pipeline_router

# Load environment variables
load_dotenv()

# Create FastAPI app
app = FastAPI(
    title="InsightForge Analytics Hub",
    description="A powerful data analytics and processing platform",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(pipeline_router.router)

@app.on_event("startup")
async def startup_event():
    """Initialize database connection pool on startup."""
    await init_db_pool()

@app.on_event("shutdown")
async def shutdown_event():
    """Close database connection pool on shutdown."""
    await close_db_pool()

@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Welcome to InsightForge Analytics Hub",
        "version": "1.0.0",
        "status": "running"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8000)),
        reload=True
    ) 