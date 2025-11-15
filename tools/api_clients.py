"""
API clients for external sustainability data sources.

Includes integration with OpenSupplyHub and other ESG data providers.
"""

import logging
from typing import Dict, List, Optional
import aiohttp
from datetime import datetime

from models.sustainability_models import (
    Certification,
    NewsArticle,
    SustainabilityDoc,
    SupplyChainAnalysis,
)

logger = logging.getLogger(__name__)


class OpenSupplyHubClient:
    """
    Client for OpenSupplyHub API.

    OpenSupplyHub provides supply chain transparency data.
    API Documentation: https://opensupplyhub.org/api/docs
    """

    BASE_URL = "https://opensupplyhub.org/api"

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize OpenSupplyHub client.

        Args:
            api_key: Optional API key for authenticated requests
        """
        self.api_key = api_key
        self.session = None

    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()

    async def search_facilities(
        self,
        company_name: str,
        limit: int = 20
    ) -> Dict:
        """
        Search for facilities associated with a company.

        Args:
            company_name: Company/brand name to search
            limit: Maximum number of results

        Returns:
            Dictionary with facility information
        """
        if not self.session:
            raise RuntimeError("Session not initialized. Use async context manager.")

        try:
            params = {
                "q": company_name,
                "page_size": limit,
            }

            headers = {}
            if self.api_key:
                headers["Authorization"] = f"Token {self.api_key}"

            async with self.session.get(
                f"{self.BASE_URL}/facilities/",
                params=params,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return self._parse_facilities_response(data, company_name)
                else:
                    logger.warning(
                        f"OpenSupplyHub API returned status {response.status}"
                    )
                    return self._empty_response(company_name)

        except aiohttp.ClientError as e:
            logger.error(f"Error connecting to OpenSupplyHub: {e}")
            return self._empty_response(company_name)

        except Exception as e:
            logger.error(f"Unexpected error searching facilities: {e}")
            return self._empty_response(company_name)

    def _parse_facilities_response(
        self,
        data: Dict,
        company_name: str
    ) -> Dict:
        """Parse response from facilities API."""
        features = data.get("features", [])

        if not features:
            return self._empty_response(company_name)

        # Extract geographic regions
        regions = set()
        for feature in features:
            properties = feature.get("properties", {})
            country = properties.get("country_name")
            if country:
                regions.add(country)

        # Assess transparency
        num_facilities = len(features)
        transparency_score = self._calculate_transparency_score(num_facilities)

        # Identify risk factors
        risk_factors = self._identify_risk_factors(features)

        return {
            "num_suppliers": num_facilities,
            "geographic_regions": list(regions),
            "transparency_score": transparency_score,
            "risk_factors": risk_factors,
        }

    def _empty_response(self, company_name: str) -> Dict:
        """Return empty response structure."""
        return {
            "num_suppliers": 0,
            "geographic_regions": [],
            "transparency_score": 0.0,
            "risk_factors": ["No supply chain data available"],
        }

    def _calculate_transparency_score(self, num_facilities: int) -> float:
        """
        Calculate transparency score based on disclosed facilities.

        Args:
            num_facilities: Number of facilities disclosed

        Returns:
            Score from 0-100
        """
        if num_facilities == 0:
            return 0.0
        elif num_facilities < 5:
            return 25.0
        elif num_facilities < 20:
            return 50.0
        elif num_facilities < 50:
            return 75.0
        else:
            return 95.0

    def _identify_risk_factors(self, features: List[Dict]) -> List[str]:
        """
        Identify potential risk factors in supply chain.

        Args:
            features: List of facility features from API

        Returns:
            List of identified risk factors
        """
        risk_factors = []

        # Check for high-risk countries (simplified - would use real risk database)
        high_risk_indicators = ["limited transparency", "multiple jurisdictions"]

        countries = set()
        for feature in features:
            properties = feature.get("properties", {})
            country = properties.get("country_name")
            if country:
                countries.add(country)

        if len(countries) > 10:
            risk_factors.append("Complex multi-country supply chain")

        if not risk_factors:
            risk_factors.append("Standard supply chain risks")

        return risk_factors


class CertificationChecker:
    """Check for sustainability certifications."""

    KNOWN_CERTIFICATIONS = {
        "B Corp": {
            "org": "B Lab",
            "description": "Meets high standards of social and environmental performance"
        },
        "Fair Trade": {
            "org": "Fair Trade USA",
            "description": "Ensures fair wages and working conditions"
        },
        "LEED": {
            "org": "U.S. Green Building Council",
            "description": "Leadership in Energy and Environmental Design"
        },
        "FSC": {
            "org": "Forest Stewardship Council",
            "description": "Responsible forest management"
        },
        "GOTS": {
            "org": "Global Organic Textile Standard",
            "description": "Organic status of textiles"
        },
        "Cradle to Cradle": {
            "org": "Cradle to Cradle Products Innovation Institute",
            "description": "Products designed for circular economy"
        },
    }

    async def check_certifications(
        self,
        company_name: str,
        description: str
    ) -> List[Certification]:
        """
        Check for mentions of sustainability certifications.

        Args:
            company_name: Company name
            description: Text to analyze for certifications

        Returns:
            List of Certification objects
        """
        certifications = []
        description_lower = description.lower()

        for cert_name, cert_info in self.KNOWN_CERTIFICATIONS.items():
            if cert_name.lower() in description_lower:
                certifications.append(
                    Certification(
                        name=cert_name,
                        issuing_organization=cert_info["org"],
                        description=cert_info["description"],
                        verified=False  # Would need actual verification
                    )
                )

        return certifications


async def get_supply_chain_data(company_name: str) -> Dict:
    """
    Get supply chain transparency data for a company.

    This is designed to be used as a tool by agents.

    Args:
        company_name: Name of the company

    Returns:
        Dictionary with supply chain information
    """
    async with OpenSupplyHubClient() as client:
        data = await client.search_facilities(company_name)

        return {
            "company": company_name,
            "num_suppliers": data["num_suppliers"],
            "regions": data["geographic_regions"],
            "transparency_score": data["transparency_score"],
            "risk_factors": data["risk_factors"],
        }


async def search_sustainability_news(
    company_name: str,
    max_results: int = 5
) -> List[Dict]:
    """
    Search for recent news about company's sustainability practices.

    This is designed to be used as a tool by agents.

    Args:
        company_name: Company name
        max_results: Maximum number of articles to return

    Returns:
        List of news article summaries
    """
    # Note: In production, this would integrate with a news API
    # For now, return mock structure to demonstrate the pattern

    return [
        {
            "title": f"{company_name} sustainability news would appear here",
            "url": "https://example.com/news",
            "summary": "This would contain actual news article content",
            "date": datetime.now().isoformat(),
            "sentiment": "neutral"
        }
    ]
