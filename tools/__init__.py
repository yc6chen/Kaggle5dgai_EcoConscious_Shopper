"""Tools for the Eco-Conscious Shopper agent system."""

from .api_clients import (
    CertificationChecker,
    OpenSupplyHubClient,
    get_supply_chain_data,
    search_sustainability_news,
)
from .web_scraper import WebScraper, scrape_company_sustainability

# Enhanced tool capabilities
from .dynamic_tool_selector import DynamicToolSelector
from .parallel_executor import ParallelToolExecutor
from .result_validator import ToolResultValidator

__all__ = [
    # Original tools
    "CertificationChecker",
    "OpenSupplyHubClient",
    "WebScraper",
    "get_supply_chain_data",
    "scrape_company_sustainability",
    "search_sustainability_news",
    # Enhanced tools
    "DynamicToolSelector",
    "ParallelToolExecutor",
    "ToolResultValidator",
]
