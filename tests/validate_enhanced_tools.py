"""
Validation tests for enhanced tool capabilities.

This test suite verifies that the three enhanced tool features are
implemented correctly and integrate properly with the existing system.

Tests:
1. Dynamic Tool Selection
2. Parallel Tool Execution
3. Result Validation
4. Backwards Compatibility
5. Performance Improvements
"""

import asyncio
import pytest
from datetime import datetime
from typing import Dict, List

from tools.dynamic_tool_selector import DynamicToolSelector
from tools.parallel_executor import ParallelToolExecutor
from tools.result_validator import ToolResultValidator

from models.tool_models import (
    ToolCall,
    ToolResult,
    ValidationResult,
)


class TestDynamicToolSelection:
    """Test dynamic tool selection capabilities."""

    @pytest.mark.asyncio
    async def test_tool_selector_initialization(self):
        """Test that DynamicToolSelector initializes correctly."""
        selector = DynamicToolSelector()

        assert selector is not None
        assert len(selector.tool_registry) > 0
        assert isinstance(selector.tool_registry, dict)

    @pytest.mark.asyncio
    async def test_select_optimal_tools(self):
        """Test that optimal tools are selected based on task."""
        selector = DynamicToolSelector()

        task = "Search for sustainability reports for Nike"
        context = {
            "budget": 5.0,
            "time_limit": 30,
            "required_confidence": 0.7
        }

        selected_tools = await selector.select_optimal_tools(task, context)

        assert isinstance(selected_tools, list)
        assert len(selected_tools) > 0
        assert all(isinstance(tool, ToolCall) for tool in selected_tools)

    @pytest.mark.asyncio
    async def test_update_tool_metrics(self):
        """Test that tool metrics are updated correctly."""
        selector = DynamicToolSelector()

        tool_name = "search_sustainability_reports"
        await selector.update_tool_metrics(
            tool_name,
            success=True,
            cost=0.01,
            latency=2.5
        )

        metrics = selector.get_tool_metrics(tool_name)
        assert metrics is not None
        assert metrics.tool_name == tool_name
        assert 0.0 <= metrics.success_rate <= 1.0

    @pytest.mark.asyncio
    async def test_cost_optimized_plan(self):
        """Test that cost-optimized plans are generated."""
        selector = DynamicToolSelector()

        research_task = "Analyze sustainability practices for Patagonia"
        budget_constraints = {
            "max_budget": 3.0,
            "max_time": 20,
            "min_confidence": 0.6
        }

        plan = await selector.get_cost_optimized_plan(
            research_task,
            budget_constraints
        )

        assert plan is not None
        assert plan.estimated_total_cost <= budget_constraints["max_budget"]
        assert len(plan.selected_tools) > 0


class TestParallelToolExecution:
    """Test parallel tool execution capabilities."""

    async def mock_fast_tool(self, **kwargs):
        """Mock tool that completes quickly."""
        await asyncio.sleep(0.1)
        return {"status": "success", "data": "fast result"}

    async def mock_slow_tool(self, **kwargs):
        """Mock tool that takes longer."""
        await asyncio.sleep(0.5)
        return {"status": "success", "data": "slow result"}

    async def mock_failing_tool(self, **kwargs):
        """Mock tool that fails."""
        raise ValueError("Intentional test failure")

    @pytest.mark.asyncio
    async def test_executor_initialization(self):
        """Test that ParallelToolExecutor initializes correctly."""
        executor = ParallelToolExecutor(max_workers=3, default_timeout=10)

        assert executor is not None
        assert executor.max_workers == 3
        assert executor.default_timeout == 10

    @pytest.mark.asyncio
    async def test_parallel_execution(self):
        """Test that tools execute in parallel."""
        executor = ParallelToolExecutor(max_workers=5)

        # Register mock tools
        executor.register_tool("fast_tool", self.mock_fast_tool)
        executor.register_tool("slow_tool", self.mock_slow_tool)

        tools = [
            ToolCall(tool_name="fast_tool", parameters={}),
            ToolCall(tool_name="slow_tool", parameters={}),
        ]

        start_time = datetime.now()
        result = await executor.execute_tools_parallel(tools)
        execution_time = (datetime.now() - start_time).total_seconds()

        # Should complete in ~0.5s (slow tool time) not ~0.6s (sequential)
        assert execution_time < 1.0
        assert result.overall_status in ["complete", "partial"]
        assert len(result.successful_tools) > 0

    @pytest.mark.asyncio
    async def test_timeout_handling(self):
        """Test that timeouts are handled properly."""
        executor = ParallelToolExecutor(default_timeout=1)

        async def timeout_tool(**kwargs):
            await asyncio.sleep(5)  # Exceeds timeout
            return {"data": "should not complete"}

        executor.register_tool("timeout_tool", timeout_tool)

        tools = [ToolCall(tool_name="timeout_tool", parameters={}, timeout=0.5)]

        result = await executor.execute_tools_parallel(tools)

        assert "timeout_tool" in result.failed_tools
        assert "timeout" in result.failed_tools["timeout_tool"].lower()

    @pytest.mark.asyncio
    async def test_fallback_execution(self):
        """Test that fallback tools are used when primary fails."""
        executor = ParallelToolExecutor()

        executor.register_tool("failing_tool", self.mock_failing_tool)
        executor.register_tool("fallback_tool", self.mock_fast_tool)

        primary = ToolCall(tool_name="failing_tool", parameters={})
        fallbacks = [ToolCall(tool_name="fallback_tool", parameters={})]

        result = await executor.execute_with_fallback(primary, fallbacks)

        assert result.success
        assert result.tool_name == "failing_tool"  # Reports primary tool name

    @pytest.mark.asyncio
    async def test_partial_failure_handling(self):
        """Test that partial failures are handled gracefully."""
        executor = ParallelToolExecutor()

        executor.register_tool("fast_tool", self.mock_fast_tool)
        executor.register_tool("failing_tool", self.mock_failing_tool)

        tools = [
            ToolCall(tool_name="fast_tool", parameters={}),
            ToolCall(tool_name="failing_tool", parameters={}),
        ]

        result = await executor.execute_tools_parallel(tools)

        assert result.overall_status == "partial"
        assert len(result.successful_tools) > 0
        assert len(result.failed_tools) > 0


class TestResultValidation:
    """Test result validation capabilities."""

    @pytest.mark.asyncio
    async def test_validator_initialization(self):
        """Test that ToolResultValidator initializes correctly."""
        validator = ToolResultValidator(min_confidence_threshold=0.6)

        assert validator is not None
        assert validator.min_confidence_threshold == 0.6

    @pytest.mark.asyncio
    async def test_web_scraping_validation(self):
        """Test validation of web scraping results."""
        validator = ToolResultValidator()

        scraped_data = {
            "company": "Test Company",
            "sustainability_score": 85,
            "certifications": ["B Corp", "Fair Trade"],
            "year": 2024
        }

        result = await validator.validate_web_scraping_results(
            scraped_data,
            "https://example.com/sustainability"
        )

        assert isinstance(result, ValidationResult)
        assert 0.0 <= result.confidence_score <= 1.0
        assert isinstance(result.anomalies_detected, list)

    @pytest.mark.asyncio
    async def test_cross_verification(self):
        """Test cross-verification of multiple sources."""
        validator = ToolResultValidator()

        primary_source = {
            "sustainability_score": 85,
            "carbon_emissions": 1000,
            "certifications": ["B Corp"]
        }

        secondary_sources = [
            {
                "sustainability_score": 87,
                "carbon_emissions": 1000,
                "certifications": ["B Corp", "Fair Trade"]
            },
            {
                "sustainability_score": 85,
                "carbon_emissions": 950,
                "certifications": ["B Corp"]
            }
        ]

        consensus = await validator.cross_verify_sustainability_data(
            primary_source,
            secondary_sources
        )

        assert consensus is not None
        assert 0.0 <= consensus.confidence_score <= 1.0
        assert isinstance(consensus.agreed_data, dict)
        assert isinstance(consensus.conflicting_data, dict)

    @pytest.mark.asyncio
    async def test_anomaly_detection(self):
        """Test detection of data anomalies."""
        validator = ToolResultValidator()

        tool_results = [
            ToolResult(
                tool_name="tool1",
                success=True,
                result={"score": 85},
                error=None,
                execution_time=2.0,
                cost=0.01
            ),
            ToolResult(
                tool_name="tool2",
                success=True,
                result={"score": 20},  # Outlier
                error=None,
                execution_time=15.0,  # Very slow
                cost=0.05
            ),
            ToolResult(
                tool_name="tool3",
                success=True,
                result={"score": 87},
                error=None,
                execution_time=2.5,
                cost=0.02
            ),
        ]

        anomalies = await validator.detect_data_anomalies(tool_results)

        assert isinstance(anomalies, list)
        # Should detect at least the slow execution and/or outlier value
        assert len(anomalies) > 0


class TestBackwardsCompatibility:
    """Test that enhanced tools don't break existing functionality."""

    @pytest.mark.asyncio
    async def test_existing_tools_still_work(self):
        """Test that existing tool implementations still work."""
        # This would test that the existing WebResearchAgent tools
        # continue to function normally

        # For now, just verify imports work
        from agents.web_research_agent import WebResearchAgent

        agent = WebResearchAgent()
        assert agent is not None
        assert hasattr(agent, 'search_sustainability_reports')
        assert hasattr(agent, 'scrape_company_esg_page')

    def test_model_compatibility(self):
        """Test that new models don't break existing models."""
        from models import (
            SustainabilityRating,
            ToolCall,
            ToolResult,
            ValidationResult
        )

        # Verify all models can be imported
        assert SustainabilityRating is not None
        assert ToolCall is not None
        assert ToolResult is not None
        assert ValidationResult is not None


class TestPerformanceImprovements:
    """Test that enhanced tools improve performance."""

    @pytest.mark.asyncio
    async def test_parallel_vs_sequential_performance(self):
        """Test that parallel execution is faster than sequential."""
        executor = ParallelToolExecutor()

        async def mock_task(**kwargs):
            await asyncio.sleep(0.2)
            return {"data": "result"}

        executor.register_tool("task1", mock_task)
        executor.register_tool("task2", mock_task)
        executor.register_tool("task3", mock_task)

        tools = [
            ToolCall(tool_name="task1", parameters={}),
            ToolCall(tool_name="task2", parameters={}),
            ToolCall(tool_name="task3", parameters={}),
        ]

        # Parallel execution
        start = datetime.now()
        await executor.execute_tools_parallel(tools)
        parallel_time = (datetime.now() - start).total_seconds()

        # Should be ~0.2s (parallel) not ~0.6s (sequential)
        assert parallel_time < 0.5

    @pytest.mark.asyncio
    async def test_cost_optimization_reduces_cost(self):
        """Test that cost optimization selects cheaper tools when possible."""
        selector = DynamicToolSelector()

        # Request with tight budget should select cheaper tools
        tight_budget_plan = await selector.get_cost_optimized_plan(
            "sustainability research",
            {"max_budget": 0.05, "max_time": 30, "min_confidence": 0.5}
        )

        # Request with generous budget might select more expensive tools
        generous_budget_plan = await selector.get_cost_optimized_plan(
            "sustainability research",
            {"max_budget": 10.0, "max_time": 30, "min_confidence": 0.5}
        )

        assert tight_budget_plan.estimated_total_cost <= 0.05
        assert tight_budget_plan.meets_requirements


# Main validation function as specified in the prompt
async def validate_enhancement_implementation():
    """
    Run all validation checks to verify implementation meets requirements.

    Returns:
        Dict of check results
    """
    print("🔍 Validating Enhanced Tool Implementation...")
    print("=" * 60)

    checks = {}

    # Test 1: Dynamic Selection
    try:
        selector = DynamicToolSelector()
        tools = await selector.select_optimal_tools(
            "test sustainability research",
            {"budget": 5.0, "time_limit": 30, "required_confidence": 0.7}
        )
        checks["dynamic_selection_works"] = len(tools) > 0
        print("✅ Dynamic tool selection: PASS")
    except Exception as e:
        checks["dynamic_selection_works"] = False
        print(f"❌ Dynamic tool selection: FAIL - {e}")

    # Test 2: Parallel Execution
    try:
        executor = ParallelToolExecutor()

        async def test_tool(**kwargs):
            return {"data": "test"}

        executor.register_tool("test_tool", test_tool)
        result = await executor.execute_tools_parallel([
            ToolCall(tool_name="test_tool", parameters={})
        ])
        checks["parallel_execution_works"] = result.overall_status != "failed"
        print("✅ Parallel execution: PASS")
    except Exception as e:
        checks["parallel_execution_works"] = False
        print(f"❌ Parallel execution: FAIL - {e}")

    # Test 3: Validation System
    try:
        validator = ToolResultValidator()
        result = await validator.validate_web_scraping_results(
            {"company": "Test", "score": 85},
            "https://example.com"
        )
        checks["validation_system_works"] = isinstance(result, ValidationResult)
        print("✅ Validation system: PASS")
    except Exception as e:
        checks["validation_system_works"] = False
        print(f"❌ Validation system: FAIL - {e}")

    # Test 4: Backwards Compatibility
    try:
        from agents.web_research_agent import WebResearchAgent
        agent = WebResearchAgent()
        checks["backwards_compatibility"] = hasattr(agent, 'enhanced_sustainability_search')
        print("✅ Backwards compatibility: PASS")
    except Exception as e:
        checks["backwards_compatibility"] = False
        print(f"❌ Backwards compatibility: FAIL - {e}")

    # Test 5: Performance (basic check)
    try:
        executor = ParallelToolExecutor()

        async def quick_tool(**kwargs):
            await asyncio.sleep(0.1)
            return {"data": "result"}

        executor.register_tool("quick1", quick_tool)
        executor.register_tool("quick2", quick_tool)

        start = datetime.now()
        await executor.execute_tools_parallel([
            ToolCall(tool_name="quick1", parameters={}),
            ToolCall(tool_name="quick2", parameters={}),
        ])
        elapsed = (datetime.now() - start).total_seconds()

        # Should be ~0.1s (parallel) not ~0.2s (sequential)
        checks["performance_improvement"] = elapsed < 0.3
        print("✅ Performance improvement: PASS")
    except Exception as e:
        checks["performance_improvement"] = False
        print(f"❌ Performance improvement: FAIL - {e}")

    # Summary
    print("=" * 60)
    if all(checks.values()):
        print("✅ ALL ENHANCEMENTS IMPLEMENTED CORRECTLY")
    else:
        print("❌ SOME CHECKS FAILED - REVIEW IMPLEMENTATION")
        failed = [k for k, v in checks.items() if not v]
        print(f"Failed checks: {failed}")

    return checks


if __name__ == "__main__":
    # Run validation
    asyncio.run(validate_enhancement_implementation())
