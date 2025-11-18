"""
Pydantic data models for enhanced tool system.

These models support the advanced tool features including dynamic tool selection,
parallel execution, and result validation.
"""

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field


class ToolPerformanceMetrics(BaseModel):
    """Performance metrics for tracking tool effectiveness."""

    tool_name: str = Field(description="Name of the tool being tracked")

    success_rate: float = Field(
        ge=0.0, le=1.0,
        description="Success rate (0.0 to 1.0)"
    )

    average_cost: float = Field(
        ge=0.0,
        description="Average cost in dollars for tool execution"
    )

    average_latency: float = Field(
        ge=0.0,
        description="Average execution time in seconds"
    )

    last_used: datetime = Field(
        description="Timestamp of last tool use"
    )

    usage_count: int = Field(
        ge=0,
        description="Total number of times tool has been used"
    )


class ToolSelectionRequest(BaseModel):
    """Request for dynamic tool selection."""

    task_description: str = Field(
        description="Description of the research task to be performed"
    )

    available_budget: float = Field(
        ge=0.0,
        description="Budget constraint in dollars"
    )

    time_constraints: int = Field(
        ge=0,
        description="Maximum time allowed in seconds"
    )

    required_confidence: float = Field(
        ge=0.0, le=1.0,
        description="Minimum required confidence score (0.0 to 1.0)"
    )


class ToolSelection(BaseModel):
    """Result of dynamic tool selection."""

    selected_tools: List[str] = Field(
        description="List of tool names selected for the task"
    )

    reasoning: str = Field(
        description="Explanation for tool selection"
    )

    estimated_cost: float = Field(
        ge=0.0,
        description="Estimated total cost for selected tools"
    )

    estimated_time: float = Field(
        ge=0.0,
        description="Estimated total time in seconds"
    )

    expected_confidence: float = Field(
        ge=0.0, le=1.0,
        description="Expected confidence score with these tools"
    )


class ToolCall(BaseModel):
    """Representation of a tool call to be executed."""

    tool_name: str = Field(description="Name of the tool to call")

    parameters: Dict[str, Any] = Field(
        default_factory=dict,
        description="Parameters to pass to the tool"
    )

    timeout: Optional[int] = Field(
        default=30,
        description="Timeout in seconds for this specific tool call"
    )

    fallback_tools: List[str] = Field(
        default_factory=list,
        description="Alternative tools to try if this one fails"
    )


class ToolResult(BaseModel):
    """Result from a tool execution."""

    tool_name: str = Field(description="Name of the tool that was executed")

    success: bool = Field(description="Whether the tool execution succeeded")

    result: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Result data if successful"
    )

    error: Optional[str] = Field(
        default=None,
        description="Error message if failed"
    )

    execution_time: float = Field(
        ge=0.0,
        description="Actual execution time in seconds"
    )

    cost: float = Field(
        ge=0.0,
        description="Actual cost incurred in dollars"
    )


class ParallelExecutionResult(BaseModel):
    """Aggregated result from parallel tool execution."""

    successful_tools: Dict[str, ToolResult] = Field(
        description="Dictionary of successful tool executions"
    )

    failed_tools: Dict[str, str] = Field(
        description="Dictionary of failed tools (tool_name -> error_message)"
    )

    overall_status: Literal["complete", "partial", "failed"] = Field(
        description="Overall execution status"
    )

    total_execution_time: float = Field(
        ge=0.0,
        description="Total wall-clock time for parallel execution"
    )

    total_cost: float = Field(
        ge=0.0,
        description="Sum of all tool costs"
    )


class ValidationResult(BaseModel):
    """Result from tool output validation."""

    is_valid: bool = Field(
        description="Whether the data passed validation"
    )

    confidence_score: float = Field(
        ge=0.0, le=1.0,
        description="Confidence in the validation result (0.0 to 1.0)"
    )

    validation_method: str = Field(
        description="Method used for validation (e.g., 'cross_reference', 'fact_check')"
    )

    cross_reference_sources: List[str] = Field(
        default_factory=list,
        description="Sources used for cross-referencing"
    )

    anomalies_detected: List[str] = Field(
        default_factory=list,
        description="List of anomalies or inconsistencies found"
    )

    details: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Additional validation details"
    )


class DataAnomaly(BaseModel):
    """Detected anomaly in tool results."""

    anomaly_type: Literal[
        "outlier",
        "inconsistency",
        "missing_data",
        "suspicious_pattern",
        "date_mismatch"
    ] = Field(description="Type of anomaly detected")

    severity: Literal["low", "medium", "high", "critical"] = Field(
        description="Severity level of the anomaly"
    )

    affected_field: str = Field(
        description="Data field affected by the anomaly"
    )

    description: str = Field(
        description="Human-readable description of the anomaly"
    )

    suggested_action: str = Field(
        description="Recommended action to address the anomaly"
    )


class ConsensusResult(BaseModel):
    """Result from cross-verification of multiple data sources."""

    consensus_reached: bool = Field(
        description="Whether sources agree on the data"
    )

    confidence_score: float = Field(
        ge=0.0, le=1.0,
        description="Overall confidence based on source agreement"
    )

    agreed_data: Dict[str, Any] = Field(
        description="Data points where sources agree"
    )

    conflicting_data: Dict[str, List[Any]] = Field(
        default_factory=dict,
        description="Data points where sources conflict (field -> [values])"
    )

    source_weights: Dict[str, float] = Field(
        description="Reliability weight assigned to each source"
    )

    final_values: Dict[str, Any] = Field(
        description="Final consensus values (using weighted voting)"
    )


class EnhancedSearchResult(BaseModel):
    """Enhanced search result with validation and confidence scoring."""

    data: Dict[str, Any] = Field(
        description="The actual search result data"
    )

    validation: ValidationResult = Field(
        description="Validation result for this data"
    )

    sources: List[str] = Field(
        description="List of sources consulted"
    )

    tool_execution_summary: ParallelExecutionResult = Field(
        description="Summary of tool executions performed"
    )

    overall_confidence: float = Field(
        ge=0.0, le=1.0,
        description="Overall confidence in the result"
    )

    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="When the search was performed"
    )


class ToolPlan(BaseModel):
    """Cost-optimized plan for tool execution."""

    research_task: str = Field(
        description="The research task to be performed"
    )

    selected_tools: List[ToolCall] = Field(
        description="Tools selected for execution"
    )

    execution_order: List[List[str]] = Field(
        description="Ordered list of tool execution batches (for parallel execution)"
    )

    estimated_total_cost: float = Field(
        ge=0.0,
        description="Estimated total cost for the plan"
    )

    estimated_total_time: float = Field(
        ge=0.0,
        description="Estimated total time including parallelization"
    )

    budget_remaining: float = Field(
        description="Budget remaining after this plan"
    )

    meets_requirements: bool = Field(
        description="Whether plan meets all requirements"
    )

    optimization_notes: str = Field(
        description="Explanation of cost optimization strategies used"
    )
