"""
Pytest configuration and shared fixtures for all tests.
"""

import os
import sys
import pytest
from typing import Dict, Any

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from models.sustainability_models import (
    SustainabilityRating,
    ResearchPlan,
    ResearchTask,
)


@pytest.fixture
def sample_product_url() -> str:
    """Sample product URL for testing."""
    return "https://www.patagonia.com/product/mens-better-sweater-jacket/25528.html"


@pytest.fixture
def sample_brand() -> str:
    """Sample brand name for testing."""
    return "Patagonia"


@pytest.fixture
def sample_research_plan(sample_brand: str, sample_product_url: str) -> ResearchPlan:
    """Create a sample research plan for testing."""
    from datetime import datetime

    tasks = [
        ResearchTask(
            task_type="sustainability_reports",
            priority=1,
            status="pending",
            assigned_agent="WebResearchAgent"
        ),
        ResearchTask(
            task_type="supply_chain",
            priority=1,
            status="pending",
            assigned_agent="SupplyChainAgent"
        ),
    ]

    return ResearchPlan(
        brand=sample_brand,
        product_url=sample_product_url,
        tasks=tasks,
        current_state="pending",
        created_at=datetime.now(),
        updated_at=datetime.now()
    )


@pytest.fixture
def sample_sustainability_rating(sample_brand: str, sample_product_url: str) -> SustainabilityRating:
    """Create a sample sustainability rating for testing."""
    from datetime import datetime

    return SustainabilityRating(
        overall_score="B",
        environmental_score="A",
        labor_score="B",
        transparency_score="B",
        rationale={
            "overall": "Strong sustainability practices with exceptional environmental leadership",
            "environmental": "Carbon neutral operations and sustainable materials",
            "labor": "Fair Trade certified with good worker conditions",
            "transparency": "Publishes detailed supply chain information"
        },
        confidence_score=0.85,
        research_timestamp=datetime.now(),
        brand=sample_brand,
        product_url=sample_product_url
    )


@pytest.fixture
def sample_research_data() -> Dict[str, Any]:
    """Sample research data from agents."""
    return {
        "web_research_findings": {
            "sustainability_reports": [
                {
                    "title": "2023 Environmental Report",
                    "url": "https://example.com/report",
                    "summary": "Carbon neutral by 2025"
                }
            ],
            "certifications": ["B-Corp", "Fair Trade", "1% for the Planet"]
        },
        "supply_chain_analysis": {
            "transparency_score": 85.0,
            "total_suppliers": 120,
            "suppliers_disclosed": 102,
            "risk_factors": []
        }
    }


@pytest.fixture
def mock_api_key() -> str:
    """Mock Google API key for testing."""
    return os.environ.get("GOOGLE_API_KEY", "test-api-key")


@pytest.fixture(autouse=True)
def setup_test_env(monkeypatch):
    """Set up test environment variables."""
    monkeypatch.setenv("GOOGLE_CLOUD_PROJECT", "test-project")
    monkeypatch.setenv("GOOGLE_CLOUD_LOCATION", "us-central1")
    monkeypatch.setenv("GOOGLE_GENAI_USE_VERTEXAI", "0")
    monkeypatch.setenv("LOG_LEVEL", "DEBUG")
    monkeypatch.setenv("CACHE_DIR", "./test_cache")
