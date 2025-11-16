# Testing Guide for Eco-Conscious Shopper

This directory contains comprehensive tests for the Eco-Conscious Shopper multi-agent system.

## Test Structure

```
tests/
├── unit/               # Unit tests for individual components
│   ├── test_models.py              # Pydantic model tests
│   ├── test_coordinator.py         # ResearchCoordinator tests
│   └── test_sustainability_scorer.py  # SustainabilityScorer tests
├── integration/        # Integration tests for workflows
│   ├── test_api.py                 # FastAPI endpoint tests
│   └── test_multi_agent_workflow.py  # Multi-agent workflow tests
├── data/              # Test data
│   └── sample_products.json        # Sample product data
└── conftest.py        # Shared pytest fixtures
```

## Running Tests

### Prerequisites

1. Install test dependencies:
```bash
pip install -r requirements.txt
```

2. Ensure `.env` file is configured with valid API credentials

### Quick Test Commands

**Run all tests:**
```bash
pytest
```

**Run only unit tests:**
```bash
pytest tests/unit/
```

**Run only integration tests:**
```bash
pytest tests/integration/
```

**Run with coverage report:**
```bash
pytest --cov=agents --cov=models --cov=tools --cov-report=html --cov-report=term
```

**Run tests matching a pattern:**
```bash
pytest -k "test_sustainability"
```

**Run tests with specific markers:**
```bash
# Run only unit tests
pytest -m unit

# Run only integration tests
pytest -m integration

# Skip slow tests
pytest -m "not slow"

# Skip tests requiring API credentials
pytest -m "not requires_api"
```

**Verbose output:**
```bash
pytest -v
```

**Show print statements:**
```bash
pytest -s
```

## Test Markers

Tests are organized with the following markers:

- `@pytest.mark.unit` - Unit tests for individual components
- `@pytest.mark.integration` - Integration tests for multi-agent workflows
- `@pytest.mark.slow` - Tests that take longer to run (>5 seconds)
- `@pytest.mark.requires_api` - Tests requiring valid API credentials

## ADK Evaluation Tests

For ADK-specific evaluation using the Google ADK framework:

**Run full evaluation suite:**
```bash
adk eval --config eval_config.yaml
```

**Run quick evaluation (faster subset):**
```bash
adk eval --config eval_quick.yaml
```

**View evaluation results:**
```bash
cat eval_results/latest_results.json
```

## Test Coverage Goals

- **Unit Tests**: >80% coverage for agents, models, and tools
- **Integration Tests**: Cover all major multi-agent workflows
- **API Tests**: Test all FastAPI endpoints
- **ADK Evaluation**: Pass rate >70%

## Writing New Tests

### Unit Test Example

```python
import pytest
from agents.my_agent import MyAgent

class TestMyAgent:
    @pytest.fixture
    def agent(self):
        return MyAgent()

    @pytest.mark.unit
    def test_agent_initialization(self, agent):
        assert agent is not None
```

### Integration Test Example

```python
import pytest

class TestWorkflow:
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_full_workflow(self):
        # Test complete multi-agent workflow
        result = await run_workflow()
        assert result is not None
```

## Continuous Integration

Tests can be run in CI/CD pipelines:

```yaml
# Example GitHub Actions workflow
- name: Run tests
  run: |
    pip install -r requirements.txt
    pytest --cov=agents --cov-report=xml
```

## Troubleshooting

**Import errors:**
- Ensure you're running pytest from project root
- Check that `PYTHONPATH` includes project directory

**API credential errors:**
- Verify `.env` file exists and contains valid credentials
- Skip API-dependent tests: `pytest -m "not requires_api"`

**Async test errors:**
- Ensure `pytest-asyncio` is installed
- Check that async tests use `@pytest.mark.asyncio`

**Timeout errors:**
- Increase timeout in `pytest.ini`
- Run slow tests separately: `pytest -m slow`

## Best Practices

1. **Isolation**: Each test should be independent
2. **Fixtures**: Use pytest fixtures for common setup
3. **Markers**: Tag tests appropriately for filtering
4. **Mocking**: Mock external APIs when possible
5. **Documentation**: Add docstrings to test functions
6. **Cleanup**: Use fixtures with teardown for cleanup

## Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [Google ADK Testing Guide](https://cloud.google.com/vertex-ai/docs/adk)
- [FastAPI Testing](https://fastapi.tiangolo.com/tutorial/testing/)
