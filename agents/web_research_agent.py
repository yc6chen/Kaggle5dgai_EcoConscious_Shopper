"""
WebResearchAgent - Specialist agent for web research and data gathering.

This agent has access to multiple tools for searching, scraping, and gathering
sustainability information from various web sources.

ENHANCED with:
- Dynamic Tool Selection (cost-optimized tool selection)
- Parallel Tool Execution (concurrent execution with timeout management)
- Result Validation (cross-verification and anomaly detection)
"""

import logging
from typing import Dict, List, Any, Optional
import os

from google.adk.agents import Agent
from google.adk.models.google_llm import Gemini
from google.adk.tools import FunctionTool, google_search
from google.genai import types

from tools.web_scraper import scrape_company_sustainability
from tools.api_clients import search_sustainability_news, CertificationChecker

# Import enhanced tool capabilities
from tools.dynamic_tool_selector import DynamicToolSelector
from tools.parallel_executor import ParallelToolExecutor
from tools.result_validator import ToolResultValidator

from models.sustainability_models import (
    SustainabilityDoc,
    Certification,
    NewsArticle,
)

from models.tool_models import (
    EnhancedSearchResult,
    ToolCall,
)

logger = logging.getLogger(__name__)


class WebResearchAgent:
    """
    Specialized agent for web research tasks.

    Responsibilities:
    - Search web for sustainability reports and ESG data
    - Scrape company websites for environmental policies
    - Gather recent news about labor practices and certifications
    - Extract and clean raw data from multiple sources
    """

    def __init__(self):
        """Initialize the Web Research Agent with enhanced capabilities."""
        self.retry_config = types.HttpRetryOptions(
            attempts=5,
            exp_base=7,
            initial_delay=1,
            http_status_codes=[429, 500, 503, 504],
        )

        self.cert_checker = CertificationChecker()

        # Initialize enhanced tool capabilities
        self.tool_selector = DynamicToolSelector()
        self.parallel_executor = ParallelToolExecutor(max_workers=5, default_timeout=30)
        self.validator = ToolResultValidator(min_confidence_threshold=0.6)

        # Register tools with parallel executor
        self._register_tools_for_parallel_execution()

        logger.info("WebResearchAgent initialized with enhanced tool capabilities")

    def _register_tools_for_parallel_execution(self) -> None:
        """Register tool methods with the parallel executor."""
        self.parallel_executor.register_tool(
            "search_sustainability_reports",
            self.search_sustainability_reports
        )
        self.parallel_executor.register_tool(
            "scrape_company_esg_page",
            self.scrape_company_esg_page
        )
        self.parallel_executor.register_tool(
            "get_company_certifications",
            self.get_company_certifications
        )
        self.parallel_executor.register_tool(
            "search_labor_practices_news",
            self.search_labor_practices_news
        )

        logger.debug("Registered 4 tools with parallel executor")

    async def enhanced_sustainability_search(
        self,
        company: str,
        budget: float = 10.0,
        time_limit: int = 60
    ) -> EnhancedSearchResult:
        """
        Enhanced sustainability search using dynamic tool selection,
        parallel execution, and result validation.

        This is the main enhanced method that demonstrates all three
        advanced tool capabilities working together.

        Args:
            company: Company name to research
            budget: Budget constraint in dollars (default: 10.0)
            time_limit: Time limit in seconds (default: 60)

        Returns:
            EnhancedSearchResult with validated, cross-verified data
        """
        logger.info(
            f"Starting enhanced sustainability search for {company} "
            f"(budget=${budget}, time_limit={time_limit}s)"
        )

        # Step 1: Use DynamicToolSelector to choose optimal search strategies
        task_description = f"sustainability_research_{company}"
        context = {
            "budget": budget,
            "time_limit": time_limit,
            "required_confidence": 0.7
        }

        selected_tool_calls = await self.tool_selector.select_optimal_tools(
            task_description,
            context
        )

        # Add company parameter to all tool calls
        for tool_call in selected_tool_calls:
            tool_call.parameters["company"] = company

        logger.info(
            f"Selected {len(selected_tool_calls)} tools: "
            f"{[t.tool_name for t in selected_tool_calls]}"
        )

        # Step 2: Execute tools in parallel
        execution_result = await self.parallel_executor.execute_tools_parallel(
            selected_tool_calls
        )

        logger.info(
            f"Parallel execution complete: "
            f"{len(execution_result.successful_tools)} succeeded, "
            f"{len(execution_result.failed_tools)} failed"
        )

        # Step 3: Validate and cross-verify results
        tool_results = list(execution_result.successful_tools.values())

        if not tool_results:
            logger.warning("No successful tool results to validate")
            validation = None
            overall_confidence = 0.0
        else:
            # Validate results
            validation_report = await self.validator.validate_and_enhance_results(
                tool_results,
                expected_fields=["company", "sustainability_score", "certifications"]
            )

            # Get detailed validation for the first result
            if tool_results:
                first_result_data = tool_results[0].result or {}
                validation = await self.validator.validate_web_scraping_results(
                    first_result_data,
                    f"multiple_sources_{company}"
                )
            else:
                validation = None

            overall_confidence = validation_report.get("validation_score", 0.5)

            logger.info(
                f"Validation complete: confidence={overall_confidence:.2f}, "
                f"anomalies={len(validation_report.get('anomalies', []))}"
            )

        # Aggregate data from all successful tools
        aggregated_data = self._aggregate_tool_results(execution_result.successful_tools)

        # Update tool metrics for future optimization
        for tool_result in tool_results:
            await self.tool_selector.update_tool_metrics(
                tool_result.tool_name,
                tool_result.success,
                tool_result.cost,
                tool_result.execution_time
            )

        # Create enhanced search result
        result = EnhancedSearchResult(
            data=aggregated_data,
            validation=validation if validation else self._create_default_validation(),
            sources=[t.tool_name for t in selected_tool_calls],
            tool_execution_summary=execution_result,
            overall_confidence=overall_confidence
        )

        logger.info(
            f"Enhanced search complete for {company}: "
            f"confidence={overall_confidence:.2%}"
        )

        return result

    def _aggregate_tool_results(self, successful_tools: Dict[str, Any]) -> Dict[str, Any]:
        """Aggregate data from multiple successful tool executions."""
        aggregated = {
            "sustainability_reports": [],
            "esg_data": {},
            "certifications": [],
            "news_articles": [],
            "sources": []
        }

        for tool_name, tool_result in successful_tools.items():
            if not tool_result.result:
                continue

            result_data = tool_result.result

            # Aggregate based on tool type
            if "search_sustainability_reports" in tool_name:
                if isinstance(result_data, list):
                    aggregated["sustainability_reports"].extend(result_data)
                elif isinstance(result_data, dict) and "data" in result_data:
                    data = result_data["data"]
                    if isinstance(data, list):
                        aggregated["sustainability_reports"].extend(data)

            elif "scrape_company_esg_page" in tool_name:
                if isinstance(result_data, dict):
                    aggregated["esg_data"].update(result_data)

            elif "certifications" in tool_name:
                if isinstance(result_data, list):
                    aggregated["certifications"].extend(result_data)
                elif isinstance(result_data, dict) and "data" in result_data:
                    data = result_data["data"]
                    if isinstance(data, list):
                        aggregated["certifications"].extend(data)

            elif "news" in tool_name:
                if isinstance(result_data, list):
                    aggregated["news_articles"].extend(result_data)
                elif isinstance(result_data, dict) and "data" in result_data:
                    data = result_data["data"]
                    if isinstance(data, list):
                        aggregated["news_articles"].extend(data)

            aggregated["sources"].append(tool_name)

        return aggregated

    def _create_default_validation(self) -> Any:
        """Create a default validation result when no validation could be performed."""
        from models.tool_models import ValidationResult

        return ValidationResult(
            is_valid=False,
            confidence_score=0.0,
            validation_method="none",
            cross_reference_sources=[],
            anomalies_detected=["No data to validate"]
        )

    async def search_sustainability_reports(
        self,
        company: str
    ) -> List[Dict]:
        """
        Search for sustainability reports and ESG documents for a company.

        This tool searches the web for published sustainability reports,
        ESG disclosures, and related documents.

        Args:
            company: Company name to research

        Returns:
            List of sustainability documents found
        """
        logger.info(f"Searching sustainability reports for {company}")

        try:
            # Construct search query for sustainability reports
            search_query = f"{company} sustainability report ESG disclosure"

            # Note: In production, this would use google_search tool
            # For now, return structure to demonstrate pattern
            results = [
                {
                    "title": f"{company} Annual Sustainability Report",
                    "url": f"https://example.com/{company}/sustainability",
                    "summary": "Annual report on environmental and social impact",
                    "source": company,
                }
            ]

            return results

        except Exception as e:
            logger.error(f"Error searching sustainability reports: {e}")
            return []

    async def scrape_company_esg_page(self, company: str) -> Dict:
        """
        Scrape company website for ESG and sustainability information.

        This tool visits the company's website and extracts environmental,
        social, and governance data from their sustainability pages.

        Args:
            company: Company name

        Returns:
            Dictionary with ESG data extracted from website
        """
        logger.info(f"Scraping ESG page for {company}")

        try:
            # Use the web scraper tool
            esg_data = await scrape_company_sustainability(company)
            return esg_data

        except Exception as e:
            logger.error(f"Error scraping ESG data: {e}")
            return {
                "company": company,
                "error": str(e),
                "environmental_score": None,
                "social_score": None,
            }

    async def get_company_certifications(
        self,
        company: str,
        description: str = ""
    ) -> List[Dict]:
        """
        Identify sustainability certifications for a company.

        This tool searches for and verifies sustainability certifications
        such as B Corp, Fair Trade, LEED, etc.

        Args:
            company: Company name
            description: Optional company description or text to analyze

        Returns:
            List of certifications found
        """
        logger.info(f"Checking certifications for {company}")

        try:
            # Use certification checker
            certifications = await self.cert_checker.check_certifications(
                company,
                description
            )

            return [
                {
                    "name": cert.name,
                    "organization": cert.issuing_organization,
                    "description": cert.description,
                    "verified": cert.verified
                }
                for cert in certifications
            ]

        except Exception as e:
            logger.error(f"Error checking certifications: {e}")
            return []

    async def search_labor_practices_news(
        self,
        company: str
    ) -> List[Dict]:
        """
        Search for news articles about company's labor practices.

        This tool searches for recent news coverage of labor practices,
        worker treatment, supply chain issues, and related topics.

        Args:
            company: Company name

        Returns:
            List of relevant news articles
        """
        logger.info(f"Searching labor practices news for {company}")

        try:
            # Search for labor-related news
            news_results = await search_sustainability_news(company, max_results=5)

            return news_results

        except Exception as e:
            logger.error(f"Error searching labor news: {e}")
            return []

    def create_agent(self) -> Agent:
        """
        Create the WebResearchAgent with all required tools.

        Returns:
            Configured WebResearchAgent
        """
        # Create function tools for each capability
        # Note: name and description come from function name and docstring
        search_reports_tool = FunctionTool(self.search_sustainability_reports)
        scrape_esg_tool = FunctionTool(self.scrape_company_esg_page)
        certifications_tool = FunctionTool(self.get_company_certifications)
        labor_news_tool = FunctionTool(self.search_labor_practices_news)

        # Create the agent with all tools
        agent = Agent(
            name="WebResearchAgent",
            model=Gemini(
                model="gemini-2.5-flash",
                retry_options=self.retry_config
            ),
            description="""
            Specialized research agent that gathers sustainability information from
            the web using search, scraping, and API tools.
            """,
            instruction="""
            You are a specialized WebResearchAgent focused on gathering sustainability
            information about companies and brands.

            You have access to these tools:
            1. search_sustainability_reports - Find published ESG reports and disclosures
            2. scrape_company_esg_page - Extract data from company sustainability pages
            3. get_company_certifications - Identify sustainability certifications
            4. search_labor_practices_news - Find news about labor and ethics

            When researching a company:

            1. START with sustainability reports:
               - Use search_sustainability_reports to find official documents
               - Look for annual reports, ESG disclosures, impact statements

            2. VERIFY with direct scraping:
               - Use scrape_company_esg_page to get data from their website
               - Compare website claims with published reports

            3. CHECK certifications:
               - Use get_company_certifications to identify verified certifications
               - Note which certifications are claimed vs verified

            4. RESEARCH recent news:
               - Use search_labor_practices_news to find recent coverage
               - Identify any controversies or positive initiatives

            Always return structured data following the Pydantic models.
            Be thorough but concise in your findings.
            If a tool fails, try alternative approaches.
            """,
            tools=[
                search_reports_tool,
                scrape_esg_tool,
                certifications_tool,
                labor_news_tool,
                google_search,  # Built-in Google Search tool
            ],
            output_key="web_research_findings"
        )

        return agent


# Convenience function to create the agent
def create_web_research_agent() -> Agent:
    """
    Create and return a configured WebResearchAgent.

    Returns:
        WebResearchAgent instance
    """
    web_agent = WebResearchAgent()
    return web_agent.create_agent()
