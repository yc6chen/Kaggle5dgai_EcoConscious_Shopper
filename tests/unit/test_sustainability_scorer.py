"""
Unit tests for SustainabilityScorer agent.
"""

import pytest
from datetime import datetime

from agents.sustainability_scorer import SustainabilityScorer
from models.sustainability_models import SustainabilityRating


class TestSustainabilityScorer:
    """Tests for SustainabilityScorer class."""

    @pytest.fixture
    def scorer(self):
        """Create a SustainabilityScorer instance."""
        return SustainabilityScorer()

    def test_scorer_uses_gemini_2_5_flash(self, scorer):
        """Test that scorer is configured to use Gemini 2.5 Flash."""
        assert scorer.model_config["model"] == "gemini-2.5-flash"

    def test_scorer_low_temperature(self, scorer):
        """Test that scorer uses low temperature for consistency."""
        assert scorer.model_config["temperature"] <= 0.2

    def test_calculate_grade_a(self, scorer):
        """Test grade calculation for A grade."""
        grade = scorer.calculate_grade(90, "environmental")
        assert grade == "A"

    def test_calculate_grade_b(self, scorer):
        """Test grade calculation for B grade."""
        grade = scorer.calculate_grade(75, "labor")
        assert grade == "B"

    def test_calculate_grade_c(self, scorer):
        """Test grade calculation for C grade."""
        grade = scorer.calculate_grade(60, "transparency")
        assert grade == "C"

    def test_calculate_grade_d(self, scorer):
        """Test grade calculation for D grade."""
        grade = scorer.calculate_grade(45, "environmental")
        assert grade == "D"

    def test_calculate_grade_f(self, scorer):
        """Test grade calculation for F grade."""
        grade = scorer.calculate_grade(30, "labor")
        assert grade == "F"

    def test_calculate_overall_grade_weighted(self, scorer):
        """Test overall grade uses weighted average."""
        # Environmental: 100 (40%), Labor: 100 (40%), Transparency: 0 (20%)
        # = 100*0.4 + 100*0.4 + 0*0.2 = 80 (B grade)
        overall = scorer.calculate_overall_grade(100, 100, 0)
        assert overall == "B"

    def test_assess_confidence_full_data(self, scorer):
        """Test confidence assessment with complete data."""
        data_quality = {
            "sustainability_reports": True,
            "supply_chain_data": True,
            "esg_data": True,
            "certifications": True
        }

        confidence = scorer.assess_confidence(data_quality)
        assert confidence >= 0.9

    def test_assess_confidence_partial_data(self, scorer):
        """Test confidence assessment with partial data."""
        data_quality = {
            "sustainability_reports": True,
            "supply_chain_data": False,
            "esg_data": False,
            "certifications": True
        }

        confidence = scorer.assess_confidence(data_quality)
        assert 0.5 <= confidence < 0.9

    def test_assess_confidence_minimal_data(self, scorer):
        """Test confidence assessment with minimal data."""
        data_quality = {
            "sustainability_reports": False,
            "supply_chain_data": False,
            "esg_data": False,
            "certifications": False
        }

        confidence = scorer.assess_confidence(data_quality)
        assert confidence <= 0.6

    @pytest.mark.asyncio
    async def test_generate_rating_success(self, scorer, sample_research_data):
        """Test generating a sustainability rating."""
        rating = await scorer.generate_rating(
            brand="Patagonia",
            product_url="https://www.patagonia.com/product/123",
            research_data=sample_research_data
        )

        assert isinstance(rating, SustainabilityRating)
        assert rating.brand == "Patagonia"
        assert rating.overall_score in ["A", "B", "C", "D", "F"]
        assert 0.0 <= rating.confidence_score <= 1.0

    @pytest.mark.asyncio
    async def test_generate_rating_with_empty_data(self, scorer):
        """Test generating rating with no research data."""
        rating = await scorer.generate_rating(
            brand="UnknownBrand",
            product_url="https://example.com/product",
            research_data={}
        )

        assert isinstance(rating, SustainabilityRating)
        # Should have low or moderate confidence with no data
        assert rating.confidence_score <= 0.7

    @pytest.mark.asyncio
    async def test_generate_rating_handles_errors(self, scorer):
        """Test that rating generation handles errors gracefully."""
        # Pass invalid data that might cause errors
        rating = await scorer.generate_rating(
            brand="Test",
            product_url="https://example.com",
            research_data={"invalid": "data"}
        )

        # Should still return a rating, even if it's all F's
        assert isinstance(rating, SustainabilityRating)
        assert rating.brand == "Test"

    def test_create_agent(self, scorer):
        """Test creating the ADK agent."""
        agent = scorer.create_agent()

        assert agent is not None
        assert agent.name == "SustainabilityScorer"
        # Scorer shouldn't have tools, it synthesizes data
        assert len(agent.tools) == 0
