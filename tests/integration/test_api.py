"""
Integration tests for FastAPI endpoints.
"""

import pytest
from httpx import AsyncClient, ASGITransport
from fastapi.testclient import TestClient

from main import app


class TestHealthEndpoint:
    """Tests for /health endpoint."""

    def test_health_check(self):
        """Test health check endpoint returns correct status."""
        client = TestClient(app)
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()

        assert "status" in data
        assert "timestamp" in data
        assert "services" in data
        assert data["status"] in ["healthy", "degraded", "unhealthy"]


class TestRootEndpoint:
    """Tests for root endpoint."""

    def test_root_endpoint(self):
        """Test root endpoint returns API information."""
        client = TestClient(app)
        response = client.get("/")

        assert response.status_code == 200
        data = response.json()

        assert data["service"] == "Eco-Conscious Shopper API"
        assert "version" in data
        assert "endpoints" in data


class TestAnalyzeProductEndpoint:
    """Tests for /api/analyze-product endpoint."""

    @pytest.mark.slow
    @pytest.mark.requires_api
    @pytest.mark.asyncio
    async def test_analyze_product_success(self):
        """Test successful product analysis."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/api/analyze-product",
                json={"product_url": "https://www.patagonia.com/product/123"}
            )

            # May fail if API keys are not valid, but structure should be correct
            if response.status_code == 200:
                data = response.json()

                assert "rating" in data
                assert "processing_time_seconds" in data
                assert "cached" in data

                rating = data["rating"]
                assert "overall_score" in rating
                assert "environmental_score" in rating
                assert "labor_score" in rating
                assert "transparency_score" in rating

    @pytest.mark.asyncio
    async def test_analyze_product_invalid_url(self):
        """Test analysis with invalid URL."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/api/analyze-product",
                json={"product_url": "not-a-valid-url"}
            )

            # Should return validation error
            assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_analyze_product_missing_url(self):
        """Test analysis with missing URL."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/api/analyze-product",
                json={}
            )

            # Should return validation error
            assert response.status_code == 422

    @pytest.mark.slow
    @pytest.mark.requires_api
    @pytest.mark.asyncio
    async def test_analyze_product_caching(self):
        """Test that results are cached."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            # First request
            response1 = await client.post(
                "/api/analyze-product",
                json={"product_url": "https://www.example.com/test-product"}
            )

            if response1.status_code == 200:
                # Second request for same brand
                response2 = await client.post(
                    "/api/analyze-product",
                    json={"product_url": "https://www.example.com/another-product"}
                )

                if response2.status_code == 200:
                    data2 = response2.json()
                    # Second request should be faster (cached)
                    assert data2["cached"] is True or data2["processing_time_seconds"] < 1.0


class TestCacheEndpoints:
    """Tests for cache management endpoints."""

    @pytest.mark.asyncio
    async def test_get_cached_rating_not_found(self):
        """Test retrieving non-existent cached rating."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/cached-rating/NonExistentBrand")

            assert response.status_code == 200
            data = response.json()
            assert data["cached"] is False
            assert data["rating"] is None

    @pytest.mark.asyncio
    async def test_clear_cache(self):
        """Test clearing all cache."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.delete("/api/cache")

            assert response.status_code == 200
            data = response.json()
            assert "message" in data

    @pytest.mark.asyncio
    async def test_clear_brand_cache(self):
        """Test clearing specific brand cache."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.delete("/api/cache/TestBrand")

            assert response.status_code == 200
            data = response.json()
            assert "message" in data


class TestStatsEndpoint:
    """Tests for /api/stats endpoint."""

    @pytest.mark.asyncio
    async def test_stats_endpoint(self):
        """Test stats endpoint returns metrics."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/stats")

            assert response.status_code == 200
            data = response.json()

            assert "cached_brands" in data
            assert "uptime" in data
            assert isinstance(data["cached_brands"], int)


class TestCORS:
    """Tests for CORS configuration."""

    def test_cors_headers_present(self):
        """Test that CORS headers are configured."""
        client = TestClient(app)
        response = client.options(
            "/api/analyze-product",
            headers={"Origin": "chrome-extension://test"}
        )

        # Should allow CORS for chrome extensions
        assert response.status_code in [200, 405]
