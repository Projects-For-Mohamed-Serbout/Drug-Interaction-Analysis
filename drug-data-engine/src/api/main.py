"""
FastAPI Application for Drug Interaction Analysis.

Provides REST API endpoints for the frontend dashboard.
"""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.config.settings import get_settings
from src.services.mongodb_service import MongoDBService
from src.services.neo4j_service import Neo4jService
from src.api.routes import dashboard, medications, interactions, ingredients, laboratories, nlp, benchmarks

logger = logging.getLogger(__name__)

# Global service instances
mongodb_service: MongoDBService = None
neo4j_service: Neo4jService = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage database connections on startup/shutdown."""
    global mongodb_service, neo4j_service

    settings = get_settings()

    # Connect to MongoDB
    mongodb_service = MongoDBService(settings.mongodb_uri, settings.mongodb_db)
    if not mongodb_service.connect():
        raise RuntimeError("Failed to connect to MongoDB")

    # Connect to Neo4j
    neo4j_service = Neo4jService(
        settings.neo4j_uri, settings.neo4j_user, settings.neo4j_password
    )
    if not neo4j_service.connect():
        logger.warning("Failed to connect to Neo4j - graph endpoints will be unavailable")
        neo4j_service = None

    logger.info("API started - database connections established")

    yield

    # Shutdown
    if mongodb_service:
        mongodb_service.disconnect()
    if neo4j_service:
        neo4j_service.disconnect()
    logger.info("API shutdown - database connections closed")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="Drug Interaction Analysis API",
        description="REST API for querying drug interaction data from MongoDB and Neo4j",
        version="2.0.0",
        lifespan=lifespan,
    )

    # CORS - allow frontend on port 5173
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Global exception handler — catches unhandled errors from any route
    # and returns a clean JSON response instead of a raw stack trace
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        logger.error(f"Unhandled error on {request.method} {request.url.path}: {exc}",
                     exc_info=True)
        return JSONResponse(
            status_code=500,
            content={
                "detail": "Internal server error. Please try again later.",
                "path": request.url.path,
            },
        )

    # Register routes
    app.include_router(dashboard.router, prefix="/dashboard", tags=["Dashboard"])
    app.include_router(medications.router, prefix="/medications", tags=["Medications"])
    app.include_router(interactions.router, prefix="/interactions", tags=["Interactions"])
    app.include_router(ingredients.router, prefix="/active-ingredients", tags=["Active Ingredients"])
    app.include_router(laboratories.router, prefix="/laboratories", tags=["Laboratories"])
    app.include_router(nlp.router, prefix="/nlp-analysis", tags=["NLP Analysis"])
    app.include_router(benchmarks.router, prefix="/database-performance", tags=["Database Performance"])

    @app.get("/health")
    async def health_check():
        """Health check endpoint with database connectivity status."""
        mongo_ok = False
        neo4j_ok = False

        if mongodb_service:
            try:
                mongodb_service.client.admin.command('ping')
                mongo_ok = True
            except Exception:
                mongo_ok = False

        if neo4j_service:
            try:
                neo4j_service.driver.verify_connectivity()
                neo4j_ok = True
            except Exception:
                neo4j_ok = False

        status = "ok" if mongo_ok else "degraded"
        return {
            "status": status,
            "mongodb": mongo_ok,
            "neo4j": neo4j_ok,
        }

    return app


app = create_app()


def get_mongodb() -> MongoDBService:
    return mongodb_service


def get_neo4j() -> Neo4jService:
    return neo4j_service
