"""
Health Check API Endpoints.

Provides /health and /ready endpoints for Kubernetes probes.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel


router = APIRouter(tags=["Health"])


class HealthResponse(BaseModel):
    """Health check response model."""
    status: str
    service: str = "classification-service"
    version: str = "1.0.0"


class ReadinessResponse(BaseModel):
    """Readiness check response model."""
    status: str
    models_loaded: bool
    service: str = "classification-service"


# Reference to orchestrator - set by main.py
_orchestrator = None


def set_orchestrator(orchestrator):
    """Set the orchestrator reference for readiness checks."""
    global _orchestrator
    _orchestrator = orchestrator


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Liveness probe endpoint.
    
    Returns 200 if the service is alive.
    """
    return HealthResponse(status="healthy")


@router.get("/ready", response_model=ReadinessResponse)
async def readiness_check():
    """
    Readiness probe endpoint.
    
    Returns 200 if models are loaded and service is ready to process requests.
    Returns 503 if not ready.
    """
    if _orchestrator is None or not _orchestrator.is_ready:
        raise HTTPException(
            status_code=503,
            detail="Service not ready - models still loading"
        )
    
    return ReadinessResponse(
        status="ready",
        models_loaded=True
    )
