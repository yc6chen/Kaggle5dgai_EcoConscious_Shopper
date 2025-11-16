"""
ResearchCoordinator Agent - Orchestrates the multi-agent sustainability research workflow.

This agent creates research plans, coordinates specialized agents, maintains session state,
and validates/aggregates results.
"""

import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from urllib.parse import urlparse
import os

from google.adk.agents import Agent
from google.adk.models.google_llm import Gemini
from google.adk.tools import AgentTool
from google.genai import types

from models.sustainability_models import (
    ResearchPlan,
    ResearchTask,
    ResearchSummary,
)

logger = logging.getLogger(__name__)


class ResearchCoordinator:
    """
    Primary orchestrator agent that coordinates sustainability research workflow.

    Responsibilities:
    - Parse product URLs and extract brand information
    - Create and execute research plans
    - Coordinate between specialized agents
    - Maintain session state and research progress
    - Validate and aggregate final results
    """

    def __init__(self):
        """Initialize the Research Coordinator agent."""
        self.retry_config = types.HttpRetryOptions(
            attempts=5,
            exp_base=7,
            initial_delay=1,
            http_status_codes=[429, 500, 503, 504],
        )

        # Session state to track research progress
        self.current_plan: Optional[ResearchPlan] = None
        self.research_cache: Dict[str, ResearchSummary] = {}

    async def create_research_plan(
        self,
        brand: str,
        product_url: str
    ) -> ResearchPlan:
        """
        Create a research plan for analyzing a brand's sustainability.

        Args:
            brand: Brand name to research
            product_url: URL of the product being analyzed

        Returns:
            ResearchPlan with tasks prioritized and assigned
        """
        logger.info(f"Creating research plan for brand: {brand}")

        # Define research tasks
        tasks = [
            ResearchTask(
                task_type="sustainability_reports",
                priority=1,
                status="pending",
                assigned_agent="WebResearchAgent"
            ),
            ResearchTask(
                task_type="labor_practices",
                priority=2,
                status="pending",
                assigned_agent="WebResearchAgent"
            ),
            ResearchTask(
                task_type="supply_chain",
                priority=1,
                status="pending",
                assigned_agent="SupplyChainAgent"
            ),
            ResearchTask(
                task_type="certifications",
                priority=3,
                status="pending",
                assigned_agent="WebResearchAgent"
            ),
        ]

        plan = ResearchPlan(
            brand=brand,
            product_url=product_url,
            tasks=tasks,
            current_state="pending",
            created_at=datetime.now(),
            updated_at=datetime.now()
        )

        self.current_plan = plan
        return plan

    async def execute_plan(self, plan: ResearchPlan) -> Dict[str, Any]:
        """
        Execute the research plan by coordinating specialized agents.

        Args:
            plan: Research plan to execute

        Returns:
            Dictionary containing aggregated research results
        """
        logger.info(f"Executing research plan for {plan.brand}")

        plan.current_state = "researching"
        plan.updated_at = datetime.now()

        results = {
            "sustainability_data": {},
            "labor_data": {},
            "supply_chain_data": {},
            "certifications": []
        }

        # Execute tasks by priority
        sorted_tasks = sorted(plan.tasks, key=lambda t: t.priority)

        for task in sorted_tasks:
            try:
                task.status = "in_progress"
                logger.info(
                    f"Executing task: {task.task_type} (agent: {task.assigned_agent})"
                )

                # Task execution would be delegated to appropriate agent
                # For now, we'll simulate the structure

                task_result = await self._execute_task(task, plan.brand)
                task.result = task_result
                task.status = "complete"

                # Store results by task type
                results[f"{task.task_type}_data"] = task_result

            except Exception as e:
                logger.error(f"Task {task.task_type} failed: {e}")
                task.status = "failed"
                task.result = {"error": str(e)}

        plan.current_state = "analyzing"
        plan.updated_at = datetime.now()

        return results

    async def _execute_task(
        self,
        task: ResearchTask,
        brand: str
    ) -> Dict[str, Any]:
        """
        Execute a specific research task.

        Args:
            task: Research task to execute
            brand: Brand being researched

        Returns:
            Task results
        """
        # This would delegate to the appropriate specialized agent
        # For now, return placeholder structure
        return {
            "task_type": task.task_type,
            "brand": brand,
            "data": {},
            "timestamp": datetime.now().isoformat()
        }

    async def validate_results(self, raw_data: Dict) -> bool:
        """
        Validate research results to ensure quality and completeness.

        Args:
            raw_data: Raw research data from agents

        Returns:
            True if results are valid, False otherwise
        """
        logger.info("Validating research results")

        # Check that we have minimum required data
        required_fields = ["sustainability_data", "supply_chain_data"]

        for field in required_fields:
            if field not in raw_data or not raw_data[field]:
                logger.warning(f"Missing required field: {field}")
                return False

        return True

    async def aggregate_findings(
        self,
        agent_outputs: List[Dict]
    ) -> ResearchSummary:
        """
        Aggregate findings from all specialized agents.

        Args:
            agent_outputs: List of outputs from specialized agents

        Returns:
            ResearchSummary with consolidated findings
        """
        logger.info("Aggregating research findings")

        if not self.current_plan:
            raise ValueError("No active research plan")

        # Aggregate data from different agents
        summary = ResearchSummary(
            brand=self.current_plan.brand,
            sustainability_reports=[],
            certifications=[],
            news_articles=[],
            supply_chain_data=None,
            esg_data=None
        )

        # Process each agent output
        for output in agent_outputs:
            # This would parse and aggregate actual agent outputs
            pass

        # Update plan status
        if self.current_plan:
            self.current_plan.current_state = "complete"
            self.current_plan.updated_at = datetime.now()

        return summary

    def create_agent(
        self,
        web_research_agent: Agent,
        supply_chain_agent: Agent,
        sustainability_scorer: Agent
    ) -> Agent:
        """
        Create the coordinator agent with access to specialized agents.

        Args:
            web_research_agent: Agent for web research
            supply_chain_agent: Agent for supply chain analysis
            sustainability_scorer: Agent for final scoring

        Returns:
            Configured ResearchCoordinator Agent
        """
        coordinator = Agent(
            name="ResearchCoordinator",
            model=Gemini(
                model="gemini-2.5-flash",
                retry_options=self.retry_config
            ),
            description="""
            Primary coordinator that orchestrates sustainability research for products
            and brands. Creates research plans and coordinates specialized agents.
            """,
            instruction="""
            You are the ResearchCoordinator for an eco-conscious shopping platform.
            Your goal is to coordinate research about a brand's sustainability practices.

            When given a product URL and brand name, you should:

            1. CREATE A RESEARCH PLAN:
               - Identify what information is needed
               - Prioritize research tasks
               - Assign tasks to appropriate specialist agents

            2. COORDINATE SPECIALIST AGENTS:
               - Call the WebResearchAgent to gather sustainability reports and news
               - Call the SupplyChainAgent to analyze supply chain transparency
               - Collect and organize all findings

            3. VALIDATE RESULTS:
               - Ensure all required data has been collected
               - Check data quality and completeness
               - Request additional research if needed

            4. PREPARE FOR SCORING:
               - Aggregate all findings into a structured summary
               - Pass complete data to SustainabilityScorer for final rating

            Be systematic, thorough, and ensure all research is well-documented.
            """,
            tools=[
                AgentTool(web_research_agent),
                AgentTool(supply_chain_agent),
                AgentTool(sustainability_scorer),
            ],
            output_key="research_results"
        )

        return coordinator

    async def get_cached_analysis(
        self,
        brand: str
    ) -> Optional[ResearchSummary]:
        """
        Retrieve cached research summary for a brand.

        Args:
            brand: Brand name

        Returns:
            ResearchSummary if cached, None otherwise
        """
        return self.research_cache.get(brand)

    async def cache_brand_analysis(
        self,
        brand: str,
        summary: ResearchSummary
    ) -> bool:
        """
        Cache research summary for future use.

        Args:
            brand: Brand name
            summary: Research summary to cache

        Returns:
            True if successful
        """
        try:
            self.research_cache[brand] = summary
            logger.info(f"Cached research summary for {brand}")
            return True
        except Exception as e:
            logger.error(f"Failed to cache summary: {e}")
            return False


def extract_brand_from_url(product_url: str) -> str:
    """
    Extract brand name from product URL.

    Args:
        product_url: Product URL

    Returns:
        Estimated brand name
    """
    parsed = urlparse(product_url)
    domain = parsed.netloc

    # Remove common prefixes
    domain = domain.replace("www.", "").replace("shop.", "")

    # Extract main domain name
    parts = domain.split(".")
    if parts:
        brand = parts[0].capitalize()
        return brand

    return "Unknown"
