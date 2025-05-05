from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import make_asgi_app

from routes import (
    auth_router, 
    user_router, 
    dataset_router, 
    analytics_router,
    pipeline_router,
    monitoring_router,
    ai_router
)

app = FastAPI(title="DataForge API", version="1.0.0")

# Set up CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify allowed origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Set up Prometheus metrics endpoint
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)

# Include routers
app.include_router(auth_router.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(user_router.router, prefix="/api/users", tags=["Users"])
app.include_router(dataset_router.router, prefix="/api/datasets", tags=["Datasets"])
app.include_router(analytics_router.router, prefix="/api/analytics", tags=["Analytics"])
app.include_router(pipeline_router.router, prefix="/api/pipeline", tags=["Pipeline"])
app.include_router(monitoring_router.router, prefix="/api/monitoring", tags=["Monitoring"])
app.include_router(ai_router.router, prefix="/api/ai", tags=["AI"])

@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "version": "1.0.0"}

@app.get("/api/python/{path:path}")
async def handle_python_endpoints(path: str):
    """
    Proxy endpoint for Python microservices.
    This simulates the API for dev purposes, in production it would route to actual services.
    """
    return {"message": f"Python endpoint {path} not implemented in demo mode"}

# If this file is run directly
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
