"""
FastAPI application for the Eco-Conscious Shopper sustainability rating service.

This is the main API server that coordinates the multi-agent system and provides
endpoints for the Chrome extension and other clients.
"""

import logging
import os
import time
from datetime import datetime
from typing import Dict, Optional

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import vertexai

from google.adk.runners import InMemoryRunner

from agents import (
    ResearchCoordinator,
    create_web_research_agent,
    create_supply_chain_agent,
    create_sustainability_scorer,
    extract_brand_from_url,
)
from models import (
    ProductAnalysisRequest,
    ProductAnalysisResponse,
    SustainabilityRating,
    HealthStatus,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Eco-Conscious Shopper API",
    description="Multi-agent system for sustainability rating of products and brands",
    version="1.0.0",
)

# CORS configuration for browser extension
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "chrome-extension://*",  # Chrome extensions
        "http://localhost:*",  # Local development
        "https://*.vertex-ai.google.com",  # Vertex AI Agent Engine
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Vertex AI
PROJECT_ID = os.environ.get("GOOGLE_CLOUD_PROJECT")
LOCATION = os.environ.get("GOOGLE_CLOUD_LOCATION", "global")

if PROJECT_ID:
    try:
        vertexai.init(project=PROJECT_ID, location=LOCATION)
        logger.info(f"Initialized Vertex AI for project {PROJECT_ID}")
    except Exception as e:
        logger.warning(f"Failed to initialize Vertex AI: {e}")

# Initialize agents
logger.info("Initializing agent system...")

# Create specialized agents
web_agent = create_web_research_agent()
supply_agent = create_supply_chain_agent(cache_dir="./cache")
scorer_agent = create_sustainability_scorer()

# Create coordinator
coordinator = ResearchCoordinator()
coordinator_agent = coordinator.create_agent(
    web_research_agent=web_agent,
    supply_chain_agent=supply_agent,
    sustainability_scorer=scorer_agent
)

# Agent runner
runner = InMemoryRunner(agent=coordinator_agent)

logger.info("Agent system initialized successfully")

# In-memory cache for ratings (in production, use Redis or similar)
rating_cache: Dict[str, SustainabilityRating] = {}


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "service": "Eco-Conscious Shopper API",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "analyze": "/api/analyze-product",
            "cached_rating": "/api/cached-rating/{brand}",
            "health": "/health"
        }
    }


@app.get("/health", response_model=HealthStatus)
async def health_check():
    """
    Health check endpoint required for Vertex AI deployment.

    Returns:
        HealthStatus indicating system health
    """
    services = {
        "fastapi": True,
        "agents": True,
        "vertexai": PROJECT_ID is not None,
    }

    # Determine overall status
    if all(services.values()):
        overall_status = "healthy"
    elif any(services.values()):
        overall_status = "degraded"
    else:
        overall_status = "unhealthy"

    return HealthStatus(
        status=overall_status,
        timestamp=datetime.now(),
        services=services
    )


@app.post("/api/analyze-product", response_model=ProductAnalysisResponse)
async def analyze_product(request: ProductAnalysisRequest):
    """
    PRIMARY ENDPOINT: Analyze product sustainability.

    Accepts a product URL and returns a comprehensive sustainability rating.
    MUST return within 30 second timeout.
    Includes CORS headers for browser extension.

    Args:
        request: ProductAnalysisRequest with product URL

    Returns:
        ProductAnalysisResponse with sustainability rating

    Raises:
        HTTPException: If analysis fails or times out
    """
    start_time = time.time()

    try:
        logger.info(f"Analyzing product: {request.product_url}")

        # Extract brand from URL
        brand = extract_brand_from_url(str(request.product_url))
        logger.info(f"Extracted brand: {brand}")

        # Check cache first
        cached_rating = rating_cache.get(brand.lower())
        if cached_rating:
            logger.info(f"Returning cached rating for {brand}")
            processing_time = time.time() - start_time

            return ProductAnalysisResponse(
                rating=cached_rating,
                processing_time_seconds=round(processing_time, 2),
                cached=True
            )

        # Create research plan
        plan = await coordinator.create_research_plan(
            brand=brand,
            product_url=str(request.product_url)
        )

        # Execute research through agent system
        # Note: In production, this would use the actual runner
        # For now, we'll create a mock rating to demonstrate the structure
        logger.info(f"Executing research plan for {brand}")

        # Simulate agent execution
        # In production: response = await runner.run_debug(f"Analyze {brand}")
        from agents.sustainability_scorer import SustainabilityScorer
        scorer = SustainabilityScorer()

        rating = await scorer.generate_rating(
            brand=brand,
            product_url=str(request.product_url),
            research_data={}  # Would contain actual research data
        )

        # Cache the rating
        rating_cache[brand.lower()] = rating

        processing_time = time.time() - start_time

        logger.info(
            f"Analysis complete for {brand} in {processing_time:.2f}s - "
            f"Overall grade: {rating.overall_score}"
        )

        # Check if we're within timeout
        if processing_time > 30:
            logger.warning(f"Analysis took {processing_time:.2f}s (>30s timeout)")

        return ProductAnalysisResponse(
            rating=rating,
            processing_time_seconds=round(processing_time, 2),
            cached=False
        )

    except Exception as e:
        logger.error(f"Error analyzing product: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Analysis failed: {str(e)}"
        )


@app.get("/api/cached-rating/{brand}")
async def get_cached_rating(brand: str) -> Optional[Dict]:
    """
    Retrieve cached sustainability rating for a brand.

    Args:
        brand: Brand name

    Returns:
        Cached rating if available, None otherwise
    """
    logger.info(f"Checking cache for {brand}")

    cached_rating = rating_cache.get(brand.lower())

    if cached_rating:
        return {
            "brand": brand,
            "rating": cached_rating.dict(),
            "cached": True
        }

    return {
        "brand": brand,
        "rating": None,
        "cached": False
    }


@app.delete("/api/cache/{brand}")
async def clear_cached_rating(brand: str):
    """
    Clear cached rating for a specific brand.

    Args:
        brand: Brand name

    Returns:
        Confirmation message
    """
    brand_key = brand.lower()

    if brand_key in rating_cache:
        del rating_cache[brand_key]
        logger.info(f"Cleared cache for {brand}")
        return {"message": f"Cache cleared for {brand}"}

    return {"message": f"No cached rating found for {brand}"}


@app.delete("/api/cache")
async def clear_all_cache():
    """
    Clear all cached ratings.

    Returns:
        Confirmation message with count of cleared entries
    """
    count = len(rating_cache)
    rating_cache.clear()
    logger.info(f"Cleared all cache ({count} entries)")

    return {"message": f"Cleared {count} cached ratings"}


@app.get("/api/stats")
async def get_stats():
    """
    Get API statistics.

    Returns:
        Dictionary with API stats
    """
    return {
        "cached_brands": len(rating_cache),
        "uptime": "running",
        "project_id": PROJECT_ID,
        "location": LOCATION,
    }


# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Handle HTTP exceptions with proper CORS headers."""
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "*",
            "Access-Control-Allow-Headers": "*",
        }
    )


if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("PORT", 8080))

    logger.info(f"Starting server on port {port}")

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        log_level="info"
    )
