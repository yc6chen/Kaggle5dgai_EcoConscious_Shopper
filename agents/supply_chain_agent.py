"""
SupplyChainAgent - Data analyst agent for supply chain transparency assessment.

This agent integrates with OpenSupplyHub API and implements memory for caching
brand analyses.
"""

import logging
from typing import Dict, Optional
import os
import json
from pathlib import Path

from google.adk.agents import Agent
from google.adk.models.google_llm import Gemini
from google.adk.tools import FunctionTool
from google.genai import types

from tools.api_clients import OpenSupplyHubClient, get_supply_chain_data
from models.sustainability_models import SupplyChainAnalysis, TransparencyScore

logger = logging.getLogger(__name__)


class SupplyChainAgent:
    """
    Specialized agent for supply chain transparency analysis.

    Responsibilities:
    - Analyze supply chain transparency using OpenSupplyHub API
    - Calculate supply chain complexity metrics
    - Assess geographic risk factors
    - Provide transparency scoring
    - Implement memory/caching for brand data
    """

    def __init__(self, cache_dir: str = "./cache"):
        """
        Initialize the Supply Chain Agent.

        Args:
            cache_dir: Directory for storing cached analyses
        """
        self.retry_config = types.HttpRetryOptions(
            attempts=5,
            exp_base=7,
            initial_delay=1,
            http_status_codes=[429, 500, 503, 504],
        )

        # Memory/cache setup
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # In-memory cache
        self.memory_cache: Dict[str, SupplyChainAnalysis] = {}

    async def analyze_supply_chain(self, brand: str) -> Dict:
        """
        Analyze supply chain transparency for a brand.

        This tool integrates with OpenSupplyHub to gather supply chain data
        and calculate transparency metrics.

        Args:
            brand: Brand name to analyze

        Returns:
            Dictionary with supply chain analysis results
        """
        logger.info(f"Analyzing supply chain for {brand}")

        try:
            # Check cache first
            cached = await self.get_cached_analysis(brand)
            if cached:
                logger.info(f"Using cached analysis for {brand}")
                return {
                    "brand": cached.brand,
                    "transparency_score": cached.transparency_score,
                    "num_suppliers": cached.num_suppliers,
                    "regions": cached.geographic_regions,
                    "risk_factors": cached.risk_factors,
                    "cached": True
                }

            # Get fresh data from OpenSupplyHub
            supply_data = await get_supply_chain_data(brand)

            # Create analysis object
            analysis = SupplyChainAnalysis(
                brand=brand,
                transparency_score=supply_data["transparency_score"],
                num_suppliers=supply_data["num_suppliers"],
                geographic_regions=supply_data["regions"],
                risk_factors=supply_data["risk_factors"],
                data_sources=["OpenSupplyHub"]
            )

            # Cache the analysis
            await self.cache_brand_analysis(brand, analysis)

            return {
                "brand": brand,
                "transparency_score": analysis.transparency_score,
                "num_suppliers": analysis.num_suppliers,
                "regions": analysis.geographic_regions,
                "risk_factors": analysis.risk_factors,
                "cached": False
            }

        except Exception as e:
            logger.error(f"Error analyzing supply chain: {e}")
            return {
                "brand": brand,
                "transparency_score": 0.0,
                "error": str(e),
                "num_suppliers": 0,
                "regions": [],
                "risk_factors": ["Analysis failed"],
            }

    async def calculate_transparency_score(
        self,
        raw_data: Dict
    ) -> TransparencyScore:
        """
        Calculate detailed transparency score breakdown.

        Args:
            raw_data: Raw supply chain data

        Returns:
            TransparencyScore with detailed breakdown
        """
        logger.info("Calculating transparency score")

        # Extract metrics
        num_suppliers = raw_data.get("num_suppliers", 0)
        has_disclosure = num_suppliers > 0

        # Calculate component scores
        supplier_disclosure = 100.0 if has_disclosure else 0.0
        traceability = min(100.0, (num_suppliers / 50) * 100)  # Scale to 100
        audit_availability = 50.0 if has_disclosure else 0.0  # Simplified

        # Overall score is weighted average
        overall = (
            supplier_disclosure * 0.4 +
            traceability * 0.4 +
            audit_availability * 0.2
        )

        return TransparencyScore(
            overall_score=round(overall, 1),
            supplier_disclosure=round(supplier_disclosure, 1),
            traceability=round(traceability, 1),
            audit_availability=round(audit_availability, 1),
            details=f"Based on {num_suppliers} disclosed suppliers"
        )

    async def cache_brand_analysis(
        self,
        brand: str,
        analysis: SupplyChainAnalysis
    ) -> bool:
        """
        Cache brand analysis to both memory and disk.

        Args:
            brand: Brand name
            analysis: SupplyChainAnalysis to cache

        Returns:
            True if successful
        """
        try:
            # Store in memory
            self.memory_cache[brand.lower()] = analysis

            # Store on disk
            cache_file = self.cache_dir / f"{brand.lower()}_supply_chain.json"

            cache_data = {
                "brand": analysis.brand,
                "transparency_score": analysis.transparency_score,
                "num_suppliers": analysis.num_suppliers,
                "geographic_regions": analysis.geographic_regions,
                "risk_factors": analysis.risk_factors,
                "data_sources": analysis.data_sources,
            }

            with open(cache_file, "w") as f:
                json.dump(cache_data, f, indent=2)

            logger.info(f"Cached analysis for {brand}")
            return True

        except Exception as e:
            logger.error(f"Failed to cache analysis: {e}")
            return False

    async def get_cached_analysis(
        self,
        brand: str
    ) -> Optional[SupplyChainAnalysis]:
        """
        Retrieve cached analysis for a brand.

        Checks memory first, then disk cache.

        Args:
            brand: Brand name

        Returns:
            SupplyChainAnalysis if cached, None otherwise
        """
        brand_key = brand.lower()

        # Check memory cache
        if brand_key in self.memory_cache:
            logger.info(f"Found {brand} in memory cache")
            return self.memory_cache[brand_key]

        # Check disk cache
        cache_file = self.cache_dir / f"{brand_key}_supply_chain.json"

        if cache_file.exists():
            try:
                with open(cache_file, "r") as f:
                    data = json.load(f)

                analysis = SupplyChainAnalysis(
                    brand=data["brand"],
                    transparency_score=data["transparency_score"],
                    num_suppliers=data.get("num_suppliers"),
                    geographic_regions=data.get("geographic_regions", []),
                    risk_factors=data.get("risk_factors", []),
                    data_sources=data.get("data_sources", [])
                )

                # Load into memory cache
                self.memory_cache[brand_key] = analysis

                logger.info(f"Loaded {brand} from disk cache")
                return analysis

            except Exception as e:
                logger.error(f"Error loading cache file: {e}")

        return None

    def create_agent(self) -> Agent:
        """
        Create the SupplyChainAgent with memory capabilities.

        Returns:
            Configured SupplyChainAgent
        """
        # Create function tools
        analyze_tool = FunctionTool(
            self.analyze_supply_chain,
            name="analyze_supply_chain",
            description="""
            Analyze supply chain transparency for a brand using OpenSupplyHub data.
            Returns transparency score, number of suppliers, geographic regions,
            and risk factors. Results are cached for faster future lookups.
            """
        )

        transparency_score_tool = FunctionTool(
            self.calculate_transparency_score,
            name="calculate_transparency_score",
            description="""
            Calculate detailed transparency score breakdown from raw supply chain data.
            Provides scores for supplier disclosure, traceability, and audit availability.
            """
        )

        # Create the agent
        agent = Agent(
            name="SupplyChainAgent",
            model=Gemini(
                model="gemini-2.5-flash",
                retry_options=self.retry_config
            ),
            description="""
            Specialized agent for analyzing supply chain transparency and complexity.
            Uses OpenSupplyHub data and implements caching for efficiency.
            """,
            instruction="""
            You are a SupplyChainAgent specialized in analyzing supply chain transparency.

            Your tools:
            1. analyze_supply_chain - Get comprehensive supply chain data for a brand
            2. calculate_transparency_score - Calculate detailed transparency metrics

            When analyzing a brand's supply chain:

            1. ANALYZE supply chain:
               - Use analyze_supply_chain tool to get data from OpenSupplyHub
               - Check if data is cached (faster) or needs fresh API call
               - Identify number of disclosed suppliers

            2. ASSESS transparency:
               - Evaluate supplier disclosure levels
               - Analyze geographic distribution
               - Identify complexity and risk factors

            3. CALCULATE scores:
               - Use calculate_transparency_score for detailed breakdown
               - Consider supplier disclosure, traceability, and audits
               - Provide clear explanations for scores

            4. IDENTIFY risks:
               - Flag complex multi-country supply chains
               - Note regions with known labor or environmental issues
               - Highlight lack of transparency where applicable

            Your analysis should be data-driven and objective.
            Always cite OpenSupplyHub as your data source.
            Explain both strengths and weaknesses in transparency.
            """,
            tools=[
                analyze_tool,
                transparency_score_tool,
            ],
            output_key="supply_chain_analysis"
        )

        return agent


# Convenience function to create the agent
def create_supply_chain_agent(cache_dir: str = "./cache") -> Agent:
    """
    Create and return a configured SupplyChainAgent.

    Args:
        cache_dir: Directory for caching analyses

    Returns:
        SupplyChainAgent instance
    """
    supply_agent = SupplyChainAgent(cache_dir=cache_dir)
    return supply_agent.create_agent()
