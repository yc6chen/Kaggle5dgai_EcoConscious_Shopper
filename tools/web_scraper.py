"""
Web scraping tools for extracting sustainability information from company websites.

Uses Playwright for robust browser automation and BeautifulSoup for HTML parsing.
"""

import asyncio
import logging
from typing import Dict, List, Optional
from urllib.parse import urlparse

from bs4 import BeautifulSoup
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout

from models.sustainability_models import CompanyESGData

logger = logging.getLogger(__name__)


class WebScraper:
    """Web scraper for sustainability and ESG information."""

    def __init__(self):
        self.browser = None
        self.playwright = None

    async def __aenter__(self):
        """Async context manager entry."""
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(headless=True)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()

    async def scrape_company_esg_page(
        self,
        company_name: str,
        url: Optional[str] = None
    ) -> CompanyESGData:
        """
        Scrape ESG/sustainability information from company website.

        Args:
            company_name: Name of the company
            url: Optional specific URL to scrape. If not provided, will search for
                 sustainability page

        Returns:
            CompanyESGData containing extracted information

        Raises:
            ValueError: If scraping fails or page not found
        """
        try:
            if not url:
                # Try common sustainability page URLs
                domain = self._get_company_domain(company_name)
                potential_urls = [
                    f"https://{domain}/sustainability",
                    f"https://{domain}/esg",
                    f"https://{domain}/responsibility",
                    f"https://{domain}/about/sustainability",
                ]
            else:
                potential_urls = [url]

            for target_url in potential_urls:
                try:
                    data = await self._scrape_url(target_url)
                    if data:
                        return CompanyESGData(
                            company_name=company_name,
                            environmental_score=data.get("environmental_score"),
                            social_score=data.get("social_score"),
                            governance_score=data.get("governance_score"),
                            data_source=target_url
                        )
                except Exception as e:
                    logger.debug(f"Failed to scrape {target_url}: {e}")
                    continue

            # If no URL worked, return minimal data
            logger.warning(f"Could not find sustainability page for {company_name}")
            return CompanyESGData(
                company_name=company_name,
                data_source="not_found"
            )

        except Exception as e:
            logger.error(f"Error scraping company ESG data: {e}")
            raise ValueError(f"Failed to scrape ESG data for {company_name}: {e}")

    async def _scrape_url(self, url: str) -> Optional[Dict]:
        """
        Internal method to scrape a specific URL.

        Args:
            url: URL to scrape

        Returns:
            Dictionary containing extracted data, or None if failed
        """
        if not self.browser:
            raise RuntimeError("Browser not initialized. Use async context manager.")

        page = await self.browser.new_page()

        try:
            # Navigate to page with timeout
            await page.goto(url, wait_until="domcontentloaded", timeout=15000)

            # Wait for content to load
            await page.wait_for_timeout(2000)

            # Get page content
            content = await page.content()
            soup = BeautifulSoup(content, "html.parser")

            # Extract text content
            text = soup.get_text(separator=" ", strip=True).lower()

            # Look for sustainability indicators
            indicators = {
                "carbon_neutral": any(
                    phrase in text
                    for phrase in ["carbon neutral", "net zero", "carbon negative"]
                ),
                "renewable_energy": any(
                    phrase in text
                    for phrase in ["renewable energy", "100% renewable", "solar power"]
                ),
                "recycling": any(
                    phrase in text
                    for phrase in ["recycling program", "circular economy", "zero waste"]
                ),
                "fair_labor": any(
                    phrase in text
                    for phrase in ["fair labor", "living wage", "worker rights"]
                ),
                "certifications": self._extract_certifications(text),
            }

            # Calculate estimated scores based on indicators
            # Note: In production, this would be more sophisticated
            environmental_score = self._calculate_score(
                indicators, ["carbon_neutral", "renewable_energy", "recycling"]
            )
            social_score = self._calculate_score(
                indicators, ["fair_labor"]
            )

            return {
                "environmental_score": environmental_score,
                "social_score": social_score,
                "governance_score": None,  # Would need different indicators
                "indicators": indicators,
            }

        except PlaywrightTimeout:
            logger.warning(f"Timeout loading {url}")
            return None

        except Exception as e:
            logger.error(f"Error scraping {url}: {e}")
            return None

        finally:
            await page.close()

    def _get_company_domain(self, company_name: str) -> str:
        """
        Attempt to determine company domain from name.

        Args:
            company_name: Company name

        Returns:
            Estimated domain name

        Note: This is a simple heuristic. In production, use a company
              database or API.
        """
        # Remove common suffixes
        clean_name = (
            company_name.lower()
            .replace(" inc.", "")
            .replace(" llc", "")
            .replace(" corp.", "")
            .replace(" ", "")
            .strip()
        )

        return f"{clean_name}.com"

    def _extract_certifications(self, text: str) -> List[str]:
        """
        Extract mention of sustainability certifications from text.

        Args:
            text: Text to analyze

        Returns:
            List of certification names found
        """
        cert_keywords = {
            "B Corp": "b corp",
            "Fair Trade": "fair trade",
            "LEED": "leed certified",
            "ISO 14001": "iso 14001",
            "FSC": "fsc certified",
            "Energy Star": "energy star",
        }

        found = []
        for cert_name, keyword in cert_keywords.items():
            if keyword in text:
                found.append(cert_name)

        return found

    def _calculate_score(
        self,
        indicators: Dict,
        relevant_keys: List[str]
    ) -> Optional[float]:
        """
        Calculate a score based on indicators.

        Args:
            indicators: Dictionary of indicators
            relevant_keys: Which indicators to consider

        Returns:
            Score from 0-100, or None if insufficient data
        """
        if not relevant_keys:
            return None

        true_count = sum(
            1 for key in relevant_keys
            if indicators.get(key, False)
        )

        # Convert to 0-100 scale
        score = (true_count / len(relevant_keys)) * 100

        return round(score, 1)


async def scrape_company_sustainability(company_name: str) -> Dict:
    """
    Convenience function to scrape company sustainability information.

    This is designed to be used as a tool by agents.

    Args:
        company_name: Name of company to research

    Returns:
        Dictionary with sustainability findings
    """
    async with WebScraper() as scraper:
        esg_data = await scraper.scrape_company_esg_page(company_name)

        return {
            "company": company_name,
            "environmental_score": esg_data.environmental_score,
            "social_score": esg_data.social_score,
            "governance_score": esg_data.governance_score,
            "data_source": esg_data.data_source,
        }
