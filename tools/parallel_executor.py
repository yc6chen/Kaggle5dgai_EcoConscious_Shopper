"""
Parallel Tool Execution with Timeout Management.

This module provides robust concurrent tool execution with proper resource management,
timeout handling, and graceful failure recovery.

DEMONSTRATES: Advanced Tool Use + Performance Optimization
INTEGRATION: Works with existing agent tool calling patterns
"""

import asyncio
import logging
import time
from typing import Any, Callable, Dict, List, Optional

from models.tool_models import ParallelExecutionResult, ToolCall, ToolResult

logger = logging.getLogger(__name__)


class ParallelToolExecutor:
    """
    Execute multiple tools concurrently with:
    - Individual timeout management
    - Resource pooling (semaphore-based)
    - Graceful partial failure handling
    - Automatic fallback execution
    """

    def __init__(
        self,
        max_workers: int = 5,
        default_timeout: int = 30
    ):
        """
        Initialize the Parallel Tool Executor.

        Args:
            max_workers: Maximum number of concurrent tool executions
            default_timeout: Default timeout in seconds for each tool
        """
        self.semaphore = asyncio.Semaphore(max_workers)
        self.default_timeout = default_timeout
        self.max_workers = max_workers

        # Registry of available tool functions
        self._tool_functions: Dict[str, Callable] = {}

        logger.info(
            f"Initialized ParallelToolExecutor with {max_workers} workers, "
            f"{default_timeout}s default timeout"
        )

    def register_tool(self, tool_name: str, tool_function: Callable) -> None:
        """
        Register a tool function for parallel execution.

        Args:
            tool_name: Name of the tool
            tool_function: Async function to execute
        """
        self._tool_functions[tool_name] = tool_function
        logger.debug(f"Registered tool: {tool_name}")

    async def execute_tools_parallel(
        self,
        tools: List[ToolCall]
    ) -> ParallelExecutionResult:
        """
        Execute multiple tools concurrently with proper resource management.

        Args:
            tools: List of ToolCall objects to execute

        Returns:
            ParallelExecutionResult with aggregated results
        """
        if not tools:
            return ParallelExecutionResult(
                successful_tools={},
                failed_tools={},
                overall_status="complete",
                total_execution_time=0.0,
                total_cost=0.0
            )

        start_time = time.time()

        # Create tasks for each tool
        tasks = [
            self._execute_single_tool(tool_call)
            for tool_call in tools
        ]

        # Execute all tools concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Aggregate results
        successful_tools: Dict[str, ToolResult] = {}
        failed_tools: Dict[str, str] = {}
        total_cost = 0.0

        for tool_call, result in zip(tools, results):
            if isinstance(result, Exception):
                # Task raised an exception
                failed_tools[tool_call.tool_name] = str(result)
                logger.error(
                    f"Tool {tool_call.tool_name} failed with exception: {result}"
                )
            elif isinstance(result, ToolResult):
                if result.success:
                    successful_tools[tool_call.tool_name] = result
                    total_cost += result.cost
                else:
                    failed_tools[tool_call.tool_name] = result.error or "Unknown error"
            else:
                failed_tools[tool_call.tool_name] = f"Unexpected result type: {type(result)}"

        # Determine overall status
        if not failed_tools:
            overall_status = "complete"
        elif successful_tools:
            overall_status = "partial"
        else:
            overall_status = "failed"

        total_time = time.time() - start_time

        logger.info(
            f"Parallel execution complete: {len(successful_tools)} succeeded, "
            f"{len(failed_tools)} failed in {total_time:.2f}s"
        )

        return ParallelExecutionResult(
            successful_tools=successful_tools,
            failed_tools=failed_tools,
            overall_status=overall_status,
            total_execution_time=total_time,
            total_cost=total_cost
        )

    async def _execute_single_tool(self, tool_call: ToolCall) -> ToolResult:
        """
        Execute a single tool with timeout and resource management.

        Args:
            tool_call: ToolCall to execute

        Returns:
            ToolResult with execution outcome
        """
        # Acquire semaphore to limit concurrency
        async with self.semaphore:
            timeout = tool_call.timeout or self.default_timeout
            start_time = time.time()

            try:
                # Get the tool function
                if tool_call.tool_name not in self._tool_functions:
                    raise ValueError(
                        f"Tool '{tool_call.tool_name}' not registered. "
                        f"Available tools: {list(self._tool_functions.keys())}"
                    )

                tool_function = self._tool_functions[tool_call.tool_name]

                # Execute with timeout
                result = await asyncio.wait_for(
                    tool_function(**tool_call.parameters),
                    timeout=timeout
                )

                execution_time = time.time() - start_time

                # Estimate cost (simplified - could be more sophisticated)
                estimated_cost = self._estimate_cost(
                    tool_call.tool_name,
                    execution_time
                )

                return ToolResult(
                    tool_name=tool_call.tool_name,
                    success=True,
                    result=result if isinstance(result, dict) else {"data": result},
                    error=None,
                    execution_time=execution_time,
                    cost=estimated_cost
                )

            except asyncio.TimeoutError:
                execution_time = time.time() - start_time
                error_msg = f"Tool execution timed out after {timeout}s"

                logger.warning(f"{tool_call.tool_name}: {error_msg}")

                return ToolResult(
                    tool_name=tool_call.tool_name,
                    success=False,
                    result=None,
                    error=error_msg,
                    execution_time=execution_time,
                    cost=0.0
                )

            except Exception as e:
                execution_time = time.time() - start_time
                error_msg = f"Tool execution failed: {str(e)}"

                logger.error(f"{tool_call.tool_name}: {error_msg}", exc_info=True)

                return ToolResult(
                    tool_name=tool_call.tool_name,
                    success=False,
                    result=None,
                    error=error_msg,
                    execution_time=execution_time,
                    cost=0.0
                )

    def _estimate_cost(self, tool_name: str, execution_time: float) -> float:
        """
        Estimate the cost of a tool execution.

        Args:
            tool_name: Name of the tool
            execution_time: Time taken to execute

        Returns:
            Estimated cost in dollars
        """
        # Simple cost model - can be enhanced with actual pricing
        base_costs = {
            "google_search": 0.005,
            "search_sustainability_reports": 0.01,
            "scrape_company_esg_page": 0.05,
            "get_company_certifications": 0.02,
            "search_labor_practices_news": 0.01,
            "analyze_supply_chain": 0.03,
        }

        base_cost = base_costs.get(tool_name, 0.01)

        # Add time-based cost component
        time_cost = execution_time * 0.001  # $0.001 per second

        return base_cost + time_cost

    async def execute_with_fallback(
        self,
        primary_tool: ToolCall,
        fallback_tools: List[ToolCall]
    ) -> ToolResult:
        """
        Execute primary tool, fall back to alternatives if failure occurs.

        Args:
            primary_tool: Primary tool to execute first
            fallback_tools: List of fallback tools to try if primary fails

        Returns:
            ToolResult from the first successful tool
        """
        logger.info(
            f"Executing with fallback: primary={primary_tool.tool_name}, "
            f"fallbacks={[t.tool_name for t in fallback_tools]}"
        )

        # Try primary tool first
        result = await self._execute_single_tool(primary_tool)

        if result.success:
            logger.info(f"Primary tool {primary_tool.tool_name} succeeded")
            return result

        logger.warning(
            f"Primary tool {primary_tool.tool_name} failed: {result.error}"
        )

        # Try fallback tools in order
        for fallback_tool in fallback_tools:
            logger.info(f"Trying fallback tool: {fallback_tool.tool_name}")

            result = await self._execute_single_tool(fallback_tool)

            if result.success:
                logger.info(f"Fallback tool {fallback_tool.tool_name} succeeded")
                return result

            logger.warning(
                f"Fallback tool {fallback_tool.tool_name} failed: {result.error}"
            )

        # All tools failed
        logger.error("All tools (primary and fallbacks) failed")

        return ToolResult(
            tool_name=primary_tool.tool_name,
            success=False,
            result=None,
            error="All tools failed (primary and fallbacks)",
            execution_time=0.0,
            cost=0.0
        )

    async def validate_tool_dependencies(
        self,
        tools: List[ToolCall]
    ) -> Dict[str, bool]:
        """
        Check if required APIs/services are available before execution.

        Args:
            tools: List of tools to validate

        Returns:
            Dictionary mapping tool names to availability status
        """
        availability = {}

        for tool_call in tools:
            tool_name = tool_call.tool_name

            # Check if tool is registered
            if tool_name not in self._tool_functions:
                availability[tool_name] = False
                logger.warning(f"Tool {tool_name} not registered")
                continue

            # For now, assume all registered tools are available
            # In a real implementation, this would check API keys,
            # network connectivity, service health, etc.
            availability[tool_name] = True

        logger.info(
            f"Dependency validation: "
            f"{sum(availability.values())}/{len(tools)} tools available"
        )

        return availability

    async def execute_with_dependency_check(
        self,
        tools: List[ToolCall]
    ) -> ParallelExecutionResult:
        """
        Execute tools after validating dependencies.

        Args:
            tools: List of tools to execute

        Returns:
            ParallelExecutionResult with execution outcomes
        """
        # Validate dependencies first
        availability = await self.validate_tool_dependencies(tools)

        # Filter to only available tools
        available_tools = [
            tool for tool in tools
            if availability.get(tool.tool_name, False)
        ]

        # Track unavailable tools as failures
        unavailable_tools = {
            tool.tool_name: "Tool or dependencies not available"
            for tool in tools
            if not availability.get(tool.tool_name, False)
        }

        if not available_tools:
            logger.error("No tools available for execution")
            return ParallelExecutionResult(
                successful_tools={},
                failed_tools=unavailable_tools,
                overall_status="failed",
                total_execution_time=0.0,
                total_cost=0.0
            )

        # Execute available tools
        result = await self.execute_tools_parallel(available_tools)

        # Add unavailable tools to failed tools
        result.failed_tools.update(unavailable_tools)

        # Update overall status if needed
        if unavailable_tools and result.overall_status == "complete":
            result.overall_status = "partial"

        return result

    async def execute_with_retry(
        self,
        tool_call: ToolCall,
        max_retries: int = 3,
        backoff_factor: float = 2.0
    ) -> ToolResult:
        """
        Execute a tool with exponential backoff retry logic.

        Args:
            tool_call: Tool to execute
            max_retries: Maximum number of retry attempts
            backoff_factor: Multiplier for backoff delay

        Returns:
            ToolResult from successful execution or final failure
        """
        last_error = None

        for attempt in range(max_retries + 1):
            if attempt > 0:
                # Calculate backoff delay
                delay = backoff_factor ** (attempt - 1)
                logger.info(
                    f"Retry attempt {attempt}/{max_retries} for {tool_call.tool_name} "
                    f"after {delay}s delay"
                )
                await asyncio.sleep(delay)

            result = await self._execute_single_tool(tool_call)

            if result.success:
                if attempt > 0:
                    logger.info(
                        f"Tool {tool_call.tool_name} succeeded on retry {attempt}"
                    )
                return result

            last_error = result.error

        # All retries exhausted
        logger.error(
            f"Tool {tool_call.tool_name} failed after {max_retries} retries"
        )

        return ToolResult(
            tool_name=tool_call.tool_name,
            success=False,
            result=None,
            error=f"Failed after {max_retries} retries. Last error: {last_error}",
            execution_time=0.0,
            cost=0.0
        )

    def get_stats(self) -> Dict[str, Any]:
        """Get executor statistics."""
        return {
            "max_workers": self.max_workers,
            "default_timeout": self.default_timeout,
            "registered_tools": list(self._tool_functions.keys()),
            "tool_count": len(self._tool_functions)
        }
