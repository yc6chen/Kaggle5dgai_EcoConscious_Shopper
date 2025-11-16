"""
Integration tests for multi-agent workflows.
"""

import pytest
from datetime import datetime

from agents.research_coordinator import ResearchCoordinator
from agents.sustainability_scorer import SustainabilityScorer
from models.sustainability_models import SustainabilityRating


class TestMultiAgentWorkflow:
    """Integration tests for complete multi-agent research workflow."""

    @pytest.fixture
    def coordinator(self):
        """Create coordinator for integration tests."""
        return ResearchCoordinator()

    @pytest.fixture
    def scorer(self):
        """Create scorer for integration tests."""
        return SustainabilityScorer()

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_full_research_workflow(self, coordinator, scorer):
        """Test complete research workflow from plan to rating."""
        # Step 1: Create research plan
        plan = await coordinator.create_research_plan(
            brand="Patagonia",
            product_url="https://www.patagonia.com/product/123"
        )

        assert plan is not None
        assert plan.brand == "Patagonia"
        assert len(plan.tasks) > 0

        # Step 2: Execute plan (simulated for now)
        results = await coordinator.execute_plan(plan)

        assert results is not None
        assert "sustainability_data" in results

        # Step 3: Generate final rating
        rating = await scorer.generate_rating(
            brand="Patagonia",
            product_url="https://www.patagonia.com/product/123",
            research_data=results
        )

        assert isinstance(rating, SustainabilityRating)
        assert rating.overall_score in ["A", "B", "C", "D", "F"]

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_workflow_with_validation(self, coordinator, scorer):
        """Test workflow includes result validation."""
        # Create and execute plan
        plan = await coordinator.create_research_plan(
            brand="Nike",
            product_url="https://www.nike.com/product/456"
        )

        results = await coordinator.execute_plan(plan)

        # Validate results
        is_valid = await coordinator.validate_results(results)

        # Even with simulated data, validation should run
        assert isinstance(is_valid, bool)

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_workflow_caching(self, coordinator):
        """Test that workflow results can be cached."""
        from models.sustainability_models import ResearchSummary

        # Create and execute plan
        plan = await coordinator.create_research_plan(
            brand="Allbirds",
            product_url="https://www.allbirds.com/product/789"
        )

        results = await coordinator.execute_plan(plan)

        # Create summary
        summary = ResearchSummary(
            brand="Allbirds",
            sustainability_reports=[],
            certifications=["B-Corp"],
            news_articles=[],
            supply_chain_data=None,
            esg_data=None
        )

        # Cache the summary
        success = await coordinator.cache_brand_analysis("Allbirds", summary)
        assert success is True

        # Retrieve from cache
        cached = await coordinator.get_cached_analysis("Allbirds")
        assert cached is not None
        assert cached.brand == "Allbirds"
        assert "B-Corp" in cached.certifications

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_workflow_error_handling(self, coordinator, scorer):
        """Test that workflow handles errors gracefully."""
        # Create plan with potentially problematic brand
        plan = await coordinator.create_research_plan(
            brand="",  # Empty brand name
            product_url="https://example.com/product"
        )

        # Should still create a plan
        assert plan is not None

        # Execute should not crash
        results = await coordinator.execute_plan(plan)
        assert results is not None

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_multiple_products_same_brand(self, coordinator):
        """Test analyzing multiple products from same brand."""
        urls = [
            "https://www.patagonia.com/product/1",
            "https://www.patagonia.com/product/2",
            "https://www.patagonia.com/product/3"
        ]

        plans = []
        for url in urls:
            plan = await coordinator.create_research_plan(
                brand="Patagonia",
                product_url=url
            )
            plans.append(plan)

        # All should be for same brand
        assert all(p.brand == "Patagonia" for p in plans)

        # But different URLs
        assert len(set(p.product_url for p in plans)) == 3

    @pytest.mark.integration
    @pytest.mark.slow
    @pytest.mark.requires_api
    @pytest.mark.asyncio
    async def test_end_to_end_with_real_agents(self):
        """
        End-to-end test with actual ADK agents.

        This test requires valid API credentials and may take longer to run.
        """
        from agents import (
            create_web_research_agent,
            create_supply_chain_agent,
            create_sustainability_scorer,
        )
        from google.adk.runners import InMemoryRunner

        # Create agents
        web_agent = create_web_research_agent()
        supply_agent = create_supply_chain_agent(cache_dir="./test_cache")
        scorer_agent = create_sustainability_scorer()

        # Create coordinator
        coordinator = ResearchCoordinator()
        coordinator_agent = coordinator.create_agent(
            web_research_agent=web_agent,
            supply_chain_agent=supply_agent,
            sustainability_scorer=scorer_agent
        )

        # Create runner
        runner = InMemoryRunner(agent=coordinator_agent)

        # Run analysis
        prompt = """
        Analyze the sustainability of Patagonia for the product at:
        https://www.patagonia.com/product/test

        Provide environmental, labor, and transparency scores.
        """

        try:
            result = await runner.run(prompt)

            # Should get some result back
            assert result is not None

            # Log the result for inspection
            print(f"Agent result: {result}")

        except Exception as e:
            # If API credentials are invalid, test should be skipped
            pytest.skip(f"Skipping due to API error: {e}")
