"""
Unit tests for Pydantic data models.
"""

import pytest
from datetime import datetime
from pydantic import ValidationError

from models.sustainability_models import (
    SustainabilityRating,
    ResearchPlan,
    ResearchTask,
    ResearchSummary,
    ProductAnalysisRequest,
    ProductAnalysisResponse,
)


class TestSustainabilityRating:
    """Tests for SustainabilityRating model."""

    def test_valid_rating_creation(self):
        """Test creating a valid sustainability rating."""
        rating = SustainabilityRating(
            overall_score="A",
            environmental_score="A",
            labor_score="B",
            transparency_score="A",
            rationale={
                "overall": "Excellent sustainability",
                "environmental": "Carbon neutral",
                "labor": "Fair trade certified",
                "transparency": "Full supply chain disclosure"
            },
            confidence_score=0.9,
            research_timestamp=datetime.now(),
            brand="Patagonia",
            product_url="https://example.com/product"
        )

        assert rating.overall_score == "A"
        assert rating.confidence_score == 0.9
        assert rating.brand == "Patagonia"

    def test_invalid_grade(self):
        """Test that invalid grades are rejected."""
        with pytest.raises(ValidationError):
            SustainabilityRating(
                overall_score="Z",  # Invalid grade
                environmental_score="A",
                labor_score="B",
                transparency_score="A",
                rationale={"overall": "test"},
                confidence_score=0.9,
                research_timestamp=datetime.now(),
                brand="Test",
                product_url="https://example.com"
            )

    def test_confidence_score_range(self):
        """Test that confidence score is validated."""
        # Valid confidence score
        rating = SustainabilityRating(
            overall_score="B",
            environmental_score="B",
            labor_score="B",
            transparency_score="B",
            rationale={"overall": "test"},
            confidence_score=0.5,
            research_timestamp=datetime.now(),
            brand="Test",
            product_url="https://example.com"
        )
        assert 0.0 <= rating.confidence_score <= 1.0

        # Invalid confidence score should be caught if model has validation
        with pytest.raises((ValidationError, ValueError)):
            SustainabilityRating(
                overall_score="B",
                environmental_score="B",
                labor_score="B",
                transparency_score="B",
                rationale={"overall": "test"},
                confidence_score=1.5,  # > 1.0
                research_timestamp=datetime.now(),
                brand="Test",
                product_url="https://example.com"
            )


class TestResearchPlan:
    """Tests for ResearchPlan model."""

    def test_research_plan_creation(self):
        """Test creating a research plan."""
        tasks = [
            ResearchTask(
                task_type="sustainability_reports",
                priority=1,
                status="pending",
                assigned_agent="WebResearchAgent"
            )
        ]

        plan = ResearchPlan(
            brand="Nike",
            product_url="https://nike.com/product",
            tasks=tasks,
            current_state="pending",
            created_at=datetime.now(),
            updated_at=datetime.now()
        )

        assert plan.brand == "Nike"
        assert len(plan.tasks) == 1
        assert plan.current_state == "pending"

    def test_task_priority_ordering(self, sample_research_plan):
        """Test that tasks can be sorted by priority."""
        sorted_tasks = sorted(sample_research_plan.tasks, key=lambda t: t.priority)
        assert all(
            sorted_tasks[i].priority <= sorted_tasks[i + 1].priority
            for i in range(len(sorted_tasks) - 1)
        )


class TestProductAnalysisRequest:
    """Tests for API request models."""

    def test_valid_request(self):
        """Test creating a valid analysis request."""
        request = ProductAnalysisRequest(
            product_url="https://www.patagonia.com/product/123"
        )
        assert str(request.product_url).startswith("https://")

    def test_url_validation(self):
        """Test that invalid URLs are rejected."""
        with pytest.raises(ValidationError):
            ProductAnalysisRequest(
                product_url="not-a-url"
            )


class TestProductAnalysisResponse:
    """Tests for API response models."""

    def test_response_with_rating(self, sample_sustainability_rating):
        """Test creating a response with rating."""
        response = ProductAnalysisResponse(
            rating=sample_sustainability_rating,
            processing_time_seconds=2.5,
            cached=False
        )

        assert response.rating.brand == "Patagonia"
        assert response.processing_time_seconds == 2.5
        assert response.cached is False

    def test_cached_response(self, sample_sustainability_rating):
        """Test response indicates when result is cached."""
        response = ProductAnalysisResponse(
            rating=sample_sustainability_rating,
            processing_time_seconds=0.1,
            cached=True
        )

        assert response.cached is True
        assert response.processing_time_seconds < 1.0
