"""
Dynamic Tool Selector with Cost Optimization.

This module provides intelligent tool selection based on task requirements,
historical performance, cost constraints, and reliability metrics.

DEMONSTRATES: Advanced Tool Use + Planning + Evaluation
INTEGRATION: Seamlessly works with existing @tool decorator pattern
"""

import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

import google.generativeai as genai

from models.tool_models import (
    ToolCall,
    ToolPerformanceMetrics,
    ToolPlan,
    ToolSelection,
    ToolSelectionRequest,
)

logger = logging.getLogger(__name__)


class DynamicToolSelector:
    """
    Intelligently selects optimal tools for research tasks based on:
    - Historical performance metrics
    - Cost constraints
    - Time requirements
    - Reliability data
    """

    def __init__(
        self,
        metrics_cache_dir: str = "./cache/tool_metrics",
        gemini_model: str = "gemini-2.5-flash"
    ):
        """
        Initialize the Dynamic Tool Selector.

        Args:
            metrics_cache_dir: Directory to store tool performance metrics
            gemini_model: Gemini model to use for intelligent selection
        """
        self.metrics_cache_dir = Path(metrics_cache_dir)
        self.metrics_cache_dir.mkdir(parents=True, exist_ok=True)

        self.tool_registry: Dict[str, Dict] = {}
        self.tool_metrics: Dict[str, ToolPerformanceMetrics] = {}

        # Initialize Gemini client for intelligent tool selection
        self.gemini_model = gemini_model

        # Load existing metrics from cache
        self._load_metrics()

        # Initialize default tool registry
        self._initialize_tool_registry()

    def _initialize_tool_registry(self) -> None:
        """Initialize the registry of available tools with their characteristics."""
        self.tool_registry = {
            "search_sustainability_reports": {
                "description": "Search for published sustainability/ESG reports",
                "typical_cost": 0.01,  # API cost in dollars
                "typical_latency": 5.0,  # seconds
                "data_quality": "high",
                "reliability": 0.9,
                "best_for": ["environmental_data", "corporate_reports"]
            },
            "scrape_company_esg_page": {
                "description": "Scrape company sustainability page for ESG data",
                "typical_cost": 0.05,
                "typical_latency": 10.0,
                "data_quality": "medium",
                "reliability": 0.75,
                "best_for": ["company_specific_data", "recent_initiatives"]
            },
            "get_company_certifications": {
                "description": "Verify sustainability certifications (B Corp, Fair Trade, etc.)",
                "typical_cost": 0.02,
                "typical_latency": 3.0,
                "data_quality": "high",
                "reliability": 0.95,
                "best_for": ["certification_verification", "standards_compliance"]
            },
            "search_labor_practices_news": {
                "description": "Search for news about labor practices and worker treatment",
                "typical_cost": 0.01,
                "typical_latency": 4.0,
                "data_quality": "medium",
                "reliability": 0.8,
                "best_for": ["labor_practices", "recent_news", "controversies"]
            },
            "google_search": {
                "description": "Built-in Google search for general information",
                "typical_cost": 0.005,
                "typical_latency": 2.0,
                "data_quality": "variable",
                "reliability": 0.85,
                "best_for": ["general_research", "quick_facts"]
            },
            "analyze_supply_chain": {
                "description": "Analyze supply chain using OpenSupplyHub API",
                "typical_cost": 0.03,
                "typical_latency": 8.0,
                "data_quality": "high",
                "reliability": 0.85,
                "best_for": ["supply_chain_transparency", "facility_data"]
            }
        }

    def _load_metrics(self) -> None:
        """Load tool performance metrics from cache."""
        metrics_file = self.metrics_cache_dir / "tool_metrics.json"

        if metrics_file.exists():
            try:
                with open(metrics_file, 'r') as f:
                    data = json.load(f)

                for tool_name, metrics_dict in data.items():
                    self.tool_metrics[tool_name] = ToolPerformanceMetrics(**metrics_dict)

                logger.info(f"Loaded metrics for {len(self.tool_metrics)} tools")
            except Exception as e:
                logger.error(f"Error loading tool metrics: {e}")
        else:
            logger.info("No cached metrics found, starting fresh")

    def _save_metrics(self) -> None:
        """Save tool performance metrics to cache."""
        metrics_file = self.metrics_cache_dir / "tool_metrics.json"

        try:
            data = {
                tool_name: metrics.model_dump(mode='json')
                for tool_name, metrics in self.tool_metrics.items()
            }

            with open(metrics_file, 'w') as f:
                json.dump(data, f, indent=2, default=str)

            logger.debug(f"Saved metrics for {len(self.tool_metrics)} tools")
        except Exception as e:
            logger.error(f"Error saving tool metrics: {e}")

    async def select_optimal_tools(
        self,
        task_description: str,
        context: Dict
    ) -> List[ToolCall]:
        """
        Select optimal tools for a given task using Gemini AI analysis.

        Args:
            task_description: Description of the research task
            context: Additional context (budget, company_size, etc.)

        Returns:
            List of ToolCall objects representing selected tools
        """
        budget = context.get("budget", 10.0)
        time_limit = context.get("time_limit", 60)
        required_confidence = context.get("required_confidence", 0.7)

        # Build prompt for Gemini to analyze task and select tools
        prompt = self._build_selection_prompt(
            task_description,
            budget,
            time_limit,
            required_confidence
        )

        try:
            # Use Gemini to intelligently select tools
            model = genai.GenerativeModel(self.gemini_model)
            response = model.generate_content(prompt)

            # Parse response and create ToolCall objects
            selected_tools = self._parse_gemini_selection(response.text)

            logger.info(
                f"Selected {len(selected_tools)} tools for task: {task_description[:50]}..."
            )

            return selected_tools

        except Exception as e:
            logger.error(f"Error in tool selection: {e}")
            # Fallback to default tool selection
            return self._fallback_selection(task_description)

    def _build_selection_prompt(
        self,
        task_description: str,
        budget: float,
        time_limit: int,
        required_confidence: float
    ) -> str:
        """Build prompt for Gemini to select optimal tools."""

        # Include current metrics in the prompt
        metrics_summary = self._get_metrics_summary()

        prompt = f"""You are a tool selection expert for sustainability research.

TASK: {task_description}

CONSTRAINTS:
- Budget: ${budget}
- Time Limit: {time_limit} seconds
- Required Confidence: {required_confidence}

AVAILABLE TOOLS:
{json.dumps(self.tool_registry, indent=2)}

HISTORICAL PERFORMANCE:
{metrics_summary}

Select the optimal combination of tools that will:
1. Stay within budget constraints
2. Complete within time limit
3. Achieve required confidence level
4. Maximize data quality and reliability

Return your selection as a JSON array with this format:
[
  {{
    "tool_name": "tool_name_here",
    "reasoning": "why this tool was selected",
    "priority": 1
  }}
]

Consider:
- Tools with higher historical success rates
- Cost-effective options that meet quality requirements
- Complementary tools that can cross-validate data
- Parallel execution opportunities
"""
        return prompt

    def _get_metrics_summary(self) -> str:
        """Generate a summary of current tool metrics."""
        if not self.tool_metrics:
            return "No historical metrics available yet."

        summary = []
        for tool_name, metrics in self.tool_metrics.items():
            summary.append(
                f"- {tool_name}: "
                f"Success Rate: {metrics.success_rate:.2%}, "
                f"Avg Cost: ${metrics.average_cost:.3f}, "
                f"Avg Latency: {metrics.average_latency:.1f}s, "
                f"Usage Count: {metrics.usage_count}"
            )

        return "\n".join(summary)

    def _parse_gemini_selection(self, response_text: str) -> List[ToolCall]:
        """Parse Gemini's tool selection response."""
        try:
            # Extract JSON from response
            start = response_text.find('[')
            end = response_text.rfind(']') + 1

            if start == -1 or end == 0:
                raise ValueError("No JSON array found in response")

            json_str = response_text[start:end]
            selections = json.loads(json_str)

            # Convert to ToolCall objects
            tool_calls = []
            for selection in selections:
                tool_name = selection.get("tool_name")

                if tool_name in self.tool_registry:
                    tool_calls.append(
                        ToolCall(
                            tool_name=tool_name,
                            parameters={},  # Will be filled by the agent
                            timeout=30,
                            fallback_tools=[]
                        )
                    )

            return tool_calls

        except Exception as e:
            logger.error(f"Error parsing Gemini selection: {e}")
            return []

    def _fallback_selection(self, task_description: str) -> List[ToolCall]:
        """Fallback tool selection based on task keywords."""
        selected_tools = []

        task_lower = task_description.lower()

        # Simple keyword-based selection
        if "sustainability" in task_lower or "environmental" in task_lower:
            selected_tools.append(
                ToolCall(tool_name="search_sustainability_reports", parameters={})
            )
            selected_tools.append(
                ToolCall(tool_name="scrape_company_esg_page", parameters={})
            )

        if "labor" in task_lower or "workers" in task_lower:
            selected_tools.append(
                ToolCall(tool_name="search_labor_practices_news", parameters={})
            )
            selected_tools.append(
                ToolCall(tool_name="get_company_certifications", parameters={})
            )

        if "supply chain" in task_lower:
            selected_tools.append(
                ToolCall(tool_name="analyze_supply_chain", parameters={})
            )

        # Always include Google search as a catch-all
        if not selected_tools:
            selected_tools.append(
                ToolCall(tool_name="google_search", parameters={})
            )

        logger.info(f"Using fallback selection: {len(selected_tools)} tools")
        return selected_tools

    async def update_tool_metrics(
        self,
        tool_name: str,
        success: bool,
        cost: float,
        latency: float
    ) -> None:
        """
        Update performance metrics for a tool after execution.

        Args:
            tool_name: Name of the tool
            success: Whether execution was successful
            cost: Actual cost incurred
            latency: Actual execution time
        """
        if tool_name not in self.tool_metrics:
            # Initialize new metrics
            self.tool_metrics[tool_name] = ToolPerformanceMetrics(
                tool_name=tool_name,
                success_rate=1.0 if success else 0.0,
                average_cost=cost,
                average_latency=latency,
                last_used=datetime.utcnow(),
                usage_count=1
            )
        else:
            # Update existing metrics using exponential moving average
            metrics = self.tool_metrics[tool_name]
            alpha = 0.3  # Weight for new values

            # Update success rate
            new_success_value = 1.0 if success else 0.0
            metrics.success_rate = (
                alpha * new_success_value +
                (1 - alpha) * metrics.success_rate
            )

            # Update average cost
            metrics.average_cost = (
                alpha * cost +
                (1 - alpha) * metrics.average_cost
            )

            # Update average latency
            metrics.average_latency = (
                alpha * latency +
                (1 - alpha) * metrics.average_latency
            )

            # Update usage info
            metrics.last_used = datetime.utcnow()
            metrics.usage_count += 1

        # Save updated metrics
        self._save_metrics()

        logger.debug(
            f"Updated metrics for {tool_name}: "
            f"success_rate={self.tool_metrics[tool_name].success_rate:.2%}"
        )

    async def get_cost_optimized_plan(
        self,
        research_task: str,
        budget_constraints: Dict
    ) -> ToolPlan:
        """
        Create a cost-optimized execution plan for a research task.

        Args:
            research_task: Description of the research to perform
            budget_constraints: Budget limits and requirements

        Returns:
            ToolPlan with optimized tool selection and execution order
        """
        max_budget = budget_constraints.get("max_budget", 5.0)
        max_time = budget_constraints.get("max_time", 30)
        min_confidence = budget_constraints.get("min_confidence", 0.7)

        # Select tools
        context = {
            "budget": max_budget,
            "time_limit": max_time,
            "required_confidence": min_confidence
        }

        selected_tools = await self.select_optimal_tools(research_task, context)

        # Calculate estimated costs and times
        total_cost = 0.0
        total_time = 0.0

        for tool_call in selected_tools:
            tool_info = self.tool_registry.get(tool_call.tool_name, {})
            total_cost += tool_info.get("typical_cost", 0.01)
            total_time += tool_info.get("typical_latency", 5.0)

        # Optimize execution order for parallelization
        # Tools with no dependencies can run in parallel
        execution_order = [
            [tool.tool_name for tool in selected_tools]  # All in first batch
        ]

        # Adjust time for parallel execution (assume ~50% speedup)
        if len(selected_tools) > 1:
            total_time *= 0.6

        return ToolPlan(
            research_task=research_task,
            selected_tools=selected_tools,
            execution_order=execution_order,
            estimated_total_cost=total_cost,
            estimated_total_time=total_time,
            budget_remaining=max_budget - total_cost,
            meets_requirements=total_cost <= max_budget and total_time <= max_time,
            optimization_notes=(
                f"Selected {len(selected_tools)} tools for parallel execution. "
                f"Estimated {total_time:.1f}s (parallelized) vs "
                f"{sum(self.tool_registry.get(t.tool_name, {}).get('typical_latency', 5.0) for t in selected_tools):.1f}s (sequential). "
                f"Cost-effective selection prioritizes high-reliability tools."
            )
        )

    def get_tool_metrics(self, tool_name: str) -> Optional[ToolPerformanceMetrics]:
        """Get current performance metrics for a specific tool."""
        return self.tool_metrics.get(tool_name)

    def reset_metrics(self, tool_name: Optional[str] = None) -> None:
        """
        Reset metrics for a specific tool or all tools.

        Args:
            tool_name: Name of tool to reset, or None to reset all
        """
        if tool_name:
            if tool_name in self.tool_metrics:
                del self.tool_metrics[tool_name]
                logger.info(f"Reset metrics for {tool_name}")
        else:
            self.tool_metrics.clear()
            logger.info("Reset all tool metrics")

        self._save_metrics()
