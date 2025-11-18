"""
Tool Result Validator with Cross-Verification.

This module provides intelligent validation of tool outputs using Gemini AI,
cross-referencing multiple sources, and detecting data anomalies.

DEMONSTRATES: Advanced Tool Use + Evaluation/Guardrails
INTEGRATION: Validates outputs from existing tool implementations
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import google.generativeai as genai

from models.tool_models import (
    ConsensusResult,
    DataAnomaly,
    ToolResult,
    ValidationResult,
)

logger = logging.getLogger(__name__)


class ToolResultValidator:
    """
    Validate and cross-verify tool results using:
    - Gemini AI for fact-checking
    - Multi-source consensus verification
    - Anomaly detection
    - Data freshness checks
    """

    def __init__(
        self,
        gemini_model: str = "gemini-2.5-flash",
        min_confidence_threshold: float = 0.6
    ):
        """
        Initialize the Tool Result Validator.

        Args:
            gemini_model: Gemini model to use for validation
            min_confidence_threshold: Minimum confidence for valid results
        """
        self.gemini_model = gemini_model
        self.min_confidence_threshold = min_confidence_threshold

        self.validation_rules: Dict[str, Dict] = {}

        # Initialize validation rules
        self._initialize_validation_rules()

        logger.info(
            f"Initialized ToolResultValidator with model {gemini_model}, "
            f"min confidence {min_confidence_threshold}"
        )

    def _initialize_validation_rules(self) -> None:
        """Initialize validation rules for different data types."""
        self.validation_rules = {
            "sustainability_score": {
                "type": "numeric",
                "min": 0,
                "max": 100,
                "check_outliers": True
            },
            "carbon_emissions": {
                "type": "numeric",
                "min": 0,
                "unit_required": True,
                "check_freshness": True
            },
            "certification": {
                "type": "string",
                "verify_source": True,
                "known_values": [
                    "B Corp",
                    "Fair Trade",
                    "LEED",
                    "FSC",
                    "Organic",
                    "Carbon Neutral"
                ]
            },
            "date": {
                "type": "date",
                "max_age_days": 730,  # 2 years
                "future_check": True
            }
        }

    async def validate_web_scraping_results(
        self,
        scraped_data: Dict,
        source_url: str
    ) -> ValidationResult:
        """
        Validate web scraping results for consistency and quality.

        Args:
            scraped_data: Data scraped from website
            source_url: URL that was scraped

        Returns:
            ValidationResult with validation outcome
        """
        logger.info(f"Validating scraped data from {source_url}")

        anomalies = []
        confidence_factors = []

        # Check data completeness
        if not scraped_data or len(scraped_data) == 0:
            return ValidationResult(
                is_valid=False,
                confidence_score=0.0,
                validation_method="completeness_check",
                cross_reference_sources=[source_url],
                anomalies_detected=["No data scraped"],
                details={"error": "Empty or missing data"}
            )

        # Check for data freshness
        freshness_check = self._check_data_freshness(scraped_data)
        if not freshness_check["is_fresh"]:
            anomalies.append(freshness_check["message"])
            confidence_factors.append(0.7)
        else:
            confidence_factors.append(1.0)

        # Use Gemini to fact-check key claims
        fact_check_result = await self._gemini_fact_check(
            scraped_data,
            source_url
        )

        confidence_factors.append(fact_check_result["confidence"])

        if not fact_check_result["consistent"]:
            anomalies.extend(fact_check_result["issues"])

        # Check for suspicious patterns
        pattern_anomalies = self._detect_suspicious_patterns(scraped_data)
        if pattern_anomalies:
            anomalies.extend([a["description"] for a in pattern_anomalies])
            confidence_factors.append(0.6)
        else:
            confidence_factors.append(1.0)

        # Calculate overall confidence
        confidence_score = sum(confidence_factors) / len(confidence_factors)

        is_valid = (
            confidence_score >= self.min_confidence_threshold and
            len(anomalies) < 3  # Allow up to 2 minor anomalies
        )

        logger.info(
            f"Validation complete: valid={is_valid}, "
            f"confidence={confidence_score:.2f}, "
            f"anomalies={len(anomalies)}"
        )

        return ValidationResult(
            is_valid=is_valid,
            confidence_score=confidence_score,
            validation_method="multi_check",
            cross_reference_sources=[source_url],
            anomalies_detected=anomalies,
            details={
                "fact_check": fact_check_result,
                "freshness_check": freshness_check,
                "pattern_check": pattern_anomalies
            }
        )

    def _check_data_freshness(self, data: Dict) -> Dict[str, Any]:
        """Check if data appears to be recent and fresh."""
        current_year = datetime.now().year

        # Look for date fields
        date_fields = ["date", "published", "updated", "timestamp", "year"]

        found_dates = []

        for key, value in data.items():
            key_lower = key.lower()

            if any(date_field in key_lower for date_field in date_fields):
                # Try to extract year
                if isinstance(value, (int, float)):
                    year = int(value)
                    if 2000 <= year <= current_year:
                        found_dates.append(year)
                elif isinstance(value, str):
                    # Try to find a year in the string
                    import re
                    years = re.findall(r'\b(20\d{2})\b', value)
                    found_dates.extend([int(y) for y in years])

        if not found_dates:
            return {
                "is_fresh": True,  # Can't determine, assume OK
                "message": "No date information found"
            }

        most_recent_year = max(found_dates)
        age = current_year - most_recent_year

        if age > 2:
            return {
                "is_fresh": False,
                "message": f"Data may be outdated (most recent year: {most_recent_year})"
            }

        return {
            "is_fresh": True,
            "message": f"Data appears fresh (most recent year: {most_recent_year})"
        }

    async def _gemini_fact_check(
        self,
        data: Dict,
        source_url: str
    ) -> Dict[str, Any]:
        """Use Gemini to fact-check data for consistency."""

        prompt = f"""You are a fact-checker for sustainability data.

SOURCE: {source_url}

DATA TO VERIFY:
{json.dumps(data, indent=2, default=str)}

Please analyze this data for:
1. Internal consistency (do the claims make sense together?)
2. Plausibility (are the numbers and claims realistic?)
3. Red flags (any suspicious or exaggerated claims?)

Return a JSON object with this structure:
{{
  "consistent": true/false,
  "confidence": 0.0-1.0,
  "issues": ["list", "of", "any", "issues", "found"],
  "notes": "explanation of your assessment"
}}
"""

        try:
            model = genai.GenerativeModel(self.gemini_model)
            response = model.generate_content(prompt)

            # Parse JSON response
            response_text = response.text.strip()

            # Extract JSON from response
            start = response_text.find('{')
            end = response_text.rfind('}') + 1

            if start != -1 and end > start:
                json_str = response_text[start:end]
                result = json.loads(json_str)

                return {
                    "consistent": result.get("consistent", True),
                    "confidence": result.get("confidence", 0.7),
                    "issues": result.get("issues", []),
                    "notes": result.get("notes", "")
                }

        except Exception as e:
            logger.error(f"Error in Gemini fact-check: {e}")

        # Fallback if Gemini check fails
        return {
            "consistent": True,
            "confidence": 0.5,
            "issues": [],
            "notes": "Unable to perform fact-check"
        }

    def _detect_suspicious_patterns(self, data: Dict) -> List[Dict[str, Any]]:
        """Detect suspicious patterns in data."""
        anomalies = []

        # Check for suspiciously round numbers
        for key, value in data.items():
            if isinstance(value, (int, float)):
                if value > 0 and value % 10 == 0 and value >= 100:
                    # Very round number - might be placeholder
                    anomalies.append({
                        "field": key,
                        "value": value,
                        "pattern": "suspiciously_round",
                        "description": f"Suspiciously round value in {key}: {value}"
                    })

        # Check for duplicate values
        values = [v for v in data.values() if isinstance(v, (int, float, str))]
        if len(values) != len(set(str(v) for v in values)):
            # Has duplicates
            from collections import Counter
            counts = Counter(str(v) for v in values)
            duplicates = [v for v, count in counts.items() if count > 1]

            if duplicates:
                anomalies.append({
                    "pattern": "duplicate_values",
                    "description": f"Duplicate values found: {duplicates}"
                })

        return anomalies

    async def cross_verify_sustainability_data(
        self,
        primary_source: Dict,
        secondary_sources: List[Dict]
    ) -> ConsensusResult:
        """
        Compare data from multiple sources to establish consensus.

        Args:
            primary_source: Main data source
            secondary_sources: Additional sources for verification

        Returns:
            ConsensusResult with consensus analysis
        """
        logger.info(
            f"Cross-verifying data with {len(secondary_sources)} secondary sources"
        )

        if not secondary_sources:
            # No secondary sources - return primary with low confidence
            return ConsensusResult(
                consensus_reached=False,
                confidence_score=0.5,
                agreed_data=primary_source,
                conflicting_data={},
                source_weights={"primary": 1.0},
                final_values=primary_source
            )

        # Compare each field across sources
        all_sources = [primary_source] + secondary_sources
        source_weights = self._calculate_source_weights(all_sources)

        agreed_data = {}
        conflicting_data = {}

        # Get all unique keys
        all_keys = set()
        for source in all_sources:
            all_keys.update(source.keys())

        # Compare each field
        for key in all_keys:
            values = []

            for i, source in enumerate(all_sources):
                if key in source:
                    values.append((i, source[key]))

            if len(values) <= 1:
                # Only one source has this field
                if values:
                    agreed_data[key] = values[0][1]
                continue

            # Check if values agree
            unique_values = list(set(str(v[1]) for v in values))

            if len(unique_values) == 1:
                # All sources agree
                agreed_data[key] = values[0][1]
            else:
                # Conflict detected
                conflicting_data[key] = [v[1] for v in values]

                # Use weighted voting to determine final value
                value_weights = {}
                for source_idx, value in values:
                    source_name = f"source_{source_idx}"
                    weight = source_weights.get(source_name, 1.0)

                    value_str = str(value)
                    value_weights[value_str] = value_weights.get(value_str, 0) + weight

                # Pick value with highest weight
                best_value = max(value_weights.items(), key=lambda x: x[1])[0]

                # Try to convert back to original type
                for _, value in values:
                    if str(value) == best_value:
                        agreed_data[key] = value
                        break

        # Calculate consensus confidence
        total_fields = len(all_keys)
        agreed_fields = len(agreed_data)
        conflicting_fields = len(conflicting_data)

        if total_fields > 0:
            agreement_ratio = agreed_fields / total_fields
        else:
            agreement_ratio = 0.0

        # Adjust confidence based on conflicts
        confidence_score = agreement_ratio * 0.7 + (1.0 - (conflicting_fields / max(total_fields, 1))) * 0.3

        consensus_reached = confidence_score >= 0.7 and conflicting_fields <= total_fields * 0.2

        logger.info(
            f"Consensus: {consensus_reached}, confidence={confidence_score:.2f}, "
            f"agreed={agreed_fields}, conflicting={conflicting_fields}"
        )

        return ConsensusResult(
            consensus_reached=consensus_reached,
            confidence_score=confidence_score,
            agreed_data=agreed_data,
            conflicting_data=conflicting_data,
            source_weights=source_weights,
            final_values=agreed_data
        )

    def _calculate_source_weights(self, sources: List[Dict]) -> Dict[str, float]:
        """Calculate reliability weights for each source."""
        weights = {}

        for i, source in enumerate(sources):
            source_name = f"source_{i}"

            # Primary source gets highest weight
            if i == 0:
                weights[source_name] = 1.0
                continue

            # Weight based on completeness
            completeness = len([v for v in source.values() if v]) / max(len(source), 1)

            # Weight based on data types (structured data is more reliable)
            structured_ratio = sum(
                1 for v in source.values()
                if isinstance(v, (int, float, bool))
            ) / max(len(source), 1)

            weights[source_name] = 0.5 + (completeness * 0.3) + (structured_ratio * 0.2)

        return weights

    async def detect_data_anomalies(
        self,
        tool_results: List[ToolResult]
    ) -> List[DataAnomaly]:
        """
        Identify outliers or suspicious patterns in tool outputs.

        Args:
            tool_results: List of ToolResult objects to analyze

        Returns:
            List of detected anomalies
        """
        logger.info(f"Detecting anomalies in {len(tool_results)} tool results")

        anomalies = []

        # Check for tools that took unusually long
        execution_times = [r.execution_time for r in tool_results if r.success]

        if len(execution_times) > 2:
            avg_time = sum(execution_times) / len(execution_times)
            max_time = max(execution_times)

            if max_time > avg_time * 3:
                # One tool took 3x longer than average
                slow_tools = [
                    r.tool_name for r in tool_results
                    if r.success and r.execution_time > avg_time * 2
                ]

                for tool_name in slow_tools:
                    anomalies.append(DataAnomaly(
                        anomaly_type="outlier",
                        severity="medium",
                        affected_field="execution_time",
                        description=f"Tool {tool_name} took unusually long to execute",
                        suggested_action="Review tool implementation or network conditions"
                    ))

        # Check for inconsistent results
        successful_results = [r for r in tool_results if r.success and r.result]

        if len(successful_results) >= 2:
            # Look for contradictions in numeric values
            numeric_fields = {}

            for result in successful_results:
                if result.result:
                    for key, value in result.result.items():
                        if isinstance(value, (int, float)):
                            if key not in numeric_fields:
                                numeric_fields[key] = []
                            numeric_fields[key].append(value)

            # Check for high variance in numeric fields
            for field, values in numeric_fields.items():
                if len(values) >= 2:
                    avg = sum(values) / len(values)
                    max_val = max(values)
                    min_val = min(values)

                    if avg > 0 and (max_val / avg > 2 or min_val / avg < 0.5):
                        anomalies.append(DataAnomaly(
                            anomaly_type="inconsistency",
                            severity="high",
                            affected_field=field,
                            description=f"Large variance in {field} across sources: {values}",
                            suggested_action="Cross-verify data with additional sources"
                        ))

        # Check for missing critical data
        for result in tool_results:
            if result.success and result.result:
                if len(result.result) < 3:
                    anomalies.append(DataAnomaly(
                        anomaly_type="missing_data",
                        severity="low",
                        affected_field=result.tool_name,
                        description=f"Tool {result.tool_name} returned minimal data",
                        suggested_action="Consider using additional tools"
                    ))

        logger.info(f"Detected {len(anomalies)} anomalies")

        return anomalies

    async def validate_and_enhance_results(
        self,
        tool_results: List[ToolResult],
        expected_fields: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Comprehensive validation and enhancement of tool results.

        Args:
            tool_results: Results to validate
            expected_fields: Optional list of fields that should be present

        Returns:
            Enhanced validation report
        """
        # Detect anomalies
        anomalies = await self.detect_data_anomalies(tool_results)

        # Extract successful results
        successful_data = [
            r.result for r in tool_results
            if r.success and r.result
        ]

        # Cross-verify if multiple sources
        if len(successful_data) > 1:
            consensus = await self.cross_verify_sustainability_data(
                successful_data[0],
                successful_data[1:]
            )
        else:
            consensus = None

        # Check for missing expected fields
        missing_fields = []
        if expected_fields and successful_data:
            all_fields = set()
            for data in successful_data:
                all_fields.update(data.keys())

            missing_fields = [
                field for field in expected_fields
                if field not in all_fields
            ]

        # Calculate overall validation score
        validation_score = self._calculate_validation_score(
            tool_results,
            anomalies,
            missing_fields
        )

        return {
            "validation_score": validation_score,
            "anomalies": [a.model_dump() for a in anomalies],
            "consensus": consensus.model_dump() if consensus else None,
            "missing_fields": missing_fields,
            "total_tools": len(tool_results),
            "successful_tools": len([r for r in tool_results if r.success]),
            "failed_tools": len([r for r in tool_results if not r.success])
        }

    def _calculate_validation_score(
        self,
        tool_results: List[ToolResult],
        anomalies: List[DataAnomaly],
        missing_fields: List[str]
    ) -> float:
        """Calculate overall validation score (0.0 to 1.0)."""
        score = 1.0

        # Penalty for failed tools
        total_tools = len(tool_results)
        if total_tools > 0:
            success_rate = len([r for r in tool_results if r.success]) / total_tools
            score *= success_rate

        # Penalty for anomalies
        severity_penalties = {
            "low": 0.05,
            "medium": 0.10,
            "high": 0.20,
            "critical": 0.30
        }

        for anomaly in anomalies:
            penalty = severity_penalties.get(anomaly.severity, 0.10)
            score -= penalty

        # Penalty for missing fields
        if missing_fields:
            score -= len(missing_fields) * 0.05

        return max(0.0, min(1.0, score))
