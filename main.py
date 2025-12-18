"""
Classification Microservice - Main Entry Point.

This is the main entry point that:
1. Sets up logging
2. Loads ML models at startup
3. Starts the FastAPI health server in a background thread
4. Runs the classification worker loop
"""

import sys
import threading
import uvicorn
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from fastapi import FastAPI

from api.health import router as health_router, set_orchestrator
from auth.jwt_handler import JWTHandler
from classifiers.classification_service import ClassificationOrchestrator
from config.settings import get_settings
from message_queue.mock_queue import MockQueue
from utils.logger import setup_logger
from workers.classification_worker import ClassificationWorker


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="Classification Microservice",
        description="Intent and Sentiment Classification Service",
        version="1.0.0"
    )
    app.include_router(health_router)
    return app


def run_api_server(app: FastAPI, host: str, port: int) -> None:
    """Run the FastAPI server (for use in background thread)."""
    uvicorn.run(app, host=host, port=port, log_level="warning")


def main():
    """Main entry point."""
    # Load settings
    settings = get_settings()
    
    # Setup logging
    logger = setup_logger(name="classification_service")
    logger.info("=" * 60)
    logger.info("Classification Microservice Starting")
    logger.info("=" * 60)
    
    # Create FastAPI app
    app = create_app()
    
    # Initialize orchestrator and load models
    logger.info("Initializing classification orchestrator...")
    orchestrator = ClassificationOrchestrator.get_instance()
    
    # Set orchestrator reference for health checks
    set_orchestrator(orchestrator)
    
    # Load models (this takes time on first run)
    orchestrator.load_models()
    
    # Start health API server in background thread
    logger.info(f"Starting health API server on {settings.API_HOST}:{settings.API_PORT}")
    api_thread = threading.Thread(
        target=run_api_server,
        args=(app, settings.API_HOST, settings.API_PORT),
        daemon=True
    )
    api_thread.start()
    
    # Initialize components
    jwt_handler = JWTHandler()
    mock_queue = MockQueue(jwt_secret=settings.JWT_SECRET)
    
    # Create and run worker
    worker = ClassificationWorker(
        queue=mock_queue,
        orchestrator=orchestrator,
        jwt_handler=jwt_handler
    )
    
    logger.info("Starting classification worker...")
    worker.run()
    
    # Print final stats
    stats = worker.stats
    logger.info("=" * 60)
    logger.info("Worker Complete")
    logger.info(f"  Processed: {stats['processed']}")
    logger.info(f"  Errors: {stats['errors']}")
    logger.info("=" * 60)
    
    # Keep the server running for a bit to allow health checks
    logger.info("Service complete. Health API still available at /health")
    logger.info("Press Ctrl+C to exit.")
    
    try:
        api_thread.join()
    except KeyboardInterrupt:
        logger.info("Shutting down...")


if __name__ == "__main__":
    main()
