from fastapi import FastAPI
from backend.app.api.endpoints import router as api_router

app = FastAPI(
    title="Cross-Hospital Generalization Platform Backend",
    version="1.0.0",
    description="Production-grade asynchronous ingestion layer for secure clinical MLOps workflows."
)

# Include the inbound data endpoint router
app.include_router(api_router)

@app.get("/health", tags=["System Health"])
async def health_check():
    return {"status": "healthy"}