"""
Pydantic data models for the Eco-Conscious Shopper sustainability rating system.

These models define the structure of data flowing through the multi-agent system.
"""

from datetime import datetime
from typing import Dict, List, Literal, Optional
from pydantic import BaseModel, Field, HttpUrl


class ResearchTask(BaseModel):
    """Individual research task within a research plan."""

    task_type: Literal[
        "sustainability_reports",
        "labor_practices",
        "supply_chain",
        "certifications"
    ] = Field(description="Type of research task to perform")

    priority: int = Field(
        ge=1, le=10,
        description="Priority level (1=highest, 10=lowest)"
    )

    status: Literal["pending", "in_progress", "complete", "failed"] = Field(
        default="pending",
        description="Current status of the task"
    )

    assigned_agent: str = Field(
        description="Name of the agent assigned to this task"
    )

    result: Optional[Dict] = Field(
        default=None,
        description="Results from task execution"
    )


class ResearchPlan(BaseModel):
    """Research plan created by the ResearchCoordinator agent."""

    brand: str = Field(description="Brand name being researched")

    product_url: HttpUrl = Field(description="URL of the product being analyzed")

    tasks: List[ResearchTask] = Field(
        description="List of research tasks to execute"
    )

    current_state: Literal[
        "pending",
        "researching",
        "analyzing",
        "complete",
        "error"
    ] = Field(
        default="pending",
        description="Current state of the research plan"
    )

    created_at: datetime = Field(
        default_factory=datetime.now,
        description="Timestamp when plan was created"
    )

    updated_at: datetime = Field(
        default_factory=datetime.now,
        description="Timestamp of last update"
    )


class SustainabilityDoc(BaseModel):
    """Sustainability report or document found during research."""

    title: str = Field(description="Document title")
    url: HttpUrl = Field(description="Document URL")
    summary: str = Field(description="Brief summary of findings")
    source: str = Field(description="Source organization/website")
    date_published: Optional[datetime] = Field(
        default=None,
        description="Publication date if available"
    )


class CompanyESGData(BaseModel):
    """Environmental, Social, and Governance data for a company."""

    company_name: str = Field(description="Company name")
    environmental_score: Optional[float] = Field(
        default=None, ge=0, le=100,
        description="Environmental rating (0-100)"
    )
    social_score: Optional[float] = Field(
        default=None, ge=0, le=100,
        description="Social responsibility rating (0-100)"
    )
    governance_score: Optional[float] = Field(
        default=None, ge=0, le=100,
        description="Governance rating (0-100)"
    )
    data_source: str = Field(description="Source of ESG data")
    last_updated: datetime = Field(
        default_factory=datetime.now,
        description="When data was last updated"
    )


class Certification(BaseModel):
    """Sustainability or ethical certification."""

    name: str = Field(description="Certification name")
    issuing_organization: str = Field(description="Organization that issues certification")
    description: str = Field(description="What the certification signifies")
    verified: bool = Field(
        default=False,
        description="Whether certification was verified"
    )


class NewsArticle(BaseModel):
    """News article about company practices."""

    title: str = Field(description="Article title")
    url: HttpUrl = Field(description="Article URL")
    summary: str = Field(description="Article summary")
    publication_date: datetime = Field(description="When article was published")
    sentiment: Literal["positive", "neutral", "negative"] = Field(
        description="Overall sentiment of article"
    )


class SupplyChainAnalysis(BaseModel):
    """Supply chain transparency analysis."""

    brand: str = Field(description="Brand name")
    transparency_score: float = Field(
        ge=0, le=100,
        description="Transparency score (0-100)"
    )
    num_suppliers: Optional[int] = Field(
        default=None,
        description="Number of known suppliers"
    )
    geographic_regions: List[str] = Field(
        default_factory=list,
        description="Geographic regions in supply chain"
    )
    risk_factors: List[str] = Field(
        default_factory=list,
        description="Identified supply chain risk factors"
    )
    data_sources: List[str] = Field(
        default_factory=list,
        description="Sources used for analysis"
    )


class TransparencyScore(BaseModel):
    """Detailed transparency scoring breakdown."""

    overall_score: float = Field(ge=0, le=100)
    supplier_disclosure: float = Field(ge=0, le=100)
    traceability: float = Field(ge=0, le=100)
    audit_availability: float = Field(ge=0, le=100)
    details: str = Field(description="Explanation of scoring")


class SustainabilityRating(BaseModel):
    """Final sustainability rating output from the system."""

    overall_score: Literal["A", "B", "C", "D", "F"] = Field(
        description="Overall sustainability grade"
    )

    environmental_score: Literal["A", "B", "C", "D", "F"] = Field(
        description="Environmental impact grade"
    )

    labor_score: Literal["A", "B", "C", "D", "F"] = Field(
        description="Labor ethics grade"
    )

    transparency_score: Literal["A", "B", "C", "D", "F"] = Field(
        description="Supply chain transparency grade"
    )

    rationale: Dict[str, str] = Field(
        description="Detailed reasoning for each category score"
    )

    confidence_score: float = Field(
        ge=0.0, le=1.0,
        description="Confidence in rating (0.0-1.0)"
    )

    research_timestamp: datetime = Field(
        default_factory=datetime.now,
        description="When research was conducted"
    )

    brand: str = Field(description="Brand that was rated")

    product_url: HttpUrl = Field(description="Product that was analyzed")


class ResearchSummary(BaseModel):
    """Aggregated research findings from all agents."""

    brand: str = Field(description="Brand name")

    sustainability_reports: List[SustainabilityDoc] = Field(
        default_factory=list,
        description="Sustainability documents found"
    )

    certifications: List[Certification] = Field(
        default_factory=list,
        description="Certifications identified"
    )

    news_articles: List[NewsArticle] = Field(
        default_factory=list,
        description="Relevant news articles"
    )

    supply_chain_data: Optional[SupplyChainAnalysis] = Field(
        default=None,
        description="Supply chain analysis results"
    )

    esg_data: Optional[CompanyESGData] = Field(
        default=None,
        description="ESG data if available"
    )


# Request/Response models for API endpoints

class ProductAnalysisRequest(BaseModel):
    """Request to analyze a product's sustainability."""

    product_url: HttpUrl = Field(description="URL of product to analyze")


class ProductAnalysisResponse(BaseModel):
    """Response containing sustainability analysis."""

    rating: SustainabilityRating = Field(description="Sustainability rating")
    processing_time_seconds: float = Field(description="Time taken to process")
    cached: bool = Field(
        default=False,
        description="Whether result was retrieved from cache"
    )


class HealthStatus(BaseModel):
    """Health check response."""

    status: Literal["healthy", "degraded", "unhealthy"]
    timestamp: datetime = Field(default_factory=datetime.now)
    services: Dict[str, bool] = Field(
        default_factory=dict,
        description="Status of individual services"
    )
