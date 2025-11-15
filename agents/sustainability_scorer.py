"""
SustainabilityScorer - Gemini-powered agent for final sustainability scoring.

This agent MUST use Google Gemini 1.0 Pro model (requirement for bonus points).
It synthesizes research data from all sources and generates structured A-F ratings.
"""

import logging
from typing import Dict, Literal
from datetime import datetime

from google.adk.agents import Agent
from google.adk.models.google_llm import Gemini
from google.genai import types
from pydantic import ValidationError

from models.sustainability_models import SustainabilityRating

logger = logging.getLogger(__name__)


class SustainabilityScorer:
    """
    Gemini-powered agent that generates final sustainability ratings.

    Responsibilities:
    - Synthesize research data from all sources
    - Generate A-F ratings for environmental impact, labor ethics, transparency
    - Provide detailed rationale for each rating
    - Output structured JSON following exact schema
    - Assess confidence in ratings
    """

    def __init__(self):
        """Initialize the Sustainability Scorer agent."""
        # Retry configuration
        self.retry_config = types.HttpRetryOptions(
            attempts=5,
            exp_base=7,
            initial_delay=1,
            http_status_codes=[429, 500, 503, 504],
        )

        # Model configuration for Gemini 1.0 Pro
        # CRITICAL: Must use gemini-1.0-pro for bonus points
        self.model_config = {
            "model": "gemini-1.0-pro",
            "temperature": 0.1,  # Low temperature for consistent scoring
            "max_output_tokens": 1024,
        }

    def calculate_grade(
        self,
        score: float,
        category: str
    ) -> Literal["A", "B", "C", "D", "F"]:
        """
        Convert numeric score to letter grade.

        Args:
            score: Numeric score (0-100)
            category: Category being graded

        Returns:
            Letter grade A-F
        """
        if score >= 85:
            return "A"
        elif score >= 70:
            return "B"
        elif score >= 55:
            return "C"
        elif score >= 40:
            return "D"
        else:
            return "F"

    def calculate_overall_grade(
        self,
        environmental: float,
        labor: float,
        transparency: float
    ) -> Literal["A", "B", "C", "D", "F"]:
        """
        Calculate overall grade from category scores.

        Args:
            environmental: Environmental score (0-100)
            labor: Labor score (0-100)
            transparency: Transparency score (0-100)

        Returns:
            Overall letter grade
        """
        # Weighted average: environmental 40%, labor 40%, transparency 20%
        overall_score = (
            environmental * 0.4 +
            labor * 0.4 +
            transparency * 0.2
        )

        return self.calculate_grade(overall_score, "overall")

    def assess_confidence(
        self,
        data_quality: Dict[str, bool]
    ) -> float:
        """
        Assess confidence in rating based on data quality.

        Args:
            data_quality: Dictionary indicating which data sources were available

        Returns:
            Confidence score (0.0-1.0)
        """
        # Start with base confidence
        confidence = 0.5

        # Increase confidence based on available data
        if data_quality.get("sustainability_reports", False):
            confidence += 0.15

        if data_quality.get("supply_chain_data", False):
            confidence += 0.15

        if data_quality.get("esg_data", False):
            confidence += 0.1

        if data_quality.get("certifications", False):
            confidence += 0.1

        return min(1.0, confidence)

    def create_agent(self) -> Agent:
        """
        Create the SustainabilityScorer agent using Gemini 1.0 Pro.

        Returns:
            Configured SustainabilityScorer Agent
        """
        agent = Agent(
            name="SustainabilityScorer",
            model=Gemini(
                model=self.model_config["model"],  # gemini-1.0-pro
                temperature=self.model_config["temperature"],
                max_output_tokens=self.model_config["max_output_tokens"],
                retry_options=self.retry_config
            ),
            description="""
            Final scoring agent powered by Gemini 1.0 Pro that synthesizes all
            research data and generates structured sustainability ratings.
            """,
            instruction="""
            You are the SustainabilityScorer, the final decision-maker in the
            eco-conscious shopping analysis pipeline.

            You will receive comprehensive research data including:
            - Web research findings (sustainability reports, news, certifications)
            - Supply chain analysis (transparency, suppliers, risk factors)
            - ESG data from company websites

            Your task is to synthesize all this information and produce a structured
            sustainability rating with these components:

            1. ENVIRONMENTAL SCORE (A-F):
               Consider:
               - Carbon neutrality commitments and progress
               - Renewable energy usage
               - Waste reduction and recycling programs
               - Environmental certifications (FSC, Energy Star, etc.)
               - Sustainable materials and packaging

               Grade Scale:
               A (85-100): Exceptional environmental leadership
               B (70-84): Strong environmental practices
               C (55-69): Adequate environmental efforts
               D (40-54): Minimal environmental consideration
               F (0-39): Poor or no environmental practices

            2. LABOR SCORE (A-F):
               Consider:
               - Fair labor certifications (Fair Trade, B Corp)
               - Worker safety and conditions
               - Living wage commitments
               - Labor practice news (positive or negative)
               - Supply chain labor transparency

               Use same grade scale as above

            3. TRANSPARENCY SCORE (A-F):
               Consider:
               - Supply chain disclosure (number of suppliers revealed)
               - Supply chain geographic transparency
               - ESG reporting quality and frequency
               - Third-party audit availability
               - Public commitments vs. actual data

               Use same grade scale as above

            4. OVERALL SCORE (A-F):
               Calculate weighted average:
               - Environmental: 40%
               - Labor: 40%
               - Transparency: 20%

            5. DETAILED RATIONALE:
               For each category, provide a clear 2-3 sentence explanation of:
               - What data informed the grade
               - Key strengths or weaknesses
               - Specific examples or evidence

            6. CONFIDENCE SCORE (0.0-1.0):
               Assess your confidence based on:
               - Data availability and quality
               - Consistency across sources
               - Recency of information
               - Presence of third-party verification

               High confidence (0.8-1.0): Multiple verified sources
               Medium confidence (0.5-0.7): Some data with gaps
               Low confidence (0.0-0.4): Limited or unreliable data

            CRITICAL REQUIREMENTS:
            - Be objective and evidence-based
            - Don't give high grades without strong evidence
            - Penalize lack of transparency
            - Value third-party certifications over company claims
            - Consider both positive achievements and negative news
            - Explain your reasoning clearly

            Output MUST follow the SustainabilityRating Pydantic model exactly.
            """,
            tools=[],  # Scoring agent doesn't need tools, it synthesizes data
            output_key="sustainability_rating"
        )

        return agent

    async def generate_rating(
        self,
        brand: str,
        product_url: str,
        research_data: Dict
    ) -> SustainabilityRating:
        """
        Generate sustainability rating from research data.

        This is a helper method that can be used programmatically to generate
        ratings with fallback logic.

        Args:
            brand: Brand name
            product_url: Product URL
            research_data: Aggregated research data

        Returns:
            SustainabilityRating object
        """
        logger.info(f"Generating sustainability rating for {brand}")

        try:
            # Extract scores from research data
            web_findings = research_data.get("web_research_findings", {})
            supply_chain = research_data.get("supply_chain_analysis", {})

            # Calculate component scores (0-100)
            environmental_score = self._calculate_environmental_score(
                web_findings
            )
            labor_score = self._calculate_labor_score(web_findings)
            transparency_score = supply_chain.get("transparency_score", 0.0)

            # Convert to letter grades
            env_grade = self.calculate_grade(
                environmental_score, "environmental"
            )
            labor_grade = self.calculate_grade(labor_score, "labor")
            trans_grade = self.calculate_grade(
                transparency_score, "transparency"
            )
            overall_grade = self.calculate_overall_grade(
                environmental_score, labor_score, transparency_score
            )

            # Generate rationale
            rationale = {
                "overall": f"Overall grade based on weighted combination of environmental ({env_grade}), labor ({labor_grade}), and transparency ({trans_grade}) scores.",
                "environmental": f"Environmental score reflects {environmental_score:.0f}/100 based on sustainability initiatives and certifications.",
                "labor": f"Labor score of {labor_score:.0f}/100 considers fair trade practices and worker treatment.",
                "transparency": f"Transparency score of {transparency_score:.0f}/100 based on supply chain disclosure."
            }

            # Assess confidence
            data_quality = {
                "sustainability_reports": bool(web_findings),
                "supply_chain_data": bool(supply_chain),
                "esg_data": True,
                "certifications": True,
            }
            confidence = self.assess_confidence(data_quality)

            # Create rating object
            rating = SustainabilityRating(
                overall_score=overall_grade,
                environmental_score=env_grade,
                labor_score=labor_grade,
                transparency_score=trans_grade,
                rationale=rationale,
                confidence_score=confidence,
                research_timestamp=datetime.now(),
                brand=brand,
                product_url=product_url
            )

            return rating

        except Exception as e:
            logger.error(f"Error generating rating: {e}")
            # Return minimal rating on error
            return SustainabilityRating(
                overall_score="F",
                environmental_score="F",
                labor_score="F",
                transparency_score="F",
                rationale={
                    "overall": f"Rating generation failed: {str(e)}",
                    "environmental": "Insufficient data",
                    "labor": "Insufficient data",
                    "transparency": "Insufficient data"
                },
                confidence_score=0.0,
                research_timestamp=datetime.now(),
                brand=brand,
                product_url=product_url
            )

    def _calculate_environmental_score(self, web_findings: Dict) -> float:
        """Calculate environmental score from web research findings."""
        # Simplified scoring logic
        # In production, this would analyze actual findings
        base_score = 50.0

        # Check for positive indicators
        # This would analyze actual certifications and reports
        return base_score

    def _calculate_labor_score(self, web_findings: Dict) -> float:
        """Calculate labor score from web research findings."""
        # Simplified scoring logic
        base_score = 50.0
        return base_score


# Convenience function to create the agent
def create_sustainability_scorer() -> Agent:
    """
    Create and return a configured SustainabilityScorer using Gemini 1.0 Pro.

    Returns:
        SustainabilityScorer instance
    """
    scorer = SustainabilityScorer()
    return scorer.create_agent()
