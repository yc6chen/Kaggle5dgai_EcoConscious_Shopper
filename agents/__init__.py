"""Agent implementations for the Eco-Conscious Shopper system."""

from .research_coordinator import ResearchCoordinator, extract_brand_from_url
from .web_research_agent import WebResearchAgent, create_web_research_agent
from .supply_chain_agent import SupplyChainAgent, create_supply_chain_agent
from .sustainability_scorer import SustainabilityScorer, create_sustainability_scorer

__all__ = [
    "ResearchCoordinator",
    "WebResearchAgent",
    "SupplyChainAgent",
    "SustainabilityScorer",
    "extract_brand_from_url",
    "create_web_research_agent",
    "create_supply_chain_agent",
    "create_sustainability_scorer",
]
