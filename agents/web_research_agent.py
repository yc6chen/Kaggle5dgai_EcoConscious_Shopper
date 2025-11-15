"""
WebResearchAgent - Specialist agent for web research and data gathering.

This agent has access to multiple tools for searching, scraping, and gathering
sustainability information from various web sources.
"""

import logging
from typing import Dict, List, Any
import os

from google.adk.agents import Agent
from google.adk.models.google_llm import Gemini
from google.adk.tools import FunctionTool, google_search
from google.genai import types

from tools.web_scraper import scrape_company_sustainability
from tools.api_clients import search_sustainability_news, CertificationChecker

from models.sustainability_models import (
    SustainabilityDoc,
    Certification,
    NewsArticle,
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
        """Initialize the Web Research Agent."""
        self.retry_config = types.HttpRetryOptions(
            attempts=5,
            exp_base=7,
            initial_delay=1,
            http_status_codes=[429, 500, 503, 504],
        )

        self.cert_checker = CertificationChecker()

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
        search_reports_tool = FunctionTool(
            self.search_sustainability_reports,
            name="search_sustainability_reports",
            description="""
            Search for sustainability reports and ESG documents for a company.
            Finds published reports, disclosures, and environmental impact statements.
            """
        )

        scrape_esg_tool = FunctionTool(
            self.scrape_company_esg_page,
            name="scrape_company_esg_page",
            description="""
            Visit company website and extract ESG (Environmental, Social, Governance)
            data from their sustainability pages. Returns environmental and social scores.
            """
        )

        certifications_tool = FunctionTool(
            self.get_company_certifications,
            name="get_company_certifications",
            description="""
            Identify and verify sustainability certifications for a company.
            Checks for B Corp, Fair Trade, LEED, FSC, and other certifications.
            """
        )

        labor_news_tool = FunctionTool(
            self.search_labor_practices_news,
            name="search_labor_practices_news",
            description="""
            Search for recent news articles about company's labor practices,
            worker treatment, and supply chain ethics.
            """
        )

        # Create the agent with all tools
        agent = Agent(
            name="WebResearchAgent",
            model=Gemini(
                model="gemini-2.5-flash-lite",
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
