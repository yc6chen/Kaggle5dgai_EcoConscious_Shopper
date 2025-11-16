"""
Unit tests for ResearchCoordinator agent.
"""

import pytest
from datetime import datetime

from agents.research_coordinator import ResearchCoordinator, extract_brand_from_url
from models.sustainability_models import ResearchPlan


class TestExtractBrandFromUrl:
    """Tests for brand extraction utility."""

    def test_extract_patagonia(self):
        """Test extracting Patagonia from URL."""
        url = "https://www.patagonia.com/product/mens-better-sweater/25528.html"
        brand = extract_brand_from_url(url)
        assert brand == "Patagonia"

    def test_extract_nike(self):
        """Test extracting Nike from URL."""
        url = "https://www.nike.com/t/air-max-90/CN8490-002"
        brand = extract_brand_from_url(url)
        assert brand == "Nike"

    def test_extract_with_shop_subdomain(self):
        """Test extracting brand from shop subdomain."""
        url = "https://shop.example.com/product/123"
        brand = extract_brand_from_url(url)
        assert brand == "Example"

    def test_extract_unknown(self):
        """Test handling of invalid URLs."""
        url = "invalid-url"
        brand = extract_brand_from_url(url)
        # Should return something, even if "Unknown"
        assert isinstance(brand, str)
        assert len(brand) > 0


class TestResearchCoordinator:
    """Tests for ResearchCoordinator class."""

    @pytest.fixture
    def coordinator(self):
        """Create a ResearchCoordinator instance."""
        return ResearchCoordinator()

    @pytest.mark.asyncio
    async def test_create_research_plan(self, coordinator):
        """Test creating a research plan."""
        plan = await coordinator.create_research_plan(
            brand="Patagonia",
            product_url="https://www.patagonia.com/product/123"
        )

        assert isinstance(plan, ResearchPlan)
        assert plan.brand == "Patagonia"
        assert plan.current_state == "pending"
        assert len(plan.tasks) > 0

    @pytest.mark.asyncio
    async def test_plan_has_required_tasks(self, coordinator):
        """Test that plan includes all required task types."""
        plan = await coordinator.create_research_plan(
            brand="Nike",
            product_url="https://www.nike.com/product/123"
        )

        task_types = [task.task_type for task in plan.tasks]

        # Should include sustainability, labor, supply chain
        assert "sustainability_reports" in task_types
        assert "labor_practices" in task_types
        assert "supply_chain" in task_types

    @pytest.mark.asyncio
    async def test_tasks_have_priorities(self, coordinator):
        """Test that tasks are assigned priorities."""
        plan = await coordinator.create_research_plan(
            brand="Test",
            product_url="https://example.com/product"
        )

        for task in plan.tasks:
            assert task.priority > 0
            assert task.status == "pending"
            assert task.assigned_agent in [
                "WebResearchAgent",
                "SupplyChainAgent"
            ]

    @pytest.mark.asyncio
    async def test_validate_results_success(self, coordinator):
        """Test validating complete research results."""
        raw_data = {
            "sustainability_data": {"reports": ["report1"]},
            "supply_chain_data": {"transparency": 0.8},
            "labor_data": {"certifications": ["Fair Trade"]}
        }

        is_valid = await coordinator.validate_results(raw_data)
        assert is_valid is True

    @pytest.mark.asyncio
    async def test_validate_results_missing_data(self, coordinator):
        """Test validation fails with missing required data."""
        raw_data = {
            "sustainability_data": {},  # Empty
            "supply_chain_data": None   # Missing
        }

        is_valid = await coordinator.validate_results(raw_data)
        assert is_valid is False

    @pytest.mark.asyncio
    async def test_caching_brand_analysis(self, coordinator):
        """Test caching and retrieving brand analysis."""
        from models.sustainability_models import ResearchSummary

        summary = ResearchSummary(
            brand="Patagonia",
            sustainability_reports=[],
            certifications=[],
            news_articles=[],
            supply_chain_data=None,
            esg_data=None
        )

        # Cache the summary
        success = await coordinator.cache_brand_analysis("Patagonia", summary)
        assert success is True

        # Retrieve cached summary
        cached = await coordinator.get_cached_analysis("Patagonia")
        assert cached is not None
        assert cached.brand == "Patagonia"

    @pytest.mark.asyncio
    async def test_get_cached_nonexistent(self, coordinator):
        """Test retrieving non-existent cached analysis."""
        cached = await coordinator.get_cached_analysis("NonExistentBrand")
        assert cached is None
